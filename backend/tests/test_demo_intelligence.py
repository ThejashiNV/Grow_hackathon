"""Tests for demo intelligence data (event clusters, impact scale)."""

from app.services.demo_data import DEMO_SYMBOLS
from app.services.demo_intelligence import get_demo_intelligence


def test_event_cluster_impact_score_is_0_to_100_scale():
    """Regression test: event cluster impact_score must be on the same 0-100
    scale as every other impact_score in the schema (news, ML anomalies,
    attention). It was previously authored 0-1 in the demo dataset, which
    silently broke the >=50/>=60 alert thresholds in intelligence.py."""
    seen_any_cluster = False
    for symbol in DEMO_SYMBOLS:
        intel = get_demo_intelligence(symbol)
        for cluster in intel.event_clusters:
            seen_any_cluster = True
            assert 1 < cluster.impact_score <= 100, (
                f"{symbol} cluster {cluster.cluster_id!r} impact_score "
                f"{cluster.impact_score} looks like a 0-1 scale value, not 0-100"
            )
    assert seen_any_cluster, "expected at least one demo stock to have event clusters"


def test_all_demo_symbols_produce_intelligence():
    for symbol in DEMO_SYMBOLS:
        intel = get_demo_intelligence(symbol)
        assert intel.symbol == symbol
        assert intel.company_name
