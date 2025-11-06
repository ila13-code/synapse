import json
from typing import Any, Dict, List, Optional

# Questo modulo usa **solo** la libreria Python ufficiale `ollama`.
# Assicurati di avere: pip install ollama e che il daemon Ollama sia in esecuzione
try:
    import ollama
except Exception as e:
    raise ImportError(
        "La libreria 'ollama' non è disponibile. Installa con `pip install ollama` "
        "e assicurati che il daemon Ollama sia in esecuzione (https://ollama.com/install)."
    ) from e


class OllamaAIService:
    """Adapter LLM che usa Ollama per generare flashcard ed embeddings.

    Uso:
        svc = OllamaAIService(model_name='gemma3')
        cards = svc.generate_flashcards("testo degli appunti", num_cards=8)
    """

    def __init__(self, model_name: str = "gemma3"):
        self.model_name = model_name

    def _call_api(self, prompt: str) -> str:
        """Metodo helper per chiamare l'API Ollama
        
        Args:
            prompt: Prompt da inviare al modello
            
        Returns:
            Risposta del modello come stringa
        """
        try:
            resp = ollama.generate(model=self.model_name, prompt=prompt, stream=False)
            # La libreria può restituire dict o str; normalizziamo a stringa
            if isinstance(resp, dict) and 'response' in resp:
                raw_text = str(resp['response'])
            else:
                raw_text = str(resp)
            return raw_text.strip()
        except Exception as e:
            raise RuntimeError(f"Errore nella chiamata a Ollama: {e}") from e

    def _clean_response_text(self, raw: str) -> str:
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
        """Genera flashcard (lista di dict) a partire dal testo fornito.

        Args:
            content: testo degli appunti
            num_cards: numero desiderato di card in output (max)
            use_web_search: se True, il prompt permette al modello di integrare conoscenza esterna

        Restituisce:
            Lista di dizionari con almeno 'front' e 'back' e opzionalmente 'difficulty' e 'tags'.
        """
        print("Generazione flashcard con Ollama...")
        if use_web_search:
            web_search_instruction = (
                "IMPORTANTE: Oltre al contenuto fornito, utilizza anche la tua conoscenza "
                "generale sull'argomento. Integra informazioni aggiuntive e contesto quando utile."
            )
        else:
            web_search_instruction = (
                "IMPORTANTE: Basati SOLO sul contenuto fornito. Non aggiungere informazioni esterne."
            )

        prompt = f"""
Sei un assistente esperto nella creazione di flashcard per studenti universitari. Il tuo obiettivo è applicare i principi di Andy Matuschak per creare flashcard "atomiche" e che favoriscano la comprensione.

{web_search_instruction}

Contenuto:
{content}

IMPORTANTE: Segui queste 5 REGOLE ASSOLUTE per OGNI flashcard che crei:
1.  **Scomponi (Focalizzata)**: Ogni flashcard deve riguardare UN SOLO concetto o fatto. NON creare flashcard che chiedono liste (es. "Quali sono i 3 tipi di X?"). Invece, crea 3 card separate o usa la scomposizione (es. "Un tipo di X è...").
2.  **Precisa**: La domanda non deve essere ambigua.
3.  **Chiedi il "Perché"**: Oltre ai fatti, crea domande sul "perché" un concetto funziona in un certo modo (es. "Perché l'algoritmo X usa una coda invece di uno stack?").
4.  **Sforzo Cognitivo**: La risposta NON deve essere intuibile dalla domanda. Evita domande Sì/No.
5.  **Concettuale**: Evita definizioni secche. Chiedi differenze (es. "Differenza tra X e Y"), attributi (es. "Cosa è sempre vero per X?"), o implicazioni (es. "Quale problema risolve X?").

Crea {num_cards} flashcard che seguono queste regole.

IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o altra formattazione.
Formato richiesto:
[{{"front": "Domanda atomica e precisa", "back": "Risposta concisa", "difficulty": "easy|medium|hard", "tags": ["tag1"]}}]
"""

        # Chiediamo a Ollama di restituire JSON (format='json') per aumentare l'affidabilità
        try:
            resp = ollama.generate(model=self.model_name, prompt=prompt, format='json', stream=False)
        except Exception as e:
            raise RuntimeError(f"Errore nella chiamata a Ollama.generate: {e}") from e

        # La libreria può restituire dict o str; normalizziamo a stringa
        if isinstance(resp, dict) and 'response' in resp:
            raw_text = str(resp['response'])
        else:
            raw_text = str(resp)

        cleaned = self._clean_response_text(raw_text)

        # Proviamo a fare il parse JSON
        try:
            flashcards = json.loads(cleaned)
        except json.JSONDecodeError:
            # tentativo di recovery: estrai la prima lista JSON valida tra '[' e ']'
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1 and end > start:
                fragment = cleaned[start:end + 1]
                try:
                    flashcards = json.loads(fragment)
                except Exception as e:
                    raise ValueError(f"Impossibile parsare la risposta dell'AI. Estratto: {fragment[:400]}...") from e
            else:
                raise ValueError(f"Impossibile parsare la risposta dell'AI: {cleaned[:400]}")

        # Validazione e normalizzazione delle card
        validated: List[Dict[str, Any]] = []
        for card in flashcards:
            if not isinstance(card, dict):
                continue
            front = card.get('front') or card.get('question') or card.get('q')
            back = card.get('back') or card.get('answer') or card.get('a')
            if not front or not back:
                continue
            validated.append({
                'front': str(front).strip(),
                'back': str(back).strip(),
                'difficulty': card.get('difficulty', 'medium'),
                'tags': card.get('tags', []),
            })
            if len(validated) >= num_cards:
                break

        return validated

    def embed_texts(self, texts: List[str], embed_model: Optional[str] = None) -> List[List[float]]:
        """Genera embeddings per una lista di testi usando Ollama.

        Nota: il nome del modello di embedding dipende dall'installazione locale (es. 'nomic-embed-text').
        """
        model = embed_model or 'nomic-embed-text'
        try:
            emb = ollama.embed(model=model, input=texts)
            return emb
        except Exception as e:
            raise RuntimeError(
                "Errore durante la richiesta di embeddings a Ollama. Assicurati che il modello di embedding sia disponibile "
                f"(es. '{model}'). Error: {e}"
            ) from e
