from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    publisher: str | None = None
    link: str | None = None
    published_at: datetime | None = None


class HistoryPoint(BaseModel):
    date: datetime
    close: float
    volume: int


class Quote(BaseModel):
    symbol: str
    company_name: str | None = None
    price: float | None = None
    previous_close: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    average_volume_20d: float | None = None
    # Daily-return standard deviation over the trailing 30 sessions (not annualized).
    volatility_30d: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    sector: str | None = None
    market_cap: float | None = None
    as_of: datetime
    source: str
    is_delayed: bool = True
    data_ok: bool = True
    error: str | None = None


class StockHistory(BaseModel):
    symbol: str
    points: list[HistoryPoint]
    as_of: datetime
    source: str
