from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.core.session import get_current_user_id
from app.repositories import history_repository
from app.schemas.history import HistoryEntry, HistoryResponse

router = APIRouter(tags=["history"])


def _build_demo_history() -> list[HistoryEntry]:
    """Generate demo history entries so the History page is never empty."""
    from app.services.demo_data import get_demo_bundle, DEMO_SYMBOLS

    entries = []
    now = datetime.now(UTC)

    for day_offset in range(7):
        dt = now - timedelta(days=day_offset)
        date_key = dt.strftime("%Y-%m-%d")

        for symbol in DEMO_SYMBOLS:
            bundle = get_demo_bundle(symbol)
            if bundle is None:
                continue
            if day_offset > 0 and bundle.attention_score < 35:
                continue

            top_event = max(bundle.events, key=lambda e: e.impact_score, default=None)
            entries.append(HistoryEntry(
                user_id="demo",
                symbol=bundle.symbol,
                company_name=bundle.company_name,
                date_key=date_key,
                detected_at=dt,
                seen_at=dt - timedelta(hours=2) if day_offset > 1 else None,
                price=bundle.price,
                change_pct=bundle.change_pct,
                attention_score=bundle.attention_score,
                surprise_score=bundle.surprise_score,
                impact_score=bundle.impact_score,
                explain_chips=bundle.explain_chips,
                top_headline=top_event.title if top_event else None,
                top_event_type=top_event.event_type if top_event else None,
                why_this=bundle.why_this,
                why_now=bundle.why_now,
                demo_label=bundle.demo_label,
            ))

    entries.sort(key=lambda e: e.detected_at, reverse=True)
    return entries


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    filter: str = Query("all", pattern="^(all|today|seen|unseen)$"),
    user_id: str = Depends(get_current_user_id),
) -> HistoryResponse:
    from app.core.config import get_settings

    if get_settings().demo_mode:
        all_entries = _build_demo_history()

        if filter == "today":
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            all_entries = [e for e in all_entries if e.date_key == today]
        elif filter == "seen":
            all_entries = [e for e in all_entries if e.seen_at is not None]
        elif filter == "unseen":
            all_entries = [e for e in all_entries if e.seen_at is None]

        return HistoryResponse(entries=all_entries[:50], total=len(all_entries))

    entries = await history_repository.get_history(user_id, filter_mode=filter)
    total = await history_repository.count_history(user_id)
    return HistoryResponse(entries=entries, total=total)
