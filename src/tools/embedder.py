"""OpenAI text embedding client — text-embedding-3-small (1536 dim, $0.02/M tokens).

Cheap, fast, multilingual (handles HK Cantonese + simplified Chinese + English).
For our scale (52 cards + per-query) cost is < $0.10/year.
"""

from __future__ import annotations

import logging
import os
from typing import Sequence

from openai import AsyncOpenAI

logger = logging.getLogger("tools.embedder")

EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536  # text-embedding-3-small dimension


class Embedder:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI()

    async def embed_one(self, text: str) -> list[float]:
        resp = await self._client.embeddings.create(
            model=EMBED_MODEL, input=[text]
        )
        return list(resp.data[0].embedding)

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = await self._client.embeddings.create(
            model=EMBED_MODEL, input=list(texts)
        )
        return [list(d.embedding) for d in resp.data]
