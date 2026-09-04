"""Curated list of major market events affecting Indian/global markets.

Well-documented, publicly known events used to annotate anomalous price
movements detected in historical data.  Not financial advice.
"""

from __future__ import annotations

from datetime import datetime, timedelta

MARKET_EVENTS: list[dict] = [
    # ── COVID-19 ──────────────────────────────────────────────────────
    {"date": "2020-01-30", "type": "pandemic",
     "title": "WHO declares COVID-19 global emergency",
     "sectors": ["all"]},
    {"date": "2020-03-12", "type": "pandemic",
     "title": "WHO declares COVID-19 pandemic — global selloff",
     "sectors": ["all"]},
    {"date": "2020-03-23", "type": "pandemic",
     "title": "India nationwide lockdown announced",
     "sectors": ["all"]},
    {"date": "2020-03-24", "type": "pandemic",
     "title": "COVID crash bottom — Nifty hits 7,511",
     "sectors": ["all"]},

    # ── Geopolitical ──────────────────────────────────────────────────
    {"date": "2019-02-27", "type": "geopolitical",
     "title": "India-Pakistan Balakot airstrikes",
     "sectors": ["all"]},
    {"date": "2022-02-24", "type": "geopolitical",
     "title": "Russia invades Ukraine — energy and metals spike",
     "sectors": ["ENERGY", "METALS", "all"]},
    {"date": "2023-10-07", "type": "geopolitical",
     "title": "Israel-Hamas conflict begins — oil prices rise",
     "sectors": ["ENERGY"]},

    # ── Policy / Government ───────────────────────────────────────────
    {"date": "2016-11-08", "type": "policy",
     "title": "India demonetisation — ₹500/₹1000 notes banned",
     "sectors": ["BANKING", "FMCG", "all"]},
    {"date": "2019-07-05", "type": "policy",
     "title": "Union Budget 2019 — FPI surcharge rattles markets",
     "sectors": ["BANKING", "all"]},
    {"date": "2019-09-20", "type": "policy",
     "title": "Corporate tax cut to 25.17% — markets rally",
     "sectors": ["all"]},
    {"date": "2020-02-01", "type": "policy",
     "title": "Union Budget 2020 — LTCG tax changes",
     "sectors": ["all"]},
    {"date": "2021-02-01", "type": "policy",
     "title": "Union Budget 2021 — disinvestment and infra push",
     "sectors": ["ENERGY", "BANKING"]},
    {"date": "2024-06-04", "type": "policy",
     "title": "India election results — BJP loses majority, coalition govt",
     "sectors": ["all"]},
    {"date": "2024-07-23", "type": "policy",
     "title": "Union Budget 2024 — LTCG raised to 12.5%, STT hiked",
     "sectors": ["all"]},

    # ── Macro / RBI ───────────────────────────────────────────────────
    {"date": "2018-10-05", "type": "macro",
     "title": "IL&FS default — NBFC crisis begins",
     "sectors": ["BANKING"]},
    {"date": "2020-03-27", "type": "macro",
     "title": "RBI emergency rate cut 75 bps to 4.4%",
     "sectors": ["BANKING", "all"]},
    {"date": "2022-05-04", "type": "macro",
     "title": "RBI surprise off-cycle rate hike 40 bps",
     "sectors": ["BANKING", "all"]},
    {"date": "2023-02-01", "type": "macro",
     "title": "Adani-Hindenburg crisis — Adani stocks crash",
     "sectors": ["ENERGY", "METALS"]},
    {"date": "2024-08-05", "type": "macro",
     "title": "Yen carry-trade unwind — global selloff",
     "sectors": ["all"]},

    # ── Commodity ─────────────────────────────────────────────────────
    {"date": "2020-04-20", "type": "commodity",
     "title": "Oil prices go negative (WTI futures)",
     "sectors": ["ENERGY"]},
    {"date": "2022-03-08", "type": "commodity",
     "title": "Nickel price spike — LME suspends trading",
     "sectors": ["METALS"]},

    # ── Regulatory ────────────────────────────────────────────────────
    {"date": "2018-02-01", "type": "regulatory",
     "title": "LTCG tax reintroduced in budget",
     "sectors": ["all"]},
    {"date": "2020-09-21", "type": "regulatory",
     "title": "SEBI tightens multi-cap fund rules",
     "sectors": ["all"]},

    # ── Global macro ──────────────────────────────────────────────────
    {"date": "2018-02-05", "type": "macro",
     "title": "US volatility spike — VIX blow-up, global selloff",
     "sectors": ["all"]},
    {"date": "2023-03-10", "type": "macro",
     "title": "Silicon Valley Bank collapse — banking fears",
     "sectors": ["BANKING", "IT"]},

    # ── Company-specific (major NSE) ──────────────────────────────────
    {"date": "2019-10-25", "type": "company",
     "title": "Infosys whistleblower complaint — CEO under scrutiny",
     "sectors": ["IT"]},
    {"date": "2020-09-21", "type": "company",
     "title": "TCS buyback announcement — ₹16,000 Cr",
     "sectors": ["IT"]},
    {"date": "2022-01-13", "type": "company",
     "title": "Reliance Q3 results — record revenue",
     "sectors": ["ENERGY"]},
    {"date": "2025-04-02", "type": "geopolitical",
     "title": "US reciprocal tariffs announced — global trade shock",
     "sectors": ["IT", "PHARMA", "METALS", "all"]},
]


def find_nearby_events(date_str: str, window_days: int = 3) -> list[dict]:
    """Return curated events within *window_days* of *date_str*."""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return []

    results = []
    for event in MARKET_EVENTS:
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
        except ValueError:
            continue
        if abs((target - event_date).days) <= window_days:
            results.append(event)
    return results
