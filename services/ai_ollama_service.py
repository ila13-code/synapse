import json
from typing import List, Dict, Optional, Any

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

    def __init__(self, model_name: str = "phi3:mini"):
        self.model_name = model_name

    def _clean_response_text(self, raw: str) -> str:
        text = raw.strip()
        # Debug: mostra primi 100 caratteri (SENZA stampare tutto)
        print(f"Cleaning text (primi 100 char): {text[:100]}")
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
        """Genera flashcards (lista di dict) a partire dal testo fornito.

        Args:
            content: testo degli appunti
            num_cards: numero desiderato di card in output (max)
            use_web_search: se True, il prompt permette al modello di integrare conoscenza esterna

        Restituisce:
            Lista di dizionari con almeno 'front' e 'back' e opzionalmente 'difficulty' e 'tags'.
        """
        print(f"Generazione flashcards con {self.model_name}...")
        
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
Sei un assistente esperto nella creazione di flashcard per studenti universitari.
Analizza il seguente contenuto e crea {num_cards} flashcard efficaci e dettagliate.

{web_search_instruction}

Contenuto:
{content}

IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o altra formattazione.
Formato richiesto:
[{{"front": "domanda", "back": "risposta", "difficulty": "easy|medium|hard", "tags": ["tag1"]}}]

Criteri:
- Domande chiare e specifiche
- Risposte complete ma concise (massimo 200 parole)
- Varietà di difficoltà (easy, medium, hard)
- Copertura dei concetti principali
- Le risposte devono essere in testo semplice
- Assicurati che il JSON sia valido e ben formattato
"""

        # Chiediamo a Ollama di restituire JSON (format='json')
        try:
            resp = ollama.generate(
                model=self.model_name, 
                prompt=prompt, 
                format='json', 
                stream=False
            )
            print("Risposta ricevuta.")
        except Exception as e:
            raise RuntimeError(f"Errore nella chiamata a Ollama.generate: {e}") from e

        # La libreria può restituire dict o str; normalizziamo a stringa
        if isinstance(resp, dict) and 'response' in resp:
            raw_text = str(resp['response'])
        else:
            raw_text = str(resp)

        # Debug DETTAGLIATO
        print(f"\n{'='*60}")
        print(f"DEBUG RESPONSE")
        print(f"{'='*60}")
        print(f"Type of resp: {type(resp)}")
        print(f"Type of raw_text: {type(raw_text)}")
        print(f"Length: {len(raw_text)}")
        print(f"First 300 chars:\n{raw_text[:300]}")
        print(f"{'='*60}\n")
        
        cleaned = self._clean_response_text(raw_text)

        # Proviamo a fare il parse JSON
        try:
            parsed = json.loads(cleaned)
            print("Risposta JSON parsata con successo.")
            
            # GESTIONE STRUTTURE DIVERSE:
            # Caso 1: Array diretto di flashcards [{front, back}, ...]
            if isinstance(parsed, list):
                flashcards = parsed
                print(f"Struttura riconosciuta: array diretto ({len(flashcards)} items)")
            
            # Caso 2: Oggetto con chiave "questions" o simili
            elif isinstance(parsed, dict):
                # Cerca chiavi comuni per le flashcards
                if 'questions' in parsed:
                    flashcards = parsed['questions']
                    print(f"Struttura riconosciuta: oggetto con 'questions' ({len(flashcards)} items)")
                elif 'flashcards' in parsed:
                    flashcards = parsed['flashcards']
                    print(f"Struttura riconosciuta: oggetto con 'flashcards' ({len(flashcards)} items)")
                elif 'cards' in parsed:
                    flashcards = parsed['cards']
                    print(f"Struttura riconosciuta: oggetto con 'cards' ({len(flashcards)} items)")
                else:
                    # Se è un singolo oggetto con front/back, wrappalo in lista
                    if 'front' in parsed or 'question' in parsed:
                        flashcards = [parsed]
                        print("Struttura riconosciuta: singola flashcard")
                    else:
                        raise ValueError(f"Struttura JSON non riconosciuta: {list(parsed.keys())}")
            else:
                raise ValueError(f"Tipo JSON non supportato: {type(parsed)}")
                
        except json.JSONDecodeError as e:
            print(f"Errore nel parsing JSON: {e}")
            # tentativo di recovery: estrai la prima lista JSON valida tra '[' e ']'
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1 and end > start:
                fragment = cleaned[start:end + 1]
                try:
                    flashcards = json.loads(fragment)
                    print(f"Recovery riuscito: estratto array ({len(flashcards)} items)")
                except Exception as e2:
                    raise ValueError(
                        f"Impossibile parsare la risposta dell'AI anche dopo recovery. "
                        f"Estratto: {fragment[:400]}..."
                    ) from e2
            else:
                raise ValueError(
                    f"Impossibile parsare la risposta dell'AI: {cleaned[:400]}"
                ) from e

        # ========== VALIDAZIONE E NORMALIZZAZIONE ========== #
        print(f"Inizio validazione di {len(flashcards)} flashcards...")
        
        validated: List[Dict[str, Any]] = []
        for i, card in enumerate(flashcards):
            # Controlla che sia un dizionario
            if not isinstance(card, dict):
                print(f"⚠️ Card {i+1} ignorata: non è un dizionario (tipo: {type(card)})")
                continue
            
            # Estrai front (supporta varianti: front, question, q)
            front = card.get('front') or card.get('question') or card.get('q')
            
            # Estrai back (supporta varianti: back, answer, a)
            back = card.get('back') or card.get('answer') or card.get('a')
            
            # Salta se mancano campi essenziali
            if not front or not back:
                print(f"⚠️ Card {i+1} ignorata: manca 'front' o 'back'")
                continue
            
            # Normalizza difficulty
            difficulty = card.get('difficulty', 'medium')
            if difficulty not in ['easy', 'medium', 'hard']:
                # Prova a mappare valori alternativi
                difficulty_map = {
                    'facile': 'easy',
                    'medio': 'medium', 
                    'difficile': 'hard',
                    'low': 'easy',
                    'high': 'hard'
                }
                difficulty = difficulty_map.get(str(difficulty).lower(), 'medium')
            
            # Normalizza tags
            tags = card.get('tags', [])
            if not isinstance(tags, list):
                tags = [str(tags)] if tags else []
            
            # Aggiungi flashcard validata
            validated.append({
                'front': str(front).strip(),
                'back': str(back).strip(),
                'difficulty': difficulty,
                'tags': tags,
            })
            
            # Limita al numero richiesto
            if len(validated) >= num_cards:
                break
        
        print(f"✓ Validazione completata: {len(validated)}/{len(flashcards)} flashcards valide")
        
        if not validated:
            raise ValueError(
                "Nessuna flashcard valida generata. "
                "Il modello potrebbe aver restituito un formato incompatibile."
            )
        
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
                "Errore durante la richiesta di embeddings a Ollama. "
                f"Assicurati che il modello di embedding sia disponibile (es. '{model}'). "
                f"Error: {e}"
            ) from e