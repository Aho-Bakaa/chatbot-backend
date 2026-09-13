# Virtual Lab AI — RAG-grounded lab assistant

A FastAPI backend for the **Virtual Labs IIT Roorkee** chat assistant ("Virtual Lab AI"). It wraps a reasoning LLM on Groq (`openai/gpt-oss-120b`) with a retrieval-grounded domain guardrail, and ships with a reproducible evaluation harness and load benchmarks.

This project began as "a prompt wrapped around an API call" and has been upgraded into a small LLM-systems project: real grounding, real evals, real benchmarks, tests, and CI. Every number in `BENCHMARKS.md` was produced by running the scripts in this repo.

## Architecture

```
User message
    │
    ▼
/chat ──► guardrail prompt (domain restriction, single constant)
    │
    ▼
retrieval ──► BGE-small embeddings ──► Chroma (persistent, 20-chunk corpus of
    │                                   lab-safety/procedure reference text)
    ▼
prompt = guardrail + retrieved passages (grounding context) + user question
    │
    ▼
LLM (Groq, openai/gpt-oss-120b) ──► response
```

- **Guardrail**: a domain-restriction system prompt instructing the assistant to refuse out-of-scope questions with a canonical refusal sentence (defined once in `app/prompts.py`).
- **Grounding**: top-k relevant corpus chunks are retrieved (embeddings: `BAAI/bge-small-en-v1.5`, store: Chroma, persistent at `chroma_db/`) and injected into the prompt before generation. The refusal instruction remains as a second layer, not a replacement.
- **Rate limiting**: thread-safe sliding window (default 15 req/min), process-local. *Known scaling limitation*: in-memory, resets on restart, not shared across workers/instances.
- **CORS**: `DEBUG=true` allows `*` (demo convenience); `DEBUG=false` uses the configured `ALLOWED_ORIGINS` list. *Known simplification* — see `.env.example`.
- **Observability**: structured JSON logs for every `/chat` and `/extract_and_questions` call (request id, latency, rate-limiter decision, message/response lengths, retrieved chunk ids/scores). User content itself is never logged.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /chat` | Guardrail + retrieval + LLM response |
| `POST /extract_and_questions` | Extract N key phrases from an experiment aim, then M questions per phrase |
| `POST /speech_to_text` | Not implemented server-side (501); the widget degrades gracefully |
| `GET /healthz` | Health check |
| `GET /` , `/chatbot.css`, `/chatbot.js`, `/aim.md` | Standalone chat widget |

## Repository layout

```
app/
  main.py               # FastAPI app, endpoints, middleware, logging
  config.py             # pydantic-settings 
  prompts.py            # prompt constants (single source of truth)
  rate_limiter.py       # sliding-window limiter
  logging_config.py     # structured JSON logging
  rag/
    corpus.py           # 20 attributed lab-safety/procedure passages
    store.py            # embeddings + Chroma retrieval
    build_index.py      # CLI: rebuild the index
  services/
    llm_client.py        # Groq wrapper
    extraction.py        # phrase extraction + question generation + fallback
eval/                   # evaluation harness (data + runners + RESULTS.md)
benchmarks/             # asyncio+httpx load/latency benchmark
tests/                  # pytest suite (mocked LLM; no network)
chatbot.py              # compatibility shim: `uvicorn chatbot:app`
chatbot.html/css/js     # frontend widget (unchanged)
inject_bot.py           # injects the widget into Virtual Labs simulation pages
aim.md                  # sample experiment aim (widget fetches this per page)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
python -m app.rag.build_index   # build the retrieval index (downloads BGE-small on first run)
uvicorn chatbot:app --host 0.0.0.0 --port 9100
```

Run tests:

```bash
pytest -q
```

## Evaluation & benchmarks

```bash
python eval/run_all.py                  # guardrail + retrieval + groundedness + extraction
python eval/run_all.py --mock           # smoke test without an API key (deterministic stubs)
python benchmarks/run_benchmarks.py     # latency/throughput/burst (needs nothing; e2e needs key)
```

Results: `eval/RESULTS.md` (raw per-query data in `eval/results/*.json`), `benchmarks/results/load_results.json`, and the summary table in `BENCHMARKS.md`.

## Credits

- Corpus passages are condensed paraphrases of public lab-safety guidance (OSHA Laboratory Safety Guidance, National Research Council *Prudent Practices in the Laboratory*, ACS *Safety in Academic Chemistry Laboratories*, CDC/NIH BMBL, NFPA/ANSI fundamentals); each entry carries its source attribution in `app/rag/corpus.py`.
