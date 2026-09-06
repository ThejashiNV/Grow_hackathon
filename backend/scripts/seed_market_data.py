"""Seed historical market data into MongoDB for all target stocks.

Usage:
    python -m backend.scripts.seed_market_data

Idempotent — only downloads data newer than what's already stored.
"""

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import yfinance as yf
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "smart_watchlist")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("seed_market_data")

# ---------------------------------------------------------------------------
# Target symbols
# ---------------------------------------------------------------------------

TARGET_STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "LT.NS",
    "TATASTEEL.NS",
    "JSWSTEEL.NS",
    "ONGC.NS",
    "NTPC.NS",
    "ADANIENT.NS",
    "HINDUNILVR.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
]

BENCHMARK_INDICES = [
    "^NSEI",      # Nifty 50
    "^NSEBANK",   # Bank Nifty
    "^CNXIT",     # Nifty IT
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetch_ohlcv(symbol: str, period: str = "5y") -> list[dict]:
    """Download OHLCV data from yfinance (blocking call)."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval="1d", auto_adjust=False)
    if hist.empty:
        return []
    rows: list[dict] = []
    for idx, row in hist.iterrows():
        # Skip rows with NaN close
        if row["Close"] != row["Close"]:
            continue
        rows.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2) if row["Open"] == row["Open"] else None,
                "high": round(float(row["High"]), 2) if row["High"] == row["High"] else None,
                "low": round(float(row["Low"]), 2) if row["Low"] == row["Low"] else None,
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,
            }
        )
    return rows


async def _bulk_upsert(collection, symbol: str, rows: list[dict]) -> int:
    """Bulk upsert price rows into a MongoDB collection.

    Uses UpdateOne with upsert=True for each row, batched via bulk_write
    for much better throughput than individual update_one calls.
    """
    if not rows:
        return 0

    ops = []
    for row in rows:
        doc = {**row, "symbol": symbol}
        ops.append(
            UpdateOne(
                {"symbol": symbol, "date": row["date"]},
                {"$set": doc},
                upsert=True,
            )
        )

    # Process in chunks of 1000 to avoid oversized bulk requests
    written = 0
    chunk_size = 1000
    for i in range(0, len(ops), chunk_size):
        result = await collection.bulk_write(ops[i : i + chunk_size], ordered=False)
        written += result.upserted_count + result.modified_count

    return written


# ---------------------------------------------------------------------------
# Core seed functions
# ---------------------------------------------------------------------------


async def seed_stock(db, symbol: str, period: str = "5y") -> dict:
    """Download and store historical OHLCV data for a single stock.

    Returns a summary dict with symbol, days downloaded, date range, and status.
    """
    result = {"symbol": symbol, "status": "ok", "days": 0, "first_date": None, "last_date": None}

    # Check existing metadata for idempotent behaviour
    meta = await db.price_history_meta.find_one({"symbol": symbol})
    existing_last_date: str | None = None
    if meta:
        existing_last_date = meta.get("last_date")

    # Fetch from yfinance in a background thread (blocking I/O)
    try:
        all_rows = await asyncio.to_thread(_fetch_ohlcv, symbol, period)
    except Exception as exc:
        logger.error("  yfinance download failed for %s: %s", symbol, exc)
        result["status"] = "download_error"
        result["error"] = str(exc)
        return result

    if not all_rows:
        logger.warning("  No data returned for %s", symbol)
        result["status"] = "no_data"
        return result

    # Filter to only new rows if we already have data
    if existing_last_date:
        new_rows = [r for r in all_rows if r["date"] > existing_last_date]
        if not new_rows:
            total = await db.daily_prices.count_documents({"symbol": symbol})
            logger.info(
                "Seeding %s... already up-to-date (%d days stored, last: %s)",
                symbol,
                total,
                existing_last_date,
            )
            result["days"] = total
            result["first_date"] = meta.get("first_date") if meta else all_rows[0]["date"]
            result["last_date"] = existing_last_date
            result["status"] = "up_to_date"
            return result
    else:
        new_rows = all_rows

    # Bulk upsert into daily_prices
    await _bulk_upsert(db.daily_prices, symbol, new_rows)

    # Update metadata
    all_dates = [r["date"] for r in all_rows]
    total_in_db = await db.daily_prices.count_documents({"symbol": symbol})
    first_date = min(all_dates)
    last_date = max(all_dates)

    # If we had prior data, first_date should be the earlier of old and new
    if meta and meta.get("first_date"):
        first_date = min(first_date, meta["first_date"])

    await db.price_history_meta.replace_one(
        {"symbol": symbol},
        {
            "symbol": symbol,
            "total_days": total_in_db,
            "first_date": first_date,
            "last_date": last_date,
            "updated_at": datetime.now(UTC),
        },
        upsert=True,
    )

    logger.info(
        "Seeding %s... %d trading days downloaded (%s to %s)",
        symbol,
        total_in_db,
        first_date,
        last_date,
    )

    result["days"] = total_in_db
    result["first_date"] = first_date
    result["last_date"] = last_date
    return result


async def seed_benchmark(db, symbol: str, period: str = "5y") -> dict:
    """Download and store historical data for a benchmark index.

    Returns a summary dict with symbol, days downloaded, date range, and status.
    """
    result = {"symbol": symbol, "status": "ok", "days": 0, "first_date": None, "last_date": None}

    # Check existing metadata for idempotent behaviour
    meta = await db.benchmark_meta.find_one({"symbol": symbol})
    existing_last_date: str | None = None
    if meta:
        existing_last_date = meta.get("last_date")

    # Fetch from yfinance
    try:
        all_rows = await asyncio.to_thread(_fetch_ohlcv, symbol, period)
    except Exception as exc:
        logger.error("  yfinance download failed for %s: %s", symbol, exc)
        result["status"] = "download_error"
        result["error"] = str(exc)
        return result

    if not all_rows:
        logger.warning("  No data returned for %s", symbol)
        result["status"] = "no_data"
        return result

    # Filter to only new rows if we already have data
    if existing_last_date:
        new_rows = [r for r in all_rows if r["date"] > existing_last_date]
        if not new_rows:
            total = await db.benchmark_prices.count_documents({"symbol": symbol})
            logger.info(
                "Seeding %s... already up-to-date (%d days stored, last: %s)",
                symbol,
                total,
                existing_last_date,
            )
            result["days"] = total
            result["first_date"] = meta.get("first_date") if meta else all_rows[0]["date"]
            result["last_date"] = existing_last_date
            result["status"] = "up_to_date"
            return result
    else:
        new_rows = all_rows

    # Mark benchmark rows
    for row in new_rows:
        row["is_benchmark"] = True

    # Bulk upsert into benchmark_prices
    await _bulk_upsert(db.benchmark_prices, symbol, new_rows)

    # Update metadata
    all_dates = [r["date"] for r in all_rows]
    total_in_db = await db.benchmark_prices.count_documents({"symbol": symbol})
    first_date = min(all_dates)
    last_date = max(all_dates)

    if meta and meta.get("first_date"):
        first_date = min(first_date, meta["first_date"])

    await db.benchmark_meta.replace_one(
        {"symbol": symbol},
        {
            "symbol": symbol,
            "total_days": total_in_db,
            "first_date": first_date,
            "last_date": last_date,
            "updated_at": datetime.now(UTC),
        },
        upsert=True,
    )

    logger.info(
        "Seeding %s... %d trading days downloaded (%s to %s)",
        symbol,
        total_in_db,
        first_date,
        last_date,
    )

    result["days"] = total_in_db
    result["first_date"] = first_date
    result["last_date"] = last_date
    return result


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def main() -> None:
    logger.info("=" * 60)
    logger.info("Market Data Seeder")
    logger.info("=" * 60)
    logger.info("MongoDB URI : %s", MONGODB_URI)
    logger.info("Database    : %s", MONGODB_DATABASE)
    logger.info("Stocks      : %d symbols", len(TARGET_STOCKS))
    logger.info("Benchmarks  : %d indices", len(BENCHMARK_INDICES))
    logger.info("=" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command("ping")
    except Exception as exc:
        logger.error("Cannot connect to MongoDB at %s: %s", MONGODB_URI, exc)
        sys.exit(1)

    db = client[MONGODB_DATABASE]

    # Ensure indexes exist (mirrors backend/app/core/database.py)
    await db.daily_prices.create_index([("symbol", 1), ("date", 1)], unique=True)
    await db.daily_prices.create_index("symbol")
    await db.price_history_meta.create_index("symbol", unique=True)
    await db.benchmark_prices.create_index([("symbol", 1), ("date", 1)], unique=True)
    await db.benchmark_meta.create_index("symbol", unique=True)

    # --- Seed stocks ---
    logger.info("")
    logger.info("--- Seeding stocks (%d) ---", len(TARGET_STOCKS))
    stock_results: list[dict] = []
    for symbol in TARGET_STOCKS:
        try:
            res = await seed_stock(db, symbol)
            stock_results.append(res)
        except Exception as exc:
            logger.error("Unexpected error seeding %s: %s", symbol, exc, exc_info=True)
            stock_results.append({"symbol": symbol, "status": "error", "error": str(exc)})

    # --- Seed benchmarks ---
    logger.info("")
    logger.info("--- Seeding benchmarks (%d) ---", len(BENCHMARK_INDICES))
    bench_results: list[dict] = []
    for symbol in BENCHMARK_INDICES:
        try:
            res = await seed_benchmark(db, symbol)
            bench_results.append(res)
        except Exception as exc:
            logger.error("Unexpected error seeding %s: %s", symbol, exc, exc_info=True)
            bench_results.append({"symbol": symbol, "status": "error", "error": str(exc)})

    # --- Summary ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    ok_stocks = [r for r in stock_results if r["status"] in ("ok", "up_to_date")]
    failed_stocks = [r for r in stock_results if r["status"] not in ("ok", "up_to_date")]
    ok_bench = [r for r in bench_results if r["status"] in ("ok", "up_to_date")]
    failed_bench = [r for r in bench_results if r["status"] not in ("ok", "up_to_date")]

    total_stock_days = sum(r.get("days", 0) for r in ok_stocks)
    total_bench_days = sum(r.get("days", 0) for r in ok_bench)

    logger.info("Stocks:     %d/%d succeeded  (%d total trading days)", len(ok_stocks), len(TARGET_STOCKS), total_stock_days)
    logger.info("Benchmarks: %d/%d succeeded  (%d total trading days)", len(ok_bench), len(BENCHMARK_INDICES), total_bench_days)

    if failed_stocks:
        logger.warning("Failed stocks: %s", ", ".join(r["symbol"] for r in failed_stocks))
    if failed_bench:
        logger.warning("Failed benchmarks: %s", ", ".join(r["symbol"] for r in failed_bench))

    logger.info("=" * 60)
    logger.info("Done.")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
