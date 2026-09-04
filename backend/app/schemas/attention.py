from datetime import datetime

from pydantic import BaseModel

from app.schemas.scoring import ChangeBundle
from app.schemas.user_state import DiffResult


class AttentionItem(BaseModel):
    bundle: ChangeBundle
    diff: DiffResult


class AttentionResponse(BaseModel):
    items: list[AttentionItem]
    """Sorted by attention_score descending. Includes non-meaningful items too."""
    meaningful_count: int
    generated_at: datetime
    empty_watchlist: bool = False
    demo_mode: bool = False
