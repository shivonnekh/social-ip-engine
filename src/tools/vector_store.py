"""pgvector-backed semantic KB store.

Schema (in CRM Postgres):
    kb_embeddings (
        card_id    text primary key,
        title      text,
        chunk_text text,
        doc_hash   text,
        embedding  vector(1536)
    )
    CREATE INDEX ON kb_embeddings USING ivfflat (embedding vector_cosine_ops);

Re-uses the same Postgres database we have for CRM — no extra service.

Index workflow:
  1. on app startup, ensure_schema()
  2. indexer reads all KB cards
  3. for each card, computes doc_hash; skip if unchanged
  4. embed + upsert otherwise

Search:
    similar_cards(query_embedding, top_k=5) → [(card_id, similarity), ...]
"""

from __future__ import annotations

import logging
from typing import Sequence

import asyncpg
from pgvector.asyncpg import register_vector

from src.tools.embedder import EMBED_DIM

logger = logging.getLogger("tools.vector_store")


SCHEMA_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS kb_embeddings (
    card_id     TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    chunk_text  TEXT NOT NULL,
    doc_hash    TEXT NOT NULL,
    embedding   vector({EMBED_DIM})
);
"""


class VectorStore:
    """Thin wrapper around pgvector for KB embeddings."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "VectorStore":
        # Postgres URL normalization
        if dsn.startswith("postgres://"):
            dsn = "postgresql://" + dsn[len("postgres://") :]
        pool = await asyncpg.create_pool(
            dsn, min_size=1, max_size=3, command_timeout=30
        )
        async with pool.acquire() as conn:
            for stmt in [s for s in SCHEMA_SQL.split(";") if s.strip()]:
                await conn.execute(stmt + ";")
            await register_vector(conn)
        # Try ivfflat index, but ignore if too few rows
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS kb_embeddings_ivfflat "
                    "ON kb_embeddings USING ivfflat (embedding vector_cosine_ops);"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("ivfflat index skipped: %s", exc)
        logger.info("VectorStore connected and schema ready")
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    # ----- index -----

    async def upsert(
        self,
        card_id: str,
        title: str,
        chunk_text: str,
        doc_hash: str,
        embedding: Sequence[float],
    ) -> None:
        async with self._pool.acquire() as conn:
            await register_vector(conn)
            await conn.execute(
                """
                INSERT INTO kb_embeddings (card_id, title, chunk_text, doc_hash, embedding)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (card_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    chunk_text = EXCLUDED.chunk_text,
                    doc_hash = EXCLUDED.doc_hash,
                    embedding = EXCLUDED.embedding
                """,
                card_id, title, chunk_text, doc_hash, list(embedding),
            )

    async def card_hashes(self) -> dict[str, str]:
        """Return {card_id: doc_hash} for all indexed cards."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT card_id, doc_hash FROM kb_embeddings")
        return {r["card_id"]: r["doc_hash"] for r in rows}

    async def count(self) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM kb_embeddings") or 0

    # ----- search -----

    async def similar(
        self, query_embedding: Sequence[float], *, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """Return [(card_id, cosine_similarity), ...] for top-k nearest."""
        async with self._pool.acquire() as conn:
            await register_vector(conn)
            rows = await conn.fetch(
                """
                SELECT card_id, 1 - (embedding <=> $1) AS similarity
                FROM kb_embeddings
                ORDER BY embedding <=> $1
                LIMIT $2
                """,
                list(query_embedding), top_k,
            )
        return [(r["card_id"], float(r["similarity"])) for r in rows]
