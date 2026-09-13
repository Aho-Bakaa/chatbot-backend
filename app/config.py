"""Application settings loaded from .env / environment via pydantic-settings.

Priority: constructor args > .env file > process environment. The .env-first
order is deliberate for this project: the developer machine carries a stale
machine-wide GROQ_API_KEY, and the project-local .env must win. Use the
APP_ENV_FILE environment variable (or constructor arg) to point at a
different env file (benchmarks do this).
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_max_tokens: int = 2000

    rate_limit_per_minute: int = 15

    debug: bool = True
    # Comma-separated list; used when DEBUG=false.
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    retrieval_enabled: bool = True
    retrieval_top_k: int = 3
    retrieval_min_score: float = 0.25

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chroma_dir: str = "chroma_db"

    benchmark_bypass_llm: bool = False

    log_file: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # .env file takes precedence over process environment variables.
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)

    @property
    def cors_origins(self) -> list[str]:
        """Demo convenience: DEBUG=True allows any origin; otherwise a fixed list."""
        if self.debug:
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


def _resolve_env_file() -> str | None:
    env_file = os.getenv("APP_ENV_FILE") or ".env"
    if os.path.exists(env_file):
        return env_file
    return None


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=_resolve_env_file())
