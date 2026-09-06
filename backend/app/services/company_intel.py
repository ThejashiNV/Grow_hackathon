"""Company intelligence: entity mapping, aliases, subsidiaries, and context.

Maps stock symbols to rich company metadata so news/event discovery can search
beyond the bare ticker string. Data comes from yfinance info + a curated
overlay for major NSE stocks.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.core.database import get_db

logger = logging.getLogger(__name__)

CURATED_COMPANIES: dict[str, dict] = {
    "RELIANCE.NS": {
        "name": "Reliance Industries Ltd",
        "aliases": ["Reliance", "RIL", "Reliance Industries"],
        "subsidiaries": ["Jio", "Reliance Retail", "Reliance Jio", "Jio Platforms", "Reliance Digital"],
        "segments": ["oil", "petrochemicals", "refining", "telecom", "retail", "media", "new energy"],
        "commodities": ["crude oil", "natural gas", "petrochemicals"],
        "macro_factors": ["oil prices", "rupee", "interest rates", "telecom regulation"],
        "competitors": ["ONGC.NS", "BPCL.NS", "BHARTIARTL.NS", "DMART.NS"],
        "sector": "ENERGY",
        "industry": "Conglomerate - Oil & Gas / Telecom / Retail",
    },
    "TCS.NS": {
        "name": "Tata Consultancy Services Ltd",
        "aliases": ["TCS", "Tata Consultancy"],
        "subsidiaries": [],
        "segments": ["IT services", "consulting", "digital transformation", "cloud"],
        "commodities": [],
        "macro_factors": ["US economy", "rupee-dollar", "H1B visa", "tech spending", "AI"],
        "competitors": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
        "sector": "IT",
        "industry": "IT Services & Consulting",
    },
    "INFY.NS": {
        "name": "Infosys Ltd",
        "aliases": ["Infosys", "INFY"],
        "subsidiaries": ["EdgeVerve", "Infosys BPM"],
        "segments": ["IT services", "consulting", "digital", "cloud", "AI"],
        "commodities": [],
        "macro_factors": ["US economy", "rupee-dollar", "H1B visa", "tech spending", "AI"],
        "competitors": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
        "sector": "IT",
        "industry": "IT Services & Consulting",
    },
    "HDFCBANK.NS": {
        "name": "HDFC Bank Ltd",
        "aliases": ["HDFC Bank", "HDFC"],
        "subsidiaries": ["HDB Financial Services"],
        "segments": ["retail banking", "wholesale banking", "treasury", "insurance"],
        "commodities": [],
        "macro_factors": ["RBI policy", "repo rate", "interest rates", "credit growth", "NPA"],
        "competitors": ["ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
        "sector": "BANKING",
        "industry": "Private Sector Bank",
    },
    "ICICIBANK.NS": {
        "name": "ICICI Bank Ltd",
        "aliases": ["ICICI Bank", "ICICI"],
        "subsidiaries": ["ICICI Prudential", "ICICI Lombard", "ICICI Securities"],
        "segments": ["retail banking", "corporate banking", "treasury", "insurance"],
        "commodities": [],
        "macro_factors": ["RBI policy", "repo rate", "interest rates", "credit growth", "NPA"],
        "competitors": ["HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
        "sector": "BANKING",
        "industry": "Private Sector Bank",
    },
    "SBIN.NS": {
        "name": "State Bank of India",
        "aliases": ["SBI", "State Bank"],
        "subsidiaries": ["SBI Life", "SBI Cards", "SBI MF"],
        "segments": ["retail banking", "corporate banking", "treasury", "international"],
        "commodities": [],
        "macro_factors": ["RBI policy", "repo rate", "government policy", "PSU reform"],
        "competitors": ["HDFCBANK.NS", "ICICIBANK.NS", "BANKBARODA.NS"],
        "sector": "BANKING",
        "industry": "Public Sector Bank",
    },
    "TATAMOTORS.NS": {
        "name": "Tata Motors Ltd",
        "aliases": ["Tata Motors", "JLR", "Jaguar Land Rover"],
        "subsidiaries": ["Jaguar Land Rover", "Tata Passenger Electric"],
        "segments": ["commercial vehicles", "passenger vehicles", "EV", "luxury cars"],
        "commodities": ["steel", "aluminium", "copper", "lithium"],
        "macro_factors": ["auto sales", "EV policy", "commodity prices", "UK economy"],
        "competitors": ["MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS"],
        "sector": "AUTO",
        "industry": "Automobile",
    },
    "MARUTI.NS": {
        "name": "Maruti Suzuki India Ltd",
        "aliases": ["Maruti", "Maruti Suzuki"],
        "subsidiaries": [],
        "segments": ["passenger vehicles", "compact cars", "SUV", "CNG vehicles"],
        "commodities": ["steel", "aluminium", "rubber"],
        "macro_factors": ["auto sales", "fuel prices", "rural demand", "interest rates"],
        "competitors": ["TATAMOTORS.NS", "M&M.NS", "HYUNDAI.NS"],
        "sector": "AUTO",
        "industry": "Automobile - Passenger Cars",
    },
    "HINDUNILVR.NS": {
        "name": "Hindustan Unilever Ltd",
        "aliases": ["HUL", "Hindustan Unilever"],
        "subsidiaries": [],
        "segments": ["home care", "beauty & personal care", "foods & refreshment"],
        "commodities": ["palm oil", "crude oil"],
        "macro_factors": ["rural demand", "FMCG demand", "inflation", "commodity prices"],
        "competitors": ["ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "GODREJCP.NS"],
        "sector": "FMCG",
        "industry": "FMCG",
    },
    "ITC.NS": {
        "name": "ITC Ltd",
        "aliases": ["ITC"],
        "subsidiaries": [],
        "segments": ["cigarettes", "FMCG", "hotels", "agri-business", "paper"],
        "commodities": ["tobacco", "wheat"],
        "macro_factors": ["GST", "tobacco regulation", "rural demand", "hotel recovery"],
        "competitors": ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
        "sector": "FMCG",
        "industry": "FMCG - Diversified",
    },
    "SUNPHARMA.NS": {
        "name": "Sun Pharmaceutical Industries Ltd",
        "aliases": ["Sun Pharma"],
        "subsidiaries": ["Taro Pharmaceutical"],
        "segments": ["generics", "specialty", "API", "OTC"],
        "commodities": [],
        "macro_factors": ["US FDA", "drug pricing", "rupee-dollar", "API regulation"],
        "competitors": ["DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
        "sector": "PHARMA",
        "industry": "Pharmaceuticals",
    },
    "TATASTEEL.NS": {
        "name": "Tata Steel Ltd",
        "aliases": ["Tata Steel"],
        "subsidiaries": ["Tata Steel Europe", "Tata Steel Long Products"],
        "segments": ["flat steel", "long steel", "tubes", "Europe operations"],
        "commodities": ["iron ore", "coking coal", "steel"],
        "macro_factors": ["steel prices", "China demand", "infrastructure spending", "import duties"],
        "competitors": ["JSWSTEEL.NS", "HINDALCO.NS", "SAIL.NS"],
        "sector": "METALS",
        "industry": "Steel",
    },
    "WIPRO.NS": {
        "name": "Wipro Ltd",
        "aliases": ["Wipro"],
        "subsidiaries": ["Capco"],
        "segments": ["IT services", "consulting", "BFSI", "healthcare IT"],
        "commodities": [],
        "macro_factors": ["US economy", "rupee-dollar", "tech spending"],
        "competitors": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "TECHM.NS"],
        "sector": "IT",
        "industry": "IT Services & Consulting",
    },
    "HCLTECH.NS": {
        "name": "HCL Technologies Ltd",
        "aliases": ["HCLTech", "HCL Tech", "HCL Technologies"],
        "subsidiaries": [],
        "segments": ["IT services", "engineering R&D", "products & platforms"],
        "commodities": [],
        "macro_factors": ["US economy", "rupee-dollar", "tech spending"],
        "competitors": ["TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
        "sector": "IT",
        "industry": "IT Services & Consulting",
    },
    "BAJFINANCE.NS": {
        "name": "Bajaj Finance Ltd",
        "aliases": ["Bajaj Finance", "BFL"],
        "subsidiaries": ["Bajaj Housing Finance"],
        "segments": ["consumer lending", "SME lending", "housing finance", "deposits"],
        "commodities": [],
        "macro_factors": ["interest rates", "credit growth", "consumption", "NPA"],
        "competitors": ["HDFCBANK.NS", "ICICIBANK.NS", "SHRIRAMFIN.NS"],
        "sector": "BANKING",
        "industry": "NBFC",
    },
    "ADANIENT.NS": {
        "name": "Adani Enterprises Ltd",
        "aliases": ["Adani Enterprises", "Adani"],
        "subsidiaries": ["Adani New Industries", "Adani Airport Holdings"],
        "segments": ["mining", "airports", "roads", "data centers", "green hydrogen", "solar"],
        "commodities": ["coal", "copper"],
        "macro_factors": ["infrastructure spending", "green energy", "Hindenburg"],
        "competitors": ["RELIANCE.NS"],
        "sector": "METALS",
        "industry": "Conglomerate - Infrastructure",
    },
    "KOTAKBANK.NS": {
        "name": "Kotak Mahindra Bank Ltd",
        "aliases": ["Kotak Bank", "Kotak"],
        "subsidiaries": ["Kotak Securities", "Kotak AMC", "Kotak Life"],
        "segments": ["banking", "insurance", "asset management", "securities"],
        "commodities": [],
        "macro_factors": ["RBI policy", "repo rate", "interest rates"],
        "competitors": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS"],
        "sector": "BANKING",
        "industry": "Private Sector Bank",
    },
    "AXISBANK.NS": {
        "name": "Axis Bank Ltd",
        "aliases": ["Axis Bank"],
        "subsidiaries": ["Axis AMC", "Axis Securities"],
        "segments": ["retail banking", "corporate banking", "treasury"],
        "commodities": [],
        "macro_factors": ["RBI policy", "repo rate", "interest rates", "credit growth"],
        "competitors": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS"],
        "sector": "BANKING",
        "industry": "Private Sector Bank",
    },
    "NTPC.NS": {
        "name": "NTPC Ltd",
        "aliases": ["NTPC"],
        "subsidiaries": ["NTPC Green Energy"],
        "segments": ["thermal power", "solar", "hydro", "nuclear"],
        "commodities": ["coal", "natural gas"],
        "macro_factors": ["power demand", "coal prices", "green energy transition"],
        "competitors": ["POWERGRID.NS", "TATAPOWER.NS", "ADANIGREEN.NS"],
        "sector": "ENERGY",
        "industry": "Power Generation",
    },
    "ONGC.NS": {
        "name": "Oil & Natural Gas Corporation Ltd",
        "aliases": ["ONGC"],
        "subsidiaries": ["HPCL", "MRPL"],
        "segments": ["crude oil exploration", "natural gas", "refining"],
        "commodities": ["crude oil", "natural gas"],
        "macro_factors": ["oil prices", "government policy", "disinvestment"],
        "competitors": ["RELIANCE.NS", "BPCL.NS", "VEDL.NS"],
        "sector": "ENERGY",
        "industry": "Oil & Gas - Exploration",
    },
    "DRREDDY.NS": {
        "name": "Dr. Reddy's Laboratories Ltd",
        "aliases": ["Dr Reddy's", "Dr Reddys", "DRL"],
        "subsidiaries": [],
        "segments": ["generics", "biosimilars", "API", "proprietary products"],
        "commodities": [],
        "macro_factors": ["US FDA", "drug pricing", "rupee-dollar"],
        "competitors": ["SUNPHARMA.NS", "CIPLA.NS", "LUPIN.NS"],
        "sector": "PHARMA",
        "industry": "Pharmaceuticals",
    },
    "BHARTIARTL.NS": {
        "name": "Bharti Airtel Ltd",
        "aliases": ["Airtel", "Bharti Airtel"],
        "subsidiaries": ["Airtel Africa", "Airtel Payments Bank", "Nxtra Data"],
        "segments": ["mobile services", "broadband", "enterprise", "digital TV", "Africa operations"],
        "commodities": [],
        "macro_factors": ["ARPU", "spectrum auction", "5G rollout", "telecom regulation", "data pricing"],
        "competitors": ["RELIANCE.NS", "IDEA.NS"],
        "sector": "TELECOM",
        "industry": "Telecom Services",
    },
    "LT.NS": {
        "name": "Larsen & Toubro Ltd",
        "aliases": ["L&T", "Larsen & Toubro", "Larsen and Toubro"],
        "subsidiaries": ["L&T Technology Services", "L&T Infotech", "L&T Finance"],
        "segments": ["infrastructure", "engineering", "construction", "IT", "financial services", "defence"],
        "commodities": ["steel", "cement"],
        "macro_factors": ["infrastructure spending", "government capex", "order inflows", "interest rates"],
        "competitors": ["ADANIENT.NS"],
        "sector": "INFRASTRUCTURE",
        "industry": "Engineering & Construction",
    },
    "JSWSTEEL.NS": {
        "name": "JSW Steel Ltd",
        "aliases": ["JSW Steel", "JSW"],
        "subsidiaries": ["JSW Paints", "JSW Cement"],
        "segments": ["flat steel", "long steel", "coated products", "value-added steel"],
        "commodities": ["iron ore", "coking coal", "steel"],
        "macro_factors": ["steel prices", "China demand", "infrastructure spending", "import duties"],
        "competitors": ["TATASTEEL.NS", "SAIL.NS", "HINDALCO.NS"],
        "sector": "METALS",
        "industry": "Steel",
    },
    "TITAN.NS": {
        "name": "Titan Company Ltd",
        "aliases": ["Titan", "Titan Company"],
        "subsidiaries": ["Tanishq", "Titan Eyeplus", "CaratLane"],
        "segments": ["jewellery", "watches", "eyecare", "accessories"],
        "commodities": ["gold", "silver", "diamonds"],
        "macro_factors": ["gold prices", "consumer spending", "wedding season", "rural demand"],
        "competitors": ["KALYANKJIL.NS", "PCJEWELLER.NS"],
        "sector": "CONSUMER",
        "industry": "Jewellery & Watches",
    },
}

_DEFAULT_ENTRY = {
    "aliases": [],
    "subsidiaries": [],
    "segments": [],
    "commodities": [],
    "macro_factors": [],
    "competitors": [],
}

CACHE_TTL_HOURS = 24


async def get_company_profile(symbol: str) -> dict:
    """Get rich company profile — curated data + yfinance info, cached in MongoDB."""
    symbol = symbol.upper()

    db = get_db()
    if db is not None:
        cached = await db.company_profiles.find_one({"symbol": symbol})
        if cached:
            updated = cached.get("updated_at", datetime.min)
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=UTC)
            age = datetime.now(UTC) - updated
            if age < timedelta(hours=CACHE_TTL_HOURS):
                cached.pop("_id", None)
                return cached

    profile = await _build_profile(symbol)

    if db is not None:
        profile["updated_at"] = datetime.now(UTC)
        try:
            await db.company_profiles.replace_one(
                {"symbol": symbol}, profile, upsert=True
            )
        except Exception:
            logger.warning("Failed to cache company profile for %s", symbol, exc_info=True)

    return profile


async def _build_profile(symbol: str) -> dict:
    curated = CURATED_COMPANIES.get(symbol, {})

    yf_info = await asyncio.to_thread(_fetch_yf_info, symbol)

    name = curated.get("name") or yf_info.get("shortName") or yf_info.get("longName") or symbol.replace(".NS", "")
    sector = curated.get("sector") or yf_info.get("sector")
    industry = curated.get("industry") or yf_info.get("industry")

    profile = {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "industry": industry,
        "exchange": "NSE" if symbol.endswith(".NS") else yf_info.get("exchange", ""),
        "market_cap": yf_info.get("marketCap"),
        "aliases": curated.get("aliases", [name.split(" Ltd")[0] if " Ltd" in name else name]),
        "subsidiaries": curated.get("subsidiaries", []),
        "segments": curated.get("segments", []),
        "commodities": curated.get("commodities", []),
        "macro_factors": curated.get("macro_factors", []),
        "competitors": curated.get("competitors", []),
    }

    return profile


def _fetch_yf_info(symbol: str) -> dict:
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        return ticker.get_info() or {}
    except Exception:
        return {}


def get_search_terms(profile: dict) -> list[str]:
    """Generate search terms for news discovery from a company profile."""
    terms = set()
    terms.add(profile.get("name", ""))
    terms.add(profile["symbol"].replace(".NS", "").replace(".BO", ""))
    for alias in profile.get("aliases", []):
        terms.add(alias)
    for sub in profile.get("subsidiaries", []):
        terms.add(sub)
    terms.discard("")
    return list(terms)


def get_context_terms(profile: dict) -> list[str]:
    """Broader context terms for macro/sector event matching."""
    terms = []
    terms.extend(profile.get("segments", []))
    terms.extend(profile.get("commodities", []))
    terms.extend(profile.get("macro_factors", []))
    return terms
