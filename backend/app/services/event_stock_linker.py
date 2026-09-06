"""Event→Stock relationship mapper.

Maps macro, sector, commodity, and geopolitical events to affected stocks
using company profiles from company_intel.py. A "crude oil price surge"
event should link to RELIANCE.NS, ONGC.NS, etc. An "RBI rate cut" should
link to all banking stocks.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.schemas.events import EventCluster, EventType
from app.services.company_intel import CURATED_COMPANIES
from app.services.event_classifier import EVENT_CATEGORY

logger = logging.getLogger(__name__)


@dataclass
class StockRelevance:
    symbol: str
    relevance_score: float  # 0-100
    reason: str


MACRO_FACTOR_KEYWORDS: dict[str, list[str]] = {
    "oil prices": ["crude", "oil", "brent", "wti", "petroleum", "opec"],
    "rupee": ["rupee", "inr", "dollar", "forex", "currency", "fx"],
    "rupee-dollar": ["rupee", "dollar", "inr", "usd", "forex", "currency"],
    "interest rates": ["rate", "interest", "repo", "lending", "mpc", "monetary"],
    "RBI policy": ["rbi", "repo", "rate", "monetary", "policy", "mpc", "npa"],
    "repo rate": ["repo", "rate", "rbi", "mpc", "monetary"],
    "credit growth": ["credit", "growth", "lending", "loan", "npa"],
    "NPA": ["npa", "bad loan", "asset quality", "provisioning"],
    "US economy": ["us economy", "wall street", "nasdaq", "s&p", "fed", "recession"],
    "H1B visa": ["h1b", "visa", "immigration", "work permit"],
    "tech spending": ["tech spend", "it spend", "digital", "cloud", "ai spend"],
    "AI": ["artificial intelligence", "ai ", "machine learning", "chatgpt", "genai"],
    "auto sales": ["auto sales", "vehicle sales", "car sales", "automobile"],
    "EV policy": ["ev ", "electric vehicle", "ev policy", "battery", "lithium"],
    "commodity prices": ["commodity", "metal", "steel", "copper", "aluminium"],
    "UK economy": ["uk economy", "britain", "british", "pound sterling"],
    "fuel prices": ["fuel price", "petrol", "diesel", "gasoline"],
    "rural demand": ["rural demand", "monsoon", "agri", "farm", "kharif", "rabi"],
    "FMCG demand": ["fmcg", "consumer goods", "staples", "consumption"],
    "inflation": ["inflation", "cpi", "wpi", "price rise", "price hike"],
    "GST": ["gst", "goods and services tax"],
    "tobacco regulation": ["tobacco", "cigarette", "smoking"],
    "US FDA": ["fda", "usfda", "us fda", "drug approval"],
    "drug pricing": ["drug price", "pharma price", "medicine price"],
    "steel prices": ["steel price", "iron ore", "coking coal"],
    "China demand": ["china demand", "china economy", "chinese"],
    "infrastructure spending": ["infrastructure", "infra spend", "capex", "roads", "highway"],
    "green energy": ["green energy", "solar", "wind", "renewable", "hydrogen"],
    "power demand": ["power demand", "electricity", "power consumption"],
    "coal prices": ["coal price", "thermal coal", "coking coal"],
    "government policy": ["government policy", "govt policy", "psu", "disinvestment"],
    "disinvestment": ["disinvestment", "privatiz", "stake sale"],
    "telecom regulation": ["telecom", "trai", "spectrum", "5g", "agr"],
}

COMMODITY_KEYWORDS: dict[str, list[str]] = {
    "crude oil": ["crude", "oil", "brent", "wti", "petroleum"],
    "natural gas": ["natural gas", "lng", "gas price"],
    "petrochemicals": ["petrochemical", "polymer", "ethylene"],
    "steel": ["steel", "hrc", "flat steel", "long steel"],
    "iron ore": ["iron ore"],
    "coking coal": ["coking coal", "met coal"],
    "coal": ["coal", "thermal coal"],
    "aluminium": ["aluminium", "aluminum", "bauxite"],
    "copper": ["copper"],
    "lithium": ["lithium", "battery metal"],
    "gold": ["gold", "bullion"],
    "palm oil": ["palm oil", "edible oil"],
    "tobacco": ["tobacco"],
    "wheat": ["wheat", "grain"],
    "rubber": ["rubber"],
}

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "IT": ["it sector", "it stocks", "tech stocks", "software", "it services"],
    "BANKING": ["banking", "bank stocks", "nifty bank", "bank nifty", "nbfc", "financial"],
    "PHARMA": ["pharma", "healthcare", "drug", "pharmaceutical"],
    "AUTO": ["auto", "automobile", "vehicle", "car", "ev "],
    "FMCG": ["fmcg", "consumer goods", "staples", "consumer staples"],
    "METALS": ["metal", "steel", "mining", "aluminium", "copper"],
    "ENERGY": ["energy", "oil", "gas", "power", "electricity", "solar"],
}


def link_event_to_stocks(
    cluster: EventCluster,
    watched_symbols: list[str] | None = None,
) -> list[StockRelevance]:
    """Find stocks affected by a non-company-specific event.

    Uses company profiles to match event content against each stock's
    commodities, macro_factors, segments, sector, and competitors.
    """
    category = EVENT_CATEGORY.get(cluster.event_type, "other")

    if category == "company":
        return []

    title_lower = cluster.canonical_title.lower()
    summary_lower = (cluster.summary or "").lower()
    text = f"{title_lower} {summary_lower}"

    candidates = watched_symbols or list(CURATED_COMPANIES.keys())
    results: list[StockRelevance] = []

    for symbol in candidates:
        profile = CURATED_COMPANIES.get(symbol, {})
        if not profile:
            continue

        score, reasons = _score_relevance(text, profile, category, cluster.event_type)

        if score > 0:
            results.append(StockRelevance(
                symbol=symbol,
                relevance_score=min(100.0, score),
                reason="; ".join(reasons),
            ))

    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results


def _score_relevance(
    text: str,
    profile: dict,
    category: str,
    event_type: EventType,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    for commodity in profile.get("commodities", []):
        keywords = COMMODITY_KEYWORDS.get(commodity, [commodity.lower()])
        for kw in keywords:
            if kw in text:
                score += 40
                reasons.append(f"commodity exposure: {commodity}")
                break

    for factor in profile.get("macro_factors", []):
        factor_kws = MACRO_FACTOR_KEYWORDS.get(factor, [factor.lower()])
        for kw in factor_kws:
            if kw in text:
                score += 35
                reasons.append(f"macro factor: {factor}")
                break

    stock_sector = profile.get("sector", "").upper()
    if category == "sector" and stock_sector:
        sector_kws = SECTOR_KEYWORDS.get(stock_sector, [])
        for kw in sector_kws:
            if kw in text:
                score += 50
                reasons.append(f"sector match: {stock_sector}")
                break

    for segment in profile.get("segments", []):
        if segment.lower() in text:
            score += 25
            reasons.append(f"business segment: {segment}")
            break

    if event_type == EventType.MACRO_RATE_CHANGE and stock_sector in ("BANKING",):
        score += 60
        reasons.append("direct rate sensitivity: banking sector")
    elif event_type == EventType.COMMODITY_PRICE:
        if any(c.lower() in text for c in profile.get("commodities", [])):
            score += 20

    if event_type == EventType.GLOBAL_MARKET:
        if stock_sector == "IT":
            if any(kw in text for kw in ["us ", "nasdaq", "wall street", "fii"]):
                score += 30
                reasons.append("US market sensitivity: IT sector")
        if "fii" in text:
            score += 15
            reasons.append("FII flow sensitivity")

    if event_type == EventType.GEOPOLITICAL:
        for factor in profile.get("macro_factors", []):
            if "china" in factor.lower() and "china" in text:
                score += 30
                reasons.append("China exposure")
                break
            if "uk" in factor.lower() and any(kw in text for kw in ["uk", "britain"]):
                score += 30
                reasons.append("UK exposure")
                break

    return score, reasons


def enrich_clusters_with_stock_links(
    clusters: list[EventCluster],
    watched_symbols: list[str] | None = None,
) -> list[EventCluster]:
    """Add affected_symbols to each cluster based on event→stock mapping."""
    for cluster in clusters:
        links = link_event_to_stocks(cluster, watched_symbols)
        if links:
            linked_symbols = [l.symbol for l in links if l.relevance_score >= 30]
            existing = set(cluster.affected_symbols)
            for sym in linked_symbols:
                if sym not in existing:
                    cluster.affected_symbols.append(sym)
    return clusters
