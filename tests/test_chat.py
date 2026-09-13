"""Endpoint tests for /chat (mocked LLM — no real API calls)."""

from app.prompts import CLASSIFICATION_INSTRUCTION


def _chat(client, message="How do I balance a centrifuge rotor?"):
    return client.post(
        "/chat",
        json={"message": message, "has_used_before": True, "conversation_history": []},
    )


def test_empty_message_rejected(client):
    resp = _chat(client, message="   ")
    assert resp.status_code == 400
    assert "Empty message" in resp.json()["detail"]


def test_happy_path_returns_mock_response(client):
    resp = _chat(client)
    assert resp.status_code == 200
    assert resp.json()["response"] == "mocked chat reply"


def test_prompt_contains_single_classification_instruction(client, mock_llm):
    _chat(client)
    prompt = mock_llm.chat_prompts[0]
    # The instruction must appear exactly once (deduplicated constant).
    assert prompt.count(CLASSIFICATION_INSTRUCTION) == 1
    assert "How do I balance a centrifuge rotor?" in prompt


def test_conversation_history_is_mapped(client, mock_llm):
    resp = client.post(
        "/chat",
        json={
            "message": "What about fire extinguishers?",
            "has_used_before": True,
            "conversation_history": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
        },
    )
    assert resp.status_code == 200
    assert mock_llm.chat_histories[0] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_rate_limited_returns_429(client, monkeypatch):
    import app.main as main_module
    from app.rate_limiter import RateLimiter

    monkeypatch.setattr(main_module, "chat_rate_limiter", RateLimiter(0))
    resp = _chat(client)
    assert resp.status_code == 429
    assert "Rate limit" in resp.json()["detail"]


def test_retrieval_context_injected_into_prompt(client, mock_llm, fake_store,
                                                monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "retrieval_enabled", True)
    resp = _chat(client)
    assert resp.status_code == 200
    prompt = mock_llm.chat_prompts[0]
    assert "Always wear safety goggles in the lab." in prompt
    assert fake_store.last_query == "How do I balance a centrifuge rotor?"


def test_llm_error_is_caught_and_logged(client, mock_llm):
    def boom(prompt, history=None):
        raise RuntimeError("api down")

    mock_llm.chat = boom
    resp = _chat(client)
    assert resp.status_code == 200  # existing behavior: degrade to error text
    assert "Error from LLM API" in resp.json()["response"]
