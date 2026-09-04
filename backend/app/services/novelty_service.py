"""Headline novelty scoring + news deduplication via ChromaDB.

Ten articles about the same CEO resignation should collapse into one event,
not ten alerts (Part 16). A headline is compared against previously-seen
headlines for the same symbol; if it's semantically close to one already
stored, it's treated as the same underlying event rather than a new signal.
"""

import hashlib
import logging
from datetime import datetime

from app.core.chroma_client import get_headlines_collection
from app.schemas.events import ClassifiedEvent, EventType
from app.services.embeddings import embed_texts
from app.services.event_classifier import classify_headline

logger = logging.getLogger(__name__)

# L2 distance over normalized embeddings; below this, headlines are treated
# as describing the same underlying event rather than distinct news.
DUPLICATE_DISTANCE_THRESHOLD = 0.5
# Above this distance, a headline is scored as fully novel.
NOVEL_DISTANCE_CEILING = 1.2


def _event_id(symbol: str, title: str, timestamp: datetime) -> str:
    raw = f"{symbol}|{title}|{timestamp.date().isoformat()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]  # noqa: S324


async def classify_and_dedupe(
    symbol: str, headlines: list[tuple[str, str | None, str | None, datetime]]
) -> list[ClassifiedEvent]:
    """headlines: list of (title, publisher, link, published_at)."""
    if not headlines:
        return []

    collection = get_headlines_collection()
    titles = [h[0] for h in headlines]
    vectors = await embed_texts(titles)

    results: list[ClassifiedEvent] = []
    for (title, publisher, link, published_at), vector in zip(headlines, vectors, strict=True):
        event_id = _event_id(symbol, title, published_at)
        event_type, impact_score = classify_headline(title)

        novelty_score = 100.0
        is_duplicate_of = None

        if collection is not None:
            try:
                existing = collection.query(
                    query_embeddings=[vector],
                    n_results=1,
                    where={"symbol": symbol},
                )
                dist_lists = existing.get("distances") or []
                if dist_lists and dist_lists[0]:
                    distance = dist_lists[0][0]
                    matched_id = existing["ids"][0][0]
                    if distance <= DUPLICATE_DISTANCE_THRESHOLD:
                        novelty_score = 5.0
                        is_duplicate_of = matched_id
                    else:
                        novelty_score = min(100.0, (distance / NOVEL_DISTANCE_CEILING) * 100.0)
                if is_duplicate_of is None:
                    collection.upsert(
                        ids=[event_id],
                        embeddings=[vector],
                        metadatas=[{"symbol": symbol, "title": title, "timestamp": published_at.isoformat()}],
                        documents=[title],
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Chroma novelty lookup failed for %s: %s", symbol, exc)

        results.append(
            ClassifiedEvent(
                event_id=event_id,
                symbol=symbol,
                event_type=EventType(event_type),
                title=title,
                impact_score=impact_score,
                novelty_score=round(novelty_score, 1),
                source=publisher,
                link=link,
                timestamp=published_at,
                is_duplicate_of=is_duplicate_of,
            )
        )

    return results
