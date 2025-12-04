import json
import os
from typing import Any, Dict, List

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
        self.model = model or "local-model"
        
    def check_connection(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:
            print(f"Check connection failed: {e}")
            return False
        
    def _call_api(self, prompt: str) -> str:
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
            raise RuntimeError(f"Error calling local LLM: {e}") from e
        
    def _clean_response_text(self, raw: str) -> str:
        text = raw.strip()
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
        web_search_instruction = ""
        if use_web_search:
            web_search_instruction = """
                                    IMPORTANT: In addition to the provided content, also use your general knowledge about the topic.
                                    Integrate additional information, recent examples, accurate details, and context to create more complete flashcards.
                                    Ensure all information is accurate and verified.
                                    """
        else:
            web_search_instruction = """
                                    IMPORTANT: Base answers ONLY on the provided content. Do not add external information.
                                    """

        prompt = f"""You are an expert assistant in creating flashcards for university students. Your goal is to apply Andy Matuschak's principles to create "atomic" flashcards that foster understanding.

                    {web_search_instruction}

                    Content:
                    {content}

                    IMPORTANTE: Segui queste 5 REGOLE ASSOLUTE per OGNI flashcard che crei:
                    1.  **Scomponi (Focalizzata)**: Ogni flashcard deve riguardare UN SOLO concetto o fatto. NON creare flashcard che chiedono liste (es. "Quali sono i 3 tipi di X?"). Invece, crea 3 card separate o usa la scomposizione (es. "Un tipo di X è...").
                    2.  **Precisa**: La domanda non deve essere ambigua.
                    3.  **Chiedi il "Perché"**: Oltre ai fatti, crea domande sul "perché" un concetto funziona in un certo modo (es. "Perché l'algoritmo X usa una coda invece di uno stack?").
                    4.  **Sforzo Cognitivo**: La risposta NON deve essere intuibile dalla domanda. Evita domande Sì/No.
                    5.  **Concettuale**: Evita definizioni secche. Chiedi differenze (es. "Differenza tra X e Y"), attributi (es. "Cosa è sempre vero per X?"), o implicazioni (es. "Quale problema risolve X?").

                    Crea {num_cards} flashcard che seguono queste regole.

                    IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o formattazione.
                    Formato richiesto:
                    [{{"front": "Domanda atomica e precisa", "back": "Risposta concisa", "difficulty": "easy|medium|hard", "tags": ["tag1", "tag2"]}}]

                    Rispondi SOLO con il JSON, nessun testo aggiuntivo."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert assistant in creating educational flashcards. Always respond with valid JSON."
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
            
            if not isinstance(flashcards, list):
                raise ValueError("Response is not a JSON array")
            
            for card in flashcards:
                if 'front' not in card or 'back' not in card:
                    raise ValueError("Flashcard missing 'front' or 'back' fields")
                card.setdefault('difficulty', 'medium')
                card.setdefault('tags', [])
            
            return flashcards[:num_cards]
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"Error generating flashcards: {e}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Embeddings non supportati da questo server: {e}")
            raise NotImplementedError(
                "Questo server LLM locale non supporta la generazione di embeddings. "
                "Considera l'uso di un modello di embedding locale separato."
            )
