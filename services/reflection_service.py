import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Flashcard:
    front: str
    back: str

    def is_valid(self) -> bool:
        return (
            isinstance(self.front, str) and self.front.strip() and
            isinstance(self.back, str) and self.back.strip()
        )

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class ReflectionService:
    """Servizio per implementare il pattern Reflection nella generazione di flashcard."""

    _POSITIVE_MARKERS = (
        "eccellente", "ottima", "perfetta", "già buona",
        "va già bene", "rispetta tutti i principi"
    )

    def __init__(self, ai_service, *, max_api_retries: int = 2):
        """
        Args:
            ai_service: Servizio AI da utilizzare (deve esporre `_call_api(prompt: str) -> str`)
            max_api_retries: Numero di tentativi in caso di risposte vuote/rotte
        """
        self.ai_service = ai_service
        self.max_api_retries = max_api_retries

    # -----------------------
    # Helpers interni
    # -----------------------

    def _call_ai(self, prompt: str) -> str:
        """Chiama l'AI con retry basilare su risposte vuote."""
        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_api_retries + 1):
            try:
                response = self.ai_service._call_api(prompt)
                if response and isinstance(response, str) and response.strip():
                    return response
                logger.warning("Tentativo %d: risposta vuota dall'AI.", attempt)
            except Exception as e:
                last_err = e
                logger.warning("Tentativo %d: errore AI: %s", attempt, e)
        if last_err:
            raise last_err
        return ""

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Rimuove blocchi ```...``` e mantiene solo il contenuto."""
        if not text:
            return ""
        text = text.strip()
        # Rimuovi fence con o senza 'json'
        if text.startswith("```"):
            # prendi ciò che sta fra i primi e gli ultimi fence
            parts = re.split(r"^```(?:json)?\s*|\s*```$", text, flags=re.IGNORECASE | re.MULTILINE)
            if len(parts) >= 2:
                return parts[1].strip()
        return text

    @staticmethod
    def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
        """
        Estrae il PRIMO oggetto JSON (dict) valido dal testo, anche se il modello
        ha aggiunto testo prima/dopo. Usa scansione a conteggio parentesi.
        """
        if not text:
            return None

        # Prima, prova la via semplice
        try:
            candidate = text.strip()
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            # Se non è un dict, continua con le strategie successive
        except Exception:
            pass

        # Rimuovi code fences eventuali
        text = ReflectionService._strip_code_fences(text)

        # Cerca blocchi che contengono "front" e "back"
        # 1) via regex tollerante (senza nested complessi)
        for match in re.finditer(r"\{[\s\S]*?\}", text):
            chunk = match.group(0)
            if '"front"' in chunk and '"back"' in chunk:
                try:
                    return json.loads(chunk)
                except Exception:
                    continue

        # 2) fallback: scansione con conteggio parentesi
        start_indexes = [m.start() for m in re.finditer(r"\{", text)]
        for start in start_indexes:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        chunk = text[start : i + 1]
                        if '"front"' in chunk and '"back"' in chunk:
                            try:
                                return json.loads(chunk)
                            except Exception:
                                break
        return None

    @staticmethod
    def _extract_json_array(text: str) -> Optional[List[Any]]:
        """
        Estrae il PRIMO array JSON valido dal testo (anche con testo extra o code fences).
        Utile per liste di topic.
        """
        if not text:
            return None

        # Tentativo diretto
        try:
            candidate = text.strip()
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Rimuovi code fences
        text = ReflectionService._strip_code_fences(text)

        # Cerca porzione tra [ ... ] con conteggio parentesi quadre
        starts = [m.start() for m in re.finditer(r"\[", text)]
        for start in starts:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                    if depth == 0:
                        chunk = text[start : i + 1]
                        try:
                            parsed = json.loads(chunk)
                            if isinstance(parsed, list):
                                return parsed
                        except Exception:
                            break
        return None

    @staticmethod
    def _validate_flashcard_payload(payload: Dict[str, Any]) -> Flashcard:
        """Converte un dict in Flashcard con validazione e trimming."""
        front = str(payload.get("front", "")).strip()
        back = str(payload.get("back", "")).strip()
        fc = Flashcard(front=front, back=back)
        if not fc.is_valid():
            raise ValueError("Payload JSON non contiene campi 'front'/'back' validi.")
        return fc

    @staticmethod
    def _fallback_flashcard(topic: str, message: str) -> Dict[str, str]:
        return {
            "front": f"Cos'è {topic}?",
            "back": message,
        }

    # -----------------------
    # Metodi pubblici
    # -----------------------

    def generate_flashcard_draft(self, context: str, topic: str) -> Dict[str, str]:
        """
        Genera una bozza di flashcard per un topic specifico.
        """
        prompt = f"""Sei un esperto di apprendimento e metacognizione. Il tuo obiettivo è creare UNA SOLA flashcard "atomica" basata sui principi di Andy Matuschak.

