"""What changed since this user last checked (Part 3/17).

Server-side last-seen state is the source of truth (never localStorage). This
module only diffs already-computed ChangeBundles against StockState -- it
does no I/O itself, so it stays trivially testable.
"""

from app.schemas.scoring import ChangeBundle
from app.schemas.user_state import DiffResult, StockState


def compute_diff(state: StockState, bundle: ChangeBundle) -> DiffResult:
    has_prior_state = state.last_seen_at is not None

    if not has_prior_state:
        return DiffResult(
            symbol=bundle.symbol,
            has_prior_state=False,
            new_event_ids=[e.event_id for e in bundle.events],
            is_new_since_last_visit=True,
        )

    price_changed_since = None
    if bundle.price is not None and state.last_seen_price:
        price_changed_since = round(
            (bundle.price - state.last_seen_price) / state.last_seen_price * 100, 2
        )

    score_changed_since = None
    if state.last_seen_score is not None:
        score_changed_since = round(bundle.attention_score - state.last_seen_score, 1)

    seen_ids = set(state.last_seen_event_ids)
    new_event_ids = [e.event_id for e in bundle.events if e.event_id not in seen_ids]

    return DiffResult(
        symbol=bundle.symbol,
        has_prior_state=True,
        price_changed_since=price_changed_since,
        new_event_ids=new_event_ids,
        score_changed_since=score_changed_since,
        is_new_since_last_visit=False,
    )
