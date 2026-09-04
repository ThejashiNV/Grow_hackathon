from fastapi import APIRouter, HTTPException, Query

from app.schemas.market import NewsItem, Quote, StockHistory
from app.services.market_data import get_market_data_provider

router = APIRouter(prefix="/stocks", tags=["market data"])


@router.get("/{symbol}", response_model=Quote)
async def get_stock_quote(symbol: str) -> Quote:
    provider = get_market_data_provider()
    quote = await provider.get_quote(symbol.upper())
    if not quote.data_ok:
        raise HTTPException(status_code=502, detail=quote.error or "Market data unavailable")
    return quote


@router.get("/{symbol}/history", response_model=StockHistory)
async def get_stock_history(symbol: str, period: str = Query(default="3mo")) -> StockHistory:
    provider = get_market_data_provider()
    return await provider.get_history(symbol.upper(), period=period)


@router.get("/{symbol}/events", response_model=list[NewsItem])
async def get_stock_news(symbol: str, limit: int = Query(default=10, le=30)) -> list[NewsItem]:
    provider = get_market_data_provider()
    return await provider.get_news(symbol.upper(), limit=limit)
