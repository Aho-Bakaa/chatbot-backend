"""Structured JSON logging for the API.

Every /chat and /extract_and_questions call emits one JSON log line with:
timestamp, request id, endpoint, latency, rate-limiter decision, and
message/response lengths (never full user content).
"""

import json
import logging
import sys
from datetime import datetime, timezone

_EXTRA_FIELDS = {
    "request_id",
    "endpoint",
    "latency_ms",
    "rate_limit_allowed",
    "message_len",
    "response_len",
    "retrieval_chunks",
    "retrieval_scores",
    "retrieval_enabled",
    "phrases_fallback",
    "questions_fallback",
    "embedding_model",
    "status",
    "error",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key in _EXTRA_FIELDS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(log_file: str = "") -> None:
    root = logging.getLogger("chatbot")
    if root.handlers:  # already configured (e.g. tests)
        return
    root.setLevel(logging.INFO)

    handler: logging.Handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(JsonFormatter())
        root.addHandler(fh)


def get_logger(name: str = "chatbot.api") -> logging.Logger:
    return logging.getLogger(name)
