import json
from typing import Dict, List

from google import genai


class AIService:
    def __init__(self, api_keys: List[str] | str, model_name: str = 'gemini-2.5-flash'):
        """
        Initialize AIService with one or multiple API keys for round-robin usage.
        
        Args:
            api_keys: A single API key string or a list of API key strings.
            model_name: The name of the Gemini model to use.
        """
        if isinstance(api_keys, str):
            self.api_keys = [api_keys]
        else:
            self.api_keys = [k for k in api_keys if k] # Filter empty keys
            
        if not self.api_keys:
            raise ValueError("At least one valid API key must be provided")

        # Create a pool of clients, one for each key
        self.clients = [genai.Client(api_key=k) for k in self.api_keys]
        self.current_client_index = 0
        self.model_name = model_name
        
        print(f"[AIService] Initialized with {len(self.clients)} API keys")
    
    def _get_next_client(self):
        """Returns the next client in the rotation"""
        client = self.clients[self.current_client_index]
        # Rotate index for next call
        self.current_client_index = (self.current_client_index + 1) % len(self.clients)
        return client
    
    def _call_api(self, prompt: str) -> str:
        try:
            # Get client from rotation
            client = self._get_next_client()
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            if not hasattr(response, 'text') or not response.text:
                print("Warning: Empty response or no text from Gemini")
                return ""
            
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return ""
        
    def generate_flashcards(self, content: str, num_cards: int = 10, use_web_search: bool = False) -> List[Dict]:
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

                    CRITICAL: You MUST generate ALL flashcards in ENGLISH ONLY, regardless of the language of the source content.
                    Even if the content is in Italian, Spanish, French, or any other language, your flashcards MUST be in English.

                    {web_search_instruction}

                    Content:
                    {content}

                    IMPORTANT: Follow these 5 ABSOLUTE RULES for EVERY flashcard you create:
                    1.  **Decompose (Focused)**: Each flashcard must address ONE SINGLE concept or fact. DO NOT create flashcards that ask for lists (e.g., "What are the 3 types of X?"). Instead, create 3 separate cards or use decomposition (e.g., "One type of X is...").
                    2.  **Precise**: The question must not be ambiguous.
                    3.  **Ask "Why"**: Beyond facts, create questions about "why" a concept works in a certain way (e.g., "Why does algorithm X use a queue instead of a stack?").
                    4.  **Cognitive Effort**: The answer MUST NOT be guessable from the question. Avoid Yes/No questions.
                    5.  **Conceptual**: Avoid dry definitions. Ask about differences (e.g., "Difference between X and Y"), attributes (e.g., "What is always true for X?"), or implications (e.g., "What problem does X solve?").

                    Create {num_cards} flashcards that follow these rules.

                    IMPORTANT: Respond ONLY with a valid JSON array, without markdown or formatting.
                    Required format:
                    [{{"front": "Atomic, precise question", "back": "Concise answer", "difficulty": "easy|medium|hard", "tags": ["tag1", "tag2"]}}]"""

        try:
            # Get client from rotation
            client = self._get_next_client()
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            content_text = response.text.strip()
            
            if content_text.startswith('```json'):
                content_text = content_text.replace('```json', '').replace('```', '').strip()
            elif content_text.startswith('```'):
                content_text = content_text.replace('```', '').strip()
            
            flashcards = json.loads(content_text)
            
            validated_cards = []
            for card in flashcards:
                if isinstance(card, dict) and 'front' in card and 'back' in card:
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
            raise Exception(f"Error parsing AI response: {e}")
        except Exception as e:
            raise Exception(f"Error generating flashcards: {e}")