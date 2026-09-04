from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class EventType(StrEnum):
    EARNINGS = "earnings"
    EARNINGS_SURPRISE = "earnings_surprise"
    REVENUE_CHANGE = "revenue_change"
    PROFIT_CHANGE = "profit_change"
    MANAGEMENT_CHANGE = "management_change"
    EXECUTIVE_RESIGNATION = "executive_resignation"
    MERGER_ACQUISITION = "merger_acquisition"
    REGULATORY_ACTION = "regulatory_action"
    LEGAL_ISSUE = "legal_issue"
    PRODUCT_LAUNCH = "product_launch"
    MAJOR_CONTRACT = "major_contract"
    DIVIDEND = "dividend"
    BUYBACK = "buyback"
    FUNDRAISING = "fundraising"
    CREDIT_RATING_CHANGE = "credit_rating_change"
    ANALYST_ACTION = "analyst_action"
    PROMOTER_ACTIVITY = "promoter_activity"
    INSIDER_ACTIVITY = "insider_activity"
    MACRO_SECTOR_EVENT = "macro_sector_event"
    OTHER = "other"


class ClassifiedEvent(BaseModel):
    event_id: str
    symbol: str
    event_type: EventType
    title: str
    summary: str | None = None
    impact_score: float
    novelty_score: float
    source: str | None = None
    link: str | None = None
    timestamp: datetime
    # Set when this headline was semantically merged into an earlier event.
    is_duplicate_of: str | None = None
