import { useEffect, useState } from "react";
import { api } from "../services/api";
import type {
  AnomalousMove,
  BenchmarkComparison,
  ExpectedVsActual,
  HorizonAnalysis,
  MLAnomaly,
  NewsItem,
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

function pct(n: number | null | undefined, signed = false): string {
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
    <span className="conf-bar" title={`${w}%`}>
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

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function scoreClass(score: number): string {
  if (score >= 70) return "score-high";
  if (score >= 40) return "score-mid";
  return "score-low";
}

function signalColor(score: number): string {
  if (score >= 60) return "var(--intel-red)";
  if (score >= 40) return "var(--intel-amber)";
  if (score >= 20) return "var(--intel-cyan)";
  return "var(--intel-text-dim)";
}

// ── sub-components ───────────────────────────────────────────────────

function FreshnessBar({ data }: { data: StockIntelligence }) {
  const f = data.freshness;
  if (!f) return null;

  const items = [
    { label: "Price", status: f.price_data, time: f.price_updated_at },
    { label: "News", status: f.news_data, time: f.news_updated_at },
    { label: "Benchmark", status: f.benchmark_data, time: null },
  ];

  return (
    <div className="freshness-bar">
      {items.map((item) => (
        <div key={item.label} className="freshness-item">
          <span className={`freshness-dot ${item.status === "live" || item.status === "available" ? "live" : item.status === "delayed" ? "delayed" : item.status === "stale" ? "stale" : "unavailable"}`} />
          <span>{item.label}: {item.status}</span>
          {item.time && <span style={{ opacity: 0.6 }}>{timeAgo(item.time)}</span>}
        </div>
      ))}
      {f.cache_hit && <div className="freshness-item" style={{ color: "var(--intel-text-dim)" }}>CACHED</div>}
      <button className="refresh-btn" onClick={() => window.dispatchEvent(new CustomEvent("intel-refresh"))}>
        ↻ Refresh
      </button>
    </div>
  );
}

function AnomalyHero({ anomalies }: { anomalies: MLAnomaly[] }) {
  const latest = anomalies[0];
  if (!latest) return null;

  return (
    <div className="anomaly-hero">
      <div className="anomaly-hero-top">
        <div
          className={`anomaly-score-ring ${scoreClass(latest.composite_score)}`}
          style={{ "--score-pct": `${latest.composite_score}%` } as React.CSSProperties}
        >
          <div className="anomaly-score-inner">
            {latest.composite_score.toFixed(0)}
          </div>
        </div>
        <div>
          <div className="anomaly-hero-label">Anomaly Score</div>
          <div className="anomaly-hero-title">
            {latest.composite_score >= 70
              ? "Highly Anomalous Behavior"
              : latest.composite_score >= 40
              ? "Notable Anomaly Detected"
              : "Behavior Within Normal Range"}
          </div>
        </div>
      </div>
      <div className="anomaly-signals">
        {latest.signals
          .filter((s) => s.score >= 15)
          .sort((a, b) => b.score - a.score)
          .slice(0, 6)
          .map((s, i) => (
            <div key={i} className="anomaly-signal-chip">
              <span className="signal-dot" style={{ background: signalColor(s.score) }} />
              {s.description}
            </div>
          ))}
      </div>
    </div>
  );
}

function NewsSection({ news }: { news: NewsItem[] }) {
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? news : news.slice(0, 8);

  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Live News & Events</h4>
        <span className="section-count">{news.length} items</span>
      </div>
      <div className="news-list">
        {shown.map((n) => (
          <div key={n.news_id} className={`news-item ${n.impact_score >= 50 ? "high-impact" : ""}`}>
            <span className={`news-impact ${n.impact_score >= 60 ? "impact-high" : n.impact_score >= 35 ? "impact-med" : "impact-low"}`}>
              {n.impact_score.toFixed(0)}
            </span>
            <div className="news-content">
              {n.link ? (
                <a className="news-title" href={n.link} target="_blank" rel="noopener noreferrer">{n.title}</a>
              ) : (
                <span className="news-title">{n.title}</span>
              )}
              <div className="news-meta">
                <span className="news-type-badge">{n.event_type.replace(/_/g, " ")}</span>
                {n.publisher && <span> · {n.publisher}</span>}
                {n.published_at && <span> · {timeAgo(n.published_at)}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      {news.length > 8 && !showAll && (
        <button className="show-more" onClick={() => setShowAll(true)}>
          Show all ({news.length - 8} more)
        </button>
      )}
    </section>
  );
}

function BenchmarkSection({ benchmarks }: { benchmarks: BenchmarkComparison[] }) {
  if (!benchmarks.length) return null;
  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Benchmark Comparison</h4>
      </div>
      <div className="benchmark-grid">
        {benchmarks.map((b) => (
          <div key={b.benchmark_symbol} className="benchmark-card">
            <div className="benchmark-name">{b.benchmark_name}</div>
            <div className="benchmark-values">
              <div>
                <div className="bench-metric-label">Stock</div>
                <div className={`bench-metric-value ${b.stock_return_pct >= 0 ? "pos" : "neg"}`}>{pct(b.stock_return_pct, true)}</div>
              </div>
              <div>
                <div className="bench-metric-label">Benchmark</div>
                <div className={`bench-metric-value ${b.benchmark_return_pct >= 0 ? "pos" : "neg"}`}>{pct(b.benchmark_return_pct, true)}</div>
              </div>
              <div>
                <div className="bench-metric-label">Alpha</div>
                <div className={`bench-metric-value ${b.outperformance_pct >= 0 ? "pos" : "neg"}`}>{pct(b.outperformance_pct, true)}</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "1rem", marginTop: "0.4rem", fontSize: "0.65rem", color: "var(--intel-text-dim)", fontFamily: "'JetBrains Mono', monospace" }}>
              {b.correlation != null && <span>Corr: {b.correlation.toFixed(2)}</span>}
              {b.beta != null && <span>Beta: {b.beta.toFixed(2)}</span>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function HorizonsSection({ horizons }: { horizons: HorizonAnalysis[] }) {
  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Multi-Horizon Behavior</h4>
      </div>
      <div className="horizons-table-wrap">
        <table className="horizons-table">
          <thead>
            <tr>
              <th>Period</th>
              <th>Return</th>
              <th>Vol</th>
              <th>Max DD</th>
              <th>Trend</th>
              <th>Mom.</th>
              <th>vs Market</th>
              <th>vs Sector</th>
              <th>Lg Moves</th>
              <th>Avg Vol</th>
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
                <td className={h.relative_performance_pct != null ? (h.relative_performance_pct >= 0 ? "outperform" : "underperform") : ""}>
                  {h.relative_performance_pct != null ? pct(h.relative_performance_pct, true) : "—"}
                </td>
                <td>
                  {h.sector_return_pct != null ? pct(h.sector_return_pct, true) : "—"}
                </td>
                <td>{h.large_move_count}</td>
                <td>{fmtVol(h.avg_daily_volume)}</td>
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
      <div className="intel-section-header">
        <h4>Behavior Regime Changes</h4>
      </div>
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
      <div className="intel-section-header">
        <h4>Anomalous Moves & Impact</h4>
        <span className="section-count">{moves.length} detected</span>
      </div>
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
            {m.abnormal_return_pct != null && (
              <span className={`anom-abnormal ${m.abnormal_return_pct >= 0 ? "pos" : "neg"}`} title="Abnormal return vs sector">
                α {pct(m.abnormal_return_pct, true)}
              </span>
            )}
            <span className="anom-post" title="Post-event: 1D → 1W → 1M">
              {pct(m.return_1d, true)} → {pct(m.return_1w, true)} → {pct(m.return_1m, true)}
            </span>
            {m.associated_event && (
              <span className="anom-event" title={m.associated_event}>
                {m.associated_event.length > 35 ? m.associated_event.slice(0, 33) + "…" : m.associated_event}
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
      <div className="intel-section-header">
        <h4>Discovered Patterns</h4>
        <span className="section-count">{patterns.length}</span>
      </div>
      <div className="card-grid">
        {patterns.map((p, i) => (
          <div key={i} className="pattern-card">
            <div className="pattern-type">{p.pattern_type.replace(/_/g, " ")}</div>
            <p className="pattern-desc">{p.description}</p>
            <div className="pattern-meta">
              {confBar(p.confidence)}
              <span className={`pattern-strength ${p.evidence_strength === "strong" ? "strength-strong" : p.evidence_strength === "moderate" ? "strength-moderate" : "strength-weak"}`}>
                {p.evidence_strength}
              </span>
              <span>{p.observations} obs</span>
              {!p.is_periodic && <span style={{ color: "var(--intel-cyan)" }}>non-periodic</span>}
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
      <div className="intel-section-header">
        <h4>Rare Event Memory</h4>
        <span className="section-count">{events.length}</span>
      </div>
      <div className="rare-list">
        {events.map((e, i) => (
          <div key={i} className="rare-row">
            <span className="rare-date">{e.date}</span>
            <span className={`rare-change ${e.change_pct >= 0 ? "pos" : "neg"}`}>
              {pct(e.change_pct, true)}
            </span>
            <span className={`rare-badge badge-${e.severity}`}>{e.severity}</span>
            <span className="rare-desc">{e.description}</span>
            {e.recovery_days !== null && (
              <span className="rare-recovery">Recovery: {e.recovery_days}d</span>
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
      <div className="intel-section-header">
        <h4>Expected vs. Actual</h4>
      </div>
      <div className="card-grid">
        {items.map((e, i) => (
          <div key={i} className={`expected-card dev-${e.deviation}`}>
            <div className={`expected-badge badge-${e.deviation}`}>{e.deviation}</div>
            <p className="expected-desc">{e.description}</p>
            <div className="expected-meta">
              <span>Hist avg: {pct(e.historical_avg_move, true)}</span>
              <span>{e.historical_observations} obs</span>
              {e.current_move !== null && <span>Current: {pct(e.current_move, true)}</span>}
              {e.historical_median !== null && <span>Median: {pct(e.historical_median, true)}</span>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CompanyContext({ data }: { data: StockIntelligence }) {
  const p = data.company_profile;
  if (!p) return null;
  const segs = p.segments ?? [];
  const comms = p.commodities ?? [];
  const macros = p.macro_factors ?? [];
  if (!segs.length && !comms.length && !macros.length) return null;

  return (
    <div className="company-context">
      {segs.slice(0, 5).map((s) => (
        <span key={s} className="context-chip segment">{s}</span>
      ))}
      {comms.slice(0, 3).map((c) => (
        <span key={c} className="context-chip commodity">{c}</span>
      ))}
      {macros.slice(0, 4).map((m) => (
        <span key={m} className="context-chip macro">{m}</span>
      ))}
    </div>
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

  const analyze = (raw: string, refresh = false) => {
    const s = raw.trim().toUpperCase();
    if (!s) return;
    const sym = s.includes(".") ? s : `${s}.NS`;
    setInput(sym);
    setLoading(true);
    setError(null);
    setData(null);
    api
      .getIntelligence(sym, refresh)
      .then(setData)
      .catch((err) => setError(err.message ?? "Analysis failed"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const handler = () => {
      if (data?.symbol) analyze(data.symbol, true);
    };
    window.addEventListener("intel-refresh", handler);
    return () => window.removeEventListener("intel-refresh", handler);
  });

  return (
    <div className="intel-page">
      <div className="intel-page-header">
        <h2>Market Intelligence</h2>
        <p className="intel-subtitle">
          Behavior analysis · Pattern discovery · Regime detection · News intelligence
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
              <button key={s.symbol} className="quick-btn" onClick={() => analyze(s.symbol)}>
                {s.symbol.replace(".NS", "")}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <p>Fetching market data, news, and benchmarks…</p>
          <p style={{ fontSize: "0.72rem", color: "var(--intel-text-dim)" }}>
            First analysis may take 10-20 seconds
          </p>
        </div>
      )}
      {error && <p className="status-text error">{error}</p>}

      {data && !loading && (
        <div className="intel-dashboard">
          <FreshnessBar data={data} />

          <div className="intel-stock-header">
            <h3>{data.company_name || data.symbol}</h3>
            <div className="intel-meta">
              <span className="meta-sym">{data.symbol}</span>
              {data.sector && <span className="badge-sector">{data.sector}</span>}
              {data.industry && <span className="badge-industry">{data.industry}</span>}
              {data.current_price != null && (
                <span className="meta-price">₹{data.current_price.toFixed(2)}</span>
              )}
              {data.change_pct != null && (
                <span className={`meta-change ${data.change_pct >= 0 ? "pos" : "neg"}`}>
                  {data.change_pct >= 0 ? "+" : ""}{data.change_pct.toFixed(2)}%
                </span>
              )}
              <span className="meta-range">
                {data.total_trading_days} days ({data.data_start} → {data.data_end})
              </span>
            </div>
            <CompanyContext data={data} />
          </div>

          {(data.ml_anomalies ?? []).length > 0 && <AnomalyHero anomalies={data.ml_anomalies} />}

          {(data.news ?? []).length > 0 && <NewsSection news={data.news} />}

          {(data.benchmark_comparison ?? []).length > 0 && <BenchmarkSection benchmarks={data.benchmark_comparison} />}

          {(data.horizons ?? []).length > 0 && <HorizonsSection horizons={data.horizons} />}
          {(data.regime_changes ?? []).length > 0 && <RegimeSection changes={data.regime_changes} />}
          {(data.anomalous_moves ?? []).length > 0 && <AnomalousSection moves={data.anomalous_moves} />}
          {(data.patterns ?? []).length > 0 && <PatternsSection patterns={data.patterns} />}
          {(data.rare_events ?? []).length > 0 && <RareEventsSection events={data.rare_events} />}
          {(data.expected_vs_actual ?? []).length > 0 && <ExpectedSection items={data.expected_vs_actual} />}

          <div className="intel-footer">
            <p className="confidence-note">{data.confidence_note}</p>
            <p className="data-source">
              Source: {data.data_source} · Generated: {timeAgo(data.generated_at)}
              {data.freshness?.cache_hit && " (cached)"}
            </p>
          </div>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="empty-state">
          <h3>Select a stock to analyze</h3>
          <p>
            Enter a symbol or select from your watchlist. The system will analyze multi-horizon
            behavior, detect anomalies, gather live news, compare with benchmarks, discover patterns,
            and identify regime changes.
          </p>
        </div>
      )}
    </div>
  );
}
