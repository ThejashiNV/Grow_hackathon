import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import type { AttentionResponse, DemoScenario } from "../types/api";
import { ChangeCard } from "../components/ChangeCard";
import "./AttentionPage.css";

function useCountUp(target: number, duration = 600) {
  const [val, setVal] = useState(0);
  const prev = useRef(0);
  useEffect(() => {
    const start = prev.current;
    const diff = target - start;
    if (diff === 0) return;
    const t0 = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / duration);
      const ease = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(start + diff * ease));
      if (p < 1) raf = requestAnimationFrame(tick);
      else prev.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

function MarketPulse({ data }: { data: AttentionResponse }) {
  const items = data.items;
  const total = items.length;
  const meaningful = items.filter(i => i.bundle.is_meaningful).length;
  const highAlert = items.filter(i => i.bundle.attention_score >= 70).length;
  const avgScore = total > 0 ? items.reduce((s, i) => s + i.bundle.attention_score, 0) / total : 0;
  const ups = items.filter(i => (i.bundle.change_pct ?? 0) > 0).length;
  const downs = items.filter(i => (i.bundle.change_pct ?? 0) < 0).length;

  const aTotal = useCountUp(total);
  const aMeaningful = useCountUp(meaningful);
  const aHighAlert = useCountUp(highAlert);
  const aAvg = useCountUp(Math.round(avgScore));
  const aUps = useCountUp(ups);
  const aDowns = useCountUp(downs);

  return (
    <div className="market-pulse">
      <div className="mp-item">
        <span className="mp-value">{aTotal}</span>
        <span className="mp-label">Tracked</span>
      </div>
      <div className="mp-divider" />
      <div className="mp-item">
        <span className="mp-value mp-meaningful">{aMeaningful}</span>
        <span className="mp-label">Changed</span>
      </div>
      <div className="mp-divider" />
      <div className="mp-item">
        <span className={`mp-value ${highAlert > 0 ? "mp-alert" : ""}`}>{aHighAlert}</span>
        <span className="mp-label">High Alert</span>
      </div>
      <div className="mp-divider" />
      <div className="mp-item">
        <span className="mp-value">{aAvg}</span>
        <span className="mp-label">Avg Score</span>
      </div>
      <div className="mp-divider" />
      <div className="mp-item">
        <span className="mp-value mp-up">{aUps}</span>
        <span className="mp-label">Up</span>
      </div>
      <div className="mp-item">
        <span className="mp-value mp-down">{aDowns}</span>
        <span className="mp-label">Down</span>
      </div>
    </div>
  );
}

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

  if (loading) return (
    <div className="attention-page">
      <div className="skeleton skeleton-card" style={{ height: 60 }} />
      <div className="skeleton skeleton-card" style={{ height: 44 }} />
      <div style={{ marginTop: "1.25rem" }}>
        <div className="skeleton skeleton-line long" />
        <div className="skeleton skeleton-line medium" />
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="skeleton skeleton-card" style={{ height: 160, marginTop: 12 }} />
      ))}
    </div>
  );
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

      <MarketPulse data={data} />

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
