"""Async Ollama client for direct inference."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def close(self):
        await self._client.aclose()

    async def list_models(self) -> list[dict[str, Any]]:
        resp = await self._client.get("/api/tags")
        resp.raise_for_status()
        return resp.json().get("models", [])

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        response_format: dict | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        if response_format:
            payload["format"] = response_format

        start = time.monotonic()
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        duration = time.monotonic() - start

        data = resp.json()
        msg = data.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        prompt_hash = hashlib.sha256(
            json.dumps(messages, sort_keys=True).encode()
        ).hexdigest()[:12]

        return {
            "content": content,
            "thinking": thinking,
            "model": model,
            "duration_s": round(duration, 2),
            "prompt_hash": prompt_hash,
            "eval_count": data.get("eval_count", 0),
            "prompt_eval_count": data.get("prompt_eval_count", 0),
        }

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
