"""Servizio per effettuare una piccola ricerca web da integrare nel flusso RAG.

Priorità:
1. Usa Tavily se è presente `TAVILY_API_KEY`.
2. Fallback: usa Wikipedia (API pubblica) per recuperare un riassunto.
3. Se tutto fallisce ritorna lista vuota.

L'obiettivo è fornire 2-5 snippet sintetici e affidabili, NON un dump.
"""
from __future__ import annotations

import os
import re
import requests
from typing import List, Dict, Optional

try:
    # Importa opzionalmente il client Tavily (se installato)
    from tavily import TavilyClient  # type: ignore
except Exception:  # pragma: no cover - nessun errore se manca
    TavilyClient = None  # type: ignore


class WebSearchService:
    def __init__(self, max_timeout: int = 12):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.max_timeout = max_timeout
        self._tavily_client = None  # istanza client Tavily se disponibile
        if self.api_key and TavilyClient is not None:
            try:
                self._tavily_client = TavilyClient(api_key=self.api_key)
                print("[WEB] Tavily attivo: userò Tavily per le ricerche")
            except Exception:
                self._tavily_client = None
                print("[WEB] Impossibile inizializzare Tavily: fallback a Wikipedia")
        else:
            print("[WEB] TAVILY_API_KEY non presente o libreria non installata: userò Wikipedia come fallback")

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def search(self, query: str, max_results: int = 5) -> List[str]:
        """Effettua una ricerca leggera e ritorna una lista di snippet testuali.

        Args:
            query: domanda o argomento utente
            max_results: numero massimo di snippet da ritornare
        """
        query = (query or "").strip()
        if not query:
            return []

        # 1) Prova Tavily
        if self._tavily_client is not None:
            try:
                print(f"[WEB] Eseguo ricerca Tavily: '{query}' (max {max_results})")
                tavily_res: Dict = self._tavily_client.search(
                    query=query,
                    max_results=max(1, min(max_results, 8)),
                    search_depth="basic",
                )
                # Struttura attesa: {"results": [{"content": "...", ...}, ...]}
                items = tavily_res.get("results", []) or []
                snippets: List[str] = []
                for item in items:
                    content = item.get("content") or ""
                    cleaned = self._clean_text(content)
                    if cleaned:
                        snippets.append(cleaned)
                    if len(snippets) >= max_results:
                        break
                print(f"[WEB] Tavily: ottenuti {len(snippets)} snippet")
                if snippets:
                    for i, s in enumerate(snippets[:2], 1):
                        print(f"[WEB] Tavily snippet {i}: {s[:120]}...")
                    return snippets
            except Exception:
                print("[WEB] Errore Tavily: fallback a Wikipedia")

        # 2) Fallback Wikipedia (summary + sezione intro)
        print(f"[WEB] Fallback Wikipedia: '{query}' (max {max_results})")
        wiki_snippets = self._wikipedia_fallback(query, max_results)
        if wiki_snippets:
            print(f"[WEB] Wikipedia: ottenuti {len(wiki_snippets)} snippet")
            for i, s in enumerate(wiki_snippets[:2], 1):
                print(f"[WEB] Wikipedia snippet {i}: {s[:120]}...")
            return wiki_snippets

        return []

    def enrich_context_block(self, query: str, max_results: int = 5) -> str:
        """Restituisce un blocco di testo formattato da inserire nel prompt.
        """
        snippets = self.search(query, max_results=max_results)
        if not snippets:
            return ""
        lines = ["[WEB SEARCH SNIPPETS]"]
        for i, s in enumerate(snippets, start=1):
            lines.append(f"{i}. {s}")
        return "\n".join(lines)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _wikipedia_fallback(self, query: str, max_results: int) -> List[str]:
        """Usa l'API di Wikipedia per recuperare un riassunto (it + en)."""
        snippets: List[str] = []
        for lang in ("it", "en"):
            try:
                url = (
                    f"https://{lang}.wikipedia.org/w/api.php?"
                    f"action=query&prop=extracts&exintro&explaintext&format=json&titles={requests.utils.quote(query)}"
                )
                resp = requests.get(url, timeout=self.max_timeout)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    extract = page.get("extract")
                    cleaned = self._clean_text(extract)
                    if cleaned:
                        snippets.append(cleaned)
                    if len(snippets) >= max_results:
                        return snippets
            except Exception:
                continue
        return snippets

    def _clean_text(self, text: str | None) -> str:
        if not text:
            return ""
        # Rimuovi eccessi di whitespace e footnote markers
        txt = re.sub(r"\s+", " ", text).strip()
        txt = re.sub(r"\[[0-9]+\]", "", txt)  # footnotes tipo [1]
        # Taglia se troppo lungo per non inquinare il prompt
        MAX_LEN = 480
        if len(txt) > MAX_LEN:
            txt = txt[:MAX_LEN].rsplit(" ", 1)[0] + "..."
        return txt


__all__ = ["WebSearchService"]
