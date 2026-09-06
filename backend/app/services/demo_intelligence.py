"""Pre-built StockIntelligence objects for demo/offline mode.

Returns deterministic, realistic data for all 18 target NSE stocks without
any API calls. Every value is hardcoded — no randomness — so the Intelligence
page is fully populated and behaves identically on every load.
"""

from __future__ import annotations

from app.schemas.intelligence import (
    AnomalousMove,
    AnomalySignalOut,
    BenchmarkComparison,
    CompanyProfile,
    DataFreshness,
    EventClusterOut,
    EventImpactOut,
    ExpectedVsActual,
    HistoricalSimilarOut,
    HorizonAnalysis,
    MLAnomalyOut,
    NewsItemOut,
    PatternDiscovery,
    ReactionWindowOut,
    RareEvent,
    RegimeChange,
    StockBaselineOut,
    StockIntelligence,
)
from app.services.company_intel import CURATED_COMPANIES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ANALYSIS_DATE = "2025-03-15"
_DATA_START = "2020-01-01"

_HORIZON_META = [
    # (period, trading_days, start_date, end_date)
    ("1W", 5, "2025-03-07", "2025-03-14"),
    ("2W", 10, "2025-02-28", "2025-03-14"),
    ("1M", 21, "2025-02-14", "2025-03-14"),
    ("3M", 63, "2024-12-14", "2025-03-14"),
    ("6M", 126, "2024-09-14", "2025-03-14"),
    ("1Y", 252, "2024-03-14", "2025-03-14"),
    ("2Y", 504, "2023-03-14", "2025-03-14"),
    ("5Y", 1260, "2020-03-14", "2025-03-14"),
]

# Shared Nifty 50 returns for each horizon
_NIFTY_RETURNS = [0.4, 0.6, 1.8, 3.5, 7.2, 12.5, 28.0, 82.0]

# Sector index returns per horizon
_SECTOR_RETURNS: dict[str, list[float]] = {
    "IT": [0.2, 0.9, 1.2, 4.0, 8.5, 14.0, 30.0, 90.0],
    "BANKING": [0.6, 0.4, 2.2, 4.5, 8.8, 15.0, 32.0, 72.0],
    "METALS": [1.5, -1.0, -2.5, -5.0, -1.5, 3.0, -2.0, 48.0],
    "ENERGY": [0.3, 0.5, 1.5, 3.0, 6.5, 10.0, 22.0, 50.0],
    "FMCG": [-0.1, -0.3, -0.8, -1.5, -2.0, -4.0, 2.0, 18.0],
    "AUTO": [0.8, 1.2, 2.5, 5.0, 9.0, 14.0, 30.0, 65.0],
    "PHARMA": [0.5, 1.0, 2.2, 5.5, 10.0, 16.0, 40.0, 85.0],
    "TELECOM": [0.6, 1.3, 3.5, 8.0, 15.0, 28.0, 60.0, 170.0],
    "INFRASTRUCTURE": [0.1, 0.7, 2.8, 5.5, 9.5, 16.0, 32.0, 68.0],
    "CONSUMER": [0.4, -0.2, 1.5, 4.0, 7.0, 10.0, 25.0, 110.0],
}

# ---------------------------------------------------------------------------
# Per-stock configuration
# ---------------------------------------------------------------------------

_STOCK_CONFIGS: dict[str, dict] = {
    # price: current price, vol: annualized vol %, beta: vs Nifty50,
    # avg_vol: avg daily volume, trend, momentum, change_pct: today,
    # returns: [1W..5Y], drawdowns: [1W..5Y]
    "RELIANCE.NS": {
        "price": 1310, "vol": 26, "beta": 1.05, "avg_vol": 12_000_000,
        "trend": "sideways", "momentum": 0.15, "change_pct": -0.32,
        "returns": [1.2, -0.5, 3.2, -2.1, 5.8, 8.5, 22.0, 65.0],
        "drawdowns": [1.9, 2.8, 4.5, 9.2, 13.0, 18.5, 26.0, 44.0],
    },
    "TCS.NS": {
        "price": 4050, "vol": 22, "beta": 0.75, "avg_vol": 3_500_000,
        "trend": "bullish", "momentum": 0.55, "change_pct": 0.48,
        "returns": [-0.8, 1.5, -2.1, 4.5, 8.2, 15.0, 28.0, 85.0],
        "drawdowns": [1.5, 2.2, 3.8, 7.0, 10.5, 15.0, 22.0, 38.0],
    },
    "INFY.NS": {
        "price": 1850, "vol": 24, "beta": 0.80, "avg_vol": 12_000_000,
        "trend": "bullish", "momentum": 0.45, "change_pct": 0.65,
        "returns": [0.5, 2.1, -1.5, 3.8, 7.5, 12.0, 25.0, 70.0],
        "drawdowns": [1.6, 2.4, 4.0, 7.5, 11.0, 16.0, 23.0, 40.0],
    },
    "HDFCBANK.NS": {
        "price": 1700, "vol": 25, "beta": 0.95, "avg_vol": 12_000_000,
        "trend": "bullish", "momentum": 0.40, "change_pct": 0.28,
        "returns": [1.5, 0.8, 2.5, 5.2, 8.0, 12.5, 18.0, 45.0],
        "drawdowns": [1.7, 2.5, 4.2, 8.0, 12.0, 17.0, 24.0, 42.0],
    },
    "ICICIBANK.NS": {
        "price": 1250, "vol": 27, "beta": 1.10, "avg_vol": 15_000_000,
        "trend": "bullish", "momentum": 0.60, "change_pct": 0.55,
        "returns": [2.0, 3.2, 4.5, 8.0, 15.0, 22.0, 55.0, 120.0],
        "drawdowns": [1.8, 2.7, 4.5, 8.5, 12.5, 17.5, 25.0, 40.0],
    },
    "SBIN.NS": {
        "price": 780, "vol": 30, "beta": 1.25, "avg_vol": 35_000_000,
        "trend": "sideways", "momentum": 0.20, "change_pct": -0.15,
        "returns": [-1.2, 1.8, 3.5, 7.5, 12.0, 18.0, 45.0, 95.0],
        "drawdowns": [2.2, 3.2, 5.5, 10.5, 15.0, 22.0, 30.0, 50.0],
    },
    "BHARTIARTL.NS": {
        "price": 1650, "vol": 24, "beta": 0.85, "avg_vol": 8_000_000,
        "trend": "bullish", "momentum": 0.70, "change_pct": 0.82,
        "returns": [0.8, 1.5, 4.0, 10.0, 18.0, 30.0, 65.0, 180.0],
        "drawdowns": [1.6, 2.3, 3.8, 7.0, 10.0, 14.5, 20.0, 35.0],
    },
    "ITC.NS": {
        "price": 470, "vol": 18, "beta": 0.55, "avg_vol": 18_000_000,
        "trend": "sideways", "momentum": 0.10, "change_pct": 0.12,
        "returns": [0.5, 1.2, 2.0, 5.0, 8.5, 15.0, 40.0, 55.0],
        "drawdowns": [1.0, 1.5, 2.5, 5.0, 7.5, 11.0, 16.0, 28.0],
    },
    "LT.NS": {
        "price": 3500, "vol": 28, "beta": 1.15, "avg_vol": 5_000_000,
        "trend": "bullish", "momentum": 0.35, "change_pct": 0.18,
        "returns": [-0.3, 1.0, 3.5, 6.0, 10.0, 18.0, 35.0, 70.0],
        "drawdowns": [2.0, 3.0, 5.0, 9.5, 14.0, 20.0, 28.0, 45.0],
    },
    "TATASTEEL.NS": {
        "price": 140, "vol": 38, "beta": 1.45, "avg_vol": 25_000_000,
        "trend": "bearish", "momentum": -0.40, "change_pct": -1.12,
        "returns": [2.5, -1.8, -4.5, -8.0, -5.0, 2.0, -10.0, 40.0],
        "drawdowns": [2.8, 4.2, 7.0, 14.0, 20.0, 30.0, 42.0, 65.0],
    },
    "JSWSTEEL.NS": {
        "price": 900, "vol": 35, "beta": 1.35, "avg_vol": 8_000_000,
        "trend": "bearish", "momentum": -0.30, "change_pct": -0.85,
        "returns": [1.8, -2.5, -3.0, -6.0, -2.0, 5.0, -5.0, 55.0],
        "drawdowns": [2.5, 3.8, 6.5, 12.5, 18.0, 27.0, 38.0, 60.0],
    },
    "ONGC.NS": {
        "price": 280, "vol": 28, "beta": 1.00, "avg_vol": 15_000_000,
        "trend": "sideways", "momentum": 0.05, "change_pct": -0.22,
        "returns": [-0.5, 1.0, 2.0, 5.0, 8.0, 12.0, 25.0, 35.0],
        "drawdowns": [2.0, 3.0, 5.0, 9.5, 14.0, 20.0, 28.0, 48.0],
    },
    "NTPC.NS": {
        "price": 380, "vol": 25, "beta": 0.90, "avg_vol": 20_000_000,
        "trend": "bullish", "momentum": 0.55, "change_pct": 0.42,
        "returns": [1.0, 2.5, 4.0, 8.0, 15.0, 25.0, 60.0, 150.0],
        "drawdowns": [1.7, 2.5, 4.2, 8.0, 11.5, 16.0, 22.0, 38.0],
    },
    "ADANIENT.NS": {
        "price": 2800, "vol": 50, "beta": 1.80, "avg_vol": 10_000_000,
        "trend": "bearish", "momentum": -0.55, "change_pct": -1.85,
        "returns": [-3.5, -5.0, -8.0, -15.0, -10.0, -20.0, 10.0, 200.0],
        "drawdowns": [3.8, 5.5, 9.0, 18.0, 28.0, 45.0, 60.0, 75.0],
    },
    "HINDUNILVR.NS": {
        "price": 2400, "vol": 18, "beta": 0.50, "avg_vol": 3_500_000,
        "trend": "bearish", "momentum": -0.35, "change_pct": -0.45,
        "returns": [-0.3, -0.8, -1.5, -3.0, -5.0, -8.0, -12.0, 15.0],
        "drawdowns": [1.0, 1.6, 2.8, 5.5, 8.5, 13.0, 20.0, 32.0],
    },
    "MARUTI.NS": {
        "price": 11500, "vol": 28, "beta": 1.05, "avg_vol": 1_500_000,
        "trend": "bullish", "momentum": 0.30, "change_pct": 0.35,
        "returns": [1.5, 2.0, 3.0, 5.5, 10.0, 15.0, 35.0, 60.0],
        "drawdowns": [2.0, 3.0, 5.0, 9.5, 14.0, 20.0, 28.0, 45.0],
    },
    "SUNPHARMA.NS": {
        "price": 1800, "vol": 25, "beta": 0.70, "avg_vol": 6_000_000,
        "trend": "bullish", "momentum": 0.50, "change_pct": 0.38,
        "returns": [0.8, 1.5, 3.0, 6.0, 12.0, 18.0, 45.0, 90.0],
        "drawdowns": [1.7, 2.5, 4.2, 8.0, 11.5, 16.0, 22.0, 38.0],
    },
    "TITAN.NS": {
        "price": 3500, "vol": 25, "beta": 1.00, "avg_vol": 3_000_000,
        "trend": "sideways", "momentum": 0.15, "change_pct": -0.10,
        "returns": [1.0, -0.5, 2.0, 5.0, 8.0, 12.0, 30.0, 120.0],
        "drawdowns": [1.7, 2.6, 4.3, 8.2, 12.0, 17.0, 24.0, 40.0],
    },
}

