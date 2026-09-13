# Evaluation Results — Virtual Lab AI

- Generated: 2026-09-13T10:31:32+00:00
- Mode: live (Groq API)
- Guardrail run: PASS (cached); Retrieval run: PASS (cached); Extraction run: PASS (cached)

## 1. Guardrail accuracy (n = 48)

Labeled test set: 20 on-topic, 20 off-topic, 4 adversarial jailbreak-style, and 4 borderline mixed queries. Expected behavior: answer on-topic queries, refuse off-topic and adversarial ones with the canonical refusal sentence. Classification is deterministic: a response containing the canonical refusal sentence counts as refused, otherwise answered.

| Metric | Value | Raw |
|---|---|---|
| Overall accuracy | 95.8% | — |
| On-topic answered correctly | 100.0% | 20/20 |
| Off-topic refused correctly | 100.0% | 20/20 |
| Adversarial refused correctly | 100.0% | 4/4 |
| Borderline mixed handled | 50.0% | — |
| API errors | 0 | — |

## 2. Retrieval quality (n = 18)

Gold-chunk hit rate at k: retrieved top-3 chunks contain at least one gold chunk. Fully local (embeddings + Chroma), no LLM involved.

| Metric | Value | Raw |
|---|---|---|
| Hit rate @ 3 | 94.4% | 17/18 |
| MRR | 0.9167 | — |
| Mean top-1 cosine similarity | 0.7602 | — |

## 3. Groundedness (LLM judge)

Each query is answered with its retrieved chunks injected as grounding context; a second LLM call (gpt-oss-120b) judges whether the answer is consistent with that context (YES/NO, allowing non-conflicting background details).

- Supported: 18/18 (100.0%)

## 4. Extraction & question generation (n = 12 aims)

LLM-judge rubric, 1-3 scale normalized to 0-1: phrase relevance, and question relevance / non-redundancy / difficulty. The JSON-parse fallback rate measures how often the line-split parser had to recover from malformed model output.

| Metric | Value | Raw |
|---|---|---|
| Phrase relevance | 0.8833 | — |
| Question relevance | 0.8028 | — |
| Question non-redundancy | 0.9139 | — |
| Question difficulty | 0.7333 | — |
| JSON fallback rate (phrases) | 0.0% | 0/12 |
| JSON fallback rate (questions) | 0.0% | 0/12 |
| Endpoint errors | 0 | — |

## Methodology notes

- Every run is reproducible: `python eval/run_all.py` (add `--mock` for a no-API smoke test).
- Raw per-query results are in `eval/results/*.json` alongside this file.
- API pacing: 4.5 s between calls to respect LLM provider rate limits.
- Mock-mode numbers are labeled as such and are for harness verification only.
