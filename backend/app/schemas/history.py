from datetime import datetime

from pydantic import BaseModel

from app.schemas.scoring import ExplainChip


class HistoryEntry(BaseModel):
    user_id: str
    symbol: str
    company_name: str | None = None
    date_key: str
    """UTC calendar date as YYYY-MM-DD — dedup key with user_id + symbol."""
    detected_at: datetime
    seen_at: datetime | None = None

    price: float | None = None
    change_pct: float | None = None
    attention_score: float
    surprise_score: float
    impact_score: float

    explain_chips: list[ExplainChip] = []
    top_headline: str | None = None
    top_event_type: str | None = None
    why_this: str
    why_now: str

    demo_label: str | None = None


class HistoryResponse(BaseModel):
    entries: list[HistoryEntry]
    total: int
