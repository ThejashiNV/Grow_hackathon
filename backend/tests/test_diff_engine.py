from datetime import UTC, datetime

from app.schemas.scoring import ChangeBundle, ScoreComponents
from app.schemas.user_state import StockState
from app.services.diff_engine import compute_diff


def _bundle(symbol="TCS.NS", price=100.0, attention=50.0, event_ids=None) -> ChangeBundle:
    return ChangeBundle(
        symbol=symbol,
        price=price,
        components=ScoreComponents(price_anomaly=0, volume_anomaly=0, sector_relative_move=0, headline_novelty=0, event_impact=0),
        surprise_score=0,
        impact_score=0,
        confidence_score=100,
        attention_score=attention,
        events=[],
        why_this="",
        why_now="",
        is_meaningful=attention >= 35,
        as_of=datetime.now(UTC),
    )


def test_first_visit_has_no_prior_state():
    state = StockState(user_id="u1", symbol="TCS.NS")
    diff = compute_diff(state, _bundle())
    assert diff.has_prior_state is False
    assert diff.is_new_since_last_visit is True


def test_price_change_computed_against_last_seen():
    state = StockState(user_id="u1", symbol="TCS.NS", last_seen_price=100.0, last_seen_at=datetime.now(UTC))
    diff = compute_diff(state, _bundle(price=105.0))
    assert diff.price_changed_since == 5.0


def test_score_change_computed_against_last_seen():
    state = StockState(user_id="u1", symbol="TCS.NS", last_seen_price=100.0, last_seen_score=30.0, last_seen_at=datetime.now(UTC))
    diff = compute_diff(state, _bundle(attention=55.0))
    assert diff.score_changed_since == 25.0
