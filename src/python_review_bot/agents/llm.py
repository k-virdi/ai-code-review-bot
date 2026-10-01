from __future__ import annotations
from openai import OpenAI
from ..config import get_settings


_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_settings().openai_api_key)
    return _client


def chat(system: str, user: str, *, json_mode: bool = False, temperature: float = 0.1) -> str:
    s = get_settings()
    kwargs = {"model": s.llm_model, "temperature": temperature,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client().chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""
