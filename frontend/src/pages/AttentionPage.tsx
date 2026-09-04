import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { AttentionResponse, DemoScenario } from "../types/api";
import { ChangeCard } from "../components/ChangeCard";
import "./AttentionPage.css";

export function AttentionPage() {
  const [data, setData] = useState<AttentionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCollapsed, setShowCollapsed] = useState(false);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api
      .getAttention()
      .then((res) => {
        setData(res);
        setError(null);
        if (res.demo_mode) {
          api.getDemoScenarios().then((d) => setScenarios(d.scenarios)).catch(() => {});
        }
      })
      .catch((err) => setError(err.message ?? "Failed to load attention feed"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <p className="status-text">Checking your watchlist...</p>;
  if (error) return <p className="status-text error">Could not load attention feed: {error}</p>;
  if (!data) return null;

  if (data.empty_watchlist && !data.demo_mode) {
    return (
      <div className="empty-state">
        <h3>Your watchlist is empty</h3>
        <p>Add stocks from the Watchlist tab to start seeing what changed.</p>
      </div>
    );
  }

  const activeSymbol = activeScenario
    ? scenarios.find((s) => s.id === activeScenario)?.symbol ?? null
    : null;

  const filteredItems = activeSymbol
    ? data.items.filter((i) => i.bundle.symbol === activeSymbol)
    : data.items;

  const meaningful = filteredItems.filter((i) => i.bundle.is_meaningful);
  const quiet = filteredItems.filter((i) => !i.bundle.is_meaningful);

  return (
    <div className="attention-page">
      {data.demo_mode && (
        <div className="demo-banner">
          <span className="demo-badge">DEMO MODE</span>
          <span className="demo-subtitle">Deterministic scenarios — no live API calls</span>
        </div>
      )}

      {data.demo_mode && scenarios.length > 0 && (
        <div className="scenario-selector">
          <button
            className={`scenario-btn ${activeScenario === null ? "active" : ""}`}
            onClick={() => setActiveScenario(null)}
          >
            All Scenarios
          </button>
          {scenarios.map((s) => (
            <button
              key={s.id}
              className={`scenario-btn ${activeScenario === s.id ? "active" : ""}`}
              onClick={() => setActiveScenario(activeScenario === s.id ? null : s.id)}
              title={s.description}
            >
              {s.title}
            </button>
          ))}
        </div>
      )}

      <div className="attention-summary">
        <h2>What needs your attention?</h2>
        <p>
          {meaningful.length === 0
            ? "You're caught up. Nothing meaningful changed across your watchlist."
            : `${meaningful.length} meaningful change${meaningful.length === 1 ? "" : "s"} since your last visit.`}
        </p>
      </div>

      {meaningful.map((item) => (
        <ChangeCard key={item.bundle.symbol} item={item} onSeen={load} />
      ))}

      {quiet.length > 0 && (
        <div className="collapsed-section">
          <button className="collapsed-toggle" onClick={() => setShowCollapsed((s) => !s)}>
            {showCollapsed ? "Hide" : "Show"} {quiet.length} stock{quiet.length === 1 ? "" : "s"} with nothing meaningful changed
          </button>
          {showCollapsed && quiet.map((item) => <ChangeCard key={item.bundle.symbol} item={item} onSeen={load} />)}
        </div>
      )}
    </div>
  );
}
