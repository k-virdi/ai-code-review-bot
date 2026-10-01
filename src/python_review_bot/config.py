from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PRB_", extra="ignore")

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"

    chroma_dir: str = ".chroma"
    knowledge_dir: str = "data/knowledge"
    collection: str = "prb_knowledge"

    max_attempts: int = 3
    sandbox_timeout: int = 10
    top_k: int = 6


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.openai_api_key:
        import os
        s.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    return s
