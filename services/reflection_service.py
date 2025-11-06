"""
Servizio Reflection per migliorare la qualità delle flashcard attraverso un processo iterativo
"""
from typing import List, Dict, Any
import json


class ReflectionService:
    """Servizio per implementare il pattern Reflection nella generazione di flashcard"""
    
    def __init__(self, ai_service):
        """
        Inizializza il servizio Reflection
        
        Args:
            ai_service: Servizio AI da utilizzare (Gemini/Ollama)
        """
        self.ai_service = ai_service
    
    def generate_flashcard_draft(self, context: str, topic: str) -> Dict[str, str]:
        """
        Genera una bozza di flashcard per un topic specifico
        
        Args:
            context: Contesto recuperato tramite RAG
            topic: Topic della flashcard
            
        Returns:
            Dizionario con front e back della flashcard
        """
        prompt = f"""Sei un esperto nell'apprendimento e nella creazione di materiali didattici.

Crea UNA SOLA flashcard sul seguente argomento: {topic}

Usa SOLO le informazioni dal seguente contesto:
{context}

Restituisci la risposta in formato JSON con questa struttura esatta:
{{
    "front": "Domanda chiara e diretta",
    "back": "Risposta completa e dettagliata"
}}

Ricorda:
- La domanda (front) deve essere chiara e specifica
- La risposta (back) deve essere completa ma concisa
- Usa SOLO informazioni presenti nel contesto fornito
- Non inventare informazioni"""

        try:
            response = self.ai_service._call_api(prompt)
            
            # Verifica che la risposta non sia vuota
            if not response or not response.strip():
                print("Avviso: Risposta vuota dal servizio AI")
                return {
                    "front": f"Cos'è {topic}?",
                    "back": "Errore: risposta vuota dal servizio AI"
                }
            
            # Pulisci eventuali markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            # Parse JSON response
            flashcard = json.loads(cleaned_response)
            
            # Validazione base
            if 'front' not in flashcard or 'back' not in flashcard:
                raise ValueError("Risposta non valida: mancano i campi 'front' o 'back'")
                
            return flashcard
            
        except json.JSONDecodeError as e:
            print(f"Errore generazione bozza (JSON decode): {e}")
            print(f"Risposta ricevuta: {response[:200] if response else 'None'}")
            return {
                "front": f"Cos'è {topic}?",
                "back": "Errore nel parsing della risposta"
            }
        except Exception as e:
            print(f"Errore generazione bozza: {e}")
            return {
                "front": f"Cos'è {topic}?",
                "back": "Errore nella generazione"
            }
    
    def critique_flashcard(self, flashcard: Dict[str, str], context: str) -> str:
        """
        Critica una flashcard e suggerisce miglioramenti
        
        Args:
            flashcard: Flashcard da criticare
            context: Contesto originale
            
        Returns:
            Critica testuale
        """
        prompt = f"""Sei un critico esperto di materiali didattici.

Analizza questa flashcard e fornisci una critica costruttiva:

FLASHCARD:
Domanda: {flashcard['front']}
Risposta: {flashcard['back']}

CONTESTO DISPONIBILE:
{context}

Valuta i seguenti aspetti:
1. La domanda è chiara e specifica?
2. La risposta è completa ma concisa?
3. La risposta è fattualmente corretta secondo il contesto?
4. Mancano dettagli importanti?
5. La risposta è troppo lunga o troppo breve?

Fornisci una critica in 2-3 frasi, concentrandoti su come migliorare la flashcard.
Se la flashcard è già eccellente, dillo chiaramente."""

        try:
            critique = self.ai_service._call_api(prompt)
            return critique.strip()
        except Exception as e:
            return "Impossibile generare critica"
    
    def refine_flashcard(self, flashcard: Dict[str, str], critique: str, 
                        context: str) -> Dict[str, str]:
        """
        Migliora una flashcard basandosi sulla critica
        
        Args:
            flashcard: Flashcard originale
            critique: Critica ricevuta
            context: Contesto originale
            
        Returns:
            Flashcard migliorata
        """
        prompt = f"""Sei un esperto nell'apprendimento e nella creazione di materiali didattici.

FLASHCARD ORIGINALE:
Domanda: {flashcard['front']}
Risposta: {flashcard['back']}

CRITICA RICEVUTA:
{critique}

CONTESTO DISPONIBILE:
{context}

Migliora la flashcard tenendo conto della critica. 
Restituisci la flashcard migliorata in formato JSON:
{{
    "front": "Domanda migliorata",
    "back": "Risposta migliorata"
}}

Assicurati che la flashcard migliorata:
- Affronti i problemi evidenziati nella critica
- Rimanga fedele al contesto fornito
- Sia chiara e utile per l'apprendimento"""

        try:
            response = self.ai_service._call_api(prompt)
            
            # Verifica che la risposta non sia vuota
            if not response or not response.strip():
                print("Avviso: Risposta vuota dal servizio AI per raffinamento")
                return flashcard  # Ritorna l'originale
            
            # Pulisci eventuali markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            # Parse JSON response
            refined = json.loads(cleaned_response)
            
            # Validazione
            if 'front' not in refined or 'back' not in refined:
                return flashcard  # Ritorna l'originale se c'è un errore
                
            return refined
            
        except json.JSONDecodeError as e:
            print(f"Errore raffinamento (JSON decode): {e}")
            print(f"Risposta ricevuta: {response[:200] if response else 'None'}")
            return flashcard  # Ritorna l'originale in caso di errore
        except Exception as e:
            print(f"Errore raffinamento: {e}")
            return flashcard  # Ritorna l'originale in caso di errore
    
    def generate_flashcard_with_reflection(self, context: str, topic: str, 
                                          max_iterations: int = 2) -> Dict[str, str]:
        """
        Genera una flashcard usando il processo completo di Reflection
        
        Args:
            context: Contesto recuperato tramite RAG
            topic: Topic della flashcard
            max_iterations: Numero massimo di iterazioni di miglioramento
            
        Returns:
            Flashcard finale migliorata
        """
        # Step 1: Genera bozza
        flashcard = self.generate_flashcard_draft(context, topic)
        
        # Step 2-3: Critica e Migliora (iterativo)
        for iteration in range(max_iterations):
            critique = self.critique_flashcard(flashcard, context)
            
            # Se la critica è positiva, fermati
            if any(word in critique.lower() for word in ['eccellente', 'ottima', 'perfetta', 'già buona']):
                break
            
            # Altrimenti, migliora
            flashcard = self.refine_flashcard(flashcard, critique, context)
        
        return flashcard
    
    def extract_topics(self, chunks: List[str], num_topics: int = 10) -> List[str]:
        """
        Estrae i topic principali da una lista di chunks
        
        Args:
            chunks: Lista di chunks di testo
            num_topics: Numero di topic da estrarre
            
        Returns:
            Lista di topic
        """
        # Prendi solo i primi chunks per l'analisi dei topic
        sample_content = "\n\n".join(chunks[:min(10, len(chunks))])
        
        prompt = f"""Analizza il seguente testo e identifica i {num_topics} argomenti principali.

TESTO:
{sample_content}

Restituisci SOLO una lista JSON di {num_topics} argomenti chiave, senza spiegazioni:
["Argomento 1", "Argomento 2", ...]

Ogni argomento deve essere:
- Specifico e concreto
- Espresso in 2-5 parole
- Rilevante per lo studio della materia"""

        try:
            response = self.ai_service._call_api(prompt)
            
            # Verifica che la risposta non sia vuota
            if not response or not response.strip():
                print("Avviso: Risposta vuota dal servizio AI per estrazione topic")
                return [f"Argomento {i+1}" for i in range(num_topics)]
            
            # Pulisci eventuali markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            topics = json.loads(cleaned_response)
            
            # Validazione
            if isinstance(topics, list) and len(topics) > 0:
                return topics[:num_topics]
            else:
                raise ValueError("Formato non valido: non è una lista o è vuota")
                
        except json.JSONDecodeError as e:
            print(f"Errore estrazione topic (JSON decode): {e}")
            print(f"Risposta ricevuta: {response[:200] if response else 'None'}")
            # Fallback: restituisci topic generici
            return [f"Argomento {i+1}" for i in range(num_topics)]
        except Exception as e:
            print(f"Errore estrazione topic: {e}")
            # Fallback: restituisci topic generici
            return [f"Argomento {i+1}" for i in range(num_topics)]