# ---------------------------------------------------------------------------
# Per-stock anomalous moves  (date, close, change%, direction, event)
# ---------------------------------------------------------------------------

_ANOMALY_DATA: dict[str, list[tuple]] = {
    "RELIANCE.NS": [
        ("2020-03-23", 875.0, -12.8, "down", "COVID-19 panic — broad market circuit breaker"),
        ("2020-04-22", 1175.0, 7.1, "up", "Facebook-Jio $5.7B deal announcement"),
        ("2020-07-15", 1850.0, 5.8, "up", "Google $4.5B Jio Platforms investment"),
        ("2022-04-22", 2620.0, -4.2, "down", "Broad FII outflow amid rate hike fears"),
        ("2023-02-01", 2430.0, -3.5, "down", "Budget 2023 windfall tax extension"),
        ("2024-06-04", 2850.0, -5.5, "down", "Election result shock — NDA below majority fear"),
        ("2024-09-12", 3050.0, 3.8, "up", "Reliance Retail pre-IPO placement reports"),
    ],
    "TCS.NS": [
        ("2020-03-23", 1625.0, -8.5, "down", "COVID-19 market crash"),
        ("2020-10-09", 2825.0, 6.2, "up", "Q2FY21 results beat — deal TCV surge"),
        ("2022-01-12", 3900.0, -5.2, "down", "Q3 results miss + attrition spike"),
        ("2023-01-10", 3350.0, 4.5, "up", "Q3 results beat + margin improvement"),
        ("2024-01-11", 3880.0, -3.8, "down", "Q3 revenue growth guidance cut"),
        ("2024-06-04", 3700.0, -3.2, "down", "Election result market-wide selloff"),
        ("2024-10-10", 4280.0, 3.5, "up", "Strong Q2 deal wins + AI services ramp"),
    ],
    "INFY.NS": [
        ("2020-03-23", 540.0, -9.2, "down", "COVID-19 market crash"),
        ("2021-04-14", 1400.0, 5.8, "up", "Q4FY21 blowout + guidance raise"),
        ("2022-04-13", 1650.0, -7.3, "down", "Q4FY22 guidance cut + whistleblower overhang"),
        ("2022-10-13", 1340.0, -5.1, "down", "Q2 attrition alarm + macro slowdown"),
        ("2023-04-13", 1420.0, 4.8, "up", "Q4FY23 large deal + margin recovery"),
        ("2024-01-11", 1680.0, -3.5, "down", "Weak Q3 guidance — discretionary weakness"),
        ("2024-07-18", 1900.0, 4.2, "up", "Q1FY25 beat + Generative AI deal pipeline"),
    ],
    "HDFCBANK.NS": [
        ("2020-03-23", 795.0, -10.5, "down", "COVID-19 + banking sector panic"),
        ("2020-09-21", 1050.0, -4.8, "down", "Fear of NPA wave from moratorium end"),
        ("2022-04-04", 1480.0, 5.2, "up", "HDFC-HDFC Bank merger announcement"),
        ("2023-04-15", 1600.0, -4.2, "down", "Q4 NIM compression concern"),
        ("2023-07-01", 1650.0, 3.8, "up", "HDFC merger effective — weight rebalance buying"),
        ("2024-01-16", 1620.0, -3.5, "down", "Q3 deposit growth concern"),
        ("2024-06-04", 1480.0, -4.8, "down", "Election shock — banking heavy selloff"),
    ],
    "ICICIBANK.NS": [
        ("2020-03-23", 312.0, -13.5, "down", "COVID-19 + banking sector panic"),
        ("2020-10-24", 425.0, 5.5, "up", "Q2FY21 asset quality surprise improvement"),
        ("2022-01-22", 820.0, 4.2, "up", "Q3 results — record ROE + NPA improvement"),
        ("2023-01-21", 870.0, 3.8, "up", "Q3 robust loan growth + asset quality stable"),
        ("2023-10-21", 940.0, 4.5, "up", "Q2FY24 — net profit jumps 36%"),
        ("2024-06-04", 1080.0, -5.2, "down", "Election result shock selloff"),
        ("2024-10-26", 1200.0, 3.2, "up", "Q2FY25 strong retail + business banking growth"),
    ],
    "SBIN.NS": [
        ("2020-03-23", 175.0, -14.5, "down", "COVID-19 + PSU bank panic"),
        ("2020-11-09", 235.0, 8.5, "up", "Vaccine news + PSU bank rally"),
        ("2021-11-05", 520.0, 5.2, "up", "Q2FY22 — record profit + NPA plunge"),
        ("2022-02-01", 480.0, -4.8, "down", "Budget FY23 — government borrowing fears"),
        ("2023-02-01", 570.0, 4.5, "up", "Budget 2023 — infra spending boost for PSUs"),
        ("2024-06-04", 810.0, -6.5, "down", "Election shock — PSU stocks hammered"),
        ("2024-11-08", 830.0, 3.8, "up", "Q2FY25 — strong fee income + lower slippage"),
    ],
    "BHARTIARTL.NS": [
        ("2020-03-23", 415.0, -8.2, "down", "COVID-19 market crash"),
        ("2021-02-01", 545.0, 4.5, "up", "Budget telecom-friendly reforms"),
        ("2021-09-15", 725.0, 5.8, "up", "Tariff hike announcement — ARPU boost"),
        ("2022-07-29", 720.0, 3.5, "up", "5G spectrum auction win + strong Q1"),
        ("2023-05-16", 820.0, -3.2, "down", "Q4 Africa revenue miss"),
        ("2024-06-04", 1350.0, -4.0, "down", "Election result broad selloff"),
        ("2024-11-26", 1680.0, 3.5, "up", "Tariff hike effective — ARPU crosses Rs 240"),
    ],
    "ITC.NS": [
        ("2020-03-23", 145.0, -7.5, "down", "COVID-19 — FMCG sell with everything"),
        ("2020-09-07", 175.0, -3.2, "down", "Cigarette GST hike fear"),
        ("2022-07-14", 290.0, 4.2, "up", "Q1FY23 cigarette volume recovery beat"),
        ("2023-02-01", 380.0, -3.8, "down", "Budget — tobacco tax hike"),
        ("2023-10-26", 445.0, 3.0, "up", "Q2FY24 — FMCG margins at inflection"),
        ("2024-02-01", 430.0, -2.8, "down", "Budget 2024 — ITC hotel demerger uncertainty"),
        ("2024-06-04", 420.0, -3.5, "down", "Election result broad market selloff"),
    ],
    "LT.NS": [
        ("2020-03-23", 780.0, -11.5, "down", "COVID-19 — construction halt fears"),
        ("2021-02-01", 1350.0, 6.2, "up", "Budget 2021 — massive infra capex push"),
        ("2022-02-01", 1850.0, 4.8, "up", "Budget 2022 — infra spending + PM Gati Shakti"),
        ("2023-01-25", 2200.0, 3.5, "up", "Q3FY23 record order inflows"),
        ("2023-10-25", 3000.0, -3.8, "down", "Q2FY24 margins below guidance"),
        ("2024-06-04", 3350.0, -5.8, "down", "Election result — infra stocks hammered"),
        ("2024-10-24", 3600.0, 3.2, "up", "Q2FY25 strong order book + Saudi wins"),
    ],
    "TATASTEEL.NS": [
        ("2020-03-23", 255.0, -14.0, "down", "COVID-19 + commodity crash"),
        ("2021-01-15", 680.0, 7.5, "up", "Steel price rally + China demand surge"),
        ("2021-05-10", 1200.0, 5.8, "up", "Record steel realisations + earnings beat"),
        ("2022-06-17", 850.0, -6.5, "down", "Export duty shock on steel"),
        ("2023-01-24", 108.0, -5.2, "down", "Hindenburg contagion + steel demand slump"),
        ("2024-01-31", 130.0, 4.5, "up", "Europe restructuring progress + steel uptick"),
        ("2024-06-04", 168.0, -7.2, "down", "Election shock + metals sector selloff"),
    ],
    "JSWSTEEL.NS": [
        ("2020-03-23", 145.0, -13.5, "down", "COVID-19 + commodity crash"),
        ("2021-01-15", 405.0, 6.8, "up", "Steel supercycle rally"),
        ("2021-05-10", 720.0, 5.5, "up", "Record EBITDA/tonne on steel boom"),
        ("2022-06-17", 540.0, -7.0, "down", "Steel export duty announcement"),
        ("2023-05-22", 730.0, -4.5, "down", "China overcapacity fears + steel price drop"),
        ("2024-06-04", 880.0, -6.2, "down", "Election shock + metals selloff"),
        ("2024-10-21", 950.0, 4.0, "up", "Q2FY25 volume growth + coking coal easing"),
    ],
    "ONGC.NS": [
        ("2020-03-23", 62.0, -15.2, "down", "COVID-19 + oil price collapse to $25"),
        ("2020-04-21", 68.0, -6.5, "down", "WTI crude goes negative"),
        ("2022-02-24", 175.0, 5.5, "up", "Russia-Ukraine war — oil jumps to $100+"),
        ("2022-07-05", 128.0, -5.2, "down", "Windfall tax announcement shock"),
        ("2023-09-20", 205.0, 4.8, "up", "Oil rally + OPEC cut extension"),
        ("2024-06-04", 275.0, -5.0, "down", "Election result selloff"),
        ("2024-10-14", 290.0, -3.5, "down", "Oil price drop on demand concerns"),
    ],
    "NTPC.NS": [
        ("2020-03-23", 72.0, -11.0, "down", "COVID-19 — power demand crash"),
        ("2021-02-01", 100.0, 5.5, "up", "Budget 2021 power sector reforms"),
        ("2022-10-05", 168.0, 4.2, "up", "Green energy capex ramp-up"),
        ("2023-06-15", 182.0, 3.5, "up", "Record power demand summer peak"),
        ("2024-01-15", 320.0, 4.8, "up", "NTPC Green IPO + renewable expansion"),
        ("2024-06-04", 355.0, -4.5, "down", "Election result selloff"),
        ("2024-09-27", 410.0, 3.2, "up", "Government green energy push + Q2 capacity add"),
    ],
    "ADANIENT.NS": [
        ("2020-03-23", 110.0, -16.0, "down", "COVID-19 market crash"),
        ("2022-01-03", 2050.0, 8.5, "up", "New energy + data center announcements"),
        ("2023-01-25", 3400.0, -18.5, "down", "Hindenburg Research short-seller report"),
        ("2023-01-27", 2700.0, -8.2, "down", "Hindenburg fallout day 2 — FPO cancelled"),
        ("2023-02-03", 1500.0, -10.5, "down", "Hindenburg continued selling — circuit breaker"),
        ("2023-06-12", 2100.0, 5.8, "up", "GQG Partners $1.9B stake purchase"),
        ("2024-06-04", 3100.0, -7.8, "down", "Election result shock"),
    ],
    "HINDUNILVR.NS": [
        ("2020-03-23", 1900.0, -6.5, "down", "COVID-19 — FMCG defensive but sold"),
        ("2021-04-29", 2350.0, -3.5, "down", "Q4FY21 volume miss — input cost pressure"),
        ("2022-10-19", 2550.0, -3.2, "down", "Weak Q2 rural demand + palm oil cost"),
        ("2023-04-27", 2530.0, -4.5, "down", "Q4FY23 revenue miss — FMCG slowdown"),
        ("2023-10-19", 2430.0, -3.0, "down", "Volume growth miss for 4th quarter"),
        ("2024-04-30", 2250.0, -3.2, "down", "Q4FY24 urban slowdown surprise"),
        ("2024-10-24", 2550.0, 2.8, "up", "Q2FY25 — first volume beat in 5 quarters"),
    ],
    "MARUTI.NS": [
        ("2020-03-23", 4100.0, -11.0, "down", "COVID-19 — auto production halt"),
        ("2020-06-01", 5600.0, 6.5, "up", "Lockdown easing — pent-up demand surge"),
        ("2021-07-07", 7400.0, -3.8, "down", "Chip shortage production cuts announced"),
        ("2022-07-27", 8600.0, 4.5, "up", "Q1FY23 — SUV mix boost + price hikes"),
        ("2023-10-26", 10800.0, -3.5, "down", "Q2FY24 festive season miss vs expectations"),
        ("2024-02-01", 10200.0, 3.2, "up", "Budget — hybrid vehicle incentives"),
        ("2024-10-25", 11300.0, 3.8, "up", "Q2FY25 — record profit + EV roadmap update"),
    ],
    "SUNPHARMA.NS": [
        ("2020-03-23", 310.0, -8.8, "down", "COVID-19 — supply chain disruption fears"),
        ("2020-07-14", 500.0, 5.5, "up", "COVID treatment portfolio demand surge"),
        ("2021-11-29", 785.0, -4.5, "down", "Omicron variant uncertainty"),
        ("2022-05-30", 860.0, 4.2, "up", "Specialty ramp-up in US + margin expansion"),
        ("2023-02-08", 1020.0, 3.8, "up", "Q3 specialty portfolio revenue beat"),
        ("2024-05-27", 1580.0, 4.0, "up", "US FDA approval for key dermatology drug"),
        ("2024-10-22", 1850.0, 3.5, "up", "Q2FY25 — US specialty at 35% of revenue"),
    ],
    "TITAN.NS": [
        ("2020-03-23", 900.0, -10.0, "down", "COVID-19 — retail shutdown"),
        ("2020-07-24", 1060.0, -5.5, "down", "Gold import duty hike fear"),
        ("2021-11-04", 2530.0, 5.2, "up", "Q2FY22 — Tanishq record festive sales"),
        ("2022-10-20", 2680.0, -4.2, "down", "Q2 margin pressure from gold prices"),
        ("2023-05-11", 2800.0, 4.5, "up", "Q4FY23 — jewellery growth 22% YoY"),
        ("2024-01-31", 3600.0, -4.0, "down", "Gold price spike — demand fear"),
        ("2024-11-07", 3400.0, 3.2, "up", "Q2FY25 — CaratLane growth + wedding demand"),
    ],
}

