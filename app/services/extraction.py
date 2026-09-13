"""Extraction / question-generation service for /extract_and_questions.

Returns phrases, questions, and whether the JSON fallback (line-split) path
was used — the fallback rate is a real reliability metric tracked in evals.
"""

import json
import logging
import re

from app.prompts import EXTRACT_PHRASES_PROMPT, GENERATE_QUESTIONS_PROMPT

logger = logging.getLogger("chatbot.extraction")


def _parse_json_array(raw: str):
    """Parse model output as a JSON array of strings. Raises on failure."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, flags=re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            raise
    if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
        raise ValueError("parsed JSON is not a list of strings")
    return [x.strip() for x in parsed if x.strip()]


def _line_split_fallback(raw: str) -> list[str]:
    lines = []
    for line in raw.splitlines():
        cleaned = line.strip()
        cleaned = cleaned.lstrip("-*0123456789.) ").strip()
        lowered = cleaned.lower()
        if not cleaned:
            continue
        if lowered.startswith(("```", "json", "[", "{")):
            continue
        if cleaned.endswith(":"):  # preamble line, e.g. "Here are the phrases:"
            continue
        cleaned = re.sub(r"^[\"'\[\]\{\},]+|[\"'\[\]\{\},]+$", "", cleaned).strip()
        cleaned = cleaned.rstrip(".")
        if cleaned:
            lines.append(cleaned)
    return lines


def run_extraction(client, aim_text: str, num_phrases: int = 5,
                   num_questions_per_phrase: int = 3) -> dict:
    """Extract key phrases from an aim, then generate questions per phrase.

    Returns {"phrases", "questions", "phrases_fallback", "questions_fallback"}.
    """
    extract_prompt = EXTRACT_PHRASES_PROMPT.format(
        num_phrases=num_phrases, aim_text=aim_text
    )
    extraction_raw = client.generate(extract_prompt)

    phrases_fallback = False
    try:
        phrases = _parse_json_array(extraction_raw)
    except Exception:
        phrases_fallback = True
        phrases = _line_split_fallback(extraction_raw)
        logger.info("phrase JSON parse failed; used line-split fallback")

    qgen_prompt = GENERATE_QUESTIONS_PROMPT.format(
        phrases_json=json.dumps(phrases, indent=2),
        num_questions=num_questions_per_phrase,
    )
    qgen_raw = client.generate(qgen_prompt)

    questions_fallback = False
    try:
        questions = _parse_json_array(qgen_raw)
    except Exception:
        questions_fallback = True
        questions = _line_split_fallback(qgen_raw)
        logger.info("question JSON parse failed; used line-split fallback")

    return {
        "phrases": phrases,
        "questions": questions,
        "phrases_fallback": phrases_fallback,
        "questions_fallback": questions_fallback,
    }
