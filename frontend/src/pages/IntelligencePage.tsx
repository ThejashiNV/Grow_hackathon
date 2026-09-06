import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../services/api";
import type {
  AnomalousMove,
  BenchmarkComparison,
  EventCluster,
  ExpectedVsActual,
  HorizonAnalysis,
  MLAnomaly,
  NewsItem,
  PatternDiscovery,
  RareEvent,
  RegimeChange,
  StockBaseline,
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

function sevIcon(s: string) {
  if (s === "critical") return "!!";
  if (s === "high") return "!";
  return "·";
}

function categoryColor(cat: string): string {
  if (cat === "macro") return "var(--intel-amber)";
  if (cat === "sector") return "var(--intel-cyan)";
  if (cat === "commodity") return "#c084fc";
  if (cat === "geopolitical") return "var(--intel-red)";
  if (cat === "global") return "#60a5fa";
  return "var(--intel-text-dim)";
}

function EventClustersSection({ clusters }: { clusters: EventCluster[] }) {
  if (!clusters.length) return null;
  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Event Intelligence</h4>
        <span className="section-count">{clusters.length} clusters</span>
      </div>
      <div className="event-clusters-list">
        {clusters.map((c) => (
          <div key={c.cluster_id} className={`event-cluster-card sev-${c.severity}`}>
            <div className="ec-header">
              <span className={`ec-sev-badge badge-${c.severity}`}>
                {sevIcon(c.severity)} {c.severity}
              </span>
              <span className="ec-type" style={{ color: categoryColor(c.category) }}>
                {c.event_type.replace(/_/g, " ")}
              </span>
              <span className="ec-category">{c.category}</span>
              <span className="ec-impact">Impact: {c.impact_score.toFixed(0)}</span>
            </div>
            <div className="ec-title">{c.canonical_title}</div>
            <div className="ec-meta">
              <span>{c.article_count} article{c.article_count > 1 ? "s" : ""}</span>
              {c.sources.length > 0 && <span> · {c.sources.slice(0, 3).join(", ")}</span>}
              {c.first_seen && <span> · {timeAgo(c.first_seen)}</span>}
            </div>
            {c.affected_symbols.length > 1 && (
              <div className="ec-affected">
                Also affects: {c.affected_symbols.filter((s) => s !== clusters[0]?.affected_symbols[0]).join(", ")}
              </div>
            )}
            {c.event_impact && c.event_impact.reactions.length > 0 && (
              <div className="ec-impact-detail">
                <div className="ec-reactions">
                  {c.event_impact.reactions.map((r) => (
                    <div key={r.window} className="ec-reaction">
                      <span className="ec-rw-label">{r.window}</span>
                      <span className={`ec-rw-val ${r.stock_return_pct >= 0 ? "pos" : "neg"}`}>
                        {r.stock_return_pct >= 0 ? "+" : ""}{r.stock_return_pct.toFixed(2)}%
                      </span>
                      {r.volume_ratio != null && (
                        <span className="ec-rw-vol">{r.volume_ratio.toFixed(1)}x vol</span>
                      )}
                    </div>
                  ))}
                </div>
                {c.event_impact.historical_event_count > 0 && (
                  <div className="ec-hist-avg">
                    Historical avg: {c.event_impact.historical_avg_reaction_5d != null
                      ? `5d ${c.event_impact.historical_avg_reaction_5d >= 0 ? "+" : ""}${c.event_impact.historical_avg_reaction_5d.toFixed(2)}%`
                      : ""}
                    {c.event_impact.historical_avg_reaction_20d != null
                      ? ` · 20d ${c.event_impact.historical_avg_reaction_20d >= 0 ? "+" : ""}${c.event_impact.historical_avg_reaction_20d.toFixed(2)}%`
                      : ""}
                    <span className="ec-hist-count"> ({c.event_impact.historical_event_count} similar)</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function BaselineSection({ baseline }: { baseline: StockBaseline | null }) {
  if (!baseline) return null;
  const regimeColor = baseline.regime_label === "EXTREME" ? "var(--intel-red)"
    : baseline.regime_label === "UNUSUAL" ? "var(--intel-amber)"
    : baseline.regime_label === "ELEVATED" ? "var(--intel-cyan)"
    : "var(--intel-green)";

  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Stock Behavior Baseline</h4>
        <span className="baseline-regime" style={{ color: regimeColor }}>
          {baseline.regime_label}
        </span>
      </div>
      <div className="baseline-grid">
        <div className="baseline-metric">
          <div className="bl-label">Ann. Volatility</div>
          <div className="bl-value">{baseline.normal_daily_vol_ann.toFixed(1)}%</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Vol Percentile</div>
          <div className="bl-value">{baseline.volatility_percentile.toFixed(0)}%</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Daily Range (med)</div>
          <div className="bl-value">{baseline.normal_daily_range_pct.toFixed(2)}%</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Daily Range (p95)</div>
          <div className="bl-value">{baseline.normal_daily_range_p95.toFixed(2)}%</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Vol Clustering</div>
          <div className="bl-value">{baseline.volume_clustering_score.toFixed(2)}</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Return Momentum</div>
          <div className="bl-value">{baseline.return_persistence.toFixed(3)}</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Gap Frequency</div>
          <div className="bl-value">{(baseline.gap_frequency * 100).toFixed(1)}%</div>
        </div>
        <div className="baseline-metric">
          <div className="bl-label">Median Volume</div>
          <div className="bl-value">{fmtVol(baseline.normal_volume_median)}</div>
        </div>
      </div>
    </section>
  );
}

function BehaviorRadar({ data }: { data: StockIntelligence }) {
  const axes = [
    "Volatility",
    "Momentum",
    "Volume Activity",
    "Anomaly Level",
    "Event Density",
    "Market Sensitivity",
  ];

  // Compute normalized values (0-100)
  const volatility = data.stock_baseline
    ? Math.min(100, (data.stock_baseline.normal_daily_vol_ann / 50) * 100)
    : 0;

  const momentum =
    (data.horizons ?? []).length > 0
      ? Math.abs(data.horizons[data.horizons.length - 1].momentum_score)
      : 0;

  const volumeActivity = data.stock_baseline
    ? Math.min(100, data.stock_baseline.volume_clustering_score * 100)
    : 0;

  const anomalyLevel =
    (data.ml_anomalies ?? []).length > 0
      ? data.ml_anomalies[0].composite_score
      : 0;

  const eventDensity = Math.min(
    100,
    (((data.news ?? []).length + (data.event_clusters ?? []).length) / 20) * 100
  );

  const benchBeta =
    (data.benchmark_comparison ?? []).length > 0 &&
    data.benchmark_comparison[0].beta != null
      ? data.benchmark_comparison[0].beta
      : 1.0;
  const marketSensitivity = Math.min(100, (benchBeta / 2) * 100);

  const values = [
    Math.max(10, volatility),
    Math.max(10, momentum),
    Math.max(10, volumeActivity),
    Math.max(10, anomalyLevel),
    Math.max(10, eventDensity),
    Math.max(10, marketSensitivity),
  ];

  const cx = 125;
  const cy = 125;
  const maxR = 85;
  const labelR = maxR + 20;
  const n = axes.length;
  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  const pointAt = (axis: number, fraction: number) => {
    const angle = startAngle + axis * angleStep;
    return {
      x: cx + maxR * fraction * Math.cos(angle),
      y: cy + maxR * fraction * Math.sin(angle),
    };
  };

  const labelAt = (axis: number) => {
    const angle = startAngle + axis * angleStep;
    return {
      x: cx + labelR * Math.cos(angle),
      y: cy + labelR * Math.sin(angle),
    };
  };

  const polyPoints = (fraction: number) =>
    Array.from({ length: n }, (_, i) => {
      const p = pointAt(i, fraction);
      return `${p.x},${p.y}`;
    }).join(" ");

  const dataPoints = values
    .map((v, i) => {
      const p = pointAt(i, v / 100);
      return `${p.x},${p.y}`;
    })
    .join(" ");

  const guides = [0.25, 0.5, 0.75, 1.0];

  return (
    <section className="intel-section">
      <div className="intel-section-header">
        <h4>Behavior Signature</h4>
      </div>
      <div className="behavior-radar-wrap">
        <svg viewBox="0 0 250 250" className="behavior-radar-svg">
          {/* Concentric guide polygons */}
          {guides.map((g) => (
            <polygon
              key={g}
              points={polyPoints(g)}
              fill="none"
              stroke="#2a3340"
              strokeWidth="1"
            />
          ))}
          {/* Axis lines */}
          {Array.from({ length: n }, (_, i) => {
            const p = pointAt(i, 1);
            return (
              <line
                key={i}
                x1={cx}
                y1={cy}
                x2={p.x}
                y2={p.y}
                stroke="#2a3340"
                strokeWidth="1"
              />
            );
          })}
          {/* Guide labels */}
          {guides.map((g) => (
            <text
              key={`gl-${g}`}
              x={cx + 2}
              y={cy - maxR * g - 2}
              fill="#3d4a5c"
              fontSize="7"
              fontFamily="'Inter', sans-serif"
            >
              {Math.round(g * 100)}
            </text>
          ))}
          {/* Data polygon */}
          <polygon
            points={dataPoints}
            fill="rgba(0,212,170,0.2)"
            stroke="#00d4aa"
            strokeWidth="2"
          />
          {/* Data vertices */}
          {values.map((v, i) => {
            const p = pointAt(i, v / 100);
            return (
              <circle
                key={i}
                cx={p.x}
                cy={p.y}
                r="3"
                fill="#00d4aa"
              />
            );
          })}
          {/* Axis labels */}
          {axes.map((label, i) => {
            const lp = labelAt(i);
            const angle = startAngle + i * angleStep;
            const deg = (angle * 180) / Math.PI;
            let anchor = "middle";
            if (deg > -80 && deg < 80) anchor = "start";
            else if (deg > 100 || deg < -100) anchor = "end";
            return (
              <text
                key={label}
                x={lp.x}
                y={lp.y}
                textAnchor={anchor}
                dominantBaseline="central"
                fill="#8b9ab0"
                fontSize="9"
                fontFamily="'Inter', sans-serif"
              >
                {label}
              </text>
            );
          })}
        </svg>
      </div>
    </section>
  );
}

function PriceSparkline({ moves }: { moves: AnomalousMove[] }) {
  if (!moves.length) return null;

  const sorted = [...moves].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const dates = sorted.map((m) => new Date(m.date).getTime());
  const prices = sorted.map((m) => m.close);

  const minDate = Math.min(...dates);
  const maxDate = Math.max(...dates);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  const padX = 8;
  const padY = 10;
  const w = 600;
  const h = 100;
  const plotW = w - padX * 2;
  const plotH = h - padY * 2;
  const dateRange = maxDate - minDate || 1;
  const priceRange = maxPrice - minPrice || 1;

  const toX = (d: number) => padX + ((d - minDate) / dateRange) * plotW;
  const toY = (p: number) => padY + plotH - ((p - minPrice) / priceRange) * plotH;

  const pathD = sorted
    .map((m, i) => {
      const x = toX(dates[i]);
      const y = toY(m.close);
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  return (
    <div className="price-sparkline-wrap">
      <svg
        width="100%"
        height="120"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        className="price-sparkline-svg"
      >
        <path d={pathD} fill="none" stroke="#00d4aa" strokeWidth="1.5" />
        {sorted.map((m, i) => {
          const x = toX(dates[i]);
          const y = toY(m.close);
          const r = Math.min(8, Math.max(3, m.magnitude_sigma * 1.5));
          const color = m.direction === "down" ? "#e84057" : "#00c853";
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={r}
              fill={color}
              opacity="0.85"
            >
              <title>
                {m.date}: {m.change_pct >= 0 ? "+" : ""}{m.change_pct.toFixed(2)}% ({m.magnitude_sigma.toFixed(1)}{"σ"})
              </title>
            </circle>
          );
        })}
      </svg>
    </div>
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
  const location = useLocation();
  const [input, setInput] = useState("");
  const [data, setData] = useState<StockIntelligence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);

  useEffect(() => {
    api.getWatchlist().then(setWatchlist).catch(() => {});
  }, []);

  // Auto-load symbol from ?s= query param (e.g. from watchlist click)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sym = params.get("s");
    if (sym && sym !== data?.symbol) {
      analyze(sym);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

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
            {(data.anomalous_moves ?? []).length > 0 && (
              <PriceSparkline moves={data.anomalous_moves} />
            )}
          </div>

          {(data.ml_anomalies ?? []).length > 0 && <AnomalyHero anomalies={data.ml_anomalies} />}

          <BehaviorRadar data={data} />

          {(data.event_clusters ?? []).length > 0 && <EventClustersSection clusters={data.event_clusters} />}

          <BaselineSection baseline={data.stock_baseline ?? null} />

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
