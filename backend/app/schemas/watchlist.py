from datetime import datetime

from pydantic import BaseModel


class WatchlistStock(BaseModel):
    symbol: str
    added_at: datetime


class Watchlist(BaseModel):
    user_id: str
    stocks: list[WatchlistStock] = []
    updated_at: datetime


class AddStockRequest(BaseModel):
    symbol: str
