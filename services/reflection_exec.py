from typing import Dict, List

import ollama
from pyparsing import Any, Optional
from services.ai_ollama_service import OllamaAIService
import json

from services.ai_service import AIService


class ReflectionExecutor:
    """
    Esegue un ciclo di reflection per migliorare iterativamente
    la qualità delle flashcards generate.
    
    Funziona con QUALSIASI servizio AI che implementa generate_flashcards().
    """

    def __init__(
        self,
        ai_service,
        max_iterations: int = 3,
        quality_threshold: float = 95.0,
    ):
        """
        Args:
            ai_service: Istanza di un servizio AI (OllamaAIService, AIService, etc.)
            max_iterations: Numero massimo di iterazioni di raffinamento
            quality_threshold: Soglia di qualità per fermare le iterazioni (0-100)
        """
        self.ai_service = ai_service
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        
        # Rileva il tipo di servizio per le chiamate di critica/raffinamento
        self._setup_critique_method()

    def _setup_critique_method(self):
        """Configura il metodo di critica in base al tipo di servizio."""
        # Controlla se è un servizio Ollama (ha attributo model_name)
        if hasattr(self.ai_service, 'model_name'):
            self.service_type = 'ollama'
            self.model_name = self.ai_service.model_name
        # Controlla se è Gemini (ha attributo model)
        elif hasattr(self.ai_service, 'model'):
            self.service_type = 'gemini'
            self.model = self.ai_service.model
        else:
            # Fallback generico
            self.service_type = 'generic'
            self.model_name = 'unknown'

    def generate_initial_flashcards(
        self, 
        content: str,
        num_cards: int = 10,
        use_web_search: bool = False
    ) -> List[Dict[str, Any]]:
        """
        STEP 1: Genera flashcards iniziali usando l'AI service fornito.
        """
        print("=== Generazione Flashcards Iniziali ===")
        try:
            cards = self.ai_service.generate_flashcards(
                content=content,
                num_cards=num_cards,
                use_web_search=use_web_search
            )
            print(f"✓ Generate {len(cards)} flashcards iniziali")
            return cards
        except Exception as e:
            print(f"✗ Errore nella generazione: {e}")
            return []

    def evaluate_flashcards(self, flashcards: List[Dict]) -> Dict[str, Any]:
        """
        STEP 2: Valuta la qualità delle flashcards generate.
        Restituisce metriche e problemi rilevati.
        """
        print("\n=== Valutazione Flashcards ===")
        
        issues = []
        valid_cards = 0
        
        for i, card in enumerate(flashcards):
            card_issues = []
            
            # Controlla campi obbligatori
            if not isinstance(card, dict):
                issues.append(f"Card {i+1}: non è un dizionario valido")
                continue
                
            front = card.get('front', '')
            back = card.get('back', '')
            
            if not front or len(front.strip()) < 5:
                card_issues.append("domanda mancante o troppo breve")
            if not back or len(back.strip()) < 5:
                card_issues.append("risposta mancante o troppo breve")
                
            # Controlla lunghezza risposta
            if back and len(back) > 1000:
                card_issues.append("risposta troppo lunga (>1000 caratteri)")
                
            # Controlla difficoltà
            difficulty = card.get('difficulty', '')
            if difficulty not in ['easy', 'medium', 'hard', '']:
                card_issues.append(f"difficoltà invalida: '{difficulty}'")
                
            # Controlla tags (opzionale)
            tags = card.get('tags', [])
            if tags and not isinstance(tags, list):
                card_issues.append("tags non è una lista")
            
            if card_issues:
                issues.append(f"Card {i+1}: {'; '.join(card_issues)}")
            else:
                valid_cards += 1
        
        # Statistiche generali
        total_cards = len(flashcards)
        quality_score = (valid_cards / total_cards * 100) if total_cards > 0 else 0
        
        evaluation = {
            "total_cards": total_cards,
            "valid_cards": valid_cards,
            "quality_score": quality_score,
            "issues": issues,
            "summary": (
                f"{valid_cards}/{total_cards} flashcards valide "
                f"(qualità: {quality_score:.1f}%)"
            )
        }
        
        print(f"Valutazione: {evaluation['summary']}")
        if issues:
            print(f"Problemi rilevati: {len(issues)}")
            for issue in issues[:3]:
                print(f"  - {issue}")
        
        return evaluation

    def critique_flashcards(
        self, 
        content: str,
        flashcards: List[Dict],
        evaluation: Dict[str, Any]
    ) -> str:
        """
        STEP 3: Genera una critica dettagliata delle flashcards.
        """
        print("\n=== Critica delle Flashcards ===")
        
        cards_json = json.dumps(flashcards, indent=2, ensure_ascii=False)
        eval_json = json.dumps(evaluation, indent=2, ensure_ascii=False)
        
        prompt = f"""
Sei un revisore esperto di materiale didattico.
Analizza criticamente le seguenti flashcards generate da questo contenuto.

Contenuto originale:
{content[:500]}...

Flashcards generate:
{cards_json}

Valutazione automatica:
{eval_json}

Fornisci una critica costruttiva che copra:
1. PROBLEMI STRUTTURALI: errori di formato, campi mancanti, JSON invalido
2. QUALITÀ DEL CONTENUTO: chiarezza domande, completezza risposte, accuratezza
3. COPERTURA: concetti principali trattati o mancanti
4. DIFFICOLTÀ: distribuzione e appropriatezza dei livelli
5. SUGGERIMENTI SPECIFICI: come migliorare ogni aspetto

Sii specifico e fornisci esempi concreti.
NON riscrivere le flashcards, solo analizzale.
"""

        try:
            if self.service_type == 'ollama':
                import ollama
                resp = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=False
                )
                critique = resp['response'] if isinstance(resp, dict) else str(resp)
                
            elif self.service_type == 'gemini':
                response = self.model.generate_content(prompt)
                critique = response.text
                
            else:
                # Fallback: usa il metodo generate_flashcards con un prompt modificato
                print("⚠️ Servizio generico: usando metodo di critica semplificato")
                critique = "Critica generica: verifica manualmente le flashcards."
            
            print(f"✓ Critica generata ({len(critique)} caratteri)")
            return critique.strip()
            
        except Exception as e:
            print(f"✗ Errore nella critica: {e}")
            return "Errore nella generazione della critica. Procedo con valutazione automatica."

    def refine_flashcards(
        self,
        content: str,
        original_flashcards: List[Dict],
        evaluation: Dict[str, Any],
        critique: str,
        num_cards: int = 10
    ) -> List[Dict[str, Any]]:
        """
        STEP 4: Raffina le flashcards usando la critica.
        """
        print("\n=== Raffinamento Flashcards ===")
        
        cards_json = json.dumps(original_flashcards, indent=2, ensure_ascii=False)
        eval_json = json.dumps(evaluation, indent=2, ensure_ascii=False)
        
        # Crea un "contenuto arricchito" con la critica
        enriched_content = f"""
{content}

FEEDBACK DA MIGLIORARE:
{critique}

PROBLEMI RILEVATI:
{eval_json}

FLASHCARDS PRECEDENTI (da migliorare):
{cards_json}

COMPITO: Genera {num_cards} flashcards MIGLIORATE che:
- Risolvono TUTTI i problemi identificati
- Mantengono i punti di forza delle flashcards originali
- Seguono il formato richiesto
- Sono complete, chiare e accurate
"""

        try:
            # Usa il metodo standard del servizio per generare flashcards migliorate
            refined_cards = self.ai_service.generate_flashcards(
                content=enriched_content,
                num_cards=num_cards,
                use_web_search=False
            )
            
            print(f"✓ Raffinate {len(refined_cards)} flashcards")
            return refined_cards
            
        except Exception as e:
            print(f"✗ Errore nel raffinamento: {e}")
            return []

    def _cards_are_similar(self, cards1: List[Dict], cards2: List[Dict]) -> bool:
        """Verifica se due set di flashcards sono sostanzialmente identici."""
        if len(cards1) != len(cards2):
            return False
        
        similarity_count = 0
        for c1, c2 in zip(cards1, cards2):
            front1 = str(c1.get('front', '')).strip().lower()
            front2 = str(c2.get('front', '')).strip().lower()
            back1 = str(c1.get('back', '')).strip().lower()
            back2 = str(c2.get('back', '')).strip().lower()
            
            # Considera simili se almeno il 90% del contenuto è uguale
            if (front1 == front2 and back1 == back2):
                similarity_count += 1
        
        # Almeno 90% delle card devono essere identiche
        similarity_ratio = similarity_count / len(cards1)
        return similarity_ratio >= 0.9

    def run(
        self, 
        content: str,
        num_cards: int = 10,
        use_web_search: bool = False
    ) -> List[Dict[str, Any]]:
        """
        MAIN LOOP: Esegue il ciclo completo di reflection.
        Restituisce le flashcards finali.
        """
        service_name = getattr(self.ai_service, 'model_name', 
                              getattr(self.ai_service, '__class__.__name__', 'Unknown'))
        
        print(f"\n{'='*60}")
        print(f"ReflectionExecutor - {service_name}")
        print(f"Target: {num_cards} flashcards")
        print(f"Max iterazioni: {self.max_iterations}")
        print(f"Soglia qualità: {self.quality_threshold}%")
        print(f"{'='*60}\n")
        
        # Step 1: Genera flashcards iniziali
        flashcards = self.generate_initial_flashcards(content, num_cards, use_web_search)
        if not flashcards:
            print("✗ Generazione iniziale fallita")
            return []
        
        # Ciclo di raffinamento
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'─'*60}")
            print(f"ITERAZIONE {iteration}/{self.max_iterations}")
            print(f"{'─'*60}")
            
            # Step 2: Valuta
            evaluation = self.evaluate_flashcards(flashcards)
            
            # Se qualità perfetta, fermati
            if evaluation['quality_score'] >= self.quality_threshold and len(evaluation['issues']) == 0:
                print(f"\n✓ Qualità ottimale raggiunta! (score: {evaluation['quality_score']:.1f}%)")
                break
            
            # Step 3: Critica
            critique = self.critique_flashcards(content, flashcards, evaluation)
            
            # Step 4: Raffina
            refined_cards = self.refine_flashcards(
                content, flashcards, evaluation, critique, num_cards
            )
            if not refined_cards:
                print("✗ Raffinamento fallito, interrompo")
                break
            
            # Step 5: Verifica convergenza
            if self._cards_are_similar(flashcards, refined_cards):
                print("\n✓ Nessun cambiamento significativo, convergenza raggiunta")
                break
            
            # Aggiorna per la prossima iterazione
            flashcards = refined_cards
        
        # Risultato finale
        print(f"\n{'='*60}")
        print("FLASHCARDS FINALI")
        print(f"{'='*60}")
        final_eval = self.evaluate_flashcards(flashcards)
        print(f"\nRisultato: {final_eval['summary']}")
        
        return flashcards