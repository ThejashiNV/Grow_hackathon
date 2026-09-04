import { useEffect, useState } from "react";
import { api } from "../services/api";
import type {
  AnomalousMove,
  ExpectedVsActual,
  HorizonAnalysis,
  PatternDiscovery,
  RareEvent,
  RegimeChange,
  StockIntelligence,
  Watchlist,
} from "../types/api";
import "./IntelligencePage.css";

// ── helpers ──────────────────────────────────────────────────────────

function trendIcon(t: string) {
  if (t === "bullish") return "▲";
  if (t === "bearish") return "▼";
  return "—";
}

function trendClass(t: string) {
  if (t === "bullish") return "pos";
  if (t === "bearish") return "neg";
  return "neutral";
}

function pct(n: number | null, signed = false): string {
  if (n === null || n === undefined) return "—";
  const s = signed && n >= 0 ? "+" : "";
  return `${s}${n.toFixed(2)}%`;
}

function sevClass(sigma: number) {
  if (sigma >= 4) return "sev-extreme";
  if (sigma >= 3) return "sev-major";
  return "sev-notable";
}

function confBar(c: number) {
  const w = Math.round(c * 100);
  return (
    <span className="conf-bar" title={`${w}% confidence`}>
      <span className="conf-fill" style={{ width: `${w}%` }} />
    </span>
  );
}

