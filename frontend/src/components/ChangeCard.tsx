import { useState } from "react";
import type { AttentionItem } from "../types/api";
import { api } from "../services/api";
import "./ChangeCard.css";

function severity(attentionScore: number): { emoji: string; label: string; className: string } {
  if (attentionScore >= 70) return { emoji: "🔴", label: "Significant change", className: "sev-high" };
  if (attentionScore >= 50) return { emoji: "🟠", label: "Notable change", className: "sev-med" };
  if (attentionScore >= 35) return { emoji: "🟡", label: "Worth a look", className: "sev-low" };
  return { emoji: "✓", label: "Nothing meaningful changed", className: "sev-none" };
}

function formatPct(n: number | null): string {
  if (n === null) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

export function ChangeCard({ item, onSeen }: { item: AttentionItem; onSeen?: (symbol: string) => void }) {
  const { bundle, diff } = item;
  const [expanded, setExpanded] = useState(false);
  const [marking, setMarking] = useState(false);
  const sev = severity(bundle.attention_score);
  const asOfTime = new Date(bundle.as_of).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const handleMarkSeen = async () => {
    setMarking(true);
    try {
      await api.markSeen(bundle.symbol);
      onSeen?.(bundle.symbol);
    } finally {
      setMarking(false);
    }
  };

  if (!bundle.data_ok) {
    return (
      <div className="change-card sev-none">
        <div className="card-header">
          <span className="symbol">{bundle.symbol}</span>
          <span className="unavailable">Market data unavailable</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`change-card ${sev.className}`}>
      <div className="card-header">
        <div className="title-row">
          <span className="severity-emoji">{sev.emoji}</span>
          <span className="symbol">{bundle.company_name || bundle.symbol}</span>
          {diff.is_new_since_last_visit && <span className="badge-new">NEW</span>}
        </div>
        <span className="sev-label">{sev.label}</span>
      </div>

      <div className="score-row">
        <div className="score-box">
          <span className="score-label">Surprise</span>
          <span className="score-value">{bundle.surprise_score.toFixed(0)}</span>
        </div>
        <div className="score-box">
          <span className="score-label">Impact</span>
          <span className="score-value">{bundle.impact_score.toFixed(0)}</span>
        </div>
        <div className="score-box">
          <span className="score-label">Confidence</span>
          <span className="score-value">{bundle.confidence_score.toFixed(0)}%</span>
        </div>
      </div>

      <div className="price-row">
        <span className="price">₹{bundle.price?.toFixed(2) ?? "—"}</span>
        <span className={`change-pct ${(bundle.change_pct ?? 0) >= 0 ? "pos" : "neg"}`}>
          {formatPct(bundle.change_pct)}
        </span>
        {bundle.normal_daily_move_pct !== null && (
          <span className="normal-move">Normal: ±{bundle.normal_daily_move_pct.toFixed(1)}%</span>
        )}
      </div>

      {bundle.explain_chips.length > 0 && (
        <div className="chips-row">
          {bundle.explain_chips.map((chip, i) => (
            <span key={i} className={`chip chip-${chip.kind}`}>
              {chip.label}
            </span>
          ))}
          {bundle.sector_wide && <span className="chip chip-sector">Sector-wide move</span>}
        </div>
      )}

      {diff.has_prior_state && diff.price_changed_since !== null && (
        <div className="since-last-visit">Since your last visit: {formatPct(diff.price_changed_since)}</div>
      )}

      <button className="why-toggle" onClick={() => setExpanded((e) => !e)}>
        {expanded ? "Hide details" : "Why?"}
      </button>

      {expanded && (
        <div className="details">
          <p>
            <strong>Why this?</strong> {bundle.why_this}
          </p>
          <p>
            <strong>Why now?</strong> {bundle.why_now}
          </p>
          {bundle.components.sector && (
            <p className="sector-line">
              Sector ({bundle.components.sector}): {formatPct(bundle.components.sector_change_pct)}
            </p>
          )}
          <div className="confidence-factors">
            <strong>Data quality:</strong>
            <ul>
              {bundle.confidence_factors.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
          {bundle.events.length > 0 && (
            <div className="events-list">
              <strong>Evidence:</strong>
              <ul>
                {bundle.events.slice(0, 5).map((e) => (
                  <li key={e.event_id}>
                    <span className="event-type">[{e.event_type.replace(/_/g, " ")}]</span>{" "}
                    {e.link ? (
                      <a href={e.link} target="_blank" rel="noreferrer">
                        {e.title}
                      </a>
                    ) : (
                      e.title
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="card-footer">
        <span className="as-of">
          As of {asOfTime} {bundle.is_delayed && <span className="delayed-tag">Delayed</span>}
        </span>
        <button className="mark-seen" onClick={handleMarkSeen} disabled={marking}>
          {marking ? "..." : "Mark as seen"}
        </button>
      </div>
    </div>
  );
}
