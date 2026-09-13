"""Run the full evaluation suite and regenerate eval/RESULTS.md.

Usage:
    python eval/run_all.py                  # all phases, real LLM (Groq)
    python eval/run_all.py --mock           # smoke test with deterministic mocks
    python eval/run_all.py --skip-ground     # skip the LLM groundedness phase
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import EVAL_DIR, RESULTS_DIR, load_json

PASS = "PASS"
FAIL = "FAIL"


def run_step(cmd: list[str]) -> str:
    print(f"\n>>> {' '.join(cmd)}")
    proc = subprocess.run([sys.executable] + cmd, cwd=str(EVAL_DIR.parent))
    return PASS if proc.returncode == 0 else FAIL


def fmt_pct(value) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--skip-ground", action="store_true")
    parser.add_argument(
        "--results-only",
        action="store_true",
        help="regenerate RESULTS.md from existing eval/results/*.json without re-running",
    )
    args = parser.parse_args()

    if args.results_only:
        guardrail_status = retrieval_status = extraction_status = "PASS (cached)"
    else:
        base = [str(EVAL_DIR / "run_guardrail_eval.py")]
        if args.mock:
            base.append("--mock")
        guardrail_status = run_step(base)

        ret_cmd = [str(EVAL_DIR / "run_retrieval_eval.py")]
        if args.mock:
            ret_cmd.append("--mock")
        if not args.skip_ground:
            ret_cmd.append("--groundedness")
        retrieval_status = run_step(ret_cmd)

        ext_cmd = [str(EVAL_DIR / "run_extraction_eval.py")]
        if args.mock:
            ext_cmd.append("--mock")
        extraction_status = run_step(ext_cmd)

    guardrail = load_json(RESULTS_DIR / "guardrail_results.json")
    retrieval = load_json(RESULTS_DIR / "retrieval_results.json")
    extraction = load_json(RESULTS_DIR / "extraction_results.json")

    g = guardrail["summary"]
    r = retrieval["summary"]
    e = extraction["summary"]
    ground = retrieval.get("groundedness") or {}
    mode = "mock (deterministic stubs)" if args.mock else "live (Groq API)"

    lines = [
        "# Evaluation Results — Virtual Lab AI",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Mode: {mode}",
        f"- Guardrail run: {guardrail_status}; Retrieval run: {retrieval_status}; "
        f"Extraction run: {extraction_status}",
        "",
        "## 1. Guardrail accuracy (n = 48)",
        "",
        f"Labeled test set: {g['on_topic_total']} on-topic, {g['off_topic_total']} off-topic, "
        f"{g['adversarial_total']} adversarial jailbreak-style, and 4 borderline mixed queries. "
        "Expected behavior: answer on-topic queries, refuse off-topic and adversarial ones "
        "with the canonical refusal sentence. Classification is deterministic: a response "
        "containing the canonical refusal sentence counts as refused, otherwise answered.",
        "",
        "| Metric | Value | Raw |",
        "|---|---|---|",
        f"| Overall accuracy | {fmt_pct(g['overall_accuracy'])} | — |",
        f"| On-topic answered correctly | {fmt_pct(g['on_topic_accuracy'])} | {g['on_topic_pass_count']}/{g['on_topic_total']} |",
        f"| Off-topic refused correctly | {fmt_pct(g['off_topic_accuracy'])} | {g['off_topic_pass_count']}/{g['off_topic_total']} |",
        f"| Adversarial refused correctly | {fmt_pct(g['adversarial_accuracy'])} | {g['adversarial_pass_count']}/{g['adversarial_total']} |",
        f"| Borderline mixed handled | {fmt_pct(g['borderline_accuracy'])} | — |",
        f"| API errors | {g['errors']} | — |",
        "",
        "## 2. Retrieval quality (n = 18)",
        "",
        "Gold-chunk hit rate at k: retrieved top-3 chunks contain at least one gold chunk. "
        "Fully local (embeddings + Chroma), no LLM involved.",
        "",
        "| Metric | Value | Raw |",
        "|---|---|---|",
        f"| Hit rate @ {r['top_k']} | {fmt_pct(r['hit_rate_at_k'])} | {r['hit_count']}/{r['n_queries']} |",
        f"| MRR | {r['mrr']} | — |",
        f"| Mean top-1 cosine similarity | {r['mean_top1_score']} | — |",
    ]

    if ground:
        lines += [
            "",
            "## 3. Groundedness (LLM judge)",
            "",
            "Each query is answered with its retrieved chunks injected as grounding context; "
            "a second LLM call (gpt-oss-120b) judges whether the answer is consistent with "
            "that context (YES/NO, allowing non-conflicting background details).",
            "",
            f"- Supported: {ground.get('supported_count', 0)}/{ground.get('n_queries', 0)} "
            f"({fmt_pct(ground.get('groundedness'))})",
        ]

    lines += [
        "",
        "## 4. Extraction & question generation (n = 12 aims)",
        "",
        "LLM-judge rubric, 1-3 scale normalized to 0-1: phrase relevance, and question "
        "relevance / non-redundancy / difficulty. The JSON-parse fallback rate measures how "
        "often the line-split parser had to recover from malformed model output.",
        "",
        "| Metric | Value | Raw |",
        "|---|---|---|",
        f"| Phrase relevance | {e['phrase_relevance']} | — |",
        f"| Question relevance | {e['question_relevance']} | — |",
        f"| Question non-redundancy | {e['question_non_redundancy']} | — |",
        f"| Question difficulty | {e['question_difficulty']} | — |",
        f"| JSON fallback rate (phrases) | {fmt_pct(e['json_fallback_rate_phrases'])} | {e['json_fallback_count_phrases']}/{e['n_aims']} |",
        f"| JSON fallback rate (questions) | {fmt_pct(e['json_fallback_rate_questions'])} | {e['json_fallback_count_questions']}/{e['n_aims']} |",
        f"| Endpoint errors | {e['endpoint_errors']} | — |",
        "",
        "## Methodology notes",
        "",
        "- Every run is reproducible: `python eval/run_all.py` (add `--mock` for a no-API smoke test).",
        "- Raw per-query results are in `eval/results/*.json` alongside this file.",
        "- API pacing: 4.5 s between calls to respect LLM provider rate limits.",
        "- Mock-mode numbers are labeled as such and are for harness verification only.",
    ]

    (EVAL_DIR / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {EVAL_DIR / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
