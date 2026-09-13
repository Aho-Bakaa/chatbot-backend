"""Retrieval quality eval (no LLM calls — runs fully locally).

For each query: retrieve top-k chunks from the live vector store and check
whether any gold chunk appears in the top-k (hit@k). Also reports MRR and
mean top-1 score. Optional --groundedness phase calls the LLM to answer each
query with its retrieved context and judge support with an LLM judge.

Usage:
    python eval/run_retrieval_eval.py                  # retrieval metrics only
    python eval/run_retrieval_eval.py --groundedness   # + LLM answer/judge (needs key)
    python eval/run_retrieval_eval.py --mock           # deterministic mock LLM (smoke test)
"""

import argparse
import json
import sys

from common import (
    DATA_DIR, RESULTS_DIR, load_json, save_json, pace, mean, parse_json_object,
)

from app.prompts import GROUNDEDNESS_JUDGE_PROMPT, CLASSIFICATION_INSTRUCTION, \
    GROUNDING_CONTEXT_TEMPLATE
from app.rag.store import get_store


def build_mock_client():
    from app.services.llm_client import LLMClient

    class MockLLM(LLMClient):
        def __init__(self):
            pass

        def chat(self, prompt, history=None):
            return "The procedure follows standard lab practice as described in the retrieved context."

        def generate(self, prompt):
            if "supported" in prompt.lower():
                return "YES"
            return "mock"

    return MockLLM()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groundedness", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    dataset = load_json(DATA_DIR / "retrieval_queries.json")
    top_k = dataset["meta"]["top_k"]

    store = get_store()
    results = []
    for item in dataset["queries"]:
        chunks = store.retrieve(item["query"], top_k=top_k)
        chunk_ids = [c[0] for c in chunks]
        hits = [cid for cid in chunk_ids if cid in item["gold_chunks"]]
        rr = 0.0
        for rank, cid in enumerate(chunk_ids, start=1):
            if cid in item["gold_chunks"]:
                rr = 1.0 / rank
                break
        results.append(
            {
                "id": item["id"],
                "query": item["query"],
                "gold_chunks": item["gold_chunks"],
                "retrieved": chunk_ids,
                "scores": [c[2] for c in chunks],
                "hit": bool(hits),
                "reciprocal_rank": rr,
            }
        )

    hit_count = sum(1 for r in results if r["hit"])
    summary = {
        "n_queries": len(results),
        "top_k": top_k,
        "hit_rate_at_k": round(hit_count / len(results), 4),
        "hit_count": hit_count,
        "mrr": round(mean([r["reciprocal_rank"] for r in results]), 4),
        "mean_top1_score": round(mean([r["scores"][0] for r in results if r["scores"]]), 4),
    }

    groundedness_summary = None
    groundedness_rows = []
    if args.groundedness:
        from app.services.llm_client import get_llm_client

        client = build_mock_client() if args.mock else get_llm_client()
        for i, r in enumerate(results):
            if i > 0:
                pace()
            chunks = store.retrieve(r["query"], top_k=top_k)
            context = "\n\n".join(f"[{cid}] {text}" for cid, text, _ in chunks)
            prompt = (
                CLASSIFICATION_INSTRUCTION + "\n\n"
                + GROUNDING_CONTEXT_TEMPLATE.format(passages=context)
                + "\n\nQuestion: " + r["query"]
            )
            answer = client.chat(prompt)
            judge_raw = client.generate(
                GROUNDEDNESS_JUDGE_PROMPT.format(answer=answer, context=context)
            )
            verdict = "no"
            try:
                parsed = parse_json_object(judge_raw)
                verdict = parsed.get("supported", "no")
            except ValueError:
                first_word = judge_raw.strip().split()[0].rstrip(".,").lower() \
                    if judge_raw.strip() else ""
                if first_word in ("yes", "no"):
                    verdict = first_word
            supported = str(verdict).strip().lower().startswith("yes")
            groundedness_rows.append(
                {
                    "id": r["id"],
                    "query": r["query"],
                    "answer": answer,
                    "judge_raw": judge_raw,
                    "supported": supported,
                }
            )
        supported_count = sum(1 for g in groundedness_rows if g["supported"])
        groundedness_summary = {
            "n_queries": len(groundedness_rows),
            "groundedness": round(supported_count / len(groundedness_rows), 4)
            if groundedness_rows else None,
            "supported_count": supported_count,
        }

    out = {
        "meta": dataset["meta"],
        "mock_mode": bool(args.mock),
        "summary": summary,
        "groundedness": groundedness_summary,
        "results": results,
        "groundedness_rows": groundedness_rows,
    }
    save_json(RESULTS_DIR / "retrieval_results.json", out)
    print(json.dumps({"summary": summary, "groundedness": groundedness_summary}, indent=2))


if __name__ == "__main__":
    main()
