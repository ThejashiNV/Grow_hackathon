"""Tests for history recording and retrieval (Phase 3)."""

from datetime import UTC, datetime

from app.repositories.history_repository import _bundle_to_entry
from app.schemas.events import ClassifiedEvent, EventType
from app.schemas.scoring import ChangeBundle, ExplainChip, ScoreComponents


def _make_bundle(symbol: str = "TEST.NS", attention: float = 50.0, meaningful: bool = True, **kwargs) -> ChangeBundle:
    return ChangeBundle(
        symbol=symbol,
        company_name=kwargs.get("company_name", "Test Corp"),
        price=kwargs.get("price", 100.0),
        previous_close=95.0,
        change_pct=kwargs.get("change_pct", 5.26),
        components=ScoreComponents(
            price_anomaly=60, volume_anomaly=40,
            sector_relative_move=30, headline_novelty=50, event_impact=55,
        ),
        surprise_score=45,
        impact_score=52,
        confidence_score=80,
        attention_score=attention,
        events=kwargs.get("events", []),
        explain_chips=kwargs.get("explain_chips", [ExplainChip(label="Price anomaly", kind="price")]),
        why_this="Test explanation.",
        why_now="Test now.",
        is_meaningful=meaningful,
        as_of=kwargs.get("as_of", datetime.now(UTC)),
        demo_label=kwargs.get("demo_label"),
    )


def test_bundle_to_entry_basic():
    bundle = _make_bundle(symbol="INFY.NS", company_name="Infosys Ltd", attention=75)
    entry = _bundle_to_entry("user-1", bundle)
    assert entry["user_id"] == "user-1"
    assert entry["symbol"] == "INFY.NS"
    assert entry["company_name"] == "Infosys Ltd"
    assert entry["attention_score"] == 75
    assert entry["seen_at"] is None
    assert entry["date_key"] == bundle.as_of.strftime("%Y-%m-%d")
    assert len(entry["explain_chips"]) == 1


def test_bundle_to_entry_extracts_top_headline():
    events = [
        ClassifiedEvent(
            event_id="ev-1", symbol="X.NS", event_type=EventType.EARNINGS,
            title="Quarterly Earnings Beat", impact_score=40, novelty_score=60,
            timestamp=datetime.now(UTC),
        ),
        ClassifiedEvent(
            event_id="ev-2", symbol="X.NS", event_type=EventType.EXECUTIVE_RESIGNATION,
            title="CEO Steps Down", impact_score=85, novelty_score=90,
            timestamp=datetime.now(UTC),
        ),
    ]
    bundle = _make_bundle(events=events)
    entry = _bundle_to_entry("user-1", bundle)
    assert entry["top_headline"] == "CEO Steps Down"
    assert entry["top_event_type"] == "executive_resignation"


def test_bundle_to_entry_no_events():
    bundle = _make_bundle(events=[])
    entry = _bundle_to_entry("user-1", bundle)
    assert entry["top_headline"] is None
    assert entry["top_event_type"] is None


def test_bundle_to_entry_preserves_demo_label():
    bundle = _make_bundle(demo_label="CEO Resignation")
    entry = _bundle_to_entry("user-1", bundle)
    assert entry["demo_label"] == "CEO Resignation"


def test_bundle_to_entry_date_key_format():
    fixed_time = datetime(2026, 9, 4, 14, 30, 0, tzinfo=UTC)
    bundle = _make_bundle(as_of=fixed_time)
    entry = _bundle_to_entry("user-1", bundle)
    assert entry["date_key"] == "2026-09-04"


def test_bundle_to_entry_includes_all_chips():
    chips = [
        ExplainChip(label="Price anomaly -4.6σ", kind="price"),
        ExplainChip(label="Volume 3.0× normal", kind="volume"),
        ExplainChip(label="Unusually muted reaction", kind="silence"),
    ]
    bundle = _make_bundle(explain_chips=chips)
    entry = _bundle_to_entry("user-1", bundle)
    assert len(entry["explain_chips"]) == 3
    assert entry["explain_chips"][2]["kind"] == "silence"
