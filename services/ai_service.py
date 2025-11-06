import json
from typing import Dict, List

from google import genai


class AIService:
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash-exp'):
        """Inizializza il servizio AI con Gemini usando la nuova API
        
        Args:
            api_key: API key di Google Gemini
            model_name: Nome del modello da utilizzare (default: gemini-2.0-flash-exp)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def _call_api(self, prompt: str) -> str:
        """Metodo helper per chiamare l'API Gemini
        
        Args:
            prompt: Prompt da inviare al modello
            
        Returns:
            Risposta del modello come stringa
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Verifica che la risposta abbia il campo text
            if not hasattr(response, 'text') or not response.text:
                print("Avviso: Risposta vuota o senza testo da Gemini")
                return ""
            
            return response.text.strip()
        except Exception as e:
            print(f"Errore nella chiamata API Gemini: {e}")
            return ""
        
    def generate_flashcards(self, content: str, num_cards: int = 10, use_web_search: bool = False) -> List[Dict]:
        """Genera flashcard dal contenuto usando Gemini
        
        Args:
            content: Contenuto dei documenti
            num_cards: Numero di flashcard da generare
            use_web_search: Se True, Gemini userà la sua conoscenza generale per integrare
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
        
        prompt = f"""Sei un assistente esperto nella creazione di flashcard per studenti universitari. Il tuo obiettivo è applicare i principi di Andy Matuschak per creare flashcard "atomiche" e che favoriscano la comprensione.

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

IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o formattazione.
Formato richiesto:
[{{"front": "Domanda atomica e precisa", "back": "Risposta concisa", "difficulty": "easy|medium|hard", "tags": ["tag1", "tag2"]}}]"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            content_text = response.text.strip()
            
            # Pulisci eventuali markdown code blocks
            if content_text.startswith('```json'):
                content_text = content_text.replace('```json', '').replace('```', '').strip()
            elif content_text.startswith('```'):
                content_text = content_text.replace('```', '').strip()
            
            # Parse JSON
            flashcards = json.loads(content_text)
            
            # Valida la struttura
            validated_cards = []
            for card in flashcards:
                if isinstance(card, dict) and 'front' in card and 'back' in card:
                    # Normalizza difficulty to English (easy, medium, hard)
                    difficulty = card.get('difficulty', 'medium').lower()
                    if difficulty in ['facile', 'easy']:
                        difficulty = 'easy'
                    elif difficulty in ['difficile', 'hard']:
                        difficulty = 'hard'
                    else:
                        difficulty = 'medium'
                    
                    validated_cards.append({
                        'front': card['front'],
                        'back': card['back'],
                        'difficulty': difficulty,
                        'tags': card.get('tags', [])
                    })
            
            return validated_cards[:num_cards]
            
        except json.JSONDecodeError as e:
            raise Exception(f"Errore nel parsing della risposta AI: {e}")
        except Exception as e:
            raise Exception(f"Errore nella generazione delle flashcard: {e}")