ARGOMENTO RICHIESTO (OBBLIGATORIO): {topic}

ATTENZIONE: La flashcard DEVE riguardare ESCLUSIVAMENTE "{topic}".
- Se il contesto non contiene informazioni rilevanti per "{topic}", indica che non ci sono informazioni sufficienti.
- NON creare flashcard su argomenti diversi da "{topic}".

Usa SOLO le informazioni dal seguente contesto che sono PERTINENTI a "{topic}":
{context}

Segui queste 5 REGOLE ASSOLUTE:
1.  **Focalizzata**: La domanda (front) deve riguardare UN SOLO concetto o fatto RELATIVO A "{topic}".
2.  **Precisa**: La domanda non deve essere ambigua. Deve far capire esattamente cosa è richiesto su "{topic}".
3.  **Coerente**: La risposta (back) deve essere l'unica risposta corretta e sempre la stessa.
4.  **Chiedi il "Perché"**: Se possibile, preferisci domande sul "perché" o sulle implicazioni, piuttosto che definizioni secche.
5.  **Sforzo Cognitivo**: La risposta NON deve essere intuibile dalla domanda (evita indizi banali o domande binarie Sì/No).

Restituisci la risposta in formato JSON con questa struttura esatta:
{{
    "front": "Domanda atomica, precisa e che richiede sforzo SU {topic}",
    "back": "Risposta concisa e accurata basata sul contesto"
}}

Non inventare informazioni non presenti nel contesto. Se il contesto non parla di "{topic}", restituisci:
{{
    "front": "Informazione non disponibile",
    "back": "Il contesto fornito non contiene informazioni rilevanti su {topic}"
}}"""

        try:
            response = self._call_ai(prompt)

            if not response or not response.strip():
                logger.warning("Risposta vuota dal servizio AI (draft).")
                return self._fallback_flashcard(topic, "Errore: risposta vuota dal servizio AI")

            payload = self._extract_json_object(response)
            if payload is None:
                logger.warning("Parsing JSON fallito (draft).")
                return self._fallback_flashcard(topic, "Errore nel parsing della risposta")

            # Validazione base
            fc = self._validate_flashcard_payload(payload)

            return fc.to_dict()

        except Exception as e:
            logger.error("Errore generazione bozza: %s", e)
            return self._fallback_flashcard(topic, "Errore nella generazione")

    def critique_flashcard(self, flashcard: Dict[str, str], context: str) -> str:
        """
        Critica una flashcard e suggerisce miglioramenti.
        """
        front = flashcard.get("front", "").strip()
        back = flashcard.get("back", "").strip()

        prompt = f"""Sei un critico esperto di materiali didattici che segue i principi di Andy Matuschak.

Analizza questa flashcard basandoti sul contesto fornito.

FLASHCARD:
Domanda: {front}
Risposta: {back}

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
- Se non rispetta le regole, spiega COSA migliorare (es. "Non è focalizzata, chiede due cose. Scomponila." OPPURE "Domanda troppo vaga, rendila precisa." OPPURE "La risposta è intuibile, riformula la domanda per richiedere più sforzo.")."""

        try:
            critique = self._call_ai(prompt)
            return (critique or "").strip() or "Critica non disponibile."
        except Exception:
            return "Impossibile generare critica"

    def refine_flashcard(
        self,
        flashcard: Dict[str, str],
        critique: str,
        context: str,
        topic: str = None
    ) -> Dict[str, str]:
        """
        Migliora una flashcard basandosi sulla critica.
        """
        topic_instruction = f"\n- Mantieni il focus ESCLUSIVAMENTE su: {topic}" if topic else ""

        prompt = f"""Sei un esperto nell'apprendimento e nella creazione di materiali didattici.

