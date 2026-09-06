"""Event impact engine.

For each event cluster, calculates stock/sector/market reaction windows:
abnormal returns at t+1, t+5, t+10, t+20 relative to the event date.
Also finds historically similar events and compares reaction patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from app.schemas.events import EventType

logger = logging.getLogger(__name__)


@dataclass
class ReactionWindow:
    window: str  # "t+1", "t+5", "t+10", "t+20"
    days: int
    stock_return_pct: float
    market_return_pct: float | None
    abnormal_return_pct: float | None
    volume_ratio: float | None


@dataclass
class HistoricalSimilar:
    date: str
    event_description: str
    stock_return_5d_pct: float
    stock_return_20d_pct: float
    severity: str


@dataclass
class EventImpactResult:
    event_type: str
    event_title: str
    event_date: str | None
    reactions: list[ReactionWindow]
    historical_avg_reaction_5d: float | None
    historical_avg_reaction_20d: float | None
    similar_events: list[HistoricalSimilar]
    historical_event_count: int


REACTION_WINDOWS = [
    ("t+1", 1),
    ("t+5", 5),
    ("t+10", 10),
    ("t+20", 20),
]


def compute_event_impact(
    event_date_str: str | None,
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
    market_closes: np.ndarray | None = None,
) -> list[ReactionWindow]:
    """Compute stock reaction at multiple windows after an event date."""
    if event_date_str is None or len(closes) < 30:
        return []

    try:
        idx = dates.index(event_date_str)
    except ValueError:
        target = event_date_str[:10]
        matches = [i for i, d in enumerate(dates) if d[:10] == target]
        if not matches:
            return []
        idx = matches[0]

    results: list[ReactionWindow] = []
    base_price = closes[idx]

    for label, days in REACTION_WINDOWS:
        end_idx = idx + days
        if end_idx >= len(closes):
            continue

        stock_ret = (closes[end_idx] / base_price - 1) * 100

        market_ret = None
        abnormal_ret = None
        if market_closes is not None and len(market_closes) > end_idx:
            market_ret = (market_closes[end_idx] / market_closes[idx] - 1) * 100
            abnormal_ret = stock_ret - market_ret

        vol_ratio = None
        if end_idx < len(volumes) and idx > 20:
            avg_vol = float(np.mean(volumes[max(0, idx - 20):idx]))
            if avg_vol > 0:
                post_avg_vol = float(np.mean(volumes[idx:min(idx + days, len(volumes))]))
                vol_ratio = round(post_avg_vol / avg_vol, 2)

        results.append(ReactionWindow(
            window=label,
            days=days,
            stock_return_pct=round(stock_ret, 2),
            market_return_pct=round(market_ret, 2) if market_ret is not None else None,
            abnormal_return_pct=round(abnormal_ret, 2) if abnormal_ret is not None else None,
            volume_ratio=vol_ratio,
        ))

    return results


def find_similar_historical_events(
    event_type: EventType,
    anomalous_moves: list[dict],
    rare_events: list[dict],
    dates: list[str],
    closes: np.ndarray,
) -> list[HistoricalSimilar]:
    """Find historically similar events from anomalous moves and rare events.

    Matches by event_type when available, otherwise uses large moves as proxies
    for similar market disruptions.
    """
    similar: list[HistoricalSimilar] = []

    for rare in rare_events:
        rare_type = rare.get("event_type") or rare.get("type")
        if rare_type and rare_type == event_type.value:
            date = rare.get("date", "")
            ret_5d = _forward_return(date, dates, closes, 5)
            ret_20d = _forward_return(date, dates, closes, 20)
            similar.append(HistoricalSimilar(
                date=date,
                event_description=rare.get("description", ""),
                stock_return_5d_pct=ret_5d,
                stock_return_20d_pct=ret_20d,
                severity=rare.get("severity", "medium"),
            ))

    for move in anomalous_moves:
        if move.get("magnitude_sigma", 0) >= 3.0:
            date = move.get("date", "")
            if any(s.date == date for s in similar):
                continue
            ret_5d = _forward_return(date, dates, closes, 5)
            ret_20d = _forward_return(date, dates, closes, 20)
            similar.append(HistoricalSimilar(
                date=date,
                event_description=f"{move.get('direction', '')} {abs(move.get('change_pct', 0)):.1f}% move ({move.get('magnitude_sigma', 0):.1f}σ)",
                stock_return_5d_pct=ret_5d,
                stock_return_20d_pct=ret_20d,
                severity="high" if move.get("magnitude_sigma", 0) >= 4.0 else "medium",
            ))

    similar.sort(key=lambda s: abs(s.stock_return_5d_pct), reverse=True)
    return similar[:10]


def _forward_return(date_str: str, dates: list[str], closes: np.ndarray, days: int) -> float:
    try:
        idx = dates.index(date_str)
    except ValueError:
        return 0.0
    end_idx = idx + days
    if end_idx >= len(closes):
        return 0.0
    return round((closes[end_idx] / closes[idx] - 1) * 100, 2)


def build_event_impact(
    event_type: EventType,
    event_title: str,
    event_date_str: str | None,
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
    market_closes: np.ndarray | None,
    anomalous_moves: list[dict],
    rare_events: list[dict],
) -> EventImpactResult:
    reactions = compute_event_impact(event_date_str, dates, closes, volumes, market_closes)

    similar = find_similar_historical_events(
        event_type, anomalous_moves, rare_events, dates, closes,
    )

    avg_5d = None
    avg_20d = None
    if similar:
        rets_5d = [s.stock_return_5d_pct for s in similar if s.stock_return_5d_pct != 0]
        rets_20d = [s.stock_return_20d_pct for s in similar if s.stock_return_20d_pct != 0]
        if rets_5d:
            avg_5d = round(float(np.mean(rets_5d)), 2)
        if rets_20d:
            avg_20d = round(float(np.mean(rets_20d)), 2)

    return EventImpactResult(
        event_type=event_type.value,
        event_title=event_title,
        event_date=event_date_str,
        reactions=reactions,
        historical_avg_reaction_5d=avg_5d,
        historical_avg_reaction_20d=avg_20d,
        similar_events=similar,
        historical_event_count=len(similar),
    )
