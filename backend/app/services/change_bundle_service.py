"""Builds a single structured ChangeBundle for a symbol (Part 8).

Orchestrates market data + sector comparison + news classification/dedup +
scoring into one story, instead of showing price/volume/news as unrelated
numbers.
"""

from datetime import UTC, datetime

from app.schemas.events import ClassifiedEvent
from app.schemas.scoring import ChangeBundle, ExplainChip, ScoreComponents
from app.services import scoring
from app.services.market_data import MarketDataProvider, get_market_data_provider
from app.services.novelty_service import classify_and_dedupe
from app.services.sector_service import get_sector_move

# A z-score-derived "normal daily move" band, expressed back in percent, for
# the human-readable "Normal movement: +-X%" line on the card.
Z_TO_NORMAL_BAND = 1.0


async def build_change_bundle(symbol: str, provider: MarketDataProvider | None = None) -> ChangeBundle:
    provider = provider or get_market_data_provider()
    now = datetime.now(UTC)

    quote = await provider.get_quote(symbol)
    if not quote.data_ok:
        return ChangeBundle(
            symbol=symbol,
            components=ScoreComponents(price_anomaly=0, volume_anomaly=0, sector_relative_move=0, headline_novelty=0, event_impact=0),
            surprise_score=0,
            impact_score=0,
            confidence_score=0,
            attention_score=0,
            why_this="Market data is currently unavailable for this symbol.",
            why_now="",
            is_meaningful=False,
            as_of=now,
            data_ok=False,
        )

    sector, sector_change_pct = await get_sector_move(symbol, provider)

    raw_news = await provider.get_news(symbol, limit=8)
    headline_tuples = [
        (n.title, n.publisher, n.link, n.published_at or now) for n in raw_news
    ]
    classified_events = await classify_and_dedupe(symbol, headline_tuples)
    fresh_events = [e for e in classified_events if e.is_duplicate_of is None]

    price_score, z = scoring.price_anomaly(quote.change_pct, quote.volatility_30d)
    volume_score, ratio = scoring.volume_anomaly(quote.volume, quote.average_volume_20d)
    sector_score = scoring.sector_relative_score(quote.change_pct, sector_change_pct)

    top_event = max(fresh_events, key=lambda e: e.impact_score, default=None)
    event_impact_score = top_event.impact_score if top_event else 0.0
    avg_novelty = (
        sum(e.novelty_score for e in fresh_events) / len(fresh_events) if fresh_events else 0.0
    )

    surprise = scoring.compute_surprise(price_score, volume_score, sector_score)
    impact = scoring.compute_impact(event_impact_score, avg_novelty)
    confidence, confidence_factors = scoring.compute_confidence(
        has_price=quote.price is not None,
        has_volume=quote.volume is not None,
        has_sector=sector_change_pct is not None,
        headline_count=len(fresh_events),
        is_stale=False,
    )
    attention = scoring.compute_attention(surprise, impact, confidence)
    meaningful = scoring.is_meaningful(attention)

    normal_band = round(quote.volatility_30d * 100 * Z_TO_NORMAL_BAND, 2) if quote.volatility_30d else None

    chips = _build_explain_chips(price_score, volume_score, sector_score, top_event, z, ratio)
    why_this, why_now = _build_explanations(
        quote.change_pct, normal_band, sector, sector_change_pct, top_event, z, ratio, event_impact_score, price_score
    )

    return ChangeBundle(
        symbol=symbol,
        company_name=quote.company_name,
        price=quote.price,
        previous_close=quote.previous_close,
        change_pct=quote.change_pct,
        normal_daily_move_pct=normal_band,
        volume=quote.volume,
        average_volume_20d=quote.average_volume_20d,
        components=ScoreComponents(
            price_anomaly=price_score,
            price_z_score=z,
            volume_anomaly=volume_score,
            volume_ratio=ratio,
            sector_relative_move=sector_score,
            sector=sector,
            sector_change_pct=sector_change_pct,
            headline_novelty=round(avg_novelty, 1),
            event_impact=event_impact_score,
        ),
        surprise_score=surprise,
        impact_score=impact,
        confidence_score=confidence,
        attention_score=attention,
        events=fresh_events,
        explain_chips=chips,
        why_this=why_this,
        why_now=why_now,
        is_meaningful=meaningful,
        as_of=quote.as_of,
        is_delayed=quote.is_delayed,
        confidence_factors=confidence_factors,
    )


def _build_explain_chips(
    price_score: float, volume_score: float, sector_score: float, top_event: ClassifiedEvent | None, z: float | None, ratio: float | None
) -> list[ExplainChip]:
    chips: list[ExplainChip] = []
    if price_score >= 40:
        label = f"Price anomaly {z:+.1f}σ" if z is not None else "Price anomaly"
        chips.append(ExplainChip(label=label, kind="price"))
    if volume_score >= 40:
        label = f"Volume {ratio:.1f}× normal" if ratio is not None else "Volume anomaly"
        chips.append(ExplainChip(label=label, kind="volume"))
    if sector_score >= 40:
        chips.append(ExplainChip(label="Sector-relative movement", kind="sector"))
    if top_event is not None and top_event.impact_score >= 50:
        chips.append(ExplainChip(label="New major event", kind="event"))
    if top_event is not None and top_event.impact_score >= 60 and price_score < 20:
        chips.append(ExplainChip(label="Unusually muted reaction", kind="silence"))
    return chips


def _build_explanations(
    change_pct: float | None,
    normal_band: float | None,
    sector: str | None,
    sector_change_pct: float | None,
    top_event: ClassifiedEvent | None,
    z: float | None,
    ratio: float | None,
    event_impact_score: float,
    price_score: float,
) -> tuple[str, str]:
    if change_pct is None:
        return "No price data available.", "No price data available."

    parts_this = [f"Moved {change_pct:+.1f}% today"]
    if normal_band is not None:
        parts_this.append(f"vs a normal daily move of about ±{normal_band:.1f}%")
    if sector and sector_change_pct is not None:
        direction = "outperformed" if (change_pct - sector_change_pct) * (1 if change_pct >= 0 else -1) >= 0 and abs(change_pct) < abs(sector_change_pct) else "moved with"
        parts_this.append(f"while the {sector.title()} sector moved {sector_change_pct:+.1f}% ({direction} sector)")
    why_this = ", ".join(parts_this) + "."

    now_parts = []
    if z is not None and abs(z) >= 1.5:
        now_parts.append(f"the move is {abs(z):.1f}× this stock's typical daily volatility")
    if ratio is not None and ratio >= 1.5:
        now_parts.append(f"volume is {ratio:.1f}× the 20-day average")
    if top_event is not None:
        now_parts.append(f'a new headline was detected: "{top_event.title}"')
        if event_impact_score >= 60 and price_score < 20:
            now_parts.append("but the price reaction has been unusually muted given the event's typical importance")
    why_now = ("This became meaningful because " + ", and ".join(now_parts) + ".") if now_parts else "No unusual signal detected right now."

    return why_this, why_now
