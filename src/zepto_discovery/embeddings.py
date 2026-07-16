"""Embedding provider wrappers.

Provides a thin `GroqClient` wrapper and convenience functions `embed_small`
and `embed_large`. If `GROQ_API_KEY` is not set, these functions fall back to a
deterministic local placeholder embedding (useful for tests and offline dev).

The Groq HTTP contract used here is intentionally generic: it posts JSON to
`{base_url}/v1/embeddings` with payload `{model, input}` and expects a JSON
response containing an `embedding` vector. If Groq's actual API shape differs,
adjust the request/response parsing accordingly.
"""
from __future__ import annotations

import os
import typing
from typing import Callable, List

import requests


class GroqClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.ai")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def embed(self, model: str, text: str) -> List[float]:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set; cannot call Groq API")
        url = f"{self.base_url.rstrip('/')}/v1/embeddings"
        payload = {"model": model, "input": text}
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Best-effort extraction: accept either data['embedding'] or data['data'][0]['embedding']
        if isinstance(data, dict) and "embedding" in data:
            return data["embedding"]
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            first = data["data"][0]
            if isinstance(first, dict) and "embedding" in first:
                return first["embedding"]
        raise RuntimeError("Unexpected Groq embedding response shape: %r" % (data,))


def _placeholder_embed(text: str, dim: int = 128) -> List[float]:
    # Deterministic lightweight embedding: byte values mod mapped into float vector
    b = text.encode("utf8")[: dim]
    vec = [float(x % 256) / 255.0 for x in b]
    # pad to dim
    if len(vec) < dim:
        vec.extend([0.0] * (dim - len(vec)))
    return vec


# Module-level client and convenience functions
_client: GroqClient | None = None


def get_client() -> GroqClient:
    global _client
    if _client is None:
        _client = GroqClient()
    return _client


def _call_or_fallback(model: str, text: str, dim: int = 128) -> List[float]:
    client = get_client()
    try:
        if client.api_key:
            return client.embed(model, text)
        # fallback
        return _placeholder_embed(text, dim=dim)
    except Exception:
        # On any error, return a deterministic placeholder so pipelines keep working
        return _placeholder_embed(text, dim=dim)


def embed_small(text: str) -> List[float]:
    model = os.getenv("GROQ_SMALL_MODEL", "bge-small")
    return _call_or_fallback(model, text, dim=128)


def embed_large(text: str) -> List[float]:
    model = os.getenv("GROQ_LARGE_MODEL", "bge-large")
    return _call_or_fallback(model, text, dim=1024)
