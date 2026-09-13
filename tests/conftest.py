"""Shared pytest fixtures: mock LLM client, retrieval isolation."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402


class MockLLM:
    """Deterministic LLM stub — unit tests never hit the real API."""

    def __init__(self, chat_reply="mocked chat reply", generate_reply='["a", "b"]'):
        self.chat_reply = chat_reply
        self.generate_reply = generate_reply
        self.chat_prompts: list[str] = []
        self.chat_histories: list[list[dict]] = []
        self.generate_prompts: list[str] = []

    def chat(self, prompt, history=None):
        self.chat_prompts.append(prompt)
        self.chat_histories.append(history or [])
        return self.chat_reply

    def generate(self, prompt):
        self.generate_prompts.append(prompt)
        return self.generate_reply


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def client(mock_llm, monkeypatch):
    from app.main import app
    from app.services.llm_client import get_llm_client

    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    # Isolate tests from the real retrieval store and any persisted state.
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "retrieval_enabled", False)
    main_module.chat_rate_limiter.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def fake_store(monkeypatch):
    """A retrieval store stub for prompt-grounding tests."""
    import app.main as main_module

    class FakeStore:
        def __init__(self):
            self.last_query = None

        def retrieve(self, query, top_k=None, min_score=None):
            self.last_query = query
            return [("chunk-a", "Always wear safety goggles in the lab.", 0.95)]

    fake = FakeStore()
    monkeypatch.setattr(main_module, "get_store", lambda: fake)
    return fake
