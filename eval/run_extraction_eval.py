"""Extraction / question-generation quality eval.

For each aim: call the real /extract_and_questions endpoint (in-process
TestClient), then score phrases (relevance) and questions (relevance,
non-redundancy, difficulty) with an LLM-judge rubric. Also records how often
the JSON line-split fallback triggered — a real reliability metric.

Usage:
    python eval/run_extraction_eval.py            # real LLM (Groq)
    python eval/run_extraction_eval.py --mock     # deterministic mock (smoke test)
"""

import argparse
import json
import sys

from fastapi.testclient import TestClient

from common import DATA_DIR, RESULTS_DIR, load_json, save_json, pace, mean, \
    parse_json_object, lift_app_rate_limit

JUDGE_PROMPT = """You are grading the output of an automatic key-phrase extraction and \
question-generation step for a virtual lab experiment.

Experiment aim: {aim}

Extracted phrases (numbered):
{phrases}

Generated questions (numbered):
{questions}

Score each phrase 1-3 on RELEVANCE to the aim (3 = core concept of the aim, \
2 = related but secondary, 1 = irrelevant).
Score each question 1-3 on three dimensions: RELEVANCE (does it test the phrase's concept), \
NON_REDUNDANCY (3 = distinct from other questions, 1 = near-duplicate), \
DIFFICULTY (3 = appropriate comprehension check for a student, 1 = trivial or absurd).

Return strict JSON only:
{{"phrase_scores": [int, ...], "question_scores": [{{"relevance": int, "non_redundancy": int, \
"difficulty": int}}, ...]}}
"""


def build_mock_client():
    from app.services.llm_client import LLMClient

    class MockLLM(LLMClient):
        def __init__(self):
            self.n = 0

        def generate(self, prompt):
            self.n += 1
            if "You are grading" in prompt:
                return (
                    '{"phrase_scores": [3, 3, 3, 2, 2], '
                    '"question_scores": [{"relevance": 3, "non_redundancy": 3, "difficulty": 3}'
                    ', {"relevance": 3, "non_redundancy": 3, "difficulty": 3}'
                    ', {"relevance": 2, "non_redundancy": 3, "difficulty": 2}]}'
                )
            if self.n % 2 == 1:
                return '["voltage gain", "input impedance", "output impedance", "frequency response", "common-emitter amplifier"]'
            return '["What is voltage gain?", "What is input impedance?", "What is output impedance?"]'

    return MockLLM()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    from app.main import app
    from app.services.llm_client import get_llm_client

    lift_app_rate_limit()
    client = TestClient(app)
    if args.mock:
        app.dependency_overrides[get_llm_client] = build_mock_client

    dataset = load_json(DATA_DIR / "extraction_aims.json")
    aims = dataset["aims"]

    rows = []
    for i, item in enumerate(aims):
        if i > 0:
            pace()
        resp = client.post(
            "/extract_and_questions",
            json={
                "aim_text": item["aim"],
                "num_phrases": dataset["meta"]["num_phrases"],
                "num_questions_per_phrase": dataset["meta"]["num_questions_per_phrase"],
            },
        )
        if resp.status_code != 200:
            rows.append(
                {
                    "id": item["id"], "status": resp.status_code,
                    "phrases": [], "questions": [],
                    "phrases_fallback": False, "questions_fallback": False,
                    "judge_raw": None, "scores": None,
                }
            )
            continue
        body = resp.json()
        row = {
            "id": item["id"],
            "status": resp.status_code,
            "phrases": body["phrases"],
            "questions": body["questions"],
            "phrases_fallback": body.get("phrases_fallback", False),
            "questions_fallback": body.get("questions_fallback", False),
        }
        # Judge the output
        judge_raw = None
        scores = None
        if body["phrases"] or body["questions"]:
            judge_prompt = JUDGE_PROMPT.format(
                aim=item["aim"],
                phrases="\n".join(f"{j + 1}. {p}" for j, p in enumerate(body["phrases"])),
                questions="\n".join(f"{j + 1}. {q}" for j, q in enumerate(body["questions"])),
            )
            try:
                judge_client = (
                    build_mock_client() if args.mock else get_llm_client()
                )
                judge_raw = judge_client.generate(judge_prompt)
                scores = parse_json_object(judge_raw)
            except Exception as exc:
                judge_raw = f"JUDGE_ERROR: {exc}"
                scores = None
        row["judge_raw"] = judge_raw
        row["scores"] = scores
        rows.append(row)

    phrase_relevances = []
    question_scores = {"relevance": [], "non_redundancy": [], "difficulty": []}
    judged_aims = 0
    for row in rows:
        if not row.get("scores"):
            continue
        judged_aims += 1
        ps = row["scores"].get("phrase_scores", [])
        qs = row["scores"].get("question_scores", [])
        if not isinstance(ps, list):
            continue
        for s in ps:
            if isinstance(s, (int, float)) and 1 <= s <= 3:
                phrase_relevances.append(s)
        if isinstance(qs, list):
            for q in qs:
                if isinstance(q, dict):
                    for dim in question_scores:
                        v = q.get(dim)
                        if isinstance(v, (int, float)) and 1 <= v <= 3:
                            question_scores[dim].append(v)

    def norm(scores):
        return round(mean([(s - 1) / 2 for s in scores]), 4) if scores else None

    fallback_phrases = sum(1 for r in rows if r.get("phrases_fallback"))
    fallback_questions = sum(1 for r in rows if r.get("questions_fallback"))
    total_rows = sum(1 for r in rows if r["status"] == 200)

    summary = {
        "mock_mode": bool(args.mock),
        "n_aims": len(aims),
        "endpoint_errors": sum(1 for r in rows if r["status"] != 200),
        "judged_aims": judged_aims,
        "phrase_relevance": norm(phrase_relevances),
        "question_relevance": norm(question_scores["relevance"]),
        "question_non_redundancy": norm(question_scores["non_redundancy"]),
        "question_difficulty": norm(question_scores["difficulty"]),
        "mean_phrase_count": round(
            mean([len(r.get("phrases", [])) for r in rows if r["status"] == 200]), 2
        ),
        "mean_question_count": round(
            mean([len(r.get("questions", [])) for r in rows if r["status"] == 200]), 2
        ),
        "json_fallback_rate_phrases": round(fallback_phrases / total_rows, 4) if total_rows else None,
        "json_fallback_rate_questions": round(fallback_questions / total_rows, 4) if total_rows else None,
        "json_fallback_count_phrases": fallback_phrases,
        "json_fallback_count_questions": fallback_questions,
    }

    out = {"meta": dataset["meta"], "summary": summary, "rows": rows}
    save_json(RESULTS_DIR / "extraction_results.json", out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