function fmtVol(v: number | null): string {
  if (!v) return "—";
  if (v >= 1e7) return `${(v / 1e7).toFixed(1)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(1)} L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

// ── sub-components ───────────────────────────────────────────────────

function HorizonsSection({ horizons }: { horizons: HorizonAnalysis[] }) {
  return (
    <section className="intel-section">
      <h4>Multi-Horizon Behavior</h4>
      <div className="horizons-table-wrap">
        <table className="horizons-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Return</th>
              <th>Vol (ann.)</th>
              <th>Max DD</th>
              <th>Trend</th>
              <th>Momentum</th>
              <th>Large Moves</th>
              <th>Avg Volume</th>
              <th>Vol Ratio</th>
            </tr>
          </thead>
          <tbody>
            {horizons.map((h) => (
              <tr key={h.period}>
                <td className="period-cell">{h.period}</td>
                <td className={h.return_pct >= 0 ? "pos" : "neg"}>{pct(h.return_pct, true)}</td>
                <td>{pct(h.annualized_volatility)}</td>
                <td className="neg">{pct(h.max_drawdown_pct)}</td>
                <td className={trendClass(h.trend)}>
                  {trendIcon(h.trend)} {h.trend}
                </td>
                <td className={h.momentum_score >= 0 ? "pos" : "neg"}>
                  {h.momentum_score.toFixed(0)}
                </td>
                <td>{h.large_move_count}</td>
                <td>{fmtVol(h.avg_daily_volume)}</td>
                <td>{h.volume_vs_baseline ? `${h.volume_vs_baseline.toFixed(2)}×` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function RegimeSection({ changes }: { changes: RegimeChange[] }) {
  return (
    <section className="intel-section">
      <h4>Behavior Regime Changes</h4>
      <div className="card-grid">
        {changes.map((r, i) => (
          <div key={i} className={`regime-card ${r.ratio > 1.3 ? "warn" : r.ratio < 0.7 ? "cool" : ""}`}>
            <div className="regime-metric">{r.metric}</div>
            <div className="regime-ratio">{r.ratio.toFixed(1)}×</div>
            <p className="regime-desc">{r.description}</p>
            <span className="regime-period">{r.period_compared}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function AnomalousSection({ moves }: { moves: AnomalousMove[] }) {
  const [limit, setLimit] = useState(8);
  const shown = moves.slice(0, limit);
  return (
    <section className="intel-section">
      <h4>Anomalous Moves & Post-Event Impact</h4>
      <div className="anomalous-list">
        {shown.map((m, i) => (
          <div key={i} className={`anomalous-row ${sevClass(m.magnitude_sigma)}`}>
            <span className="anom-date">{m.date}</span>
            <span className={`anom-change ${m.direction === "up" ? "pos" : "neg"}`}>
              {pct(m.change_pct, true)}
            </span>
            <span className="anom-sigma">{m.magnitude_sigma.toFixed(1)}σ</span>
            <span className="anom-price">₹{m.close.toFixed(2)}</span>
            {m.volume_ratio && <span className="anom-vol">{m.volume_ratio.toFixed(1)}× vol</span>}
            <span className="anom-post" title="Post-event returns: 1D / 1W / 2W / 1M">
              {pct(m.return_1d, true)} → {pct(m.return_1w, true)} → {pct(m.return_1m, true)}
            </span>
            {m.associated_event && (
              <span className="anom-event" title={m.associated_event}>
                {m.associated_event.length > 40
                  ? m.associated_event.slice(0, 38) + "…"
                  : m.associated_event}
              </span>
            )}
          </div>
        ))}
      </div>
      {moves.length > limit && (
        <button className="show-more" onClick={() => setLimit((l) => l + 8)}>
          Show more ({moves.length - limit} remaining)
        </button>
      )}
    </section>
  );
}

function PatternsSection({ patterns }: { patterns: PatternDiscovery[] }) {
  return (
    <section className="intel-section">
      <h4>Discovered Patterns</h4>
      <div className="card-grid">
        {patterns.map((p, i) => (
          <div key={i} className="pattern-card">
            <div className="pattern-type">{p.pattern_type.replace(/_/g, " ")}</div>
            <p className="pattern-desc">{p.description}</p>
            <div className="pattern-meta">
              {confBar(p.confidence)}
              <span>{p.observations} observations</span>
              <span className="pattern-period">{p.period_analyzed}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function RareEventsSection({ events }: { events: RareEvent[] }) {
  return (
    <section className="intel-section">
      <h4>Rare Event Memory</h4>
      <div className="rare-list">
        {events.map((e, i) => (
          <div key={i} className={`rare-row sev-${e.severity}`}>
            <span className="rare-date">{e.date}</span>
            <span className={`rare-change ${e.change_pct >= 0 ? "pos" : "neg"}`}>
              {pct(e.change_pct, true)}
            </span>
            <span className={`rare-badge badge-${e.severity}`}>{e.severity}</span>
            <span className="rare-desc">{e.description}</span>
            {e.recovery_days !== null && (
              <span className="rare-recovery">
                Recovery: {e.recovery_days} days
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function ExpectedSection({ items }: { items: ExpectedVsActual[] }) {
  return (
    <section className="intel-section">
      <h4>Expected vs. Actual</h4>
      <div className="card-grid">
        {items.map((e, i) => (
          <div key={i} className={`expected-card dev-${e.deviation}`}>
            <div className={`expected-badge badge-${e.deviation}`}>{e.deviation}</div>
            <p className="expected-desc">{e.description}</p>
            <div className="expected-meta">
              <span>Hist. avg: {pct(e.historical_avg_move, true)}</span>
              <span>{e.historical_observations} observations</span>
              {e.current_move !== null && (
                <span>Current: {pct(e.current_move, true)}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── main page ────────────────────────────────────────────────────────

export function IntelligencePage() {
  const [input, setInput] = useState("");
  const [data, setData] = useState<StockIntelligence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);

  useEffect(() => {
    api.getWatchlist().then(setWatchlist).catch(() => {});
  }, []);

  const analyze = (raw: string) => {
    const s = raw.trim().toUpperCase();
    if (!s) return;
    const sym = s.includes(".") ? s : `${s}.NS`;
    setInput(sym);
    setLoading(true);
    setError(null);
    setData(null);
    api
      .getIntelligence(sym)
      .then(setData)
      .catch((err) => setError(err.message ?? "Analysis failed"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="intel-page">
      <div className="intel-header">
        <h2>Market Intelligence</h2>
        <p className="intel-subtitle">
          Historical behavior analysis, pattern discovery &amp; regime detection
        </p>
      </div>

      <div className="intel-selector">
        <div className="intel-search">
          <input
            type="text"
            placeholder="Enter symbol (e.g., RELIANCE)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && analyze(input)}
          />
          <button onClick={() => analyze(input)} disabled={loading}>
            {loading ? "Analyzing…" : "Analyze"}
          </button>
        </div>
        {watchlist && watchlist.stocks.length > 0 && (
          <div className="intel-quickselect">
            {watchlist.stocks.map((s) => (
              <button
                key={s.symbol}
                className="quick-btn"
                onClick={() => analyze(s.symbol)}
              >
                {s.symbol.replace(".NS", "")}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <p className="status-text">
          Fetching up to 5 years of historical data and running analysis…
        </p>
      )}
      {error && <p className="status-text error">{error}</p>}

      {data && !loading && (
        <div className="intel-dashboard">
          <div className="intel-stock-header">
            <h3>{data.company_name || data.symbol}</h3>
            <div className="intel-meta">
              <span className="meta-sym">{data.symbol}</span>
              {data.sector && <span className="badge-sector">{data.sector}</span>}
              {data.current_price != null && (
                <span className="meta-price">₹{data.current_price.toFixed(2)}</span>
              )}
              <span className="meta-range">
                {data.total_trading_days} days ({data.data_start} → {data.data_end})
              </span>
            </div>
          </div>

          {data.horizons.length > 0 && <HorizonsSection horizons={data.horizons} />}
          {data.regime_changes.length > 0 && <RegimeSection changes={data.regime_changes} />}
          {data.anomalous_moves.length > 0 && <AnomalousSection moves={data.anomalous_moves} />}
          {data.patterns.length > 0 && <PatternsSection patterns={data.patterns} />}
          {data.rare_events.length > 0 && <RareEventsSection events={data.rare_events} />}
          {data.expected_vs_actual.length > 0 && (
            <ExpectedSection items={data.expected_vs_actual} />
          )}

          <div className="intel-footer">
            <p className="confidence-note">{data.confidence_note}</p>
            <p className="data-source">
              Source: {data.data_source} · Generated:{" "}
              {new Date(data.generated_at).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="empty-state">
          <h3>Select a stock to analyze</h3>
          <p>
            Enter a symbol or select from your watchlist to see multi-horizon
            behavior, anomalous moves, discovered patterns and regime changes.
          </p>
        </div>
      )}
    </div>
  );
}
