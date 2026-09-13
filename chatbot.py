"""Compatibility shim: re-exports the FastAPI app from the app package.

Keeps `uvicorn chatbot:app` (Dockerfile CMD) and any existing imports working.
"""

from app.main import app  # noqa: F401
