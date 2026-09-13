# Benchmarks — Virtual Lab AI

Every number in this file was produced by running the scripts in this repo on
2026-09-13. Nothing here is estimated or extrapolated.

- LLM: `openai/gpt-oss-120b` on Groq (OpenAI-compatible API), max_tokens 2000, temperature 0.
- Embeddings: `BAAI/bge-small-en-v1.5` (384-dim), Chroma persistent collection, 20-passage
  lab-safety/procedure corpus.
- Guardrail, retrieval, groundedness, extraction: `python eval/run_all.py` (raw data in
  `eval/results/*.json`, methodology in `eval/RESULTS.md`).
- Load/latency: `python benchmarks/run_benchmarks.py` (raw data in
  `benchmarks/results/load_results.json`).

## Summary table

| Metric | Value | Raw |
|---|---|---|
| Guardrail accuracy (overall) | 95.8% | 46/48 labeled queries |
| Guardrail accuracy (adversarial subset) | 100% | 4/4 jailbreak-style queries refused |
| Guardrail accuracy (on-topic) | 100% | 20/20 answered |
| Guardrail accuracy (off-topic) | 100% | 20/20 refused |
| Retrieval hit rate @3 | 94.4% | 17/18 gold chunks in top-3 |
| Retrieval MRR | 0.917 | n=18 |
| Groundedness (LLM judge) | 100% | 18/18 answers consistent with retrieved context |
| Extraction — phrase relevance | 0.883 | 1-3 rubric normalized to 0-1, n=12 aims |
| Extraction — question relevance | 0.803 | same rubric |
| Extraction — question non-redundancy | 0.914 | same rubric |
| Extraction — question difficulty | 0.733 | same rubric |
| JSON-parse fallback rate (extraction) | 0.0% | 0/12 phrases, 0/12 questions |
| p50 / p95 / p99 latency, 10 concurrent users (app-layer, retrieval ON) | 1224.9 / 1438.9 / 1445.0 ms | 200 requests |
| p50 / p95 / p99 latency, 10 concurrent users (app-layer, retrieval OFF) | 35.2 / 186.4 / 285.5 ms | 200 requests |
| End-to-end latency incl. LLM (sequential, n=10) | p50 2494.1 ms, mean 10191.3 ms, p95 77894.4 ms | 1 request hit a ~78 s provider-side queue spike |
| Burst behavior (60 simultaneous requests, 30 req/min limit) | 30 allowed, 30 rejected with HTTP 429, 0 errors | graceful degradation |
| Max observed throughput, retrieval OFF (25 users) | 162.3 req/s | — |
| Max observed throughput, retrieval ON (25 users) | 2.3 req/s | thread contention in embed/Chroma path |

## Notes on the numbers

- **Guardrail**: classification is deterministic — a response containing the canonical refusal
  sentence counts as "refused". The borderline subset (mixed on/off-topic queries) scored 50%
  (2/4): the guardrail conservatively refused two queries that contained a lab question
  alongside off-topic content. This is the known failure mode of a pure prompt guardrail.
- **Retrieval**: hit@3 = 17/18. The single miss ("Where should volatile solvents be handled?"
  → gold `fume-hood`) retrieved `acid-base` at rank 1, which does mention handling volatiles in
  a fume hood — a semantically defensible miss, kept as-is rather than re-tuning the corpus to
  make the number prettier.
- **Groundedness judge**: a second `gpt-oss-120b` call scores YES/NO on whether the answer is
  consistent with the retrieved context (non-conflicting background detail allowed). 18/18 YES.
- **RAG cost**: at 10 concurrent users the retrieval path adds ~1.2 s to p50 latency
  (1224.9 ms vs 35.2 ms without). The retrieval bottleneck is thread contention in the
  in-process embedder/Chroma call path, not the vector search itself.
- **Rate limiting**: the in-process sliding-window limiter degrades gracefully — a 60-request
  burst against a 30/min limit produced exactly 30 × 200 and 30 × 429, zero errors. It remains
  process-local (documented limitation for multi-worker deployments).
