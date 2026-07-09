"""Unified LLM client — Local (Ollama), Cloud (OpenAI-compatible), dan llama.cpp."""

from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import (
    CLOUD_API_KEY,
    CLOUD_API_URL,
    CLOUD_MODEL,
    CLOUD_REFERER,
    CLOUD_TITLE,
    LLAMACPP_API_URL,
    LLAMACPP_MODEL,
    LLAMACPP_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)


class LLMClient:
    def __init__(self, provider: str, model: Optional[str] = None):
        self.provider = provider
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        if self.provider == "cloud":
            return await self._cloud(prompt, **kwargs)
        if self.provider == "llamacpp":
            return await self._llamacpp(prompt, **kwargs)
        return await self._local(prompt, **kwargs)

    async def _local(self, prompt: str, **kwargs) -> str:
        model = self.model or OLLAMA_MODEL
        timeout = kwargs.get("timeout", OLLAMA_TIMEOUT)
        temperature = kwargs.get("temperature", 0.3)
        num_predict = kwargs.get("num_predict", 512)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,
                    },
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()

    async def _cloud(self, prompt: str, **kwargs) -> str:
        model = self.model or CLOUD_MODEL
        timeout = kwargs.get("timeout", 120)
        temperature = kwargs.get("temperature", 0.3)
        max_tokens = kwargs.get("max_tokens", 512)

        client = AsyncOpenAI(
            api_key=CLOUD_API_KEY,
            base_url=CLOUD_API_URL,
            default_headers={
                "HTTP-Referer": CLOUD_REFERER,
                "X-Title": CLOUD_TITLE,
            },
            timeout=timeout,
        )
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    async def _llamacpp(self, prompt: str, **kwargs) -> str:
        model = self.model or LLAMACPP_MODEL
        timeout = kwargs.get("timeout", LLAMACPP_TIMEOUT)
        temperature = kwargs.get("temperature", 0.3)
        max_tokens = kwargs.get("max_tokens", 2048)

        client = AsyncOpenAI(
            api_key="",
            base_url=LLAMACPP_API_URL,
            timeout=timeout,
        )
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    async def check_health(self) -> bool:
        try:
            if self.provider == "cloud":
                return bool(CLOUD_API_KEY)
            if self.provider == "llamacpp":
                async with httpx.AsyncClient(timeout=5) as client:
                    r = await client.get(f"{LLAMACPP_API_URL}/models")
                    return r.status_code == 200
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{OLLAMA_HOST}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
