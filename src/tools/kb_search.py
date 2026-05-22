"""KBSearch — query → ranked list of relevant cards.

Two-tier algorithm:
  1. KEYWORD (cheap, < 5 ms, free): trigger-phrase + title/objective
     substring + bigram overlap. Default min_score=2.5.
  2. SEMANTIC fallback (pgvector + OpenAI embedding, ~150 ms, $0.0001):
     fires only when keyword returns 0 hits OR top score is weak.
     Enabled when `vector_store` + `embedder` are supplied. If they're
     None, search behaves exactly like the old keyword-only path.

Scoring is deterministic — no LLM call here. The LLM extract step
happens in the FAQ Agent AFTER retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.tools.embedder import Embedder
from src.tools.kb_index import KBCard, KBIndex, _tokenize_zh
from src.tools.vector_store import VectorStore

logger = logging.getLogger("tools.kb_search")

# Domain hint words → bump cards in that domain
_DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "soups": ("湯水", "湯", "煲湯", "食譜", "茶飲", "食療"),
    "constitution": ("體質", "氣虛", "陽虛", "陰虛", "濕熱", "痰濕", "血瘀", "氣鬱", "脷"),
    "faq": (),  # generic — no specific keywords
}


@dataclass(frozen=True)
class SearchHit:
    card: KBCard
    score: float
    matched_phrases: tuple[str, ...]
    domain_bonus: float


class KBSearch:
    def __init__(
        self,
        index: KBIndex,
        *,
        vector_store: VectorStore | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self._index = index
        self._vector_store = vector_store
        self._embedder = embedder

    # -- sync keyword-only --

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: float = 3.0,
    ) -> list[SearchHit]:
        return self._keyword_search(query, top_k=top_k, min_score=min_score)

    def _keyword_search(
        self, query: str, *, top_k: int, min_score: float
    ) -> list[SearchHit]:
        if not query or not query.strip():
            return []

        query_lc = query.strip().lower()
        query_bigrams = set(_tokenize_zh(query))

        hits: list[SearchHit] = []
        for card in self._index.all_cards():
            score, matched, dom_bonus = _score_card(card, query_lc, query_bigrams)
            if score >= min_score:
                hits.append(
                    SearchHit(
                        card=card,
                        score=score,
                        matched_phrases=matched,
                        domain_bonus=dom_bonus,
                    )
                )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    # -- async hybrid --

    async def search_async(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: float = 2.5,
        semantic_threshold: float = 0.55,
    ) -> list[SearchHit]:
        """Keyword first; fall back to semantic vector search on miss."""
        if not query or not query.strip():
            return []

        kw_hits = self._keyword_search(query, top_k=top_k, min_score=min_score)
        # Strong keyword result wins (high recall, deterministic)
        if kw_hits and kw_hits[0].score >= min_score + 2.0:
            return kw_hits

        # Semantic fallback
        if self._vector_store is None or self._embedder is None:
            return kw_hits  # no vector — return what we have

        try:
            qvec = await self._embedder.embed_one(query)
            pairs = await self._vector_store.similar(qvec, top_k=top_k * 2)
        except Exception as exc:  # noqa: BLE001
            logger.warning("semantic search failed (%s); keyword only", exc)
            return kw_hits

        sem_hits: list[SearchHit] = []
        for card_id, sim in pairs:
            if sim < semantic_threshold:
                continue
            card = self._index.get_card(card_id)
            if card is None:
                continue
            # Map cosine similarity (0–1) → score in the same range
            # as keyword (~3–15) so downstream code can compare apples.
            sem_hits.append(
                SearchHit(
                    card=card,
                    score=round(sim * 10, 2),  # 0.6 sim → 6.0 score
                    matched_phrases=("semantic",),
                    domain_bonus=0.0,
                )
            )

        # Merge: prefer keyword hits if any, top up with semantic
        seen = {h.card.card_id for h in kw_hits}
        merged = list(kw_hits)
        for h in sem_hits:
            if h.card.card_id in seen:
                continue
            seen.add(h.card.card_id)
            merged.append(h)
            if len(merged) >= top_k:
                break
        merged.sort(key=lambda h: h.score, reverse=True)
        return merged[:top_k]


def _score_card(
    card: KBCard, query_lc: str, query_bigrams: set[str]
) -> tuple[float, tuple[str, ...], float]:
    score = 0.0
    matched: list[str] = []

    # 1. Trigger phrase match — bidirectional substring
    for phrase in card.trigger_conditions:
        p = phrase.strip().lower()
        if not p:
            continue
        if p in query_lc:
            score += 5
            matched.append(phrase)
        elif len(p) >= 4 and query_lc in p:
            # query is contained inside a trigger phrase — weaker match
            score += 2
            matched.append(phrase)

    # 2. Title substring match — if any 2+ char chunk from the query
    # appears in the title verbatim, that's a strong topical signal
    # ("美容" in "中醫面部美容療法" → +4 per matching bigram).
    title_lc = card.title.lower()
    for bg in query_bigrams:
        if len(bg) >= 2 and bg in title_lc:
            score += 4
            matched.append(f"title:{bg}")
            break  # one title hit is enough; don't compound

    # 2b. Objective substring match (slightly weaker than title).
    if card.objective:
        obj_lc = card.objective.lower()
        for bg in query_bigrams:
            if len(bg) >= 2 and bg in obj_lc:
                score += 2
                matched.append(f"objective:{bg}")
                break

    # 3. Title bigram bigram match (intersection set — kept as
    # secondary signal for stem-shared topics).
    title_bigrams = set(_tokenize_zh(card.title))
    overlap = title_bigrams & query_bigrams
    score += 1 * len(overlap)

    # 4. Domain hint bump
    dom_bonus = 0.0
    for hint in _DOMAIN_HINTS.get(card.domain, ()):
        if hint in query_lc:
            dom_bonus += 3
    score += dom_bonus

    return score, tuple(matched), dom_bonus
