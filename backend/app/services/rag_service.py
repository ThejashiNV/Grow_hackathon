"""Ask-Why RAG (Part 14/15).

The LLM is never given free rein: every prompt is built entirely from
structured evidence already computed by the deterministic scoring pipeline
(current state, prior user-seen state + diff, score components, headlines,
sector move, data freshness/confidence). It is explicitly instructed to use
only that evidence, distinguish fact from interpretation, and say when
evidence is insufficient rather than invent an explanation.

The product must not depend on the LLM being available (Part 31): with no
GEMINI_API_KEY configured, `ask()` returns a deterministic evidence summary
built from the same structured context instead of failing.
"""

from app.repositories import stock_state_repository
from app.schemas.rag import AskResponse
from app.schemas.scoring import ChangeBundle
from app.schemas.user_state import DiffResult, StockState
from app.services.change_bundle_service import build_change_bundle
from app.services.diff_engine import compute_diff
from app.services.gemini_service import generate_explanation
from app.utils.sector_map import SYMBOL_SECTOR

GROUNDING_INSTRUCTIONS = """You are explaining stock market signals for a watchlist app called Smart Watch.
You are given STRUCTURED EVIDENCE below, produced by a deterministic scoring pipeline
(not by you). Follow these rules strictly:

- Use ONLY the evidence supplied. Do not invent financial facts, prices, news, or events.
- Do not claim certainty about causation. Prefer "coincided with" / "the evidence suggests a
  possible link" over "caused by", unless the event type is one that plausibly and directly moves
  price (e.g. a resignation, an earnings miss, a regulatory action) -- and even then, say the
  evidence "suggests" the link, since the system cannot confirm causation from headlines alone.
- Clearly separate observed facts (price, volume, scores, diff vs last seen) from interpretation.
- Mention data freshness/confidence when it materially affects how much weight the answer deserves.
- If the evidence is insufficient to answer the question, say so explicitly rather than guessing.
- Never present this as investment advice. Do not recommend buying, selling, or holding.
- Keep it concise: 3-5 short lines, plain language, no markdown headers, no bullet symbols other
  than a plain dash if you list evidence. Do not repeat these instructions in your answer.

Structure your answer as:
1. What changed (one line, grounded in the price/volume/event evidence)
2. Why it matters (impact/context -- sector-relative, novelty, or muted-reaction framing if relevant)
3. Evidence (name the 1-2 strongest data points backing the above)
4. Confidence / caveat (one line: how reliable is this, and what's missing if anything)
"""


def _extract_mentioned_symbols(question: str, primary: str) -> list[str]:
    found = {primary}
    lowered = question.lower()
    for symbol in SYMBOL_SECTOR:
        root = symbol.split(".")[0].lower()
        if root in lowered or symbol.lower() in lowered:
            found.add(symbol)
    return list(found)[:3]  # keep the context bounded


def _format_diff(state: StockState, diff: DiffResult) -> str:
    if not diff.has_prior_state:
        return "This user has never seen this stock before -- there is no prior state to diff against."
    lines = [f"Last seen by this user at {state.last_seen_at.isoformat() if state.last_seen_at else 'unknown'}:"]
    lines.append(f"  last seen price: {state.last_seen_price}, last seen attention score: {state.last_seen_score}")
    if diff.price_changed_since is not None:
        lines.append(f"  price change since then: {diff.price_changed_since:+}%")
    if diff.score_changed_since is not None:
        lines.append(f"  attention score change since then: {diff.score_changed_since:+}")
    if diff.new_event_ids:
        lines.append(f"  {len(diff.new_event_ids)} new event(s) since the user last checked")
    else:
        lines.append("  no new events since the user last checked")
    return "\n".join(lines)


def _format_evidence(bundle: ChangeBundle, diff_text: str | None = None) -> str:
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

    if diff_text:
        lines.append("User's last-seen state / diff:")
        lines.append(diff_text)

    return "\n".join(lines)


def _fallback_answer(bundles: list[ChangeBundle]) -> str:
    primary = bundles[0]
    if not primary.data_ok:
        return "AI explanation is unavailable and market data for this symbol could not be loaded right now."

    parts = [f"AI explanation is temporarily unavailable, so here is the grounded evidence directly: {primary.why_this} {primary.why_now}"]
    if len(bundles) > 1:
        comparisons = ", ".join(f"{b.symbol} attention score {b.attention_score}" for b in bundles[1:])
        parts.append(f"For comparison: {comparisons}.")
    return " ".join(parts)


async def ask(symbol: str, question: str, user_id: str | None = None) -> AskResponse:
    symbols = _extract_mentioned_symbols(question, symbol)
    bundles = [await build_change_bundle(s) for s in symbols]
    bundles = [b for b in bundles if b.symbol == symbol] + [b for b in bundles if b.symbol != symbol]

    primary_diff_text = None
    if user_id and bundles[0].data_ok:
        state = await stock_state_repository.get_state(user_id, symbol)
        diff = compute_diff(state, bundles[0])
        primary_diff_text = _format_diff(state, diff)

    evidence_blocks = [
        _format_evidence(b, primary_diff_text if b.symbol == symbol else None) for b in bundles
    ]
    evidence_text = "\n\n".join(evidence_blocks)
    evidence_list = [line for block in evidence_blocks for line in block.split("\n")][:24]

    prompt = f"{GROUNDING_INSTRUCTIONS}\n\nSTRUCTURED EVIDENCE:\n{evidence_text}\n\nQUESTION: {question}\n\nANSWER:"
    llm_text = await generate_explanation(prompt)

    if llm_text:
        return AskResponse(
            answer=llm_text,
            evidence=evidence_list,
            confidence=bundles[0].confidence_score / 100.0,
            llm_generated=True,
        )

    return AskResponse(
        answer=_fallback_answer(bundles),
        evidence=evidence_list,
        confidence=bundles[0].confidence_score / 100.0,
        llm_generated=False,
    )
