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
    _POSITIVE_MARKERS = (
        "excellent", "great", "perfect", "already good",
        "good enough", "respects all principles"
    )

    def __init__(self, ai_service, *, max_api_retries: int = 2):
        self.ai_service = ai_service
        self.max_api_retries = max_api_retries


    def _call_ai(self, prompt: str) -> str:
        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_api_retries + 1):
            try:
                response = self.ai_service._call_api(prompt)
                if response and isinstance(response, str) and response.strip():
                    return response
                logger.warning("Attempt %d: empty response from AI.", attempt)
            except Exception as e:
                last_err = e
                logger.warning("Attempt %d: AI error: %s", attempt, e)
        if last_err:
            raise last_err
        return ""

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if text.startswith("```"):
            parts = re.split(r"^```(?:json)?\s*|\s*```$", text, flags=re.IGNORECASE | re.MULTILINE)
            if len(parts) >= 2:
                return parts[1].strip()
        return text

    @staticmethod
    def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None

        try:
            candidate = text.strip()
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        text = ReflectionService._strip_code_fences(text)

        for match in re.finditer(r"\{[\s\S]*?\}", text):
            chunk = match.group(0)
            if '"front"' in chunk and '"back"' in chunk:
                try:
                    return json.loads(chunk)
                except Exception:
                    continue

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
        if not text:
            return None

        try:
            candidate = text.strip()
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        text = ReflectionService._strip_code_fences(text)

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
        front = str(payload.get("front", "")).strip()
        back = str(payload.get("back", "")).strip()
        fc = Flashcard(front=front, back=back)
        if not fc.is_valid():
            raise ValueError("Payload JSON does not contain valid 'front'/'back' fields.")
        return fc

    @staticmethod
    def _fallback_flashcard(topic: str, message: str) -> Dict[str, str]:
        return {
            "front": f"What is {topic}?",
            "back": message,
        }

    def generate_flashcard_draft(self, context: str, topic: str) -> Dict[str, str]:
        prompt = f"""You are an expert in learning and metacognition. Your goal is to create ONE "atomic" flashcard based on Andy Matuschak's principles.

                    REQUIRED TOPIC (MANDATORY): {topic}

                    ATTENTION: The flashcard MUST be EXCLUSIVELY about "{topic}".
                    - If the context does not contain relevant information for "{topic}", indicate that there is insufficient information.
                    - DO NOT create flashcards on topics other than "{topic}".

                    Use ONLY the information from the following context that is RELEVANT to "{topic}":
                    {context}

                    Follow these 5 ABSOLUTE RULES:
                    1.  **Focused**: The question (front) must concern ONLY ONE concept or fact RELATED TO "{topic}".
                    2.  **Precise**: The question must not be ambiguous. It must be clear exactly what is required about "{topic}".
                    3.  **Consistent**: The answer (back) must be the only correct answer and always the same.
                    4.  **Ask "Why"**: If possible, prefer questions about "why" or implications, rather than dry definitions.
                    5.  **Cognitive Effort**: The answer MUST NOT be guessable from the question (avoid trivial clues or binary Yes/No questions).

                    Return the answer in JSON format with this exact structure:
                    {{
                        "front": "Atomic, precise question requiring effort ABOUT {topic}",
                        "back": "Concise and accurate answer based on context"
                    }}

                    Do not invent information not present in the context. If the context does not speak of "{topic}", return:
                    {{
                        "front": "Information not available",
                        "back": "The provided context does not contain relevant information about {topic}"
                    }}"""

        try:
            response = self._call_ai(prompt)

            if not response or not response.strip():
                logger.warning("Empty response from AI service (draft).")
                return self._fallback_flashcard(topic, "Error: empty response from AI service")

            payload = self._extract_json_object(response)
            if payload is None:
                logger.warning("JSON parsing failed (draft).")
                return self._fallback_flashcard(topic, "Error parsing response")

            fc = self._validate_flashcard_payload(payload)

            return fc.to_dict()

        except Exception as e:
            logger.error("Draft generation error: %s", e)
            return self._fallback_flashcard(topic, "Generation error")

    def critique_flashcard(self, flashcard: Dict[str, str], context: str) -> str:
        front = flashcard.get("front", "").strip()
        back = flashcard.get("back", "").strip()

        prompt = f"""You are an expert critic of educational materials who follows Andy Matuschak's principles.

                    Analyze this flashcard based on the provided context.

                    FLASHCARD:
                    Question: {front}
                    Answer: {back}

                    AVAILABLE CONTEXT:
                    {context}

                    Evaluate the flashcard EXCLUSIVELY according to these 5 RULES:
                    1.  **Focused**: Does it ask for only one concept? Or is it too broad (e.g. asks for a list)?
                    2.  **Precise**: Is it ambiguous? Is it clear exactly what is wanted?
                    3.  **Context**: Is the answer correct and based ONLY on the context?
                    4.  **Cognitive Effort**: Is the answer too obvious reading the question?
                    5.  **Conceptual**: Is it a dry definition (negative) or does it ask "why", a difference, or an implication (positive)?

                    Provide a CONSTRUCTIVE critique in 2-3 sentences.
                    - If the flashcard is already excellent and respects the rules, say so (e.g. "Excellent, respects all principles.").
                    - If it does not respect the rules, explain WHAT to improve (e.g. "It is not focused, it asks two things. Break it down." OR "Question too vague, make it precise." OR "The answer is guessable, rephrase the question to require more effort.")."""

        try:
            critique = self._call_ai(prompt)
            return (critique or "").strip() or "Critique not available."
        except Exception:
            return "Unable to generate critique"

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

        prompt = f"""You are an expert in learning and creating educational materials.

                    ORIGINAL FLASHCARD:
                    Question: {flashcard.get('front','')}
                    Answer: {flashcard.get('back','')}

                    CRITIQUE RECEIVED:
                    {critique}

                    AVAILABLE CONTEXT:
                    {context}

                    Improve the flashcard taking into account the critique.
                    Return the improved flashcard in JSON format:
                    {{
                        "front": "Improved question",
                        "back": "Improved answer"
                    }}

                    Ensure the improved flashcard:
                    - Addresses the issues highlighted in the critique
                    - Remains faithful to the provided context
                    - Is clear and useful for learning{topic_instruction}"""

        try:
            response = self._call_ai(prompt)

            if not response or not response.strip():
                logger.warning("Empty response from AI service for refinement.")
                return flashcard  # Return original

            payload = self._extract_json_object(response)
            if payload is None:
                logger.warning("JSON parsing failed (refine).")
                return flashcard

            refined = self._validate_flashcard_payload(payload)
            return refined.to_dict()

        except Exception as e:
            logger.warning("Refinement error: %s", e)
            return flashcard 

    def generate_flashcard_with_reflection(
        self,
        context: str,
        topic: str,
        max_iterations: int = 2
    ) -> Dict[str, str]:

        flashcard = self.generate_flashcard_draft(context, topic)

        for _ in range(max_iterations):
            critique = self.critique_flashcard(flashcard, context)
            low = critique.lower()
            if any(marker in low for marker in self._POSITIVE_MARKERS):
                break
            flashcard = self.refine_flashcard(flashcard, critique, context, topic)

        return flashcard

    def extract_topics(self, chunks: List[str], num_topics: int = 10) -> List[str]:
        sample_content = "\n\n".join(chunks[:min(10, len(chunks))])
        
        is_query = len(chunks) == 1 and len(sample_content) < 200
        
        if is_query:

            prompt = f"""The following is a student's question/query:

                        QUERY: {sample_content}

                        Extract {num_topics} sub-topics or key concepts FROM THE QUERY ITSELF that can be explored to fully answer the question.

                        Return ONLY a JSON list of {num_topics} topics, without explanations:
                        ["Topic 1", "Topic 2", ...]

                        Each topic must be:
                        - Specific and relevant to the query
                        - Expressed in 2-5 words
                        - Useful for understanding the answer to the question

                        IMPORTANT: If the query is very specific and cannot be decomposed, repeat the main query with slight variations.

                        Example:
                        Query: "How do SQL databases work?"
                        → ["Relational databases", "SQL language", "Tables and relationships", "SELECT queries", "ACID transactions", ...]
                        """
        else:
            prompt = f"""Analyze the following text and identify the {num_topics} main topics.

                        TEXT:
                        {sample_content}

                        Return ONLY a JSON list of {num_topics} key topics, without explanations:
                        ["Topic 1", "Topic 2", ...]

                        Each topic must be:
                        - Specific and concrete
                        - Expressed in 2-5 words
                        - Relevant to the study of the subject"""

        try:
            response = self._call_ai(prompt)
            if not response or not response.strip():
                logger.warning("Empty response from AI service for topic extraction.")
                return [f"Topic {i+1}" for i in range(num_topics)]

            payload_list = self._extract_json_array(response)
            if not isinstance(payload_list, list) or not payload_list:
                raise ValueError("Invalid format: response is not a non-empty list.")

            topics: List[str] = []
            for t in payload_list[:num_topics]:
                s = str(t).strip()
                if s:
                    topics.append(s)
            if not topics:
                raise ValueError("Topic list empty after normalization.")
            return topics[:num_topics]

        except Exception as e:
            logger.warning("Topic extraction error: %s", e)
            return [f"Topic {i+1}" for i in range(num_topics)]