FLASHCARD ORIGINALE:
Domanda: {flashcard.get('front','')}
Risposta: {flashcard.get('back','')}

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
- Sia chiara e utile per l'apprendimento{topic_instruction}"""

        try:
            response = self._call_ai(prompt)

            if not response or not response.strip():
                logger.warning("Risposta vuota dal servizio AI per raffinamento.")
                return flashcard  # Ritorna l'originale

            payload = self._extract_json_object(response)
            if payload is None:
                logger.warning("Parsing JSON fallito (refine).")
                return flashcard

            refined = self._validate_flashcard_payload(payload)
            return refined.to_dict()

        except Exception as e:
            logger.warning("Errore raffinamento: %s", e)
            return flashcard  # Ritorna l'originale in caso di errore

    def generate_flashcard_with_reflection(
        self,
        context: str,
        topic: str,
        max_iterations: int = 2
    ) -> Dict[str, str]:
        """
        Genera una flashcard usando il processo completo di Reflection.
        """
        # Step 1: Genera bozza
        flashcard = self.generate_flashcard_draft(context, topic)

        # Step 2-3: Critica e Migliora (iterativo)
        for _ in range(max_iterations):
            critique = self.critique_flashcard(flashcard, context)
            low = critique.lower()
            if any(marker in low for marker in self._POSITIVE_MARKERS):
                break
            flashcard = self.refine_flashcard(flashcard, critique, context, topic)

        return flashcard

    def extract_topics(self, chunks: List[str], num_topics: int = 10) -> List[str]:
        """
        Estrae i topic principali da una lista di chunks.
        Se chunks contiene solo la query utente (1 elemento breve), estrae sub-topic dalla query stessa.
        """
        sample_content = "\n\n".join(chunks[:min(10, len(chunks))])
        
        # Determina se stiamo analizzando documenti o una query utente
        is_query = len(chunks) == 1 and len(sample_content) < 200
        
        if is_query:
            # Estrai topic DALLA QUERY utente
            prompt = f"""La seguente è una domanda/query di uno studente:

QUERY: {sample_content}

Estrai {num_topics} sotto-argomenti o concetti chiave DALLA QUERY STESSA che possono essere approfonditi per rispondere completamente alla domanda.

Restituisci SOLO una lista JSON di {num_topics} argomenti, senza spiegazioni:
["Argomento 1", "Argomento 2", ...]

Ogni argomento deve essere:
- Specifico e pertinente alla query
- Espresso in 2-5 parole
- Utile per comprendere la risposta alla domanda

IMPORTANTE: Se la query è molto specifica e non può essere scomposta, ripeti la query principale con leggere variazioni.

Esempio:
Query: "Come funzionano i database SQL?"
→ ["Database relazionali", "Linguaggio SQL", "Tabelle e relazioni", "Query SELECT", "Transazioni ACID", ...]
"""
        else:
            # Estrai topic DAI DOCUMENTI
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
            response = self._call_ai(prompt)
            if not response or not response.strip():
                logger.warning("Risposta vuota dal servizio AI per estrazione topic.")
                return [f"Argomento {i+1}" for i in range(num_topics)]

            # Estrai un array JSON, anche se è incapsulato in testo extra
            payload_list = self._extract_json_array(response)
            if not isinstance(payload_list, list) or not payload_list:
                raise ValueError("Formato non valido: la risposta non è una lista non vuota.")

            # Normalizza: stringhe 2-5 parole
            topics: List[str] = []
            for t in payload_list[:num_topics]:
                s = str(t).strip()
                if s:
                    topics.append(s)
            if not topics:
                raise ValueError("Lista topics vuota dopo normalizzazione.")
            return topics[:num_topics]

        except Exception as e:
            logger.warning("Errore estrazione topic: %s", e)
            return [f"Argomento {i+1}" for i in range(num_topics)]
