"""Deterministic demo scenarios for hackathon demos (Phase 2).

Each scenario produces a pre-built ChangeBundle with realistic data,
bypassing yfinance/news APIs entirely. The bundles flow through the
same attention/diff/mark-seen/Ask-Why architecture as live data.
"""

from datetime import UTC, datetime

from app.schemas.events import ClassifiedEvent, EventType
from app.schemas.scoring import ChangeBundle, ExplainChip, ScoreComponents

DEMO_SYMBOLS = ["INFY.NS", "TATASTEEL.NS", "RELIANCE.NS", "HDFCBANK.NS"]

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
}


def get_demo_scenarios() -> list[dict]:
    return [
        {"id": sid, "title": s["title"], "description": s["description"], "symbol": s["symbol"]}
        for sid, s in DEMO_SCENARIOS.items()
    ]


def _now() -> datetime:
    return datetime.now(UTC)


def _build_scenario_1() -> ChangeBundle:
    """CEO resignation — INFY.NS: sharp drop, huge volume, high-impact headline."""
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
            price_anomaly=92,
            price_z_score=-4.6,
            volume_anomaly=85,
            volume_ratio=3.0,
            sector_relative_move=78,
            sector="it",
            sector_change_pct=0.3,
            headline_novelty=95,
            event_impact=90,
        ),
        surprise_score=88,
        impact_score=88,
        confidence_score=95,
        attention_score=82,
        events=[
            ClassifiedEvent(
                event_id="demo-infy-ceo-001",
                symbol="INFY.NS",
                event_type=EventType.EXECUTIVE_RESIGNATION,
                title="Infosys CEO Salil Parekh Steps Down Citing Personal Reasons",
                summary="Board initiates search for successor; CFO appointed interim CEO.",
                impact_score=90,
                novelty_score=95,
                source="Demo / Economic Times",
                timestamp=now,
            ),
            ClassifiedEvent(
                event_id="demo-infy-analyst-002",
                symbol="INFY.NS",
                event_type=EventType.ANALYST_ACTION,
                title="Multiple Brokerages Cut Infosys Target Price After CEO Exit",
                impact_score=65,
                novelty_score=80,
                source="Demo / Moneycontrol",
                timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly -4.6σ", kind="price"),
            ExplainChip(label="Volume 3.0× normal", kind="volume"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved -5.55% today, vs a normal daily move of about ±1.2%, while the IT sector moved +0.3% (diverged from sector).",
        why_now="This became meaningful because the move is 4.6× this stock's typical daily volatility, volume is 3.0× the 20-day average, and a new headline was detected: \"Infosys CEO Salil Parekh Steps Down Citing Personal Reasons\".",
        is_meaningful=True,
        as_of=now,
        is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 2 fresh"],
        demo_label="CEO Resignation",
    )


def _build_scenario_2() -> ChangeBundle:
    """Sector outperformer — TATASTEEL.NS: rallying while metals sector drops."""
    now = _now()
    return ChangeBundle(
        symbol="TATASTEEL.NS",
        company_name="Tata Steel Ltd",
        price=161.40,
        previous_close=152.50,
        change_pct=5.84,
        normal_daily_move_pct=2.8,
        volume=32_000_000,
        average_volume_20d=25_000_000,
        components=ScoreComponents(
            price_anomaly=55,
            price_z_score=2.1,
            volume_anomaly=25,
            volume_ratio=1.28,
            sector_relative_move=88,
            sector="metals",
            sector_change_pct=-1.2,
            headline_novelty=75,
            event_impact=60,
        ),
        surprise_score=62,
        impact_score=65,
        confidence_score=90,
        attention_score=58,
        events=[
            ClassifiedEvent(
                event_id="demo-tatasteel-contract-001",
                symbol="TATASTEEL.NS",
                event_type=EventType.MAJOR_CONTRACT,
                title="Tata Steel Reports Record Export Orders From European Markets",
                impact_score=60,
                novelty_score=75,
                source="Demo / Business Standard",
                timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="Price anomaly +2.1σ", kind="price"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
            ExplainChip(label="New major event", kind="event"),
        ],
        why_this="Moved +5.84% today, vs a normal daily move of about ±2.8%, while the Metals sector moved -1.2% (diverged from sector).",
        why_now="This became meaningful because the move is 2.1× this stock's typical daily volatility, and a new headline was detected: \"Tata Steel Reports Record Export Orders From European Markets\".",
        is_meaningful=True,
        as_of=now,
        is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Sector Outperformer",
    )


def _build_scenario_3() -> ChangeBundle:
    """Price + volume anomaly — RELIANCE.NS: big move, huge volume, no news."""
    now = _now()
    return ChangeBundle(
        symbol="RELIANCE.NS",
        company_name="Reliance Industries Ltd",
        price=2985.50,
        previous_close=2890.00,
        change_pct=3.30,
        normal_daily_move_pct=1.0,
        volume=28_000_000,
        average_volume_20d=8_000_000,
        components=ScoreComponents(
            price_anomaly=82,
            price_z_score=3.3,
            volume_anomaly=90,
            volume_ratio=3.5,
            sector_relative_move=45,
            sector="energy",
            sector_change_pct=0.8,
            headline_novelty=0,
            event_impact=0,
        ),
        surprise_score=78,
        impact_score=0,
        confidence_score=72,
        attention_score=55,
        events=[],
        explain_chips=[
            ExplainChip(label="Price anomaly +3.3σ", kind="price"),
            ExplainChip(label="Volume 3.5× normal", kind="volume"),
            ExplainChip(label="Sector-relative movement", kind="sector"),
        ],
        why_this="Moved +3.30% today, vs a normal daily move of about ±1.0%, while the Energy sector moved +0.8% (diverged from sector).",
        why_now="This became meaningful because the move is 3.3× this stock's typical daily volatility, and volume is 3.5× the 20-day average.",
        is_meaningful=True,
        as_of=now,
        is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "No headlines found"],
        demo_label="Price + Volume Anomaly",
    )


def _build_scenario_4() -> ChangeBundle:
    """Muted reaction — HDFCBANK.NS: major regulatory headline, price barely moved."""
    now = _now()
    return ChangeBundle(
        symbol="HDFCBANK.NS",
        company_name="HDFC Bank Ltd",
        price=1715.20,
        previous_close=1720.00,
        change_pct=-0.28,
        normal_daily_move_pct=1.1,
        volume=12_000_000,
        average_volume_20d=10_000_000,
        components=ScoreComponents(
            price_anomaly=8,
            price_z_score=-0.25,
            volume_anomaly=15,
            volume_ratio=1.2,
            sector_relative_move=10,
            sector="banking",
            sector_change_pct=-0.5,
            headline_novelty=90,
            event_impact=75,
        ),
        surprise_score=10,
        impact_score=80,
        confidence_score=90,
        attention_score=42,
        events=[
            ClassifiedEvent(
                event_id="demo-hdfc-rbi-001",
                symbol="HDFCBANK.NS",
                event_type=EventType.REGULATORY_ACTION,
                title="RBI Imposes ₹2 Crore Penalty on HDFC Bank for KYC Violations",
                summary="Penalty relates to deficiencies in KYC norms; bank says corrective action taken.",
                impact_score=75,
                novelty_score=90,
                source="Demo / LiveMint",
                timestamp=now,
            ),
        ],
        explain_chips=[
            ExplainChip(label="New major event", kind="event"),
            ExplainChip(label="Unusually muted reaction", kind="silence"),
        ],
        why_this="Moved -0.28% today, vs a normal daily move of about ±1.1%, while the Banking sector moved -0.5% (moved with sector).",
        why_now='This became meaningful because a new headline was detected: "RBI Imposes ₹2 Crore Penalty on HDFC Bank for KYC Violations", but the price reaction has been unusually muted given the event\'s typical importance.',
        is_meaningful=True,
        as_of=now,
        is_delayed=False,
        confidence_factors=["Price: present", "Volume: present", "Sector: present", "Headlines: 1 fresh"],
        demo_label="Muted Reaction",
    )


_BUILDERS: dict[str, callable] = {
    "INFY.NS": _build_scenario_1,
    "TATASTEEL.NS": _build_scenario_2,
    "RELIANCE.NS": _build_scenario_3,
    "HDFCBANK.NS": _build_scenario_4,
}


def get_demo_bundle(symbol: str) -> ChangeBundle | None:
    builder = _BUILDERS.get(symbol)
    return builder() if builder else None
