"""Tests for demo mode scenarios (Phase 2)."""

from app.schemas.scoring import ChangeBundle
from app.services.demo_data import (
    DEMO_SCENARIOS,
    DEMO_SYMBOLS,
    get_demo_bundle,
    get_demo_scenarios,
)


def test_all_demo_symbols_have_builders():
    for sym in DEMO_SYMBOLS:
        bundle = get_demo_bundle(sym)
        assert bundle is not None, f"No demo bundle for {sym}"
        assert isinstance(bundle, ChangeBundle)


def test_unknown_symbol_returns_none():
    assert get_demo_bundle("FAKE.NS") is None


def test_scenario_1_ceo_resignation():
    bundle = get_demo_bundle("INFY.NS")
    assert bundle.symbol == "INFY.NS"
    assert bundle.attention_score >= 70
    assert bundle.demo_label == "CEO Resignation"
    assert any(e.event_type == "executive_resignation" for e in bundle.events)
    assert bundle.is_meaningful is True
    assert bundle.data_ok is True
    chip_kinds = {c.kind for c in bundle.explain_chips}
    assert "price" in chip_kinds
    assert "event" in chip_kinds


def test_scenario_2_sector_outperformer():
    bundle = get_demo_bundle("TATASTEEL.NS")
    assert bundle.symbol == "TATASTEEL.NS"
    assert bundle.demo_label == "Sector Outperformer"
    assert bundle.components.sector_relative_move >= 60
    assert bundle.components.sector_change_pct < 0
    assert bundle.change_pct > 0
    chip_kinds = {c.kind for c in bundle.explain_chips}
    assert "sector" in chip_kinds


def test_scenario_3_volume_anomaly():
    bundle = get_demo_bundle("RELIANCE.NS")
    assert bundle.symbol == "RELIANCE.NS"
    assert bundle.demo_label == "Price + Volume Anomaly"
    assert bundle.components.volume_ratio >= 3.0
    assert len(bundle.events) == 0
    chip_kinds = {c.kind for c in bundle.explain_chips}
    assert "volume" in chip_kinds


def test_scenario_4_muted_reaction():
    bundle = get_demo_bundle("HDFCBANK.NS")
    assert bundle.symbol == "HDFCBANK.NS"
    assert bundle.demo_label == "Muted Reaction"
    assert abs(bundle.change_pct) < 1.0
    assert bundle.components.event_impact >= 60
    chip_kinds = {c.kind for c in bundle.explain_chips}
    assert "silence" in chip_kinds


def test_all_bundles_have_valid_scores():
    for sym in DEMO_SYMBOLS:
        bundle = get_demo_bundle(sym)
        assert 0 <= bundle.surprise_score <= 100
        assert 0 <= bundle.impact_score <= 100
        assert 0 <= bundle.confidence_score <= 100
        assert 0 <= bundle.attention_score <= 100
        assert bundle.as_of is not None


def test_get_demo_scenarios_returns_all():
    scenarios = get_demo_scenarios()
    assert len(scenarios) == len(DEMO_SCENARIOS)
    for s in scenarios:
        assert "id" in s
        assert "title" in s
        assert "description" in s
        assert "symbol" in s


def test_demo_bundles_have_confidence_factors():
    for sym in DEMO_SYMBOLS:
        bundle = get_demo_bundle(sym)
        assert len(bundle.confidence_factors) > 0


def test_demo_event_ids_are_unique():
    all_ids = []
    for sym in DEMO_SYMBOLS:
        bundle = get_demo_bundle(sym)
        all_ids.extend(e.event_id for e in bundle.events)
    assert len(all_ids) == len(set(all_ids))
