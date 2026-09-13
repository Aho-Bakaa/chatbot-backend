"""LLM client for Groq (OpenAI-compatible API).

Designed for testability: FastAPI routes obtain the client through
`get_llm_client()`, which tests and evals can override via
dependency_overrides.
"""

import logging

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger("chatbot.llm")

_client_instance = None


def _build_client() -> "LLMClient":
    global _client_instance
    if _client_instance is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client_instance = GroqClient(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url=settings.groq_base_url,
            max_tokens=settings.llm_max_tokens,
        )
    return _client_instance


class LLMClient:
    """Minimal interface used by the app: chat (with history) and generate."""

    def chat(self, prompt: str, history: list[dict] | None = None) -> str:
        raise NotImplementedError

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class GroqClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str,
                 max_tokens: int = 1000, temperature: float = 0.0):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def _complete(self, messages: list[dict]) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        choice = resp.choices[0]
        if not (choice.message.content or "").strip():
            raise RuntimeError(
                f"empty completion from {self.model} "
                f"(finish_reason={choice.finish_reason})"
            )
        return choice.message.content

    def chat(self, prompt: str, history: list[dict] | None = None) -> str:
        messages = []
        for msg in history or []:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})
        return self._complete(messages)

    def generate(self, prompt: str) -> str:
        return self._complete([{"role": "user", "content": prompt}])


class LazyLLMClient(LLMClient):
    """Resolves the real client only on first use.

    FastAPI resolves `Depends(get_llm_client)` eagerly for every request,
    even in benchmark-bypass mode where the LLM is never called. This wrapper
    defers the API-key check and client construction until chat()/generate().
    """

    def __init__(self):
        self._inner = None

    def _ensure(self) -> LLMClient:
        if self._inner is None:
            self._inner = _build_client()
        return self._inner

    def chat(self, prompt: str, history: list[dict] | None = None) -> str:
        return self._ensure().chat(prompt, history)

    def generate(self, prompt: str) -> str:
        return self._ensure().generate(prompt)


_lazy_instance = None


def get_llm_client() -> LLMClient:
    global _lazy_instance
    if _lazy_instance is None:
        _lazy_instance = LazyLLMClient()
    return _lazy_instance
