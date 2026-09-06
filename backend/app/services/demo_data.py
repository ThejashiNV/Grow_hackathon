"""Deterministic demo scenarios for hackathon demos.

Each scenario produces a pre-built ChangeBundle with realistic data,
bypassing yfinance/news APIs entirely. The bundles flow through the
same attention/diff/mark-seen/Ask-Why architecture as live data.

Covers all 18 target NSE stocks so the entire app feels populated.
"""

from datetime import UTC, datetime

from app.schemas.events import ClassifiedEvent, EventType
from app.schemas.scoring import ChangeBundle, ExplainChip, ScoreComponents

DEMO_SYMBOLS = [
    "INFY.NS", "TATASTEEL.NS", "RELIANCE.NS", "HDFCBANK.NS",
    "TCS.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS",
    "ITC.NS", "LT.NS", "JSWSTEEL.NS", "ONGC.NS",
    "NTPC.NS", "ADANIENT.NS", "HINDUNILVR.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS",
]

DEMO_SCENARIOS: dict[str, dict] = {
    "ceo_resignation": {
        "title": "CEO Resignation",
        "description": "Major leadership change triggers sharp selloff — high surprise, high impact.",
        "symbol": "INFY.NS",
    },
    "sector_outperformer": {
        "title": "Sector Outperformer",
        "description": "Stock rallies while its sector drops — the move is company-specific, not macro.",
        "symbol": "TATASTEEL.NS",
    },
    "volume_anomaly": {
        "title": "Price + Volume Anomaly",
        "description": "Unusual buying with no headline — the numbers moved before the news.",
        "symbol": "RELIANCE.NS",
    },
    "muted_reaction": {
        "title": "Muted Reaction",
        "description": "Major regulatory headline but the price barely moved — silence is the signal.",
        "symbol": "HDFCBANK.NS",
    },
    "earnings_beat": {
        "title": "Earnings Beat",
        "description": "Strong quarterly results drive post-earnings momentum across the sector.",
        "symbol": "TCS.NS",
    },
    "rate_sensitivity": {
        "title": "Rate Sensitivity",
        "description": "RBI rate decision creates asymmetric moves across banking stocks.",
        "symbol": "SBIN.NS",
    },
    "5g_expansion": {
        "title": "5G Expansion",
        "description": "Spectrum allocation and subscriber growth accelerate telecom momentum.",
        "symbol": "BHARTIARTL.NS",
    },
    "commodity_cycle": {
        "title": "Commodity Cycle",
        "description": "Global commodity price surge lifts metals and energy stocks.",
        "symbol": "ONGC.NS",
    },
}


def get_demo_scenarios() -> list[dict]:
    return [
        {"id": sid, "title": s["title"], "description": s["description"], "symbol": s["symbol"]}
        for sid, s in DEMO_SCENARIOS.items()
    ]


def _now() -> datetime:
    return datetime.now(UTC)


