"""
Servizio AI unificato per LLM locali (LM Studio, Ollama) con API OpenAI-like
"""
import json
import os
from typing import List, Dict, Any
from openai import OpenAI


class LocalLLMService:
    """
    Servizio per LLM locali che espongono API OpenAI-like.
    Compatibile con:
    - LM Studio (http://127.0.0.1:1234/v1)
    - Ollama con ollama-openai-proxy
    - text-generation-webui con estensione openai
    - qualsiasi altro server OpenAI-compatibile
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = None,
        api_key: str = "not-needed"
    ):
        """
        Inizializza il servizio LLM locale.
        
        Args:
            base_url: URL del server locale (default: LM Studio)
            model: Nome del modello (opzionale, LM Studio usa quello caricato)
            api_key: API key (non necessaria per server locali, ma richiesta dal client)
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model or "local-model"  # LM Studio ignora questo se hai un modello caricato
        
    def _call_api(self, prompt: str) -> str:
        """Metodo helper per chiamare l'API del LLM locale
        
        Args:
            prompt: Prompt da inviare al modello
            
        Returns:
            Risposta del modello come stringa
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            raw_text = response.choices[0].message.content
            return raw_text.strip() if raw_text else ""
        except Exception as e:
            raise RuntimeError(f"Errore nella chiamata al LLM locale: {e}") from e
        
    def _clean_response_text(self, raw: str) -> str:
        """Pulisce la risposta da eventuali markdown code blocks"""
        text = raw.strip()
        # rimuovi code fences (```json ... ``` o ``` ... ```)
        if text.startswith('```json'):
            text = text.replace('```json', '', 1).rstrip('`').strip()
        elif text.startswith('```'):
            text = text.replace('```', '', 1).rstrip('`').strip()
        return text

    def generate_flashcards(
        self,
        content: str,
        num_cards: int = 10,
        use_web_search: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Genera flashcard dal contenuto usando l'LLM locale.
        
        Args:
            content: testo degli appunti
            num_cards: numero desiderato di card in output (max)
            use_web_search: se True, il prompt permette al modello di integrare conoscenza esterna
            
        Returns:
            Lista di dizionari con 'front', 'back', 'difficulty' e 'tags'
        """
        web_search_instruction = ""
        if use_web_search:
            web_search_instruction = """
IMPORTANTE: Oltre al contenuto fornito, utilizza anche la tua conoscenza generale sull'argomento.
Integra informazioni aggiuntive, esempi recenti, dettagli accurati e contesto per creare flashcard più complete.
Assicurati che tutte le informazioni siano accurate e verificate.
"""
        else:
            web_search_instruction = """
IMPORTANTE: Basati SOLO sul contenuto fornito. Non aggiungere informazioni esterne.
"""

        prompt = f"""Sei un assistente esperto nella creazione di flashcard per studenti universitari.
Analizza il seguente contenuto e crea {num_cards} flashcard efficaci e dettagliate.

{web_search_instruction}

Contenuto:
{content}

IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o formattazione.
Formato richiesto:
[{{"front": "domanda", "back": "risposta", "difficulty": "easy|medium|hard", "tags": ["tag1", "tag2"]}}]

Criteri:
- Domande chiare e specifiche
- Risposte complete ma concise (massimo 200 parole)
- Varietà di difficoltà (easy, medium, hard)
- Copertura dei concetti principali
- Tag pertinenti per ogni flashcard
- Le risposte devono essere in formato testo semplice, evita formattazioni complesse
- Assicurati che il JSON sia valido e ben formattato

Rispondi SOLO con il JSON, nessun testo aggiuntivo."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sei un assistente esperto nella creazione di flashcard educative. Rispondi sempre con JSON valido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            
            raw_text = response.choices[0].message.content
            cleaned = self._clean_response_text(raw_text)
            flashcards = json.loads(cleaned)
            
            # Valida che sia una lista
            if not isinstance(flashcards, list):
                raise ValueError("La risposta non è un array JSON")
            
            # Assicurati che ogni flashcard abbia i campi necessari
            for card in flashcards:
                if 'front' not in card or 'back' not in card:
                    raise ValueError("Flashcard mancante di campi 'front' o 'back'")
                # Aggiungi campi opzionali se mancanti
                card.setdefault('difficulty', 'medium')
                card.setdefault('tags', [])
            
            return flashcards[:num_cards]  # Limita al numero richiesto
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore nel parsing JSON della risposta: {e}")
        except Exception as e:
            raise RuntimeError(f"Errore nella generazione delle flashcard: {e}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings per i testi forniti.
        
        Nota: Non tutti i server locali supportano embeddings.
        LM Studio non supporta nativamente l'endpoint /embeddings.
        
        Args:
            texts: lista di testi da embedded
            
        Returns:
            Lista di vettori embedding
        """
        try:
            # Prova a usare l'endpoint embeddings se disponibile
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            # Se non supportato, ritorna embeddings fittizi
            print(f"Embeddings non supportati da questo server: {e}")
            # Ritorna vettori zero o solleva eccezione
            raise NotImplementedError(
                "Questo server LLM locale non supporta la generazione di embeddings. "
                "Considera l'uso di un modello di embedding locale separato."
            )
