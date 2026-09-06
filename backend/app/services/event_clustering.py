"""Event clustering: groups semantically similar headlines into EventClusters.

Instead of just marking duplicates, this builds proper clusters with canonical
titles, article counts, time ranges, and aggregated severity. Uses the same
ChromaDB embeddings as novelty_service but produces structured cluster objects.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime

import numpy as np

from app.schemas.events import ClassifiedEvent, EventCluster, EventType
from app.services.embeddings import embed_texts
from app.services.event_classifier import classify_headline

logger = logging.getLogger(__name__)

CLUSTER_DISTANCE_THRESHOLD = 0.5


def _cluster_id(symbol: str, title: str, ts: datetime) -> str:
    raw = f"cluster:{symbol}|{title}|{ts.date().isoformat()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]  # noqa: S324


def _event_id(symbol: str, title: str, ts: datetime) -> str:
    raw = f"{symbol}|{title}|{ts.date().isoformat()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]  # noqa: S324


def _severity_from_impact(impact: float) -> str:
    if impact >= 80:
        return "critical"
    if impact >= 60:
        return "high"
    if impact >= 40:
        return "medium"
    return "low"


async def cluster_events(
    symbol: str,
    headlines: list[dict],
) -> tuple[list[EventCluster], list[ClassifiedEvent]]:
    """Cluster a list of news headlines into EventClusters.

    Args:
        symbol: Stock symbol.
        headlines: List of dicts with keys: title, publisher, link, published_at, summary.

    Returns:
        (clusters, all_events) — clusters sorted by impact, and the flat event list.
    """
    if not headlines:
        return [], []

    titles = [h.get("title", "") for h in headlines]
    try:
        vectors = await embed_texts(titles)
    except Exception:
        logger.warning("Embeddings unavailable for %s, using title-based clustering", symbol)
        vectors = None

    if not vectors or len(vectors) != len(headlines):
        events = _classify_without_embeddings(symbol, headlines)
        clusters = _title_based_clusters(symbol, events)
        return clusters, events

    events: list[ClassifiedEvent] = []
    embeddings: list[list[float]] = []

    for headline, vector in zip(headlines, vectors, strict=True):
        title = headline.get("title", "")
        publisher = headline.get("publisher")
        link = headline.get("link")
        pub_at_raw = headline.get("published_at")
        summary = headline.get("summary", "")

        if isinstance(pub_at_raw, str):
            try:
                pub_at = datetime.fromisoformat(pub_at_raw)
            except ValueError:
                pub_at = datetime.utcnow()
        elif isinstance(pub_at_raw, datetime):
            pub_at = pub_at_raw
        else:
            pub_at = datetime.utcnow()

        event_type, impact_score = classify_headline(title)
        eid = _event_id(symbol, title, pub_at)

        events.append(ClassifiedEvent(
            event_id=eid,
            symbol=symbol,
            event_type=event_type,
            title=title,
            summary=summary or None,
            impact_score=impact_score,
            novelty_score=100.0,
            source=publisher,
            link=link,
            timestamp=pub_at,
        ))
        embeddings.append(vector)

    cluster_assignments = _agglomerative_cluster(embeddings, CLUSTER_DISTANCE_THRESHOLD)

    cluster_map: dict[int, list[int]] = {}
    for idx, cid in enumerate(cluster_assignments):
        cluster_map.setdefault(cid, []).append(idx)

    clusters: list[EventCluster] = []
    for indices in cluster_map.values():
        cluster_events_list = [events[i] for i in indices]

        anchor = max(cluster_events_list, key=lambda e: e.impact_score)
        canonical_title = anchor.title

        sources = list({e.source for e in cluster_events_list if e.source})
        timestamps = [e.timestamp for e in cluster_events_list]
        max_impact = max(e.impact_score for e in cluster_events_list)

        for i, idx in enumerate(indices):
            if i == 0:
                events[idx].novelty_score = 100.0
            else:
                events[idx].novelty_score = 5.0
                events[idx].is_duplicate_of = cluster_events_list[0].event_id

        cid = _cluster_id(symbol, canonical_title, min(timestamps))

        clusters.append(EventCluster(
            cluster_id=cid,
            canonical_title=canonical_title,
            event_type=anchor.event_type,
            article_count=len(cluster_events_list),
            sources=sources,
            first_seen=min(timestamps),
            last_seen=max(timestamps),
            impact_score=max_impact,
            novelty_score=100.0,
            severity=_severity_from_impact(max_impact),
            articles=cluster_events_list,
            affected_symbols=[symbol],
            summary=anchor.summary,
        ))

    clusters.sort(key=lambda c: c.impact_score, reverse=True)

    return clusters, events


def _agglomerative_cluster(
    embeddings: list[list[float]],
    threshold: float,
) -> list[int]:
    """Simple single-linkage clustering on cosine distance."""
    n = len(embeddings)
    if n == 0:
        return []
    if n == 1:
        return [0]

    vecs = np.array(embeddings, dtype=np.float64)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms < 1e-10, 1.0, norms)
    vecs = vecs / norms

    labels = list(range(n))

    for i in range(n):
        for j in range(i + 1, n):
            cosine_dist = 1.0 - float(np.dot(vecs[i], vecs[j]))
            if cosine_dist <= threshold:
                old_label = labels[j]
                new_label = labels[i]
                for k in range(n):
                    if labels[k] == old_label:
                        labels[k] = new_label

    unique = sorted(set(labels))
    remap = {old: new for new, old in enumerate(unique)}
    return [remap[l] for l in labels]


def _classify_without_embeddings(
    symbol: str, headlines: list[dict]
) -> list[ClassifiedEvent]:
    events = []
    for h in headlines:
        title = h.get("title", "")
        pub_at_raw = h.get("published_at")
        if isinstance(pub_at_raw, str):
            try:
                pub_at = datetime.fromisoformat(pub_at_raw)
            except ValueError:
                pub_at = datetime.utcnow()
        elif isinstance(pub_at_raw, datetime):
            pub_at = pub_at_raw
        else:
            pub_at = datetime.utcnow()

        event_type, impact = classify_headline(title)
        events.append(ClassifiedEvent(
            event_id=_event_id(symbol, title, pub_at),
            symbol=symbol,
            event_type=event_type,
            title=title,
            summary=h.get("summary") or None,
            impact_score=impact,
            novelty_score=100.0,
            source=h.get("publisher"),
            link=h.get("link"),
            timestamp=pub_at,
        ))
    return events


def _single_event_clusters(
    symbol: str, events: list[ClassifiedEvent]
) -> list[EventCluster]:
    clusters = []
    for e in events:
        clusters.append(EventCluster(
            cluster_id=_cluster_id(symbol, e.title, e.timestamp),
            canonical_title=e.title,
            event_type=e.event_type,
            article_count=1,
            sources=[e.source] if e.source else [],
            first_seen=e.timestamp,
            last_seen=e.timestamp,
            impact_score=e.impact_score,
            novelty_score=100.0,
            severity=_severity_from_impact(e.impact_score),
            articles=[e],
            affected_symbols=[symbol],
            summary=e.summary,
        ))
    return clusters


def _title_based_clusters(
    symbol: str, events: list[ClassifiedEvent]
) -> list[EventCluster]:
    """Group events by event_type when embeddings are unavailable."""
    by_type: dict[EventType, list[ClassifiedEvent]] = {}
    for e in events:
        by_type.setdefault(e.event_type, []).append(e)

    clusters: list[EventCluster] = []
    for event_type, group in by_type.items():
        anchor = max(group, key=lambda e: e.impact_score)
        sources = list({e.source for e in group if e.source})
        timestamps = [e.timestamp for e in group]

        for i, e in enumerate(group):
            if i > 0:
                e.novelty_score = 5.0
                e.is_duplicate_of = group[0].event_id

        clusters.append(EventCluster(
            cluster_id=_cluster_id(symbol, anchor.title, min(timestamps)),
            canonical_title=anchor.title,
            event_type=event_type,
            article_count=len(group),
            sources=sources,
            first_seen=min(timestamps),
            last_seen=max(timestamps),
            impact_score=anchor.impact_score,
            novelty_score=100.0,
            severity=_severity_from_impact(anchor.impact_score),
            articles=group,
            affected_symbols=[symbol],
            summary=anchor.summary,
        ))

    clusters.sort(key=lambda c: c.impact_score, reverse=True)
    return clusters
