"""Sector-relative movement (Part 5 / Part 20).

Answers: did this stock move because of something company-specific, or is
the whole sector moving together? Tries the NSE sector index first; falls
back to averaging the other mapped peers in the same sector if the index
ticker isn't available from the provider.
"""

import asyncio
import logging

from app.services.market_data import MarketDataProvider
from app.utils.sector_map import SECTOR_INDEX_TICKER, get_sector, peers_in_sector

logger = logging.getLogger(__name__)


async def get_sector_move(symbol: str, provider: MarketDataProvider) -> tuple[str | None, float | None]:
    """Returns (sector, sector_change_pct). Either may be None if unavailable."""
    sector = get_sector(symbol)
    if sector is None:
        return None, None

    index_ticker = SECTOR_INDEX_TICKER.get(sector)
    if index_ticker:
        quote = await provider.get_quote(index_ticker)
        if quote.data_ok and quote.change_pct is not None:
            return sector, quote.change_pct

    peers = peers_in_sector(symbol)[:5]
    if not peers:
        return sector, None

    quotes = await asyncio.gather(*(provider.get_quote(p) for p in peers))
    changes = [q.change_pct for q in quotes if q.data_ok and q.change_pct is not None]
    if not changes:
        return sector, None
    return sector, round(sum(changes) / len(changes), 4)