def _build_infy() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="INFY.NS",
        company_name="Infosys Ltd",
        price=1492.30,
        previous_close=1580.00,
        change_pct=-5.55,
        normal_daily_move_pct=1.2,
        volume=45_000_000,
        average_volume_20d=15_000_000,
        components=ScoreComponents(
            price_anomaly=92, price_z_score=-4.6,
            volume_anomaly=85, volume_ratio=3.0,
            sector_relative_move=78, sector="it", sector_change_pct=0.3,
            headline_novelty=95, event_impact=90,
        ),
        surprise_score=88, impact_score=88, confidence_score=95, attention_score=82,
        events=[
            ClassifiedEvent(
                event_id="demo-infy-ceo-001", symbol="INFY.NS",
                event_type=EventType.EXECUTIVE_RESIGNATION,
                title="Infosys CEO Salil Parekh Steps Down Citing Personal Reasons",
                summary="Board initiates search for successor; CFO appointed interim CEO.",
                impact_score=90, novelty_score=95,
                source="Demo / Economic Times", timestamp=now,
            ),
            ClassifiedEvent(
                event_id="demo-infy-analyst-002", symbol="INFY.NS",
                event_type=EventType.ANALYST_ACTION,
                title="Multiple Brokerages Cut Infosys Target Price After CEO Exit",
                impact_score=65, novelty_score=80,
                source="Demo / Moneycontrol", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly -4.6σ", kind="price"),
            ExplainChip(label="Volume 3.0× normal", kind="volume"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved -5.55% today, vs a normal daily move of about ±1.2%, while the IT sector moved +0.3% (diverged from sector).",
        why_now='This became meaningful because the move is 4.6× this stock\'s typical daily volatility, volume is 3.0× the 20-day average, and a new headline was detected: "Infosys CEO Salil Parekh Steps Down Citing Personal Reasons".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 2 fresh"],
        demo_label="CEO Resignation",
    )


def _build_tatasteel() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="TATASTEEL.NS",
        company_name="Tata Steel Ltd",
        price=161.40, previous_close=152.50, change_pct=5.84,
        normal_daily_move_pct=2.8, volume=32_000_000, average_volume_20d=25_000_000,
        components=ScoreComponents(
            price_anomaly=55, price_z_score=2.1,
            volume_anomaly=25, volume_ratio=1.28,
            sector_relative_move=88, sector="metals", sector_change_pct=-1.2,
            headline_novelty=75, event_impact=60,
        ),
        surprise_score=62, impact_score=65, confidence_score=90, attention_score=58,
        events=[
            ClassifiedEvent(
                event_id="demo-tatasteel-contract-001", symbol="TATASTEEL.NS",
                event_type=EventType.MAJOR_CONTRACT,
                title="Tata Steel Reports Record Export Orders From European Markets",
                impact_score=60, novelty_score=75,
                source="Demo / Business Standard", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +2.1σ", kind="price"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +5.84% today, vs a normal daily move of about ±2.8%, while the Metals sector moved -1.2% (diverged from sector).",
        why_now='This became meaningful because the move is 2.1× this stock\'s typical daily volatility, and a new headline was detected: "Tata Steel Reports Record Export Orders From European Markets".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Sector Outperformer",
    )


def _build_reliance() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="RELIANCE.NS",
        company_name="Reliance Industries Ltd",
        price=2985.50, previous_close=2890.00, change_pct=3.30,
        normal_daily_move_pct=1.0, volume=28_000_000, average_volume_20d=8_000_000,
        components=ScoreComponents(
            price_anomaly=82, price_z_score=3.3,
            volume_anomaly=90, volume_ratio=3.5,
            sector_relative_move=45, sector="energy", sector_change_pct=0.8,
            headline_novelty=0, event_impact=0,
        ),
        surprise_score=78, impact_score=0, confidence_score=72, attention_score=55,
        events=[],
        explain_chips=[
            ExplainChip(label="Price anomaly +3.3σ", kind="price"),
            ExplainChip(label="Volume 3.5× normal", kind="volume"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
        ],
        why_this="Moved +3.30% today, vs a normal daily move of about ±1.0%, while the Energy sector moved +0.8% (diverged from sector).",
        why_now="This became meaningful because the move is 3.3× this stock's typical daily volatility, and volume is 3.5× the 20-day average.",
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "No headlines found"],
        demo_label="Price + Volume Anomaly",
    )


def _build_hdfcbank() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="HDFCBANK.NS",
        company_name="HDFC Bank Ltd",
        price=1715.20, previous_close=1720.00, change_pct=-0.28,
        normal_daily_move_pct=1.1, volume=12_000_000, average_volume_20d=10_000_000,
        components=ScoreComponents(
            price_anomaly=8, price_z_score=-0.25,
            volume_anomaly=15, volume_ratio=1.2,
            sector_relative_move=10, sector="banking", sector_change_pct=-0.5,
            headline_novelty=90, event_impact=75,
        ),
        surprise_score=10, impact_score=80, confidence_score=90, attention_score=42,
        events=[
            ClassifiedEvent(
                event_id="demo-hdfc-rbi-001", symbol="HDFCBANK.NS",
                event_type=EventType.REGULATORY_ACTION,
                title="RBI Imposes ₹2 Crore Penalty on HDFC Bank for KYC Violations",
                summary="Penalty relates to deficiencies in KYC norms; bank says corrective action taken.",
                impact_score=75, novelty_score=90,
                source="Demo / LiveMint", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="New major event", kind="event"),
            ExplainChip(label="Unusually muted reaction", kind="silence"),
        ],
        why_this="Moved -0.28% today, vs a normal daily move of about ±1.1%, while the Banking sector moved -0.5% (moved with sector).",
        why_now='This became meaningful because a new headline was detected: "RBI Imposes ₹2 Crore Penalty on HDFC Bank for KYC Violations", but the price reaction has been unusually muted given the event\'s typical importance.',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Muted Reaction",
    )


def _build_tcs() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="TCS.NS",
        company_name="Tata Consultancy Services Ltd",
        price=4280.00, previous_close=4120.00, change_pct=3.88,
        normal_daily_move_pct=1.3, volume=18_000_000, average_volume_20d=7_500_000,
        components=ScoreComponents(
            price_anomaly=78, price_z_score=2.98,
            volume_anomaly=72, volume_ratio=2.4,
            sector_relative_move=55, sector="it", sector_change_pct=1.2,
            headline_novelty=85, event_impact=80,
        ),
        surprise_score=72, impact_score=78, confidence_score=92, attention_score=70,
        events=[
            ClassifiedEvent(
                event_id="demo-tcs-earnings-001", symbol="TCS.NS",
                event_type=EventType.EARNINGS_SURPRISE,
                title="TCS Q4 Net Profit Beats Estimates, Revenue Up 12% YoY",
                summary="Strong deal wins in North America; management guides for double-digit growth.",
                impact_score=80, novelty_score=85,
                source="Demo / CNBC-TV18", timestamp=now,
            ),
            ClassifiedEvent(
                event_id="demo-tcs-buyback-002", symbol="TCS.NS",
                event_type=EventType.BUYBACK,
                title="TCS Board Approves ₹18,000 Crore Buyback at ₹4,500/Share",
                impact_score=70, novelty_score=75,
                source="Demo / Economic Times", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +3.0σ", kind="price"),
            ExplainChip(label="Volume 2.4× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +3.88% today, vs a normal daily move of about ±1.3%, while the IT sector moved +1.2% (outperformed sector).",
        why_now='This became meaningful because the move is 3.0× this stock\'s typical daily volatility, volume is 2.4× the 20-day average, and a new headline was detected: "TCS Q4 Net Profit Beats Estimates, Revenue Up 12% YoY".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 2 fresh"],
        demo_label="Earnings Beat",
    )


def _build_icicibank() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="ICICIBANK.NS",
        company_name="ICICI Bank Ltd",
        price=1185.60, previous_close=1155.00, change_pct=2.65,
        normal_daily_move_pct=1.4, volume=22_000_000, average_volume_20d=14_000_000,
        components=ScoreComponents(
            price_anomaly=52, price_z_score=1.89,
            volume_anomaly=40, volume_ratio=1.57,
            sector_relative_move=65, sector="banking", sector_change_pct=-0.5,
            headline_novelty=70, event_impact=65,
        ),
        surprise_score=55, impact_score=60, confidence_score=88, attention_score=52,
        events=[
            ClassifiedEvent(
                event_id="demo-icici-npa-001", symbol="ICICIBANK.NS",
                event_type=EventType.EARNINGS,
                title="ICICI Bank Reports Record Low NPA Ratio at 1.97% in Q4",
                impact_score=65, novelty_score=70,
                source="Demo / Business Standard", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +1.9σ", kind="price"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +2.65% today, vs a normal daily move of about ±1.4%, while the Banking sector moved -0.5% (diverged from sector).",
        why_now='This became meaningful because the move is 1.9× this stock\'s typical daily volatility, and a new headline was detected: "ICICI Bank Reports Record Low NPA Ratio at 1.97% in Q4".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Banking Outperformer",
    )


def _build_sbin() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="SBIN.NS",
        company_name="State Bank of India",
        price=832.50, previous_close=815.00, change_pct=2.15,
        normal_daily_move_pct=1.8, volume=35_000_000, average_volume_20d=20_000_000,
        components=ScoreComponents(
            price_anomaly=35, price_z_score=1.19,
            volume_anomaly=48, volume_ratio=1.75,
            sector_relative_move=60, sector="banking", sector_change_pct=-0.5,
            headline_novelty=80, event_impact=72,
        ),
        surprise_score=45, impact_score=70, confidence_score=90, attention_score=50,
        events=[
            ClassifiedEvent(
                event_id="demo-sbin-rbi-001", symbol="SBIN.NS",
                event_type=EventType.MACRO_RATE_CHANGE,
                title="RBI Keeps Repo Rate Unchanged at 6.5%, Shifts to Neutral Stance",
                summary="Market interprets neutral stance as prelude to rate cuts. PSU banks rally.",
                impact_score=72, novelty_score=80,
                source="Demo / Reuters India", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Volume 1.75× normal", kind="volume"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +2.15% today, vs a normal daily move of about ±1.8%, while the Banking sector moved -0.5% (diverged from sector).",
        why_now='This became meaningful because volume is 1.75× the 20-day average, and a new headline was detected: "RBI Keeps Repo Rate Unchanged at 6.5%, Shifts to Neutral Stance".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Rate Sensitivity",
    )


def _build_bhartiartl() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="BHARTIARTL.NS",
        company_name="Bharti Airtel Ltd",
        price=1620.00, previous_close=1565.00, change_pct=3.51,
        normal_daily_move_pct=1.5, volume=15_000_000, average_volume_20d=8_000_000,
        components=ScoreComponents(
            price_anomaly=68, price_z_score=2.34,
            volume_anomaly=58, volume_ratio=1.88,
            sector_relative_move=72, sector="telecom", sector_change_pct=0.4,
            headline_novelty=82, event_impact=75,
        ),
        surprise_score=65, impact_score=72, confidence_score=88, attention_score=62,
        events=[
            ClassifiedEvent(
                event_id="demo-airtel-5g-001", symbol="BHARTIARTL.NS",
                event_type=EventType.PRODUCT_LAUNCH,
                title="Airtel 5G Reaches 500 Cities, Adds 45M Subscribers in Q4",
                summary="5G subscriber base crosses 100M; ARPU rises 8% QoQ to ₹233.",
                impact_score=75, novelty_score=82,
                source="Demo / LiveMint", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +2.3σ", kind="price"),
            ExplainChip(label="Volume 1.9× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +3.51% today, vs a normal daily move of about ±1.5%, while the Telecom sector moved +0.4% (outperformed sector).",
        why_now='This became meaningful because the move is 2.3× this stock\'s typical daily volatility, and a new headline was detected: "Airtel 5G Reaches 500 Cities, Adds 45M Subscribers in Q4".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="5G Expansion",
    )


def _build_itc() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="ITC.NS",
        company_name="ITC Ltd",
        price=465.80, previous_close=458.00, change_pct=1.70,
        normal_daily_move_pct=1.0, volume=25_000_000, average_volume_20d=18_000_000,
        components=ScoreComponents(
            price_anomaly=42, price_z_score=1.70,
            volume_anomaly=30, volume_ratio=1.39,
            sector_relative_move=48, sector="fmcg", sector_change_pct=0.3,
            headline_novelty=65, event_impact=55,
        ),
        surprise_score=40, impact_score=50, confidence_score=85, attention_score=38,
        events=[
            ClassifiedEvent(
                event_id="demo-itc-demerger-001", symbol="ITC.NS",
                event_type=EventType.MERGER_ACQUISITION,
                title="ITC Hotels Demerger Gets NCLT Approval, Listing Expected in Q2",
                impact_score=55, novelty_score=65,
                source="Demo / Moneycontrol", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +1.7σ", kind="price"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +1.70% today, vs a normal daily move of about ±1.0%, while the FMCG sector moved +0.3% (outperformed sector).",
        why_now='This became meaningful because the move is 1.7× this stock\'s typical daily volatility, and a new headline was detected: "ITC Hotels Demerger Gets NCLT Approval, Listing Expected in Q2".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Demerger Play",
    )


def _build_lt() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="LT.NS",
        company_name="Larsen & Toubro Ltd",
        price=3580.00, previous_close=3490.00, change_pct=2.58,
        normal_daily_move_pct=1.6, volume=8_500_000, average_volume_20d=5_000_000,
        components=ScoreComponents(
            price_anomaly=48, price_z_score=1.61,
            volume_anomaly=45, volume_ratio=1.70,
            sector_relative_move=55, sector="infrastructure", sector_change_pct=0.5,
            headline_novelty=78, event_impact=70,
        ),
        surprise_score=50, impact_score=65, confidence_score=88, attention_score=48,
        events=[
            ClassifiedEvent(
                event_id="demo-lt-order-001", symbol="LT.NS",
                event_type=EventType.MAJOR_CONTRACT,
                title="L&T Wins ₹25,000 Crore Saudi Arabia Mega Infrastructure Order",
                summary="Largest single international order in company history; pipeline now at ₹4.8L Cr.",
                impact_score=70, novelty_score=78,
                source="Demo / Economic Times", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +1.6σ", kind="price"),
            ExplainChip(label="Volume 1.7× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +2.58% today, vs a normal daily move of about ±1.6%, while the Infrastructure sector moved +0.5% (outperformed sector).",
        why_now='This became meaningful because the move is 1.6× this stock\'s typical daily volatility, and a new headline was detected: "L&T Wins ₹25,000 Crore Saudi Arabia Mega Infrastructure Order".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Mega Order Win",
    )


def _build_jswsteel() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="JSWSTEEL.NS",
        company_name="JSW Steel Ltd",
        price=920.00, previous_close=895.00, change_pct=2.79,
        normal_daily_move_pct=2.5, volume=12_000_000, average_volume_20d=8_500_000,
        components=ScoreComponents(
            price_anomaly=32, price_z_score=1.12,
            volume_anomaly=35, volume_ratio=1.41,
            sector_relative_move=42, sector="metals", sector_change_pct=-1.2,
            headline_novelty=55, event_impact=45,
        ),
        surprise_score=35, impact_score=42, confidence_score=85, attention_score=32,
        events=[
            ClassifiedEvent(
                event_id="demo-jsw-capacity-001", symbol="JSWSTEEL.NS",
                event_type=EventType.PRODUCT_LAUNCH,
                title="JSW Steel Commissioning New 5 MTPA Capacity at Vijayanagar Plant",
                impact_score=45, novelty_score=55,
                source="Demo / Business Standard", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +2.79% today, vs a normal daily move of about ±2.5%, while the Metals sector moved -1.2% (diverged from sector).",
        why_now='This became meaningful because a new headline was detected: "JSW Steel Commissioning New 5 MTPA Capacity at Vijayanagar Plant".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Capacity Expansion",
    )


def _build_ongc() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="ONGC.NS",
        company_name="Oil & Natural Gas Corporation Ltd",
        price=278.50, previous_close=265.00, change_pct=5.09,
        normal_daily_move_pct=1.8, volume=42_000_000, average_volume_20d=18_000_000,
        components=ScoreComponents(
            price_anomaly=75, price_z_score=2.83,
            volume_anomaly=70, volume_ratio=2.33,
            sector_relative_move=62, sector="energy", sector_change_pct=1.5,
            headline_novelty=72, event_impact=68,
        ),
        surprise_score=68, impact_score=62, confidence_score=90, attention_score=60,
        events=[
            ClassifiedEvent(
                event_id="demo-ongc-oil-001", symbol="ONGC.NS",
                event_type=EventType.COMMODITY_PRICE,
                title="Brent Crude Surges Past $95 on OPEC+ Supply Cuts, ONGC a Key Beneficiary",
                impact_score=68, novelty_score=72,
                source="Demo / Reuters India", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +2.8σ", kind="price"),
            ExplainChip(label="Volume 2.3× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +5.09% today, vs a normal daily move of about ±1.8%, while the Energy sector moved +1.5% (outperformed sector).",
        why_now='This became meaningful because the move is 2.8× this stock\'s typical daily volatility, volume is 2.3× the 20-day average, and a new headline was detected: "Brent Crude Surges Past $95 on OPEC+ Supply Cuts".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Commodity Cycle",
    )


def _build_ntpc() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="NTPC.NS",
        company_name="NTPC Ltd",
        price=375.20, previous_close=368.00, change_pct=1.96,
        normal_daily_move_pct=1.4, volume=22_000_000, average_volume_20d=15_000_000,
        components=ScoreComponents(
            price_anomaly=38, price_z_score=1.40,
            volume_anomaly=35, volume_ratio=1.47,
            sector_relative_move=30, sector="energy", sector_change_pct=1.5,
            headline_novelty=60, event_impact=52,
        ),
        surprise_score=35, impact_score=48, confidence_score=85, attention_score=34,
        events=[
            ClassifiedEvent(
                event_id="demo-ntpc-green-001", symbol="NTPC.NS",
                event_type=EventType.PRODUCT_LAUNCH,
                title="NTPC Green Energy IPO Lists at 15% Premium, Parent Benefits from Re-Rating",
                impact_score=52, novelty_score=60,
                source="Demo / Moneycontrol", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +1.96% today, vs a normal daily move of about ±1.4%, while the Energy sector moved +1.5% (moved with sector).",
        why_now='This became meaningful because a new headline was detected: "NTPC Green Energy IPO Lists at 15% Premium".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Green Energy Listing",
    )


def _build_adanient() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="ADANIENT.NS",
        company_name="Adani Enterprises Ltd",
        price=2780.00, previous_close=2850.00, change_pct=-2.46,
        normal_daily_move_pct=2.8, volume=20_000_000, average_volume_20d=12_000_000,
        components=ScoreComponents(
            price_anomaly=28, price_z_score=-0.88,
            volume_anomaly=42, volume_ratio=1.67,
            sector_relative_move=35, sector="metals", sector_change_pct=-1.2,
            headline_novelty=75, event_impact=68,
        ),
        surprise_score=30, impact_score=65, confidence_score=82, attention_score=40,
        events=[
            ClassifiedEvent(
                event_id="demo-adani-probe-001", symbol="ADANIENT.NS",
                event_type=EventType.LEGAL_ISSUE,
                title="US DOJ Investigation Into Adani Group Bribery Allegations — Stock Under Pressure",
                impact_score=68, novelty_score=75,
                source="Demo / Financial Times", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Volume 1.7× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved -2.46% today, vs a normal daily move of about ±2.8%, while the Metals sector moved -1.2% (moved with sector).",
        why_now='This became meaningful because volume is 1.7× the 20-day average, and a new headline was detected: "US DOJ Investigation Into Adani Group Bribery Allegations".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Legal Overhang",
    )


def _build_hindunilvr() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="HINDUNILVR.NS",
        company_name="Hindustan Unilever Ltd",
        price=2540.00, previous_close=2560.00, change_pct=-0.78,
        normal_daily_move_pct=0.9, volume=5_500_000, average_volume_20d=4_800_000,
        components=ScoreComponents(
            price_anomaly=22, price_z_score=-0.87,
            volume_anomaly=12, volume_ratio=1.15,
            sector_relative_move=20, sector="fmcg", sector_change_pct=0.3,
            headline_novelty=50, event_impact=40,
        ),
        surprise_score=18, impact_score=35, confidence_score=85, attention_score=22,
        events=[
            ClassifiedEvent(
                event_id="demo-hul-rural-001", symbol="HINDUNILVR.NS",
                event_type=EventType.SECTOR_TREND,
                title="FMCG Sector Faces Volume Headwinds as Rural Recovery Slows",
                impact_score=40, novelty_score=50,
                source="Demo / CNBC-TV18", timestamp=now,
            ),
        ],
        explain_chips=[],
        why_this="Moved -0.78% today, vs a normal daily move of about ±0.9%, while the FMCG sector moved +0.3% (underperformed sector).",
        why_now="No unusual signal detected right now.",
        is_meaningful=False, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Quiet Day",
    )


def _build_maruti() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="MARUTI.NS",
        company_name="Maruti Suzuki India Ltd",
        price=12850.00, previous_close=12500.00, change_pct=2.80,
        normal_daily_move_pct=1.6, volume=4_200_000, average_volume_20d=2_800_000,
        components=ScoreComponents(
            price_anomaly=50, price_z_score=1.75,
            volume_anomaly=38, volume_ratio=1.50,
            sector_relative_move=58, sector="auto", sector_change_pct=0.5,
            headline_novelty=72, event_impact=65,
        ),
        surprise_score=48, impact_score=60, confidence_score=88, attention_score=46,
        events=[
            ClassifiedEvent(
                event_id="demo-maruti-sales-001", symbol="MARUTI.NS",
                event_type=EventType.EARNINGS,
                title="Maruti Suzuki Reports Record Monthly Sales of 2.1 Lakh Units in March",
                summary="SUV segment drives growth; market share reaches 42.3%.",
                impact_score=65, novelty_score=72,
                source="Demo / Economic Times", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +1.8σ", kind="price"),
            ExplainChip(label="Volume 1.5× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +2.80% today, vs a normal daily move of about ±1.6%, while the Auto sector moved +0.5% (outperformed sector).",
        why_now='This became meaningful because the move is 1.8× this stock\'s typical daily volatility, and a new headline was detected: "Maruti Suzuki Reports Record Monthly Sales of 2.1 Lakh Units in March".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Record Sales",
    )


def _build_sunpharma() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="SUNPHARMA.NS",
        company_name="Sun Pharmaceutical Industries Ltd",
        price=1780.00, previous_close=1720.00, change_pct=3.49,
        normal_daily_move_pct=1.5, volume=10_000_000, average_volume_20d=6_000_000,
        components=ScoreComponents(
            price_anomaly=65, price_z_score=2.33,
            volume_anomaly=42, volume_ratio=1.67,
            sector_relative_move=70, sector="pharma", sector_change_pct=0.2,
            headline_novelty=80, event_impact=75,
        ),
        surprise_score=60, impact_score=72, confidence_score=90, attention_score=58,
        events=[
            ClassifiedEvent(
                event_id="demo-sunpharma-fda-001", symbol="SUNPHARMA.NS",
                event_type=EventType.REGULATORY_ACTION,
                title="Sun Pharma's Specialty Drug Ilumya Gets US FDA Approval for New Indication",
                summary="Expanded label expected to add $400M to annual US revenue.",
                impact_score=75, novelty_score=80,
                source="Demo / Reuters India", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +2.3σ", kind="price"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +3.49% today, vs a normal daily move of about ±1.5%, while the Pharma sector moved +0.2% (outperformed sector).",
        why_now='This became meaningful because the move is 2.3× this stock\'s typical daily volatility, and a new headline was detected: "Sun Pharma\'s Specialty Drug Ilumya Gets US FDA Approval for New Indication".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="FDA Approval",
    )


def _build_titan() -> ChangeBundle:
    now = _now()
    return ChangeBundle(
        symbol="TITAN.NS",
        company_name="Titan Company Ltd",
        price=3650.00, previous_close=3580.00, change_pct=1.96,
        normal_daily_move_pct=1.4, volume=5_500_000, average_volume_20d=3_500_000,
        components=ScoreComponents(
            price_anomaly=38, price_z_score=1.40,
            volume_anomaly=40, volume_ratio=1.57,
            sector_relative_move=45, sector="consumer", sector_change_pct=0.5,
            headline_novelty=68, event_impact=58,
        ),
        surprise_score=38, impact_score=55, confidence_score=85, attention_score=40,
        events=[
            ClassifiedEvent(
                event_id="demo-titan-tanishq-001", symbol="TITAN.NS",
                event_type=EventType.EARNINGS,
                title="Titan's Tanishq Brand Crosses ₹40,000 Crore Revenue, Jewellery Segment Up 22%",
                impact_score=58, novelty_score=68,
                source="Demo / Business Standard", timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Volume 1.6× normal", kind="volume"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +1.96% today, vs a normal daily move of about ±1.4%, while the Consumer sector moved +0.5% (outperformed sector).",
        why_now='This became meaningful because volume is 1.6× the 20-day average, and a new headline was detected: "Titan\'s Tanishq Brand Crosses ₹40,000 Crore Revenue".',
        is_meaningful=True, as_of=now, is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Revenue Milestone",
    )


_BUILDERS: dict[str, callable] = {
    "INFY.NS": _build_infy,
    "TATASTEEL.NS": _build_tatasteel,
    "RELIANCE.NS": _build_reliance,
    "HDFCBANK.NS": _build_hdfcbank,
    "TCS.NS": _build_tcs,
    "ICICIBANK.NS": _build_icicibank,
    "SBIN.NS": _build_sbin,
    "BHARTIARTL.NS": _build_bhartiartl,
    "ITC.NS": _build_itc,
    "LT.NS": _build_lt,
    "JSWSTEEL.NS": _build_jswsteel,
    "ONGC.NS": _build_ongc,
    "NTPC.NS": _build_ntpc,
    "ADANIENT.NS": _build_adanient,
    "HINDUNILVR.NS": _build_hindunilvr,
    "MARUTI.NS": _build_maruti,
    "SUNPHARMA.NS": _build_sunpharma,
    "TITAN.NS": _build_titan,
}


def get_demo_bundle(symbol: str) -> ChangeBundle | None:
    builder = _BUILDERS.get(symbol)
    return builder() if builder else None
