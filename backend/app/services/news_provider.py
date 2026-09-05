"""News/event provider abstraction with multiple source support.

Gathers news from accessible sources, normalizes and deduplicates.
Designed for replacement/extension without touching consumers.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from app.core.database import get_db
from app.services.event_classifier import classify_headline

logger = logging.getLogger(__name__)


class NormalizedNews(dict):
    """Dict-based news item with standard fields."""
    pass


def _make_id(source: str, title: str, published: str) -> str:
    raw = f"{source}:{title}:{published}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class NewsProvider(ABC):
    source_name: str = "unknown"

    @abstractmethod
    async def fetch_news(self, search_terms: list[str], limit: int = 30) -> list[NormalizedNews]:
        ...


class YFinanceNewsProvider(NewsProvider):
    source_name = "yfinance"

    async def fetch_news(self, search_terms: list[str], limit: int = 30) -> list[NormalizedNews]:
        """Fetch news for a symbol via yfinance. Uses the first term as ticker."""
        results = []
        seen_titles = set()

        for term in search_terms[:3]:
            items = await asyncio.to_thread(self._fetch_sync, term, limit)
            for item in items:
                title_key = item.get("title", "").lower().strip()
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    results.append(item)

        return results[:limit]

    def _fetch_sync(self, symbol_or_term: str, limit: int) -> list[NormalizedNews]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol_or_term)
            raw = ticker.news or []
            items = []
            for entry in raw[:limit]:
                content = entry.get("content", entry)
                title = content.get("title") or entry.get("title")
                if not title:
                    continue

                pub_date = content.get("pubDate")
                published_at = None
                if pub_date:
                    try:
                        published_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                publisher = None
                provider_data = content.get("provider")
                if isinstance(provider_data, dict):
                    publisher = provider_data.get("displayName")
                elif entry.get("publisher"):
                    publisher = entry["publisher"]

                link = None
                canon = content.get("canonicalUrl")
                if isinstance(canon, dict):
                    link = canon.get("url")
                elif entry.get("link"):
                    link = entry["link"]

                summary = content.get("summary") or ""

                event_type, impact_score = classify_headline(title)

                pub_str = published_at.isoformat() if published_at else datetime.now(UTC).isoformat()
                news_id = _make_id(self.source_name, title, pub_str)

                items.append(NormalizedNews({
                    "news_id": news_id,
                    "title": title,
                    "summary": _clean_summary(summary),
                    "publisher": publisher,
                    "link": link,
                    "published_at": pub_str,
                    "source": self.source_name,
                    "event_type": event_type.value,
                    "impact_score": impact_score,
                    "fetched_at": datetime.now(UTC).isoformat(),
                }))
            return items
        except Exception as exc:
            logger.warning("yfinance news fetch failed for %s: %s", symbol_or_term, exc)
            return []


class GoogleNewsRSSProvider(NewsProvider):
    """Fetches news from Google News RSS — no API key required."""
    source_name = "google_news_rss"

    async def fetch_news(self, search_terms: list[str], limit: int = 20) -> list[NormalizedNews]:
        results = []
        seen_titles = set()

        for term in search_terms[:4]:
            items = await asyncio.to_thread(self._fetch_rss, term, limit)
            for item in items:
                title_key = item.get("title", "").lower().strip()
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    results.append(item)

        return results[:limit]

    def _fetch_rss(self, query: str, limit: int) -> list[NormalizedNews]:
        import urllib.request
        import xml.etree.ElementTree as ET

        try:
            encoded = urllib.parse.quote(f"{query} stock market India")
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketIntel/1.0)"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            items = []
            for item_el in root.findall(".//item")[:limit]:
                title = item_el.findtext("title", "")
                if not title:
                    continue

                link = item_el.findtext("link", "")
                pub_date_str = item_el.findtext("pubDate", "")
                source_el = item_el.findtext("source", "")

                published_at = None
                if pub_date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(pub_date_str)
                    except Exception:
                        pass

                title_clean = re.sub(r'\s*-\s*[^-]+$', '', title).strip()

                event_type, impact_score = classify_headline(title_clean)
                pub_str = published_at.isoformat() if published_at else datetime.now(UTC).isoformat()
                news_id = _make_id(self.source_name, title_clean, pub_str)

                items.append(NormalizedNews({
                    "news_id": news_id,
                    "title": title_clean,
                    "summary": "",
                    "publisher": source_el or None,
                    "link": link or None,
                    "published_at": pub_str,
                    "source": self.source_name,
                    "event_type": event_type.value,
                    "impact_score": impact_score,
                    "fetched_at": datetime.now(UTC).isoformat(),
                }))

            return items
        except Exception as exc:
            logger.warning("Google News RSS failed for '%s': %s", query, exc)
            return []


def _clean_summary(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500] if text else ""


NEWS_CACHE_TTL_MINUTES = 30


async def fetch_and_store_news(
    symbol: str,
    search_terms: list[str],
    providers: list[NewsProvider] | None = None,
) -> list[dict]:
    """Fetch news from all providers, deduplicate, persist to MongoDB, return merged list."""
    if providers is None:
        providers = [YFinanceNewsProvider(), GoogleNewsRSSProvider()]

    db = get_db()

    if db is not None:
        cached = await _get_cached_news(db, symbol)
        if cached is not None:
            return cached

    all_news: list[NormalizedNews] = []
    tasks = [p.fetch_news(search_terms) for p in providers]
    provider_results = await asyncio.gather(*tasks, return_exceptions=True)

    seen_titles: set[str] = set()
    for result in provider_results:
        if isinstance(result, Exception):
            logger.warning("News provider failed: %s", result)
            continue
        for item in result:
            title_key = item.get("title", "").lower().strip()[:80]
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                item["symbol"] = symbol
                all_news.append(item)

    all_news.sort(
        key=lambda x: x.get("published_at", ""),
        reverse=True,
    )

    if db is not None and all_news:
        await _store_news(db, symbol, all_news)

    return all_news


async def _get_cached_news(db, symbol: str) -> list[dict] | None:
    try:
        meta = await db.news_cache_meta.find_one({"symbol": symbol})
        if meta is None:
            return None
        age = datetime.now(UTC) - meta.get("fetched_at", datetime.min.replace(tzinfo=UTC))
        if age > timedelta(minutes=NEWS_CACHE_TTL_MINUTES):
            return None
        cursor = db.news_items.find({"symbol": symbol}).sort("published_at", -1).limit(50)
        items = []
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        return items if items else None
    except Exception:
        logger.warning("Failed to read news cache for %s", symbol, exc_info=True)
        return None


async def _store_news(db, symbol: str, items: list[dict]) -> None:
    try:
        for item in items:
            await db.news_items.update_one(
                {"news_id": item["news_id"]},
                {"$set": item},
                upsert=True,
            )
        await db.news_cache_meta.replace_one(
            {"symbol": symbol},
            {"symbol": symbol, "fetched_at": datetime.now(UTC), "count": len(items)},
            upsert=True,
        )
    except Exception:
        logger.warning("Failed to store news for %s", symbol, exc_info=True)


async def get_historical_news(symbol: str, days_back: int = 30, limit: int = 50) -> list[dict]:
    """Retrieve persisted news from MongoDB for a symbol."""
    db = get_db()
    if db is None:
        return []
    try:
        cutoff = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
        cursor = db.news_items.find({
            "symbol": symbol,
            "published_at": {"$gte": cutoff},
        }).sort("published_at", -1).limit(limit)
        items = []
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        return items
    except Exception:
        logger.warning("Failed to read historical news for %s", symbol, exc_info=True)
        return []
