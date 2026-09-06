from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class EventType(StrEnum):
    # Company-specific
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
    # Macro / Central bank
    MACRO_RATE_CHANGE = "macro_rate_change"
    MACRO_INFLATION = "macro_inflation"
    MACRO_GDP = "macro_gdp"
    MACRO_FISCAL = "macro_fiscal"
    # Sector-wide
    SECTOR_TREND = "sector_trend"
    SECTOR_REGULATION = "sector_regulation"
    # Commodity
    COMMODITY_PRICE = "commodity_price"
    # Geopolitical
    GEOPOLITICAL = "geopolitical"
    # Global markets
    GLOBAL_MARKET = "global_market"
    # Legacy catch-all
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
    is_duplicate_of: str | None = None


class EventCluster(BaseModel):
    cluster_id: str
    canonical_title: str
    event_type: EventType
    article_count: int
    sources: list[str]
    first_seen: datetime
    last_seen: datetime
    impact_score: float
    novelty_score: float
    severity: str  # critical / high / medium / low
    articles: list[ClassifiedEvent] = []
    affected_symbols: list[str] = []
    summary: str | None = None