# ---------------------------------------------------------------------------
# Per-stock rare events (date, change%, desc, recovery_days, severity, type, source)
# ---------------------------------------------------------------------------

_RARE_EVENTS_DATA: dict[str, list[tuple]] = {
    "RELIANCE.NS": [
        ("2020-03-23", -12.8, "COVID-19 market circuit breaker", 45, "extreme", "market_crash", "market_wide"),
        ("2020-04-22", 7.1, "Facebook Jio mega deal", 0, "high", "corporate_action", "company_specific"),
        ("2022-04-22", -4.2, "FII outflow amid global rate hike cycle", 12, "moderate", "macro_shock", "global"),
        ("2024-06-04", -5.5, "Election result NDA seat shortfall panic", 8, "high", "political", "domestic"),
    ],
    "TCS.NS": [
        ("2020-03-23", -8.5, "COVID-19 market crash", 52, "extreme", "market_crash", "market_wide"),
        ("2022-01-12", -5.2, "Q3 attrition spike + margin miss", 20, "high", "earnings", "company_specific"),
        ("2024-06-04", -3.2, "Election result broad selloff", 5, "moderate", "political", "domestic"),
    ],
    "INFY.NS": [
        ("2020-03-23", -9.2, "COVID-19 market crash", 48, "extreme", "market_crash", "market_wide"),
        ("2022-04-13", -7.3, "FY23 guidance cut + whistleblower overhang", 30, "high", "corporate_governance", "company_specific"),
        ("2024-06-04", -3.5, "Election result broad selloff", 6, "moderate", "political", "domestic"),
    ],
    "HDFCBANK.NS": [
        ("2020-03-23", -10.5, "COVID-19 banking panic", 60, "extreme", "market_crash", "market_wide"),
        ("2020-09-21", -4.8, "Post-moratorium NPA wave fear", 15, "high", "regulatory", "sector_wide"),
        ("2024-06-04", -4.8, "Election result banking selloff", 7, "high", "political", "domestic"),
    ],
    "ICICIBANK.NS": [
        ("2020-03-23", -13.5, "COVID-19 banking panic", 55, "extreme", "market_crash", "market_wide"),
        ("2024-06-04", -5.2, "Election result banking selloff", 6, "high", "political", "domestic"),
        ("2022-06-16", -3.8, "Global rate hike selloff — banking contagion fear", 10, "moderate", "macro_shock", "global"),
    ],
    "SBIN.NS": [
        ("2020-03-23", -14.5, "COVID-19 PSU bank panic", 65, "extreme", "market_crash", "market_wide"),
        ("2020-03-06", -8.5, "Yes Bank crisis contagion to PSU banks", 18, "high", "contagion", "sector_wide"),
        ("2024-06-04", -6.5, "Election result — PSU stocks hammered", 10, "high", "political", "domestic"),
    ],
    "BHARTIARTL.NS": [
        ("2020-03-23", -8.2, "COVID-19 market crash", 30, "extreme", "market_crash", "market_wide"),
        ("2021-09-15", 5.8, "Tariff hike ARPU inflection", 0, "moderate", "regulatory", "sector_wide"),
        ("2024-06-04", -4.0, "Election result broad selloff", 5, "moderate", "political", "domestic"),
    ],
    "ITC.NS": [
        ("2020-03-23", -7.5, "COVID-19 FMCG selloff", 55, "extreme", "market_crash", "market_wide"),
        ("2023-02-01", -3.8, "Budget tobacco tax hike", 12, "moderate", "regulatory", "company_specific"),
        ("2024-06-04", -3.5, "Election result broad market selloff", 5, "moderate", "political", "domestic"),
    ],
    "LT.NS": [
        ("2020-03-23", -11.5, "COVID-19 construction halt fears", 50, "extreme", "market_crash", "market_wide"),
        ("2021-02-01", 6.2, "Budget FY22 record infrastructure capex", 0, "high", "regulatory", "sector_wide"),
        ("2024-06-04", -5.8, "Election result infra selloff", 8, "high", "political", "domestic"),
    ],
    "TATASTEEL.NS": [
        ("2020-03-23", -14.0, "COVID-19 + commodity crash", 70, "extreme", "market_crash", "market_wide"),
        ("2022-06-17", -6.5, "Steel export duty shock announcement", 25, "high", "regulatory", "sector_wide"),
        ("2024-06-04", -7.2, "Election result metals selloff", 12, "high", "political", "domestic"),
        ("2021-05-10", 5.8, "Steel supercycle record realisation", 0, "moderate", "commodity", "sector_wide"),
    ],
    "JSWSTEEL.NS": [
        ("2020-03-23", -13.5, "COVID-19 + commodity crash", 68, "extreme", "market_crash", "market_wide"),
        ("2022-06-17", -7.0, "Steel export duty shock", 22, "high", "regulatory", "sector_wide"),
        ("2024-06-04", -6.2, "Election result metals selloff", 10, "high", "political", "domestic"),
    ],
    "ONGC.NS": [
        ("2020-03-23", -15.2, "COVID-19 + oil collapse to $25/bbl", 80, "extreme", "market_crash", "market_wide"),
        ("2020-04-21", -6.5, "WTI crude goes negative", 30, "extreme", "commodity", "global"),
        ("2022-07-05", -5.2, "Windfall tax announcement on oil producers", 18, "high", "regulatory", "sector_wide"),
        ("2024-06-04", -5.0, "Election result broad selloff", 7, "high", "political", "domestic"),
    ],
    "NTPC.NS": [
        ("2020-03-23", -11.0, "COVID-19 power demand crash", 45, "extreme", "market_crash", "market_wide"),
        ("2024-06-04", -4.5, "Election result selloff", 6, "moderate", "political", "domestic"),
        ("2024-01-15", 4.8, "NTPC Green Energy IPO filing + capacity expansion", 0, "moderate", "corporate_action", "company_specific"),
    ],
    "ADANIENT.NS": [
        ("2020-03-23", -16.0, "COVID-19 market crash", 40, "extreme", "market_crash", "market_wide"),
        ("2023-01-25", -18.5, "Hindenburg Research short-seller report", 120, "extreme", "corporate_governance", "company_specific"),
        ("2023-02-03", -10.5, "Hindenburg fallout — FPO cancelled, circuit breaker", 90, "extreme", "corporate_governance", "company_specific"),
        ("2024-06-04", -7.8, "Election result shock — Adani group selloff", 15, "high", "political", "domestic"),
    ],
    "HINDUNILVR.NS": [
        ("2020-03-23", -6.5, "COVID-19 FMCG defensive sell", 25, "extreme", "market_crash", "market_wide"),
        ("2023-04-27", -4.5, "Four consecutive quarters of volume miss", 30, "moderate", "earnings", "company_specific"),
        ("2024-04-30", -3.2, "Urban FMCG slowdown surprise", 20, "moderate", "earnings", "company_specific"),
    ],
    "MARUTI.NS": [
        ("2020-03-23", -11.0, "COVID-19 auto production shutdown", 55, "extreme", "market_crash", "market_wide"),
        ("2021-07-07", -3.8, "Global chip shortage production cuts", 35, "moderate", "supply_chain", "global"),
        ("2024-06-04", -4.2, "Election result broad selloff", 6, "moderate", "political", "domestic"),
        ("2020-06-01", 6.5, "Pent-up demand surge post-lockdown", 0, "moderate", "demand_recovery", "sector_wide"),
    ],
    "SUNPHARMA.NS": [
        ("2020-03-23", -8.8, "COVID-19 supply chain disruption", 35, "extreme", "market_crash", "market_wide"),
        ("2024-05-27", 4.0, "US FDA approval for key dermatology drug", 0, "moderate", "regulatory", "company_specific"),
        ("2021-11-29", -4.5, "Omicron variant uncertainty", 10, "moderate", "pandemic", "global"),
    ],
    "TITAN.NS": [
        ("2020-03-23", -10.0, "COVID-19 retail shutdown", 50, "extreme", "market_crash", "market_wide"),
        ("2020-07-24", -5.5, "Gold import duty hike fear", 15, "high", "regulatory", "sector_wide"),
        ("2024-01-31", -4.0, "Gold price spike — demand erosion fear", 12, "moderate", "commodity", "global"),
    ],
}

