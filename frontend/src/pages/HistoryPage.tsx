import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { HistoryEntry, HistoryResponse } from "../types/api";
import "./HistoryPage.css";

type FilterMode = "all" | "today" | "seen" | "unseen";

function severity(score: number): { className: string; emoji: string } {
  if (score >= 70) return { className: "sev-high", emoji: "🔴" };
  if (score >= 50) return { className: "sev-med", emoji: "🟠" };
  if (score >= 35) return { className: "sev-low", emoji: "🟡" };
  return { className: "sev-none", emoji: "✓" };
}

function formatPct(n: number | null): string {
  if (n === null) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function groupByDate(entries: HistoryEntry[]): Map<string, HistoryEntry[]> {
  const groups = new Map<string, HistoryEntry[]>();
  for (const entry of entries) {
    const key = entry.date_key;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(entry);
  }
  return groups;
}

function formatDateLabel(dateKey: string): string {
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  if (dateKey === today) return "Today";
  if (dateKey === yesterday) return "Yesterday";
  return new Date(dateKey + "T00:00:00").toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function TimelineEntry({ entry }: { entry: HistoryEntry }) {
  const sev = severity(entry.attention_score);
  const time = new Date(entry.detected_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`timeline-entry ${sev.className}`}>
      <div className="timeline-dot-col">
        <span className="timeline-time">{time}</span>
        <span className={`timeline-dot ${sev.className}`} />
        <span className="timeline-line" />
      </div>
      <div className="timeline-content">
        <div className="timeline-header">
          <span className="timeline-emoji">{sev.emoji}</span>
          <span className="timeline-symbol">{entry.company_name || entry.symbol}</span>
          {entry.seen_at ? (
            <span className="badge-seen">SEEN</span>
          ) : (
            <span className="badge-unseen">NEW</span>
          )}
          {entry.demo_label && <span className="badge-demo">{entry.demo_label}</span>}
        </div>

        <div className="timeline-scores">
          <span>Attention <strong>{entry.attention_score.toFixed(0)}</strong></span>
          <span>Surprise <strong>{entry.surprise_score.toFixed(0)}</strong></span>
          <span>Impact <strong>{entry.impact_score.toFixed(0)}</strong></span>
        </div>

        {entry.price !== null && (
          <div className="timeline-price">
            <span>₹{entry.price.toFixed(2)}</span>
            <span className={`change-pct ${(entry.change_pct ?? 0) >= 0 ? "pos" : "neg"}`}>
              {formatPct(entry.change_pct)}
            </span>
          </div>
        )}

        {entry.explain_chips.length > 0 && (
          <div className="timeline-chips">
            {entry.explain_chips.map((chip, i) => (
              <span key={i} className={`chip chip-${chip.kind}`}>{chip.label}</span>
            ))}
          </div>
        )}

        {entry.top_headline && (
          <div className="timeline-headline">
            <span className="event-type">[{entry.top_event_type?.replace(/_/g, " ")}]</span>{" "}
            {entry.top_headline}
          </div>
        )}

        <button className="timeline-expand" onClick={() => setExpanded((e) => !e)}>
          {expanded ? "Hide details" : "Why?"}
        </button>

        {expanded && (
          <div className="timeline-details">
            <p><strong>Why this?</strong> {entry.why_this}</p>
            <p><strong>Why now?</strong> {entry.why_now}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export function HistoryPage() {
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterMode>("all");

  const load = (f: FilterMode) => {
    setLoading(true);
    api
      .getHistory(f)
      .then((res) => { setData(res); setError(null); })
      .catch((err) => setError(err.message ?? "Failed to load history"))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(filter), [filter]);

  const handleFilter = (f: FilterMode) => {
    setFilter(f);
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <h2>Change History</h2>
        <p className="history-subtitle">Timeline of detected meaningful changes across your watchlist.</p>
      </div>

      <div className="history-filters">
        {(["all", "today", "seen", "unseen"] as FilterMode[]).map((f) => (
          <button
            key={f}
            className={`filter-btn ${filter === f ? "active" : ""}`}
            onClick={() => handleFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading && <p className="status-text">Loading history...</p>}
      {error && <p className="status-text error">Could not load history: {error}</p>}

      {!loading && data && data.entries.length === 0 && (
        <div className="empty-state">
          <h3>No history yet</h3>
          <p>
            {filter === "all"
              ? "Visit the Attention tab to start detecting changes. Meaningful changes are recorded here automatically."
              : `No ${filter} entries found. Try a different filter.`}
          </p>
        </div>
      )}

      {!loading && data && data.entries.length > 0 && (
        <div className="timeline">
          {[...groupByDate(data.entries)].map(([dateKey, entries]) => (
            <div key={dateKey} className="timeline-day">
              <div className="timeline-date-label">{formatDateLabel(dateKey)}</div>
              {entries.map((entry, i) => (
                <TimelineEntry key={`${entry.symbol}-${entry.date_key}-${i}`} entry={entry} />
              ))}
            </div>
          ))}
        </div>
      )}

      {!loading && data && data.total > 0 && (
        <div className="history-footer">
          <span className="history-count">{data.total} total entries recorded</span>
        </div>
      )}
    </div>
  );
}
