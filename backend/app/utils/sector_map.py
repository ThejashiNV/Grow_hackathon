"""Hardcoded sector mapping for ~40 common NSE stocks across 7 sectors.

Hackathon MVP per the problem statement: a perfect sector-classification system
isn't worth building in 24 hours. This is deliberately small and swappable.
"""

SYMBOL_SECTOR: dict[str, str] = {
    # IT
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "WIPRO.NS": "IT",
    "HCLTECH.NS": "IT",
    "TECHM.NS": "IT",
    "LTIM.NS": "IT",
    # Banking / Financials
    "HDFCBANK.NS": "BANKING",
    "ICICIBANK.NS": "BANKING",
    "SBIN.NS": "BANKING",
    "KOTAKBANK.NS": "BANKING",
    "AXISBANK.NS": "BANKING",
    "INDUSINDBK.NS": "BANKING",
    "BAJFINANCE.NS": "BANKING",
    # Auto
    "MARUTI.NS": "AUTO",
    "TATAMOTORS.NS": "AUTO",
    "M&M.NS": "AUTO",
    "BAJAJ-AUTO.NS": "AUTO",
    "HEROMOTOCO.NS": "AUTO",
    "EICHERMOT.NS": "AUTO",
    # Pharma
    "SUNPHARMA.NS": "PHARMA",
    "DRREDDY.NS": "PHARMA",
    "CIPLA.NS": "PHARMA",
    "DIVISLAB.NS": "PHARMA",
    "APOLLOHOSP.NS": "PHARMA",
    # FMCG
    "HINDUNILVR.NS": "FMCG",
    "ITC.NS": "FMCG",
    "NESTLEIND.NS": "FMCG",
    "BRITANNIA.NS": "FMCG",
    "TATACONSUM.NS": "FMCG",
    # Energy / Oil & Gas
    "RELIANCE.NS": "ENERGY",
    "ONGC.NS": "ENERGY",
    "NTPC.NS": "ENERGY",
    "POWERGRID.NS": "ENERGY",
    "BPCL.NS": "ENERGY",
    "COALINDIA.NS": "ENERGY",
    # Metals & Materials
    "TATASTEEL.NS": "METALS",
    "JSWSTEEL.NS": "METALS",
    "HINDALCO.NS": "METALS",
    "ADANIENT.NS": "METALS",
    "ULTRACEMCO.NS": "METALS",
    # Telecom
    "BHARTIARTL.NS": "TELECOM",
    # Infrastructure
    "LT.NS": "INFRASTRUCTURE",
    # Consumer
    "TITAN.NS": "CONSUMER",
}

# NSE sector index tickers used to compute a sector-relative move.
# yfinance coverage of these can be inconsistent; the sector service falls
# back to averaging peer stocks in the same sector when the index is unavailable.
SECTOR_INDEX_TICKER: dict[str, str] = {
    "IT": "^CNXIT",
    "BANKING": "^NSEBANK",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "ENERGY": "^CNXENERGY",
    "METALS": "^CNXMETAL",
}


def get_sector(symbol: str) -> str | None:
    return SYMBOL_SECTOR.get(symbol.upper())


def peers_in_sector(symbol: str) -> list[str]:
    sector = get_sector(symbol)
    if sector is None:
        return []
    return [s for s, sec in SYMBOL_SECTOR.items() if sec == sector and s != symbol.upper()]