# ---------------------------------------------------------------------------
# Per-stock news items (title, publisher, event_type, impact_score)
# ---------------------------------------------------------------------------

_NEWS_DATA: dict[str, list[tuple]] = {
    "RELIANCE.NS": [
        ("Reliance Q3 profit rises 12% on Jio, Retail strength", "Moneycontrol", "earnings", 0.72),
        ("Reliance Retail pre-IPO buzz — valuation nears $100B", "Economic Times", "corporate", 0.68),
        ("Jio 5G subscriber base crosses 150M milestone", "LiveMint", "technology", 0.55),
        ("OPEC+ output cut lifts Reliance refining margins", "Business Standard", "commodity", 0.48),
        ("Reliance New Energy invests $50M in solar cell plant", "CNBC-TV18", "corporate", 0.42),
        ("FIIs trim Reliance stake by 0.3% in Q3 — data", "ET Markets", "flows", 0.35),
    ],
    "TCS.NS": [
        ("TCS wins $2.5B deal from UK financial services major", "Moneycontrol", "deal_win", 0.78),
        ("TCS Q3 results: revenue up 6% YoY, EBIT margin at 25.3%", "Economic Times", "earnings", 0.72),
        ("TCS AI services order book crosses $1B annually", "LiveMint", "technology", 0.65),
        ("TCS announces Rs 17,000 Cr buyback at Rs 4,150/share", "Business Standard", "corporate", 0.55),
        ("Attrition falls to 12.5%, lowest in 3 years", "CNBC-TV18", "corporate", 0.42),
        ("US banking clients ramp up tech spending — TCS key beneficiary", "ET Markets", "sector", 0.38),
    ],
    "INFY.NS": [
        ("Infosys wins mega deal from European auto major worth $1.5B", "Moneycontrol", "deal_win", 0.75),
        ("Infosys Q3: revenue guidance raised to 4-5% for FY25", "Economic Times", "earnings", 0.70),
        ("Infosys AI-first strategy drives 8 large deals in Q3", "LiveMint", "technology", 0.62),
        ("Infosys topaz AI platform adoption triples in H2", "Business Standard", "technology", 0.55),
        ("Infosys CFO signals margin improvement path to 22%", "CNBC-TV18", "earnings", 0.48),
        ("H1B visa reform debate — Infosys exposure analysis", "ET Markets", "regulatory", 0.35),
    ],
    "HDFCBANK.NS": [
        ("HDFC Bank Q3: NIM stable at 3.5%, deposit growth at 16%", "Moneycontrol", "earnings", 0.70),
        ("Post-merger HDFC Bank sees retail loan growth accelerate", "Economic Times", "corporate", 0.62),
        ("RBI lifts business restriction on HDFC Bank digital products", "LiveMint", "regulatory", 0.58),
        ("HDFC Bank inclusion weight rises in MSCI — FPI inflows expected", "Business Standard", "flows", 0.52),
        ("HDFC Bank reaches 8,500 branch milestone — rural push", "CNBC-TV18", "corporate", 0.40),
        ("Credit growth at 18% — HDFC Bank leading private banks", "ET Markets", "sector", 0.35),
    ],
    "ICICIBANK.NS": [
        ("ICICI Bank Q3 net profit jumps 25% — record ROE of 18%", "Moneycontrol", "earnings", 0.75),
        ("ICICI Bank digital transactions up 45% — tech platform edge", "Economic Times", "technology", 0.60),
        ("ICICI Bank NPA at decade low of 2.1% GNPA", "LiveMint", "earnings", 0.55),
        ("ICICI Prudential Life posts strong premium growth", "Business Standard", "subsidiary", 0.42),
        ("RBI rate hold — ICICI Bank NIM impact neutral", "CNBC-TV18", "regulatory", 0.38),
        ("ICICI Bank retail loan book crosses Rs 5 lakh crore", "ET Markets", "corporate", 0.35),
    ],
    "SBIN.NS": [
        ("SBI Q2 net profit rises 28% to Rs 18,331 Cr", "Moneycontrol", "earnings", 0.72),
        ("SBI slippage ratio at historic low — asset quality strength", "Economic Times", "earnings", 0.65),
        ("Government disinvestment in SBI off the table — FM", "LiveMint", "regulatory", 0.55),
        ("SBI Cards IPO buzz — potential partial listing", "Business Standard", "corporate", 0.48),
        ("SBI leads PSU bank rally on Budget infrastructure push", "CNBC-TV18", "regulatory", 0.42),
        ("SBI YONO digital users cross 70M — digital banking leader", "ET Markets", "technology", 0.35),
    ],
    "BHARTIARTL.NS": [
        ("Airtel ARPU crosses Rs 240 after latest tariff hike", "Moneycontrol", "earnings", 0.75),
        ("Airtel 5G reaches 700 cities — coverage at 90% urban", "Economic Times", "technology", 0.65),
        ("Airtel Africa revenue jumps 18% in constant currency", "LiveMint", "earnings", 0.55),
        ("TRAI recommends spectrum allocation reform — Airtel positive", "Business Standard", "regulatory", 0.50),
        ("Airtel Business enterprise segment grows 25% YoY", "CNBC-TV18", "corporate", 0.42),
        ("Google invests additional $350M in Airtel for AI push", "ET Markets", "corporate", 0.60),
    ],
    "ITC.NS": [
        ("ITC Q2: cigarette volume up 5%, FMCG EBITDA positive", "Moneycontrol", "earnings", 0.68),
        ("ITC Hotels demerger record date set — listing timeline", "Economic Times", "corporate", 0.62),
        ("ITC FMCG brands cross Rs 30,000 Cr annual revenue", "LiveMint", "corporate", 0.55),
        ("Tobacco regulation risk — WHO framework concerns", "Business Standard", "regulatory", 0.45),
        ("ITC agri-business exports jump on global food demand", "CNBC-TV18", "earnings", 0.40),
        ("ITC sustainability report — carbon neutral by 2030 target", "ET Markets", "esg", 0.30),
    ],
    "LT.NS": [
        ("L&T wins Rs 15,000 Cr Middle East infrastructure order", "Moneycontrol", "deal_win", 0.78),
        ("L&T Q2: order inflow up 30%, order book at Rs 4.8 lakh Cr", "Economic Times", "earnings", 0.72),
        ("L&T enters green hydrogen EPC with first Saudi project", "LiveMint", "corporate", 0.60),
        ("Infrastructure spending at Rs 11.1 lakh Cr — L&T key beneficiary", "Business Standard", "regulatory", 0.55),
        ("L&T Technology Services Q2 deal pipeline at record", "CNBC-TV18", "subsidiary", 0.45),
        ("L&T semiconductor fab venture moves to Phase 2", "ET Markets", "technology", 0.42),
    ],
    "TATASTEEL.NS": [
        ("Tata Steel Q2: India operations EBITDA/t at Rs 14,200", "Moneycontrol", "earnings", 0.65),
        ("Tata Steel Europe restructuring — UK Port Talbot progress", "Economic Times", "corporate", 0.60),
        ("Steel prices drop 5% on China overcapacity flood", "LiveMint", "commodity", 0.55),
        ("Anti-dumping duty petition on Chinese steel imports", "Business Standard", "regulatory", 0.50),
        ("Tata Steel Kalinganagar expansion commissioning on track", "CNBC-TV18", "corporate", 0.45),
        ("India steel demand growth at 8% — infrastructure driven", "ET Markets", "sector", 0.38),
    ],
    "JSWSTEEL.NS": [
        ("JSW Steel Q2 crude steel production at record 7.2 MT", "Moneycontrol", "earnings", 0.68),
        ("JSW Steel capacity expansion to 37 MTPA by FY26", "Economic Times", "corporate", 0.60),
        ("Coking coal prices ease 15% — margin tailwind for JSW", "LiveMint", "commodity", 0.55),
        ("JSW Paints reaches Rs 2,500 Cr revenue milestone", "Business Standard", "subsidiary", 0.42),
        ("China steel exports hit Indian prices — margin pressure", "CNBC-TV18", "commodity", 0.50),
        ("JSW value-added steel mix reaches 60% — realisation boost", "ET Markets", "corporate", 0.40),
    ],
    "ONGC.NS": [
        ("ONGC Q2: net profit up 18% on higher oil realisations", "Moneycontrol", "earnings", 0.65),
        ("Brent crude at $82 — ONGC realisations above $75/bbl", "Economic Times", "commodity", 0.55),
        ("ONGC KG basin gas output ramp-up on schedule", "LiveMint", "corporate", 0.50),
        ("Government windfall tax reduced to zero — ONGC relief", "Business Standard", "regulatory", 0.60),
        ("ONGC Videsh acquires 30% stake in Azerbaijan field", "CNBC-TV18", "corporate", 0.45),
        ("OPEC+ extends output cuts — positive for Indian upstream", "ET Markets", "commodity", 0.42),
    ],
    "NTPC.NS": [
        ("NTPC Q2: power generation up 12%, PLF at 78%", "Moneycontrol", "earnings", 0.68),
        ("NTPC Green Energy IPO subscribed 3.2x — strong debut", "Economic Times", "corporate", 0.72),
        ("NTPC adds 2.5 GW renewable capacity in H1 FY25", "LiveMint", "corporate", 0.58),
        ("India peak power demand hits 250 GW — NTPC key supplier", "Business Standard", "sector", 0.55),
        ("NTPC hydrogen pilot project achieves first output", "CNBC-TV18", "technology", 0.45),
        ("Coal India allocation to NTPC up 10% — fuel security", "ET Markets", "supply_chain", 0.40),
    ],
    "ADANIENT.NS": [
        ("Adani Enterprises Q2: revenue up 15% on airports, solar", "Moneycontrol", "earnings", 0.60),
        ("Hindenburg impact fading — Adani bonds recover to par", "Economic Times", "corporate", 0.55),
        ("Adani Group $100B infra investment plan over 10 years", "LiveMint", "corporate", 0.65),
        ("SEBI investigation update — no adverse findings so far", "Business Standard", "regulatory", 0.58),
        ("Adani Green achieves 10 GW operational capacity", "CNBC-TV18", "subsidiary", 0.50),
        ("GQG Partners increases Adani stake — confidence signal", "ET Markets", "flows", 0.45),
        ("US DOJ Adani bribery allegations — stock under pressure", "Reuters India", "legal", 0.80),
    ],
    "HINDUNILVR.NS": [
        ("HUL Q2: volume growth turns positive at 2% after 5 quarters", "Moneycontrol", "earnings", 0.70),
        ("HUL price cuts in soaps, detergents to drive volumes", "Economic Times", "corporate", 0.55),
        ("Rural FMCG recovery — HUL distribution reach at 9M outlets", "LiveMint", "sector", 0.50),
        ("HUL beauty and personal care margin at record 25%", "Business Standard", "earnings", 0.48),
        ("D2C competition intensifies — impact on HUL market share", "CNBC-TV18", "competitive", 0.42),
        ("Palm oil price drop — input cost tailwind for HUL", "ET Markets", "commodity", 0.38),
    ],
    "MARUTI.NS": [
        ("Maruti Q2: net profit up 20% on SUV mix + price hikes", "Moneycontrol", "earnings", 0.72),
        ("Maruti EV launch timeline — first electric SUV by 2025-end", "Economic Times", "technology", 0.65),
        ("Maruti domestic sales up 8% in Oct — festive demand strong", "LiveMint", "earnings", 0.58),
        ("CNG vehicle share crosses 30% of Maruti sales", "Business Standard", "corporate", 0.48),
        ("New Kharkhoda plant Phase 1 — 250K capacity operational", "CNBC-TV18", "corporate", 0.45),
        ("Budget hybrid vehicle incentive — positive for Maruti", "ET Markets", "regulatory", 0.55),
    ],
    "SUNPHARMA.NS": [
        ("Sun Pharma Q2: specialty revenue up 28% — US franchise grows", "Moneycontrol", "earnings", 0.72),
        ("FDA clears Sun Pharma Halol plant — no observations", "Economic Times", "regulatory", 0.68),
        ("Sun Pharma specialty pipeline — 3 new US filings in H2", "LiveMint", "corporate", 0.60),
        ("India pharma exports at record $28B — Sun Pharma leads", "Business Standard", "sector", 0.50),
        ("Taro Pharmaceutical turnaround — EBITDA margins at 18%", "CNBC-TV18", "subsidiary", 0.45),
        ("Sun Pharma biosimilar strategy — partnership with global MNC", "ET Markets", "corporate", 0.42),
    ],
    "TITAN.NS": [
        ("Titan Q2: jewellery revenue up 18%, Tanishq record quarter", "Moneycontrol", "earnings", 0.72),
        ("CaratLane crosses Rs 4,000 Cr annual revenue — growth engine", "Economic Times", "subsidiary", 0.65),
        ("Gold prices at Rs 78,000/10g — Titan hedging strategy works", "LiveMint", "commodity", 0.55),
        ("Titan Eyeplus reaches 1,000 stores — optical expansion", "Business Standard", "corporate", 0.42),
        ("Wedding season demand strong — Tanishq 22% studded growth", "CNBC-TV18", "earnings", 0.58),
        ("Titan wearables exits — focus on core jewellery + watches", "ET Markets", "corporate", 0.38),
    ],
}

