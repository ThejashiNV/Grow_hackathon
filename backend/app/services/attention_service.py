"""Aggregates change bundles for a whole watchlist into the triage inbox
(Part 11), including cross-symbol sector-wide movement detection (Part 20).
"""

import asyncio
from datetime import UTC, datetime

from app.core.config import get_settings
from app.repositories import stock_state_repository, watchlist_repository
from app.schemas.attention import AttentionItem, AttentionResponse
from app.schemas.scoring import ChangeBundle
from app.services.change_bundle_service import build_change_bundle
from app.services.diff_engine import compute_diff

# If >=2 watchlist stocks share a sector, both moved with (not against) the
# sector, and the sector itself moved meaningfully, the move is broad-market
# rather than company-specific -- don't let each one alert independently.
SECTOR_WIDE_MIN_PEERS = 2
SECTOR_WIDE_MIN_SECTOR_MOVE = 1.5
SECTOR_WIDE_MAX_DIVERGENCE_SCORE = 25.0


def _apply_sector_wide_flags(bundles: list[ChangeBundle]) -> None:
    by_sector: dict[str, list[ChangeBundle]] = {}
    for b in bundles:
        sector = b.components.sector
        if sector:
            by_sector.setdefault(sector, []).append(b)

    for sector, group in by_sector.items():
        if len(group) < SECTOR_WIDE_MIN_PEERS:
            continue
        sector_move = group[0].components.sector_change_pct
        if sector_move is None or abs(sector_move) < SECTOR_WIDE_MIN_SECTOR_MOVE:
            continue
        moving_with_sector = [b for b in group if b.components.sector_relative_move <= SECTOR_WIDE_MAX_DIVERGENCE_SCORE]
        if len(moving_with_sector) >= SECTOR_WIDE_MIN_PEERS:
            for b in moving_with_sector:
                b.sector_wide = True


async def build_attention_feed(user_id: str) -> AttentionResponse:
    settings = get_settings()

    if settings.demo_mode:
        from app.services.demo_data import DEMO_SYMBOLS

        symbols = list(DEMO_SYMBOLS)
    else:
        watchlist = await watchlist_repository.get_watchlist(user_id)
        symbols = [s.symbol for s in watchlist.stocks]

    if not symbols:
        return AttentionResponse(items=[], meaningful_count=0, generated_at=datetime.now(UTC), empty_watchlist=True)

    bundles = await asyncio.gather(*(build_change_bundle(sym) for sym in symbols))
    bundles = list(bundles)
    _apply_sector_wide_flags(bundles)

    states = await stock_state_repository.get_states_bulk(user_id, symbols)

    items = [
        AttentionItem(bundle=bundle, diff=compute_diff(states[bundle.symbol], bundle))
        for bundle in bundles
    ]
    items.sort(key=lambda item: item.bundle.attention_score, reverse=True)

    meaningful_count = sum(1 for item in items if item.bundle.is_meaningful)

    return AttentionResponse(
        items=items,
        meaningful_count=meaningful_count,
        generated_at=datetime.now(UTC),
        demo_mode=settings.demo_mode,
    )
