"""Virtual Lab AI — FastAPI backend.

Pipeline: guardrail prompt -> retrieval grounding (RAG) -> Gemini -> response.

Compatibility shim: `chatbot.py` at the repo root re-exports this `app` object,
so the Dockerfile (`uvicorn chatbot:app`) and any existing imports keep working.
"""

import logging
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

from app.config import get_settings
from app.logging_config import setup_logging, get_logger
from app.prompts import CLASSIFICATION_INSTRUCTION, GROUNDING_CONTEXT_TEMPLATE
from app.rate_limiter import RateLimiter
from app.rag.store import get_store
from app.services.extraction import run_extraction
from app.services.llm_client import get_llm_client

settings = get_settings()
setup_logging(settings.log_file)
logger = get_logger("chatbot.api")

app = FastAPI(title="Virtual Lab AI", version="2.0.0")

# Known simplification: DEBUG=True allows any CORS origin (demo convenience).
# In production set DEBUG=false and configure ALLOWED_ORIGINS explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: process-local, in-memory rate limiter. Resets on restart and does not
# scale across multiple workers/instances (see rate_limiter.py).
chat_rate_limiter = RateLimiter(max_per_minute=settings.rate_limit_per_minute)

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def _log_call(request: Request, event: str, **fields):
    extra = {
        "request_id": getattr(request.state, "request_id", None),
        "endpoint": request.url.path,
    }
    extra.update(fields)
    logger.info(event, extra=extra)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    has_used_before: bool
    conversation_history: Optional[List[ChatMessage]] = []


class ExtractionRequest(BaseModel):
    aim_text: str
    num_phrases: Optional[int] = 5
    num_questions_per_phrase: Optional[int] = 3


class ExtractionResponse(BaseModel):
    phrases: List[str]
    questions: List[str]
    phrases_fallback: bool = False
    questions_fallback: bool = False


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/chat")
async def chat_endpoint(req: ChatRequest, request: Request, client=Depends(get_llm_client)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message not allowed.")

    if not chat_rate_limiter.allow():
        _log_call(request, "chat.rate_limited", rate_limit_allowed=False,
                  message_len=len(req.message))
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please wait a minute and retry."},
        )

    t0 = time.perf_counter()
    retrieval_chunks = []
    if settings.retrieval_enabled:
        try:
            retrieval_chunks = get_store().retrieve(req.message)
        except Exception as exc:  # degrade gracefully if the store is unavailable
            logger.warning("retrieval failed; continuing without grounding",
                           extra={"error": str(exc)})

    prompt = CLASSIFICATION_INSTRUCTION + "\n\n"
    if retrieval_chunks:
        passages = "\n\n".join(
            f"[{doc_id}] {text}" for doc_id, text, _score in retrieval_chunks
        )
        prompt += GROUNDING_CONTEXT_TEMPLATE.format(passages=passages)
    prompt += f"\nUser question:\n{req.message}"

    try:
        if settings.benchmark_bypass_llm:
            response_text = (
                "[benchmark-mode] Deterministic response for load testing. "
                f"Retrieved {len(retrieval_chunks)} grounding chunk(s)."
            )
        else:
            history = [m.model_dump() for m in (req.conversation_history or [])]
            response_text = client.chat(prompt, history=history)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        _log_call(request, "chat.error", latency_ms=latency_ms,
                  rate_limit_allowed=True, message_len=len(req.message),
                  response_len=0, retrieval_enabled=settings.retrieval_enabled,
                  retrieval_chunks=[c[0] for c in retrieval_chunks],
                  retrieval_scores=[c[2] for c in retrieval_chunks],
                  status=500, error=str(exc))
        return {"response": f"Error from LLM API: {str(exc)}"}

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    _log_call(request, "chat.completed", latency_ms=latency_ms,
              rate_limit_allowed=True, message_len=len(req.message),
              response_len=len(response_text),
              retrieval_enabled=settings.retrieval_enabled,
              retrieval_chunks=[c[0] for c in retrieval_chunks],
              retrieval_scores=[c[2] for c in retrieval_chunks],
              status=200)
    return {"response": response_text}


@app.post("/extract_and_questions", response_model=ExtractionResponse)
async def extract_and_questions(req: ExtractionRequest, request: Request,
                                client=Depends(get_llm_client)):
    if not req.aim_text.strip():
        raise HTTPException(status_code=400, detail="Empty aim not allowed.")

    if not chat_rate_limiter.allow():
        _log_call(request, "extract.rate_limited", rate_limit_allowed=False,
                  message_len=len(req.aim_text))
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please wait a minute and retry."},
        )

    t0 = time.perf_counter()
    try:
        result = run_extraction(
            client,
            req.aim_text,
            num_phrases=req.num_phrases or 5,
            num_questions_per_phrase=req.num_questions_per_phrase or 3,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        _log_call(request, "extract.error", latency_ms=latency_ms,
                  rate_limit_allowed=True, message_len=len(req.aim_text),
                  response_len=0, status=500, error=str(exc))
        return {"phrases": [], "questions": [],
                "detail": f"Error from LLM API: {str(exc)}"}

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    response_len = sum(len(p) for p in result["phrases"]) + sum(
        len(q) for q in result["questions"]
    )
    _log_call(request, "extract.completed", latency_ms=latency_ms,
              rate_limit_allowed=True, message_len=len(req.aim_text),
              response_len=response_len, status=200,
              phrases_fallback=result["phrases_fallback"],
              questions_fallback=result["questions_fallback"])
    return ExtractionResponse(**result)


@app.post("/speech_to_text")
async def speech_to_text():
    """Voice input is not implemented server-side; the widget degrades gracefully."""
    return JSONResponse(
        status_code=501,
        content={"text": "", "detail": "Speech-to-text not implemented."},
    )


@app.get("/")
async def widget():
    return FileResponse(os.path.join(_REPO_ROOT, "chatbot.html"))


@app.get("/chatbot.css")
async def widget_css():
    return FileResponse(os.path.join(_REPO_ROOT, "chatbot.css"))


@app.get("/chatbot.js")
async def widget_js():
    return FileResponse(os.path.join(_REPO_ROOT, "chatbot.js"))


@app.get("/aim.md")
async def widget_aim():
    path = os.path.join(_REPO_ROOT, "aim.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="aim.md not found.")
    return FileResponse(path)


app.mount("/static", StaticFiles(directory=os.path.join(_REPO_ROOT, "static")), name="static")