# ---------------------------------------------------------------------------
# Per-stock event clusters (id, title, type, category, article_count,
#    sources, first_seen, last_seen, impact_score, severity, summary)
# ---------------------------------------------------------------------------

_EVENT_CLUSTERS_DATA: dict[str, list[tuple]] = {
    "RELIANCE.NS": [
        ("rel_retail_ipo", "Reliance Retail IPO Speculation", "corporate", "markets", 6,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-15", "2025-03-10", 0.68, "medium",
         "Growing speculation about Reliance Retail IPO timing and valuation."),
        ("jio_5g_expansion", "Jio 5G Network Expansion", "technology", "telecom", 4,
         ["CNBC-TV18", "ET"], "2025-02-01", "2025-03-08", 0.52, "low",
         "Jio 5G rollout reaches 95% of urban India."),
    ],
    "TCS.NS": [
        ("tcs_ai_deals", "TCS AI Services Deal Pipeline", "deal_win", "technology", 5,
         ["Moneycontrol", "ET", "BS"], "2025-01-20", "2025-03-12", 0.72, "medium",
         "TCS secures multiple large AI transformation deals."),
        ("it_sector_outlook", "IT Sector FY26 Growth Outlook", "sector", "macro", 4,
         ["LiveMint", "CNBC-TV18"], "2025-02-15", "2025-03-10", 0.45, "low",
         "Analyst consensus upgrades for IT sector growth."),
    ],
    "INFY.NS": [
        ("infy_ai_platform", "Infosys Topaz AI Adoption", "technology", "corporate", 5,
         ["Moneycontrol", "ET"], "2025-01-10", "2025-03-05", 0.65, "medium",
         "Infosys Topaz AI platform adopted by 200+ enterprise clients."),
        ("infy_margin_recovery", "Infosys Margin Improvement Path", "earnings", "corporate", 3,
         ["BS", "CNBC-TV18"], "2025-02-20", "2025-03-12", 0.50, "low",
         "Infosys on track to reach 22% EBIT margin target."),
    ],
    "HDFCBANK.NS": [
        ("hdfc_merger_integration", "HDFC Bank Post-Merger Integration", "corporate", "banking", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-05", "2025-03-10", 0.62, "medium",
         "HDFC Bank completes key merger integration milestones."),
        ("rbi_rate_decision", "RBI Monetary Policy Impact", "regulatory", "macro", 4,
         ["BS", "CNBC-TV18"], "2025-02-08", "2025-02-12", 0.55, "medium",
         "RBI holds repo rate — impact on bank NIMs assessed."),
    ],
    "ICICIBANK.NS": [
        ("icici_digital_growth", "ICICI Bank Digital Transformation", "technology", "banking", 4,
         ["Moneycontrol", "ET"], "2025-01-25", "2025-03-08", 0.58, "low",
         "ICICI digital platform processes 85% of retail transactions."),
        ("icici_asset_quality", "ICICI Bank Asset Quality Trend", "earnings", "banking", 3,
         ["LiveMint", "BS"], "2025-02-10", "2025-03-05", 0.52, "low",
         "ICICI Bank GNPA trends to sub-2% — best in decade."),
    ],
    "SBIN.NS": [
        ("sbi_q3_results", "SBI Record Quarterly Profit", "earnings", "banking", 5,
         ["Moneycontrol", "ET", "CNBC-TV18"], "2025-02-05", "2025-02-12", 0.70, "medium",
         "SBI posts highest-ever quarterly net profit."),
        ("psu_bank_reforms", "PSU Banking Sector Reform Push", "regulatory", "macro", 3,
         ["LiveMint", "BS"], "2025-01-15", "2025-02-28", 0.48, "low",
         "Government signals further PSU bank consolidation."),
    ],
    "BHARTIARTL.NS": [
        ("airtel_tariff_hike", "Airtel Tariff Revision Impact", "corporate", "telecom", 6,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-20", "2025-03-12", 0.75, "medium",
         "Airtel tariff hike boosts ARPU beyond Rs 240."),
        ("5g_monetization", "5G Monetization Progress", "technology", "telecom", 4,
         ["BS", "CNBC-TV18"], "2025-02-05", "2025-03-08", 0.55, "low",
         "Telecom 5G ARPU premium begins reflecting in revenues."),
    ],
    "ITC.NS": [
        ("itc_hotel_demerger", "ITC Hotels Demerger Progress", "corporate", "corporate", 5,
         ["Moneycontrol", "ET"], "2025-01-10", "2025-03-10", 0.65, "medium",
         "ITC Hotels demerger on track — listing expected by Q2 FY26."),
        ("fmcg_margin_inflection", "ITC FMCG Profitability Inflection", "earnings", "corporate", 3,
         ["LiveMint", "BS"], "2025-02-15", "2025-03-05", 0.50, "low",
         "ITC FMCG segment approaches sustained EBITDA profitability."),
    ],
    "LT.NS": [
        ("lt_order_inflow", "L&T Record Order Pipeline", "deal_win", "infrastructure", 5,
         ["Moneycontrol", "ET", "BS"], "2025-01-15", "2025-03-10", 0.72, "medium",
         "L&T order book swells to Rs 5 lakh Cr on Middle East wins."),
        ("infra_budget_push", "Union Budget Infrastructure Spending", "regulatory", "macro", 4,
         ["LiveMint", "CNBC-TV18"], "2025-02-01", "2025-02-10", 0.60, "medium",
         "Budget FY26 allocates Rs 11.5 lakh Cr for infrastructure."),
    ],
    "TATASTEEL.NS": [
        ("steel_price_pressure", "China Steel Dumping Concerns", "commodity", "metals", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-20", "2025-03-12", 0.65, "medium",
         "China steel overcapacity drives global price concerns."),
        ("tata_europe_restructure", "Tata Steel Europe Restructuring", "corporate", "corporate", 4,
         ["BS", "CNBC-TV18"], "2025-02-01", "2025-03-05", 0.58, "medium",
         "Tata Steel UK operations restructuring — cost savings on track."),
    ],
    "JSWSTEEL.NS": [
        ("jsw_capacity_expansion", "JSW Steel Capacity Ramp-Up", "corporate", "metals", 4,
         ["Moneycontrol", "ET"], "2025-01-25", "2025-03-08", 0.60, "medium",
         "JSW Steel capacity expansion to 37 MTPA progresses on schedule."),
        ("steel_import_duty", "Steel Import Duty Petition", "regulatory", "metals", 3,
         ["LiveMint", "BS"], "2025-02-10", "2025-03-01", 0.55, "medium",
         "Indian steel producers petition for anti-dumping duties on China."),
    ],
    "ONGC.NS": [
        ("oil_price_outlook", "Crude Oil Price Outlook", "commodity", "energy", 5,
         ["Moneycontrol", "ET", "BS"], "2025-01-15", "2025-03-10", 0.62, "medium",
         "Brent crude stabilizes at $80-85 — ONGC realisations healthy."),
        ("windfall_tax_update", "Windfall Tax Policy Review", "regulatory", "energy", 3,
         ["LiveMint", "CNBC-TV18"], "2025-02-01", "2025-02-20", 0.55, "medium",
         "Government reviews windfall tax — potential permanent removal."),
    ],
    "NTPC.NS": [
        ("ntpc_green_ipo", "NTPC Green Energy IPO Success", "corporate", "energy", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-10", "2025-02-15", 0.70, "medium",
         "NTPC Green Energy lists at 20% premium — strong institutional demand."),
        ("power_demand_surge", "India Power Demand at Record", "sector", "energy", 4,
         ["BS", "CNBC-TV18"], "2025-02-20", "2025-03-10", 0.55, "low",
         "India peak power demand touches 250 GW in pre-summer."),
    ],
    "ADANIENT.NS": [
        ("adani_legal_issues", "Adani Group Legal Developments", "legal", "corporate", 8,
         ["Moneycontrol", "ET", "Reuters", "BS"], "2025-01-05", "2025-03-12", 0.82, "high",
         "US DOJ allegations and ongoing SEBI investigation weigh on group."),
        ("adani_infra_plan", "Adani Infrastructure Investment Plan", "corporate", "infrastructure", 4,
         ["LiveMint", "CNBC-TV18"], "2025-02-01", "2025-03-05", 0.55, "medium",
         "Adani Group $100B infrastructure investment plan over next decade."),
    ],
    "HINDUNILVR.NS": [
        ("fmcg_recovery_hopes", "FMCG Volume Recovery Signals", "sector", "consumer", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-20", "2025-03-10", 0.58, "medium",
         "FMCG sector shows early signs of rural demand recovery."),
        ("hul_pricing_strategy", "HUL Price Cut Strategy Impact", "corporate", "consumer", 3,
         ["BS", "CNBC-TV18"], "2025-02-10", "2025-03-05", 0.48, "low",
         "HUL price cuts in key categories begin driving volume improvement."),
    ],
    "MARUTI.NS": [
        ("maruti_ev_launch", "Maruti Electric Vehicle Launch", "technology", "auto", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-15", "2025-03-08", 0.68, "medium",
         "Maruti confirms first electric SUV launch timeline."),
        ("auto_demand_festive", "Auto Sector Festive Demand", "sector", "auto", 4,
         ["BS", "CNBC-TV18"], "2025-02-01", "2025-03-05", 0.52, "low",
         "Auto sector posts strong festive season numbers."),
    ],
    "SUNPHARMA.NS": [
        ("sun_specialty_growth", "Sun Pharma US Specialty Revenue", "earnings", "pharma", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-20", "2025-03-10", 0.70, "medium",
         "Sun Pharma specialty portfolio reaches 35% of US revenue."),
        ("fda_inspection_clean", "FDA Inspection Outcomes", "regulatory", "pharma", 3,
         ["BS", "CNBC-TV18"], "2025-02-15", "2025-03-01", 0.58, "medium",
         "Clean FDA inspections strengthen Sun Pharma compliance track record."),
    ],
    "TITAN.NS": [
        ("titan_wedding_demand", "Wedding Season Jewellery Demand", "earnings", "consumer", 5,
         ["Moneycontrol", "ET", "LiveMint"], "2025-01-10", "2025-03-05", 0.65, "medium",
         "Strong wedding season drives Tanishq to record quarterly revenue."),
        ("gold_price_impact", "Gold Price Impact on Titan", "commodity", "consumer", 4,
         ["BS", "CNBC-TV18", "ET Markets"], "2025-02-01", "2025-03-10", 0.55, "medium",
         "Gold at Rs 78,000 — Titan hedging limits margin impact."),
    ],
}


