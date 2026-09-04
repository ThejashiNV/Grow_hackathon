"""Deterministic scoring functions.

Kept as pure functions (no I/O, no DB) so they're trivially unit-testable and
so scoring logic never leaks into API routes (Part 6). All scores are 0-100
unless noted. Weights are named constants, not magic numbers, so they can be
tuned without touching the math.

Architecture (per the corrected plan): Surprise <- price/volume/sector.
Impact <- event type/impact/novelty. Confidence <- data quality. Attention
combines all three, with confidence acting as a multiplier/damper rather than
an additive term -- a low-confidence signal should never rank as high as a
well-evidenced one, even if the raw surprise number is identical.
"""

import math

# Surprise component weights (must sum to 1.0)
PRICE_WEIGHT = 0.5
VOLUME_WEIGHT = 0.3
SECTOR_WEIGHT = 0.2

# Impact component weights (must sum to 1.0)
EVENT_IMPACT_WEIGHT = 0.65
NOVELTY_WEIGHT = 0.35

# Meaningful-change gate
ATTENTION_THRESHOLD = 35.0


def price_anomaly(change_pct: float | None, volatility_30d: float | None) -> tuple[float, float | None]:
    """Z-score of today's move against the stock's own trailing volatility.

    No fixed percentage threshold: a 2% move is huge for a low-volatility
    stock and noise for a high-volatility one, because the denominator here
    is that stock's own historical daily-return stddev.
    """
    if change_pct is None or volatility_30d is None or volatility_30d <= 0:
        return 0.0, None
    z = (change_pct / 100.0) / volatility_30d
    score = min(100.0, abs(z) * 25.0)
    return round(score, 1), round(z, 2)


def volume_anomaly(volume: int | None, average_volume_20d: float | None) -> tuple[float, float | None]:
    """Log-normalized volume ratio so a 10x spike doesn't blow past a 3x spike
    by a factor of 10 -- diminishing returns past the first few multiples."""
    if not volume or not average_volume_20d or average_volume_20d <= 0:
        return 0.0, None
    ratio = volume / average_volume_20d
    if ratio <= 1:
        return 0.0, round(ratio, 2)
    score = min(100.0, math.log2(ratio) * 40.0)
    return round(score, 1), round(ratio, 2)


def sector_relative_score(change_pct: float | None, sector_change_pct: float | None) -> float:
    """How much the stock's move diverges from its sector's move, not just
    the raw magnitude -- a stock falling with its whole sector is expected
    behavior, not a company-specific surprise."""
    if change_pct is None or sector_change_pct is None:
        return 0.0
    divergence = abs(change_pct - sector_change_pct)
    return round(min(100.0, divergence * 20.0), 1)


def compute_surprise(price_score: float, volume_score: float, sector_score: float) -> float:
    surprise = PRICE_WEIGHT * price_score + VOLUME_WEIGHT * volume_score + SECTOR_WEIGHT * sector_score
    return round(min(100.0, surprise), 1)


def compute_impact(event_impact_score: float, novelty_score: float) -> float:
    impact = EVENT_IMPACT_WEIGHT * event_impact_score + NOVELTY_WEIGHT * novelty_score
    return round(min(100.0, impact), 1)


def compute_confidence(
    has_price: bool,
    has_volume: bool,
    has_sector: bool,
    headline_count: int,
    is_stale: bool,
) -> tuple[float, list[str]]:
    score = 100.0
    factors: list[str] = []

    if not has_price:
        score -= 40
        factors.append("Price data unavailable")
    else:
        factors.append("Price data available")

    if not has_volume:
        score -= 15
        factors.append("Volume data unavailable")
    else:
        factors.append("Volume data available")

    if not has_sector:
        score -= 10
        factors.append("Sector data unavailable")
    else:
        factors.append("Sector data available")

    if headline_count == 0:
        factors.append("No relevant headlines found")
    elif headline_count == 1:
        score -= 5
        factors.append("Only one relevant headline")
    else:
        factors.append(f"{headline_count} relevant headlines")

    if is_stale:
        score -= 15
        factors.append("Market data may be delayed")
    else:
        factors.append("Fresh data")

    return round(max(0.0, score), 1), factors


def compute_attention(surprise: float, impact: float, confidence: float) -> float:
    """Confidence dampens rather than adds: a 90-surprise signal backed by
    40%-confidence evidence should not outrank a 70-surprise signal backed by
    95%-confidence evidence."""
    raw = 0.55 * surprise + 0.45 * impact
    attention = raw * (confidence / 100.0)
    return round(min(100.0, attention), 1)


def is_meaningful(attention_score: float) -> bool:
    return attention_score >= ATTENTION_THRESHOLD
