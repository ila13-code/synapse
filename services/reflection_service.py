"""
Servizio Reflection per migliorare la qualità delle flashcard attraverso un processo iterativo
"""
import json
from typing import Any, Dict, List


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
        prompt = f"""Sei un esperto di apprendimento e metacognizione. Il tuo obiettivo è creare UNA SOLA flashcard "atomica" basata sui principi di Andy Matuschak.

Argomento: {topic}

Usa SOLO le informazioni dal seguente contesto:
{context}

Segui queste 5 REGOLE ASSOLUTE:
1.  **Focalizzata**: La domanda (front) deve riguardare UN SOLO concetto o fatto.
2.  **Precisa**: La domanda non deve essere ambigua. Deve far capire esattamente cosa è richiesto.
3.  **Coerente**: La risposta (back) deve essere l'unica risposta corretta e sempre la stessa.
4.  **Chiedi il "Perché"**: Se possibile, preferisci domande sul "perché" o sulle implicazioni, piuttosto che definizioni secche.
5.  **Sforzo Cognitivo**: La risposta NON deve essere intuibile dalla domanda (evita indizi banali o domande binarie Sì/No).

Restituisci la risposta in formato JSON con questa struttura esatta:
{{
    "front": "Domanda atomica, precisa e che richiede sforzo",
    "back": "Risposta concisa e accurata basata sul contesto"
}}

Non inventare informazioni non presenti nel contesto."""

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
        prompt = f"""Sei un critico esperto di materiali didattici che segue i principi di Andy Matuschak.

Analizza questa flashcard basandoti sul contesto fornito.

FLASHCARD:
Domanda: {flashcard['front']}
Risposta: {flashcard['back']}

CONTESTO DISPONIBILE:
{context}

Valuta la flashcard ESCLUSIVAMENTE secondo queste 5 REGOLE:
1.  **Focalizzata**: Chiede un solo concetto? O è troppo ampia (es. chiede una lista)?
2.  **Precisa**: È ambigua? Si capisce esattamente cosa vuole?
3.  **Contesto**: La risposta è corretta e basata SOLO sul contesto?
4.  **Sforzo Cognitivo**: La risposta è troppo ovvia leggendo la domanda?
5.  **Concettuale**: È una definizione secca (negativo) o chiede il "perché", una differenza, o un'implicazione (positivo)?

Fornisci una critica COSTRUTTIVA in 2-3 frasi.
- Se la flashcard è già eccellente e rispetta le regole, dillo (es. "Eccellente, rispetta tutti i principi.").
- Se non rispetta le regole, spiega COSA migliorare (es. "Non è focalizzata, chiede due cose. Scomponila." OPPURE "Domanda troppo vaga, rendila precisa." OPPURE "La risposta è intuibile, riformula la domanda per richiedere più sforzo.")"""

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
