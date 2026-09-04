"""Market data abstraction layer.

Everything downstream (scoring, diff engine, RAG) talks to `MarketDataProvider`,
never to yfinance directly. Swapping the provider later means implementing this
interface, not touching the scoring system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import numpy as np
import yfinance as yf

from app.core.config import get_settings
from app.schemas.market import HistoryPoint, NewsItem, Quote, StockHistory
from app.utils.sector_map import get_sector

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    async def get_history(self, symbol: str, period: str = "3mo") -> StockHistory: ...

    @abstractmethod
    async def get_news(self, symbol: str, limit: int = 10) -> list[NewsItem]: ...


class YFinanceProvider(MarketDataProvider):
    """Wraps yfinance (a synchronous, blocking library) behind an async interface."""

    source_name = "yfinance"

    async def get_quote(self, symbol: str) -> Quote:
        return await asyncio.to_thread(self._get_quote_sync, symbol)

    async def get_history(self, symbol: str, period: str = "3mo") -> StockHistory:
        return await asyncio.to_thread(self._get_history_sync, symbol, period)

    async def get_news(self, symbol: str, limit: int = 10) -> list[NewsItem]:
        return await asyncio.to_thread(self._get_news_sync, symbol, limit)

    def _get_quote_sync(self, symbol: str) -> Quote:
        now = datetime.now(UTC)
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo", interval="1d", auto_adjust=False)
            if hist.empty:
                return Quote(
                    symbol=symbol,
                    as_of=now,
                    source=self.source_name,
                    data_ok=False,
                    error="No price history returned by provider",
                )

            info = _safe_get_info(ticker)
            closes = hist["Close"].dropna()
            volumes = hist["Volume"].dropna()

            price = float(closes.iloc[-1])
            previous_close = float(closes.iloc[-2]) if len(closes) > 1 else price
            change_pct = ((price - previous_close) / previous_close * 100) if previous_close else None

            avg_volume_20d = float(volumes.tail(20).mean()) if len(volumes) else None
            volatility_30d = _daily_return_std(closes.tail(31))

            return Quote(
                symbol=symbol,
                company_name=info.get("shortName") or info.get("longName"),
                price=price,
                previous_close=previous_close,
                change_pct=round(change_pct, 4) if change_pct is not None else None,
                volume=int(volumes.iloc[-1]) if len(volumes) else None,
                average_volume_20d=avg_volume_20d,
                volatility_30d=volatility_30d,
                day_high=float(hist["High"].iloc[-1]) if "High" in hist else None,
                day_low=float(hist["Low"].iloc[-1]) if "Low" in hist else None,
                sector=get_sector(symbol) or info.get("sector"),
                market_cap=info.get("marketCap"),
                as_of=now,
                source=self.source_name,
                is_delayed=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance quote failed for %s: %s", symbol, exc)
            return Quote(symbol=symbol, as_of=now, source=self.source_name, data_ok=False, error=str(exc))

    def _get_history_sync(self, symbol: str, period: str) -> StockHistory:
        now = datetime.now(UTC)
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d", auto_adjust=False)
            points = [
                HistoryPoint(date=idx.to_pydatetime(), close=float(row["Close"]), volume=int(row["Volume"]))
                for idx, row in hist.iterrows()
                if row["Close"] == row["Close"]  # drop NaN rows
            ]
            return StockHistory(symbol=symbol, points=points, as_of=now, source=self.source_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance history failed for %s: %s", symbol, exc)
            return StockHistory(symbol=symbol, points=[], as_of=now, source=self.source_name)

    def _get_news_sync(self, symbol: str, limit: int) -> list[NewsItem]:
        try:
            ticker = yf.Ticker(symbol)
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
                        published_at = None
                items.append(
                    NewsItem(
                        title=title,
                        publisher=(content.get("provider") or {}).get("displayName") if isinstance(content.get("provider"), dict) else entry.get("publisher"),
                        link=(content.get("canonicalUrl") or {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else entry.get("link"),
                        published_at=published_at,
                    )
                )
            return items
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance news failed for %s: %s", symbol, exc)
            return []


def _safe_get_info(ticker: "yf.Ticker") -> dict:
    try:
        return ticker.get_info() or {}
    except Exception:  # noqa: BLE001
        return {}


def _daily_return_std(closes) -> float | None:
    if len(closes) < 5:
        return None
    returns = np.diff(closes.to_numpy()) / closes.to_numpy()[:-1]
    return float(np.std(returns))


_provider: MarketDataProvider | None = None


def get_market_data_provider() -> MarketDataProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.market_data_provider == "yfinance":
            _provider = YFinanceProvider()
        else:
            raise ValueError(f"Unknown market data provider: {settings.market_data_provider}")
    return _provider
