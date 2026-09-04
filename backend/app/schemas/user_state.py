from datetime import datetime

from pydantic import BaseModel


class StockState(BaseModel):
    user_id: str
    symbol: str
    last_seen_price: float | None = None
    last_seen_volume: int | None = None
    last_seen_score: float | None = None
    """last_seen_score is the attention_score at the time it was marked seen."""
    last_seen_event_ids: list[str] = []
    last_seen_at: datetime | None = None
    """None means this user has never seen this symbol before."""


class DiffResult(BaseModel):
    symbol: str
    has_prior_state: bool
    price_changed_since: float | None = None
    """Percentage-point change in price since last seen, if any."""
    new_event_ids: list[str] = []
    score_changed_since: float | None = None
    is_new_since_last_visit: bool = False
