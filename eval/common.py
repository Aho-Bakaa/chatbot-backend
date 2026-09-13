"""Shared helpers for the evaluation harness.

IMPORTANT: import this module before importing `app.*` so that the app-level
rate limiter can be lifted for eval runs (pacing against the LLM provider's
limits is handled by `pace()` instead).
"""

import json
import os
import re
import sys
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
DATA_DIR = EVAL_DIR / "data"
RESULTS_DIR = EVAL_DIR / "results"

REPO_ROOT = EVAL_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

# 4.5 s spacing keeps us comfortably under the provider RPM limits.
PACE_SECONDS = float(os.environ.get("EVAL_PACE_SECONDS", "4.5"))


def lift_app_rate_limit() -> None:
    """Replace the app-level rate limiter with a no-op for in-process evals."""
    import app.main as main_module
    from app.rate_limiter import RateLimiter

    main_module.chat_rate_limiter = RateLimiter(max_per_minute=10**6)


def pace():
    time.sleep(PACE_SECONDS)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def parse_json_object(raw: str):
    """Parse model output as a JSON object; tolerates surrounding prose."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("no JSON object found in model output")


def mean(values) -> float:
    return sum(values) / len(values) if values else 0.0