# ---------------------------------------------------------------------------
# Sector-level pattern templates
# ---------------------------------------------------------------------------

def _sector_patterns(sector: str, vol: float) -> list[PatternDiscovery]:
    """Return sector-appropriate pattern discoveries."""
    daily_vol = round(vol / 15.87, 2)
    base = [
        PatternDiscovery(
            pattern_type="day_of_week",
            description="Monday shows marginally positive bias; Friday sees higher volume and wider range.",
            confidence=0.62,
            observations=520,
            period_analyzed="2020-01-01 to 2025-03-14",
            details={"monday_avg_return": 0.08, "friday_avg_volume_ratio": 1.12},
            is_periodic=True,
            evidence_strength="moderate",
        ),
        PatternDiscovery(
            pattern_type="vol_clustering",
            description=f"High-volatility days (>{daily_vol * 2:.1f}% moves) cluster in streaks of 3-5 days.",
            confidence=0.78,
            observations=85,
            period_analyzed="2020-01-01 to 2025-03-14",
            details={"avg_cluster_length": 3.8, "max_cluster_length": 12},
            is_periodic=False,
            evidence_strength="strong",
        ),
        PatternDiscovery(
            pattern_type="gap_and_reverse",
            description=f"Opening gaps > {daily_vol:.1f}% fill within the first 90 minutes 58% of the time.",
            confidence=0.58,
            observations=120,
            period_analyzed="2022-01-01 to 2025-03-14",
            details={"fill_rate": 0.58, "avg_fill_time_minutes": 72},
            is_periodic=False,
            evidence_strength="moderate",
        ),
        PatternDiscovery(
            pattern_type="momentum_exhaustion",
            description="After 5+ consecutive positive days, next-day returns average -0.3%.",
            confidence=0.65,
            observations=42,
            period_analyzed="2020-01-01 to 2025-03-14",
            details={"avg_streak_before_reversal": 5.2, "avg_reversal_pct": -0.3},
            is_periodic=False,
            evidence_strength="moderate",
        ),
    ]

    sector_specific: dict[str, list[PatternDiscovery]] = {
        "IT": [
            PatternDiscovery(
                pattern_type="monthly",
                description="January and April show elevated volatility around quarterly results season.",
                confidence=0.72,
                observations=20,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"jan_avg_range": daily_vol * 1.4, "apr_avg_range": daily_vol * 1.5},
                is_periodic=True,
                evidence_strength="strong",
            ),
            PatternDiscovery(
                pattern_type="volume_price_divergence",
                description="Price rallies on declining volume tend to reverse within 8 trading days.",
                confidence=0.60,
                observations=35,
                period_analyzed="2021-01-01 to 2025-03-14",
                details={"avg_reversal_days": 7.5, "avg_reversal_pct": -1.8},
                is_periodic=False,
                evidence_strength="moderate",
            ),
        ],
        "BANKING": [
            PatternDiscovery(
                pattern_type="monthly",
                description="RBI MPC weeks (Feb, Apr, Jun, Aug, Oct, Dec) show 20% higher implied vol.",
                confidence=0.75,
                observations=30,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"mpc_week_vol_premium": 0.20, "avg_mpc_day_range": daily_vol * 1.3},
                is_periodic=True,
                evidence_strength="strong",
            ),
            PatternDiscovery(
                pattern_type="volume_price_divergence",
                description="Large FII selling days predict 2-day drawdown with 65% accuracy.",
                confidence=0.65,
                observations=48,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"fii_sell_threshold_cr": -2000, "avg_2d_drawdown": -1.2},
                is_periodic=False,
                evidence_strength="strong",
            ),
        ],
        "METALS": [
            PatternDiscovery(
                pattern_type="monthly",
                description="China PMI release days (1st of month) drive 30% of monthly volatility.",
                confidence=0.70,
                observations=60,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"pmi_day_avg_move": daily_vol * 1.6, "pmi_day_vol_share": 0.30},
                is_periodic=True,
                evidence_strength="strong",
            ),
            PatternDiscovery(
                pattern_type="volume_price_divergence",
                description="Steel price moves lead stock price by 2-3 trading days.",
                confidence=0.68,
                observations=55,
                period_analyzed="2021-01-01 to 2025-03-14",
                details={"lead_lag_days": 2.5, "correlation": 0.72},
                is_periodic=False,
                evidence_strength="strong",
            ),
        ],
        "ENERGY": [
            PatternDiscovery(
                pattern_type="monthly",
                description="Brent crude weekly inventory reports drive mid-week volatility spikes.",
                confidence=0.68,
                observations=180,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"wed_avg_range": daily_vol * 1.3, "inventory_correlation": 0.55},
                is_periodic=True,
                evidence_strength="moderate",
            ),
            PatternDiscovery(
                pattern_type="volume_price_divergence",
                description="Oil price rallies without volume confirmation reverse within 5 days.",
                confidence=0.62,
                observations=40,
                period_analyzed="2021-01-01 to 2025-03-14",
                details={"avg_reversal_days": 4.8, "reversal_rate": 0.62},
                is_periodic=False,
                evidence_strength="moderate",
            ),
        ],
        "FMCG": [
            PatternDiscovery(
                pattern_type="monthly",
                description="December-January shows reduced volatility as institutional activity slows.",
                confidence=0.70,
                observations=10,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"dec_jan_vol_ratio": 0.82},
                is_periodic=True,
                evidence_strength="moderate",
            ),
            PatternDiscovery(
                pattern_type="volume_price_divergence",
                description="FMCG sells off on market-wide panic but recovers fastest — mean reversion within 3 days.",
                confidence=0.72,
                observations=25,
                period_analyzed="2020-01-01 to 2025-03-14",
                details={"avg_recovery_days": 2.8, "outperformance_in_selloffs": 1.5},
                is_periodic=False,
                evidence_strength="strong",
            ),
        ],
    }

    # Defaults for sectors without specific patterns
    for s in ("AUTO", "PHARMA", "TELECOM", "INFRASTRUCTURE", "CONSUMER"):
        if s not in sector_specific:
            sector_specific[s] = [
                PatternDiscovery(
                    pattern_type="monthly",
                    description="Quarterly results months show 15-25% higher intraday range.",
                    confidence=0.65,
                    observations=20,
                    period_analyzed="2020-01-01 to 2025-03-14",
                    details={"results_month_range_premium": 0.20},
                    is_periodic=True,
                    evidence_strength="moderate",
                ),
                PatternDiscovery(
                    pattern_type="volume_price_divergence",
                    description="Volume spikes without corresponding price movement often precede a directional move within 5 days.",
                    confidence=0.60,
                    observations=38,
                    period_analyzed="2021-01-01 to 2025-03-14",
                    details={"volume_spike_threshold": 2.0, "directional_move_rate": 0.60},
                    is_periodic=False,
                    evidence_strength="moderate",
                ),
            ]

    return base + sector_specific.get(sector, [])


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

