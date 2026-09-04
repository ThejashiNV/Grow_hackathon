from datetime import UTC, datetime

import pytest

from app.schemas.scoring import ChangeBundle, ScoreComponents
from app.services import rag_service


def _bundle(symbol="TCS.NS", data_ok=True, attention=40.0) -> ChangeBundle:
    return ChangeBundle(
        symbol=symbol,
        price=100.0,
        components=ScoreComponents(price_anomaly=0, volume_anomaly=0, sector_relative_move=0, headline_novelty=0, event_impact=0),
        surprise_score=0,
        impact_score=0,
        confidence_score=80,
        attention_score=attention,
        events=[],
        why_this="Moved +1.0% today.",
        why_now="Nothing unusual detected.",
        is_meaningful=attention >= 35,
        as_of=datetime.now(UTC),
        data_ok=data_ok,
    )


@pytest.mark.asyncio
async def test_ask_falls_back_when_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(rag_service, "build_change_bundle", lambda symbol: _fake_bundle_coro(_bundle(symbol)))
    monkeypatch.setattr(rag_service, "generate_explanation", lambda prompt: _fake_none_coro())

    result = await rag_service.ask("TCS.NS", "Why is this flagged?")

    assert result.llm_generated is False
    assert "evidence" in result.answer.lower() or "unavailable" in result.answer.lower()
    assert result.confidence == 0.8


@pytest.mark.asyncio
async def test_ask_uses_llm_answer_when_available(monkeypatch):
    monkeypatch.setattr(rag_service, "build_change_bundle", lambda symbol: _fake_bundle_coro(_bundle(symbol)))
    monkeypatch.setattr(rag_service, "generate_explanation", lambda prompt: _fake_text_coro("Grounded AI answer."))

    result = await rag_service.ask("TCS.NS", "Why is this flagged?")

    assert result.llm_generated is True
    assert result.answer == "Grounded AI answer."


@pytest.mark.asyncio
async def test_ask_handles_unavailable_market_data(monkeypatch):
    monkeypatch.setattr(rag_service, "build_change_bundle", lambda symbol: _fake_bundle_coro(_bundle(symbol, data_ok=False)))
    monkeypatch.setattr(rag_service, "generate_explanation", lambda prompt: _fake_none_coro())

    result = await rag_service.ask("TCS.NS", "Why is this flagged?")

    assert result.llm_generated is False
    assert "unavailable" in result.answer.lower()


async def _fake_bundle_coro(bundle):
    return bundle


async def _fake_none_coro():
    return None


async def _fake_text_coro(text):
    return text
