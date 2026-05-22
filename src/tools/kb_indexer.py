"""KB → vector store indexer.

Idempotent: on each call, walks all loaded KB cards, hashes a canonical
doc representation, and re-embeds only the cards whose hash changed.

Doc text for each card is built from title + objective + top trigger
phrases + a slice of core_answer. That's the text we embed and search
against.

Called from web.py lifespan on startup. Safe to call multiple times.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from src.tools.embedder import Embedder
from src.tools.kb_index import KBCard, KBIndex
from src.tools.vector_store import VectorStore

logger = logging.getLogger("tools.kb_indexer")


def _build_doc_text(card: KBCard) -> str:
    """Compose the embedding input for a card."""
    parts: list[str] = []
    if card.title:
        parts.append(f"標題：{card.title}")
    if card.objective:
        parts.append(f"概要：{card.objective[:400]}")
    # Top 10 trigger phrases (already manually curated)
    if card.trigger_conditions:
        triggers = "、".join(card.trigger_conditions[:10])
        parts.append(f"關鍵詞：{triggers}")
    # First 600 chars of core_answer for topical context
    if card.core_answer:
        parts.append(f"內容：{card.core_answer[:600]}")
    return "\n".join(parts)


def _doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def index_kb(
    *,
    kb: KBIndex,
    store: VectorStore,
    embedder: Embedder,
) -> dict[str, int]:
    """Index all KB cards. Returns counts dict {indexed, skipped, total}."""
    t0 = time.time()
    existing_hashes = await store.card_hashes()
    cards = kb.all_cards()
    logger.info(
        "kb_indexer: %d cards, %d already in vector store",
        len(cards), len(existing_hashes),
    )

    to_embed: list[tuple[KBCard, str, str]] = []
    skipped = 0
    for c in cards:
        doc = _build_doc_text(c)
        h = _doc_hash(doc)
        if existing_hashes.get(c.card_id) == h:
            skipped += 1
            continue
        to_embed.append((c, doc, h))

    if not to_embed:
        logger.info("kb_indexer: all %d cards up to date", len(cards))
        return {"indexed": 0, "skipped": skipped, "total": len(cards)}

    # Batch embed (OpenAI handles up to 2048 input strings per request)
    texts = [doc for _, doc, _ in to_embed]
    logger.info("kb_indexer: embedding %d cards…", len(texts))
    vectors = await embedder.embed_many(texts)
    if len(vectors) != len(to_embed):
        raise RuntimeError(
            f"embedder returned {len(vectors)} vectors for {len(to_embed)} cards"
        )

    for (card, doc, h), vec in zip(to_embed, vectors):
        await store.upsert(card.card_id, card.title, doc, h, vec)

    dt = time.time() - t0
    logger.info(
        "kb_indexer: ✓ indexed %d cards in %.2fs (skipped %d)",
        len(to_embed), dt, skipped,
    )
    return {"indexed": len(to_embed), "skipped": skipped, "total": len(cards)}