def _build_horizons(symbol: str, cfg: dict) -> list[HorizonAnalysis]:
    price = cfg["price"]
    returns = cfg["returns"]
    drawdowns = cfg["drawdowns"]
    vol = cfg["vol"]
    avg_vol = cfg["avg_vol"]
    sector = _get_sector(symbol)
    sector_rets = _SECTOR_RETURNS.get(sector, _SECTOR_RETURNS["ENERGY"])

    horizons = []
    for i, (period, tdays, start_d, end_d) in enumerate(_HORIZON_META):
        ret = returns[i]
        start_price = round(price / (1 + ret / 100), 2)
        # Volume fluctuates mildly across horizons
        vol_vs_base = round(1.0 + (i - 3) * 0.02, 2)
        # Large moves scale with time and vol
        large_count = max(0, int(tdays * vol / 800))

        horizons.append(HorizonAnalysis(
            period=period,
            trading_days=tdays,
            start_date=start_d,
            end_date=end_d,
            start_price=start_price,
            end_price=float(price),
            return_pct=ret,
            annualized_volatility=round(vol + (i - 4) * 0.5, 1),
            max_drawdown_pct=-drawdowns[i],
            avg_daily_volume=float(avg_vol),
            volume_vs_baseline=vol_vs_base,
            large_move_count=large_count,
            trend=cfg["trend"] if i <= 3 else "varies",
            momentum_score=round(cfg["momentum"] * (1 - i * 0.08), 2),
            sector_return_pct=sector_rets[i],
            market_return_pct=_NIFTY_RETURNS[i],
            relative_performance_pct=round(ret - _NIFTY_RETURNS[i], 2),
        ))
    return horizons


def _build_anomalous_moves(symbol: str, cfg: dict) -> list[AnomalousMove]:
    raw = _ANOMALY_DATA.get(symbol, [])
    daily_vol_pct = cfg["vol"] / 15.87
    avg_vol = cfg["avg_vol"]
    moves = []
    for date, close, change_pct, direction, event in raw:
        sigma = round(abs(change_pct) / daily_vol_pct, 1)
        vol_ratio = round(1.5 + abs(change_pct) / 8, 1)
        volume = int(avg_vol * vol_ratio)
        # Mean-reversion estimates for aftermath
        if direction == "down":
            r1d = round(abs(change_pct) * 0.25, 1)
            r1w = round(abs(change_pct) * 0.45, 1)
            r2w = round(abs(change_pct) * 0.55, 1)
            r1m = round(abs(change_pct) * 0.65, 1)
        else:
            r1d = round(-change_pct * 0.15, 1)
            r1w = round(change_pct * 0.20, 1)
            r2w = round(change_pct * 0.15, 1)
            r1m = round(change_pct * 0.25, 1)

        moves.append(AnomalousMove(
            date=date,
            close=close,
            change_pct=change_pct,
            volume=volume,
            volume_ratio=vol_ratio,
            direction=direction,
            magnitude_sigma=sigma,
            return_1d=r1d,
            return_1w=r1w,
            return_2w=r2w,
            return_1m=r1m,
            associated_event=event,
            sector_return_pct=round(change_pct * 0.6, 1),
            market_return_pct=round(change_pct * 0.45, 1),
            abnormal_return_pct=round(change_pct - change_pct * 0.45, 1),
        ))
    return moves


def _build_regime_changes(cfg: dict) -> list[RegimeChange]:
    vol = cfg["vol"]
    avg_vol = cfg["avg_vol"]
    return [
        RegimeChange(
            metric="volatility",
            current_value=round(vol * 1.15, 1),
            baseline_value=float(vol),
            ratio=1.15,
            description="Current 30-day realised vol is 15% above the 1-year average.",
            period_compared="30d vs 1Y",
        ),
        RegimeChange(
            metric="volume",
            current_value=round(avg_vol * 1.22),
            baseline_value=float(avg_vol),
            ratio=1.22,
            description="Recent 2-week average volume is 22% above the 6-month median.",
            period_compared="2W vs 6M",
        ),
        RegimeChange(
            metric="trend_strength",
            current_value=round(abs(cfg["momentum"]) * 100, 1),
            baseline_value=30.0,
            ratio=round(abs(cfg["momentum"]) * 100 / 30, 2),
            description=f"ADX-based trend strength indicates a {'trending' if abs(cfg['momentum']) > 0.3 else 'range-bound'} regime.",
            period_compared="current vs historical",
        ),
        RegimeChange(
            metric="correlation",
            current_value=round(0.65 + cfg["beta"] * 0.1, 2),
            baseline_value=0.60,
            ratio=round((0.65 + cfg["beta"] * 0.1) / 0.60, 2),
            description="30-day rolling correlation with Nifty 50 is slightly above normal.",
            period_compared="30d vs 1Y",
        ),
    ]


def _build_rare_events(symbol: str) -> list[RareEvent]:
    raw = _RARE_EVENTS_DATA.get(symbol, [])
    events = []
    for date, change_pct, desc, recovery, severity, etype, source in raw:
        events.append(RareEvent(
            date=date,
            change_pct=change_pct,
            description=desc,
            recovery_days=recovery if recovery > 0 else None,
            severity=severity,
            event_type=etype,
            source=source,
        ))
    return events


def _build_expected_vs_actual(cfg: dict) -> list[ExpectedVsActual]:
    vol = cfg["vol"]
    daily_vol = round(vol / 15.87, 2)
    return [
        ExpectedVsActual(
            description="Budget Day reaction (Union Budget announcement day)",
            historical_avg_move=round(daily_vol * 1.8, 2),
            historical_observations=5,
            current_move=round(daily_vol * 1.2, 2),
            deviation="within_range",
            historical_median=round(daily_vol * 1.5, 2),
            historical_range_low=round(daily_vol * 0.5, 2),
            historical_range_high=round(daily_vol * 3.2, 2),
            similarity_score=0.72,
        ),
        ExpectedVsActual(
            description="RBI MPC day reaction",
            historical_avg_move=round(daily_vol * 1.3, 2),
            historical_observations=18,
            current_move=round(daily_vol * 0.8, 2),
            deviation="below_average",
            historical_median=round(daily_vol * 1.1, 2),
            historical_range_low=round(daily_vol * 0.2, 2),
            historical_range_high=round(daily_vol * 2.8, 2),
            similarity_score=0.65,
        ),
        ExpectedVsActual(
            description="Quarterly earnings reaction (T+1 day post results)",
            historical_avg_move=round(daily_vol * 2.2, 2),
            historical_observations=20,
            current_move=round(daily_vol * 1.8, 2),
            deviation="within_range",
            historical_median=round(daily_vol * 2.0, 2),
            historical_range_low=round(daily_vol * 0.8, 2),
            historical_range_high=round(daily_vol * 4.5, 2),
            similarity_score=0.78,
        ),
    ]


def _build_ml_anomalies(cfg: dict) -> list[MLAnomalyOut]:
    vol = cfg["vol"]
    daily_vol = round(vol / 15.87, 2)
    return [
        MLAnomalyOut(
            date="2025-03-10",
            composite_score=0.82,
            is_anomalous=True,
            explanation="Elevated volume with suppressed price range — absorption pattern detected.",
            signals=[
                AnomalySignalOut(name="volume_spike", score=0.88, z_score=2.8,
                                 description="Volume 2.8x above 20-day median"),
                AnomalySignalOut(name="range_compression", score=0.75, z_score=-1.5,
                                 description=f"Daily range at {daily_vol * 0.4:.1f}% vs normal {daily_vol:.1f}%"),
                AnomalySignalOut(name="vwap_divergence", score=0.72, z_score=2.1,
                                 description="VWAP diverging from closing price trend"),
            ],
        ),
        MLAnomalyOut(
            date="2025-02-18",
            composite_score=0.68,
            is_anomalous=True,
            explanation="Unusual price momentum without corresponding news catalyst.",
            signals=[
                AnomalySignalOut(name="momentum_without_news", score=0.78, z_score=2.3,
                                 description="3-day momentum in top 5 percentile with no significant news"),
                AnomalySignalOut(name="options_skew", score=0.65, z_score=1.8,
                                 description="Put-call ratio shifted significantly toward calls"),
            ],
        ),
        MLAnomalyOut(
            date="2025-01-22",
            composite_score=0.55,
            is_anomalous=False,
            explanation="Mild volume anomaly during sector rotation — within normal bounds.",
            signals=[
                AnomalySignalOut(name="sector_rotation", score=0.60, z_score=1.5,
                                 description="Sector relative strength shifted 1.5 sigma"),
                AnomalySignalOut(name="volume_profile", score=0.50, z_score=1.2,
                                 description="Volume concentration at specific price levels"),
            ],
        ),
        MLAnomalyOut(
            date="2024-12-05",
            composite_score=0.72,
            is_anomalous=True,
            explanation="End-of-year institutional rebalancing detected in order flow patterns.",
            signals=[
                AnomalySignalOut(name="block_trade_activity", score=0.80, z_score=2.5,
                                 description="Block deal volume 2.5x above quarterly average"),
                AnomalySignalOut(name="closing_auction_anomaly", score=0.68, z_score=2.0,
                                 description="Closing auction volume disproportionately high"),
            ],
        ),
    ]


def _build_baseline(cfg: dict) -> StockBaselineOut:
    vol = cfg["vol"]
    daily_vol = round(vol / 15.87, 2)
    return StockBaselineOut(
        normal_daily_vol_ann=float(vol),
        normal_volume_median=float(cfg["avg_vol"]),
        normal_daily_range_pct=round(daily_vol * 1.4, 2),
        normal_daily_range_p95=round(daily_vol * 2.8, 2),
        volume_clustering_score=0.65,
        return_persistence=round(0.02 + cfg["momentum"] * 0.1, 3),
        gap_frequency=round(0.15 + vol / 500, 3),
        regime_label="ELEVATED_VOL" if vol > 30 else "NORMAL",
        volatility_percentile=round(50 + (vol - 25) * 3, 1),
    )


