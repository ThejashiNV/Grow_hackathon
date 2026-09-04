"""Ask-Why RAG (Part 14/15).

The LLM is never given free rein: every prompt is built entirely from
structured evidence already computed by the deterministic scoring pipeline
(current state, prior user-seen state, score components, headlines, sector
move, data freshness/confidence). It is explicitly instructed to use only
that evidence, distinguish fact from interpretation, and say when evidence
is insufficient rather than invent an explanation.

The product must not depend on the LLM being available (Part 31): with no
GEMINI_API_KEY configured, `ask()` returns a deterministic evidence summary
built from the same structured context instead of failing.
"""

import logging
import re

from app.core.config import get_settings
from app.schemas.rag import AskResponse
from app.schemas.scoring import ChangeBundle
from app.services.change_bundle_service import build_change_bundle
from app.utils.sector_map import SYMBOL_SECTOR

logger = logging.getLogger(__name__)

GROUNDING_INSTRUCTIONS = """You are explaining stock market signals for a watchlist app. You are given
STRUCTURED EVIDENCE below. Follow these rules strictly:

- Only use the evidence supplied. Do not invent financial facts, prices, or news.
- Do not claim a causal relationship (e.g. "the stock fell because of X") unless the
  evidence directly supports it. Prefer "the move coincided with X" over "X caused the move"
  unless the event is clearly the kind that would move price (e.g. a resignation, an earnings miss).
- Clearly distinguish observed facts (price, volume, scores) from interpretation.
- Mention data freshness/confidence when it's relevant to how much weight the answer deserves.
- If the evidence is insufficient to answer the question, say so explicitly rather than guessing.
- Never present this as investment advice. Do not recommend buying or selling.
- Keep the answer to 2-4 sentences, plain language, no markdown headers.
"""


def _extract_mentioned_symbols(question: str, primary: str) -> list[str]:
    found = {primary}
    lowered = question.lower()
    for symbol in SYMBOL_SECTOR:
        root = symbol.split(".")[0].lower()
        if root in lowered or symbol.lower() in lowered:
            found.add(symbol)
    return list(found)[:3]  # keep the context bounded


def _format_evidence(bundle: ChangeBundle) -> str:
    lines = [f"=== {bundle.symbol} ({bundle.company_name or 'unknown company'}) ==="]
    if not bundle.data_ok:
        lines.append("Market data is currently unavailable for this symbol.")
        return "\n".join(lines)

    lines.append(f"Price: {bundle.price} (previous close: {bundle.previous_close}, change: {bundle.change_pct}%)")
    if bundle.normal_daily_move_pct is not None:
        lines.append(f"This stock's typical daily move: +-{bundle.normal_daily_move_pct}%")
    lines.append(f"Volume: {bundle.volume} (20-day average: {bundle.average_volume_20d})")
    if bundle.components.sector:
        lines.append(f"Sector: {bundle.components.sector}, sector move today: {bundle.components.sector_change_pct}%")
    lines.append(
        f"Scores (0-100) -- Surprise: {bundle.surprise_score}, Impact: {bundle.impact_score}, "
        f"Confidence: {bundle.confidence_score}, Attention (final ranking): {bundle.attention_score}"
    )
    lines.append(
        f"Score components -- price anomaly: {bundle.components.price_anomaly} "
        f"(z-score {bundle.components.price_z_score}), volume anomaly: {bundle.components.volume_anomaly} "
        f"(ratio {bundle.components.volume_ratio}x), sector-relative divergence: {bundle.components.sector_relative_move}, "
        f"headline novelty: {bundle.components.headline_novelty}, event impact: {bundle.components.event_impact}"
    )
    lines.append(f"Data quality factors: {'; '.join(bundle.confidence_factors)}")
    lines.append(f"Data as of: {bundle.as_of.isoformat()} ({'delayed' if bundle.is_delayed else 'real-time'})")

    if bundle.events:
        lines.append("Recent headlines (deduplicated, most impactful first):")
        for e in sorted(bundle.events, key=lambda ev: ev.impact_score, reverse=True)[:5]:
            lines.append(f"  - [{e.event_type}] \"{e.title}\" (source: {e.source}, impact: {e.impact_score}, novelty: {e.novelty_score})")
    else:
        lines.append("No relevant headlines found for this symbol right now.")

    return "\n".join(lines)


def _fallback_answer(question: str, bundles: list[ChangeBundle]) -> str:
    primary = bundles[0]
    if not primary.data_ok:
        return "AI explanation is unavailable and market data for this symbol could not be loaded right now."

    parts = [f"AI explanation is temporarily unavailable, so here is the grounded evidence directly: {primary.why_this} {primary.why_now}"]
    if len(bundles) > 1:
        comparisons = ", ".join(f"{b.symbol} attention score {b.attention_score}" for b in bundles[1:])
        parts.append(f"For comparison: {comparisons}.")
    return " ".join(parts)


async def _llm_answer(question: str, evidence_text: str) -> str | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.llm_model)
        prompt = f"{GROUNDING_INSTRUCTIONS}\n\nSTRUCTURED EVIDENCE:\n{evidence_text}\n\nQUESTION: {question}\n\nANSWER:"
        response = await model.generate_content_async(prompt)
        text = (response.text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed, falling back to evidence summary: %s", exc)
        return None


async def ask(symbol: str, question: str) -> AskResponse:
    symbols = _extract_mentioned_symbols(question, symbol)
    bundles = [await build_change_bundle(s) for s in symbols]
    bundles = [b for b in bundles if b.symbol == symbol] + [b for b in bundles if b.symbol != symbol]

    evidence_text = "\n\n".join(_format_evidence(b) for b in bundles)
    evidence_list = [line for b in bundles for line in _format_evidence(b).split("\n")][:20]

    llm_text = await _llm_answer(question, evidence_text)
    if llm_text:
        return AskResponse(
            answer=llm_text,
            evidence=evidence_list,
            confidence=bundles[0].confidence_score / 100.0,
            llm_generated=True,
        )

    return AskResponse(
        answer=_fallback_answer(question, bundles),
        evidence=evidence_list,
        confidence=bundles[0].confidence_score / 100.0,
        llm_generated=False,
    )
