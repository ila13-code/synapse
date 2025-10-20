import json
import google.generativeai as genai
from typing import List, Dict

class AIService:
    def __init__(self, api_key: str):
        """Inizializza il servizio AI con Gemini"""
        genai.configure(api_key=api_key)
        # Usa il modello base - la ricerca web la gestiamo nel prompt
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
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
        
        prompt = f"""Sei un assistente esperto nella creazione di flashcard per studenti universitari.
Analizza il seguente contenuto e crea {num_cards} flashcard efficaci e dettagliate.

{web_search_instruction}

Contenuto:
{content}

IMPORTANTE: Rispondi SOLO con un array JSON valido, senza markdown o formattazione.
Formato richiesto:
[{{"front": "domanda", "back": "risposta", "difficulty": "easy|medium|hard"}}]

Criteri:
- Domande chiare e specifiche
- Risposte complete ma concise (massimo 200 parole)
- Varietà di difficoltà (easy, medium, hard)
- Copertura dei concetti principali
- Le risposte devono essere in formato testo semplice, evita formattazioni complesse
- Assicurati che il JSON sia valido e ben formattato"""

        try:
            response = self.model.generate_content(prompt)
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
                    validated_cards.append({
                        'front': card['front'],
                        'back': card['back'],
                        'difficulty': card.get('difficulty', 'medium')
                    })
            
            return validated_cards[:num_cards]
            
        except json.JSONDecodeError as e:
            raise Exception(f"Errore nel parsing della risposta AI: {e}")
        except Exception as e:
            raise Exception(f"Errore nella generazione delle flashcard: {e}")