def _build_news(symbol: str) -> list[NewsItemOut]:
    raw = _NEWS_DATA.get(symbol, [])
    items = []
    base_dates = [
        "2025-03-12T08:30:00Z", "2025-03-10T09:15:00Z", "2025-03-07T10:00:00Z",
        "2025-03-04T07:45:00Z", "2025-02-28T11:20:00Z", "2025-02-24T08:00:00Z",
        "2025-02-18T09:30:00Z", "2025-02-12T10:45:00Z",
    ]
    ticker = symbol.replace(".NS", "")
    for idx, (title, publisher, event_type, impact) in enumerate(raw):
        items.append(NewsItemOut(
            news_id=f"demo_{ticker.lower()}_{idx + 1:03d}",
            title=title,
            summary=f"Analysis: {title}",
            publisher=publisher,
            link=f"https://example.com/news/{ticker.lower()}/{idx + 1}",
            published_at=base_dates[idx] if idx < len(base_dates) else "2025-02-10T08:00:00Z",
            source="demo",
            event_type=event_type,
            impact_score=impact,
        ))
    return items


def _build_event_clusters(symbol: str, cfg: dict) -> list[EventClusterOut]:
    raw = _EVENT_CLUSTERS_DATA.get(symbol, [])
    clusters = []
    daily_vol = cfg["vol"] / 15.87
    for cid, title, etype, category, count, sources, first, last, impact, severity, summary in raw:
        # Build plausible impact reactions
        r5d = round(daily_vol * 1.5 * (1 if impact > 0.5 else 0.5), 1)
        r20d = round(r5d * 1.8, 1)
        event_impact = EventImpactOut(
            event_type=etype,
            event_date=first,
            reactions=[
                ReactionWindowOut(window="1d", days=1, stock_return_pct=round(r5d * 0.3, 1),
                                  market_return_pct=round(r5d * 0.1, 1),
                                  abnormal_return_pct=round(r5d * 0.2, 1), volume_ratio=1.8),
                ReactionWindowOut(window="5d", days=5, stock_return_pct=r5d,
                                  market_return_pct=round(r5d * 0.3, 1),
                                  abnormal_return_pct=round(r5d * 0.7, 1), volume_ratio=1.4),
                ReactionWindowOut(window="20d", days=20, stock_return_pct=r20d,
                                  market_return_pct=round(r20d * 0.25, 1),
                                  abnormal_return_pct=round(r20d * 0.75, 1), volume_ratio=1.1),
            ],
            historical_avg_reaction_5d=round(r5d * 0.8, 1),
            historical_avg_reaction_20d=round(r20d * 0.7, 1),
            similar_events=[
                HistoricalSimilarOut(
                    date="2023-08-15",
                    event_description=f"Similar {etype} event in 2023",
                    stock_return_5d_pct=round(r5d * 0.6, 1),
                    stock_return_20d_pct=round(r20d * 0.5, 1),
                    severity="moderate",
                ),
            ],
            historical_event_count=5,
        )
        clusters.append(EventClusterOut(
            cluster_id=cid,
            canonical_title=title,
            event_type=etype,
            category=category,
            article_count=count,
            sources=sources,
            first_seen=first,
            last_seen=last,
            impact_score=impact,
            severity=severity,
            affected_symbols=[symbol],
            summary=summary,
            event_impact=event_impact,
        ))
    return clusters


def _build_benchmarks(symbol: str, cfg: dict) -> list[BenchmarkComparison]:
    sector = _get_sector(symbol)
    stock_1y = cfg["returns"][5]
    nifty_1y = _NIFTY_RETURNS[5]
    sector_1y = _SECTOR_RETURNS.get(sector, _SECTOR_RETURNS["ENERGY"])[5]
    sector_idx = {
        "IT": ("Nifty IT", "^CNXIT"),
        "BANKING": ("Nifty Bank", "^NSEBANK"),
        "METALS": ("Nifty Metal", "^CNXMETAL"),
        "ENERGY": ("Nifty Energy", "^CNXENERGY"),
        "FMCG": ("Nifty FMCG", "^CNXFMCG"),
        "AUTO": ("Nifty Auto", "^CNXAUTO"),
        "PHARMA": ("Nifty Pharma", "^CNXPHARMA"),
        "TELECOM": ("Nifty IT", "^CNXIT"),
        "INFRASTRUCTURE": ("Nifty Infra", "^CNXINFRA"),
        "CONSUMER": ("Nifty Consumption", "^CNXCONSUM"),
    }
    sidx_name, sidx_sym = sector_idx.get(sector, ("Nifty 50", "^NSEI"))

    comps = [
        BenchmarkComparison(
            benchmark_name="Nifty 50",
            benchmark_symbol="^NSEI",
            stock_return_pct=stock_1y,
            benchmark_return_pct=nifty_1y,
            outperformance_pct=round(stock_1y - nifty_1y, 2),
            correlation=round(0.55 + cfg["beta"] * 0.15, 2),
            beta=cfg["beta"],
        ),
    ]
    if sidx_sym != "^NSEI":
        comps.append(BenchmarkComparison(
            benchmark_name=sidx_name,
            benchmark_symbol=sidx_sym,
            stock_return_pct=stock_1y,
            benchmark_return_pct=sector_1y,
            outperformance_pct=round(stock_1y - sector_1y, 2),
            correlation=round(0.65 + cfg["beta"] * 0.1, 2),
            beta=round(cfg["beta"] * 0.95, 2),
        ))
    return comps


def _build_profile(symbol: str) -> CompanyProfile:
    curated = CURATED_COMPANIES.get(symbol, {})
    name = curated.get("name", symbol.replace(".NS", ""))
    return CompanyProfile(
        name=name,
        sector=curated.get("sector"),
        industry=curated.get("industry"),
        exchange="NSE",
        market_cap=_MARKET_CAPS.get(symbol),
        aliases=curated.get("aliases", [name]),
        subsidiaries=curated.get("subsidiaries", []),
        segments=curated.get("segments", []),
        commodities=curated.get("commodities", []),
        macro_factors=curated.get("macro_factors", []),
        competitors=curated.get("competitors", []),
    )


def _build_freshness() -> DataFreshness:
    return DataFreshness(
        price_data="demo",
        price_updated_at=f"{_ANALYSIS_DATE}T15:30:00+05:30",
        news_data="demo",
        news_updated_at=f"{_ANALYSIS_DATE}T14:00:00+05:30",
        benchmark_data="demo",
        intelligence_generated_at=f"{_ANALYSIS_DATE}T16:00:00+05:30",
        cache_hit=False,
    )


# ---------------------------------------------------------------------------
# Auxiliary data
# ---------------------------------------------------------------------------

_MARKET_CAPS: dict[str, float] = {
    "RELIANCE.NS": 18_000_000_000_000,
    "TCS.NS": 15_000_000_000_000,
    "INFY.NS": 7_500_000_000_000,
    "HDFCBANK.NS": 13_000_000_000_000,
    "ICICIBANK.NS": 8_800_000_000_000,
    "SBIN.NS": 7_200_000_000_000,
    "BHARTIARTL.NS": 10_000_000_000_000,
    "ITC.NS": 5_800_000_000_000,
    "LT.NS": 4_800_000_000_000,
    "TATASTEEL.NS": 1_700_000_000_000,
    "JSWSTEEL.NS": 2_200_000_000_000,
    "ONGC.NS": 3_500_000_000_000,
    "NTPC.NS": 3_800_000_000_000,
    "ADANIENT.NS": 3_200_000_000_000,
    "HINDUNILVR.NS": 5_600_000_000_000,
    "MARUTI.NS": 3_600_000_000_000,
    "SUNPHARMA.NS": 4_300_000_000_000,
    "TITAN.NS": 3_100_000_000_000,
}

_SECTOR_MAP: dict[str, str] = {
    "RELIANCE.NS": "ENERGY", "TCS.NS": "IT", "INFY.NS": "IT",
    "HDFCBANK.NS": "BANKING", "ICICIBANK.NS": "BANKING", "SBIN.NS": "BANKING",
    "BHARTIARTL.NS": "TELECOM", "ITC.NS": "FMCG", "LT.NS": "INFRASTRUCTURE",
    "TATASTEEL.NS": "METALS", "JSWSTEEL.NS": "METALS", "ONGC.NS": "ENERGY",
    "NTPC.NS": "ENERGY", "ADANIENT.NS": "METALS", "HINDUNILVR.NS": "FMCG",
    "MARUTI.NS": "AUTO", "SUNPHARMA.NS": "PHARMA", "TITAN.NS": "CONSUMER",
}


def _get_sector(sym_or_cfg) -> str:
    if isinstance(sym_or_cfg, str):
        return _SECTOR_MAP.get(sym_or_cfg, "ENERGY")
    return "ENERGY"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_demo_intelligence(symbol: str) -> StockIntelligence:
    """Return a fully populated StockIntelligence for the given symbol.

    Deterministic — returns identical data on every call. Covers all 18 target
    NSE stocks; returns a minimal fallback for unknown symbols.
    """
    symbol = symbol.upper()
    cfg = _STOCK_CONFIGS.get(symbol)

    if cfg is None:
        # Minimal fallback for unknown symbols
        return StockIntelligence(
            symbol=symbol,
            company_name=symbol.replace(".NS", ""),
            data_source="demo",
            confidence_note="Demo mode — limited data for this symbol",
            freshness=_build_freshness(),
            generated_at=f"{_ANALYSIS_DATE}T16:00:00+05:30",
        )

    sector = _SECTOR_MAP.get(symbol, "ENERGY")
    curated = CURATED_COMPANIES.get(symbol, {})
    name = curated.get("name", symbol.replace(".NS", ""))
    industry = curated.get("industry")

    return StockIntelligence(
        symbol=symbol,
        company_name=name,
        sector=sector,
        industry=industry,
        data_start=_DATA_START,
        data_end="2025-03-14",
        total_trading_days=1290,
        current_price=float(cfg["price"]),
        change_pct=cfg["change_pct"],

        company_profile=_build_profile(symbol),
        freshness=_build_freshness(),

        horizons=_build_horizons(symbol, cfg),
        anomalous_moves=_build_anomalous_moves(symbol, cfg),
        patterns=_sector_patterns(sector, cfg["vol"]),
        regime_changes=_build_regime_changes(cfg),
        rare_events=_build_rare_events(symbol),
        expected_vs_actual=_build_expected_vs_actual(cfg),

        ml_anomalies=_build_ml_anomalies(cfg),
        stock_baseline=_build_baseline(cfg),
        news=_build_news(symbol),
        event_clusters=_build_event_clusters(symbol, cfg),
        benchmark_comparison=_build_benchmarks(symbol, cfg),

        generated_at=f"{_ANALYSIS_DATE}T16:00:00+05:30",
        data_source="demo",
        confidence_note="Demo mode — pre-built intelligence with realistic historical parameters. No live API data.",
    )
