from datetime import datetime

from pydantic import BaseModel

from app.schemas.events import ClassifiedEvent


class ScoreComponents(BaseModel):
    price_anomaly: float
    """0-100: how unusual today's price move is vs this stock's own volatility."""
    price_z_score: float | None = None

    volume_anomaly: float
    """0-100: log-normalized today_volume / avg_volume_20d."""
    volume_ratio: float | None = None

    sector_relative_move: float
    """0-100: magnitude of divergence from the stock's sector move."""
    sector: str | None = None
    sector_change_pct: float | None = None

    headline_novelty: float
    """0-100: average novelty of today's classified headlines (0 if none)."""

    event_impact: float
    """0-100: baseline importance of the most impactful classified event today."""


class ExplainChip(BaseModel):
    label: str
    kind: str  # "price" | "volume" | "sector" | "event" | "silence"


class ChangeBundle(BaseModel):
    symbol: str
    company_name: str | None = None
    price: float | None = None
    previous_close: float | None = None
    change_pct: float | None = None
    normal_daily_move_pct: float | None = None
    volume: int | None = None
    average_volume_20d: float | None = None

    components: ScoreComponents
    surprise_score: float
    impact_score: float
    confidence_score: float
    attention_score: float

    sector_wide: bool = False
    """True when multiple watchlist peers moved together (Part 20)."""

    events: list[ClassifiedEvent] = []
    explain_chips: list[ExplainChip] = []
    why_this: str
    why_now: str
    is_meaningful: bool

    as_of: datetime
    is_delayed: bool = True
    data_ok: bool = True
    confidence_factors: list[str] = []
    demo_label: str | None = None
