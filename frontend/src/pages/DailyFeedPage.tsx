import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { DailyFeed, WatchlistIntelItem } from "../types/api";
import "./DailyFeedPage.css";

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function alertIcon(type: string) {
  if (type === "anomaly") return "⚠️";
  if (type === "regime_change") return "🔄";
  if (type === "news_cluster") return "📰";
  if (type === "event_cluster") return "🔗";
  return "ℹ️";
}

function ecCategoryColor(cat: string) {
  if (cat === "macro") return "#3b82f6";
  if (cat === "sector") return "#8b5cf6";
  if (cat === "commodity") return "#f59e0b";
  if (cat === "geopolitical") return "#ef4444";
  if (cat === "global") return "#06b6d4";
  return "#6e7681";
}

function ecSevLabel(sev: string) {
  if (sev === "critical") return "CRIT";
  if (sev === "high") return "HIGH";
  if (sev === "medium") return "MED";
  return "LOW";
}

function impactClass(score: number) {
  if (score >= 60) return "high";
  if (score >= 30) return "medium";
  return "low";
}

function changeTypeIcon(type: string) {
  if (type === "anomaly_change") return "⚠";
  if (type === "regime_change") return "⇄";
  if (type === "price_move") return "↕";
  if (type === "new_news") return "●";
  return "•";
}

export function DailyFeedPage() {
  const [feed, setFeed] = useState<DailyFeed | null>(null);
  const [intelSummary, setIntelSummary] = useState<WatchlistIntelItem[]>([]);
  const [totalNewChanges, setTotalNewChanges] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getDailyFeed(),
      api.getWatchlistIntelligence(),
    ])
      .then(([f, intel]) => {
        setFeed(f);
        setIntelSummary(intel.items);
        setTotalNewChanges(intel.total_new_changes ?? 0);
      })
      .catch(err => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      Promise.all([
        api.getDailyFeed(),
        api.getWatchlistIntelligence(),
      ]).then(([f, intel]) => {
        setFeed(f);
        setIntelSummary(intel.items);
        setTotalNewChanges(intel.total_new_changes ?? 0);
      }).catch(() => {});
    }, 180_000);
    return () => clearInterval(id);
  }, []);

  const handleMarkSeen = async () => {
    setMarking(true);
    try {
      await api.markIntelSeen();
      const intel = await api.getWatchlistIntelligence();
      setIntelSummary(intel.items);
      setTotalNewChanges(intel.total_new_changes ?? 0);
    } catch { /* ignore */ }
    setMarking(false);
  };

  if (loading) {
    return (
      <div className="daily-feed">
        <div className="df-loading"><div className="df-spinner" /> Loading today's intelligence...</div>
      </div>
    );
  }

  if (error) {
    return <div className="daily-feed"><p className="wl-error">{error}</p></div>;
  }

  if (!feed) {
    return <div className="daily-feed"><div className="df-empty">No data available.</div></div>;
  }

  const hasAlerts = feed.alerts.length > 0;
  const hasMovers = feed.movers.length > 0;
  const hasNews = feed.news_digest.length > 0;
  const hasSectors = Object.keys(feed.sector_summary).length > 0;
  const hasEventClusters = (feed.event_clusters ?? []).length > 0;
  const hasChanges = (feed.recent_changes ?? []).length > 0;
  const isEmpty = !hasAlerts && !hasMovers && !hasNews && !hasEventClusters;

  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "short", year: "numeric" });

  const stocksWithChanges = intelSummary.filter(
    i => (i.changes_since_last_check?.length ?? 0) > 0 || i.never_seen
  );

  return (
    <div className="daily-feed">
      <div className="df-header">
        <h2>Today's Intelligence</h2>
        <span className="df-date">{today}</span>
        {feed.refresh_status && (
          <span className="df-pipeline">
            <span className="df-pulse" />
            Pipeline {feed.refresh_status.running ? "active" : "idle"}
            {feed.refresh_status.last_run && ` · ${timeAgo(feed.refresh_status.last_run)}`}
          </span>
        )}
      </div>

      {/* What Changed Since Last Check — top of page */}
      {totalNewChanges > 0 && (
        <div className="df-whats-new">
          <div className="df-whats-new-header">
            <div className="df-whats-new-title">
              <span className="df-whats-new-count">{totalNewChanges}</span>
              <span>{totalNewChanges === 1 ? "change" : "changes"} since your last check</span>
            </div>
            <button
              className="df-mark-seen-btn"
              onClick={handleMarkSeen}
              disabled={marking}
            >
              {marking ? "Marking..." : "Mark reviewed"}
            </button>
          </div>
          <div className="df-whats-new-list">
            {stocksWithChanges.map(item => (
              <div key={item.symbol} className="df-whats-new-stock">
                <div className="df-whats-new-sym">
                  {item.symbol.replace(".NS", "")}
                  {item.never_seen && <span className="df-new-tag">NEW</span>}
                </div>
                {(item.changes_since_last_check ?? []).slice(0, 3).map((c, i) => (
                  <div key={i} className={`df-whats-new-change ${c.severity}`}>
                    <span className="df-wnc-icon">{changeTypeIcon(c.type)}</span>
                    <span className="df-wnc-detail">{c.detail}</span>
                    {c.timestamp && <span className="df-wnc-time">{timeAgo(c.timestamp)}</span>}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {isEmpty && totalNewChanges === 0 && (
        <div className="df-empty">
          <p>No significant intelligence today. Your watchlist is quiet.</p>
          <p>Add stocks via the Watchlist tab to start tracking.</p>
        </div>
      )}

      {/* Alerts */}
      {hasAlerts && (
        <div className="df-section">
          <h3 className="df-section-title">
            Alerts Requiring Attention <span className="count">{feed.alerts.length}</span>
          </h3>
          <div className="df-alerts">
            {feed.alerts.map((a, i) => (
              <div key={i} className={`df-alert ${a.severity}`}>
                <span className="df-alert-icon">{alertIcon(a.type)}</span>
                <div className="df-alert-body">
                  <div className="df-alert-header">
                    <span className="df-alert-sym">{a.symbol.replace(".NS", "")}</span>
                    {a.company_name && <span className="df-alert-name">{a.company_name}</span>}
                  </div>
                  <div className="df-alert-detail">{a.detail}</div>
                </div>
                <span className="df-alert-score">{Math.round(a.score)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event Clusters */}
      {hasEventClusters && (
        <div className="df-section">
          <h3 className="df-section-title">
            Event Clusters <span className="count">{feed.event_clusters.length}</span>
          </h3>
          <div className="df-ec-list">
            {feed.event_clusters.map(ec => (
              <div key={ec.cluster_id} className={`df-ec-card ${ec.severity}`}>
                <div className="df-ec-top">
                  <span className={`df-ec-sev ${ec.severity}`}>{ecSevLabel(ec.severity)}</span>
                  <span className="df-ec-type">{ec.event_type.replace(/_/g, " ")}</span>
                  <span className="df-ec-cat" style={{ color: ecCategoryColor(ec.category) }}>
                    {ec.category}
                  </span>
                  <span className="df-ec-impact">{Math.round(ec.impact_score)}</span>
                </div>
                <div className="df-ec-title">{ec.canonical_title}</div>
                <div className="df-ec-meta">
                  <span className="df-ec-sym">{ec.symbol.replace(".NS", "")}</span>
                  <span>{ec.article_count} article{ec.article_count !== 1 ? "s" : ""}</span>
                  {ec.first_seen && <span>{timeAgo(ec.first_seen)}</span>}
                </div>
                {ec.affected_symbols.length > 1 && (
                  <div className="df-ec-affected">
                    Affects: {ec.affected_symbols.map(s => s.replace(".NS", "")).join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Movers */}
      {hasMovers && (
        <div className="df-section">
          <h3 className="df-section-title">
            Top Movers <span className="count">{feed.movers.length}</span>
          </h3>
          <div className="df-movers">
            {feed.movers.map(m => (
              <div key={m.symbol} className="df-mover">
                <div className="df-mover-sym">{m.symbol.replace(".NS", "")}</div>
                <div className={`df-mover-change ${m.direction}`}>
                  {m.change_pct >= 0 ? "+" : ""}{m.change_pct.toFixed(2)}%
                </div>
                {m.current_price != null && (
                  <div className="df-mover-price">
                    {"₹"}{m.current_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* News Digest */}
      {hasNews && (
        <div className="df-section">
          <h3 className="df-section-title">
            News Digest <span className="count">{feed.news_digest.length}</span>
          </h3>
          <div className="df-news-list">
            {feed.news_digest.slice(0, 15).map((n, i) => (
              <div key={i} className="df-news-item">
                <span className={`df-news-impact ${impactClass(n.impact_score)}`}>
                  {n.impact_score}
                </span>
                <div className="df-news-body">
                  <div className="df-news-title">
                    {n.link ? <a href={n.link} target="_blank" rel="noopener noreferrer">{n.title}</a> : n.title}
                  </div>
                  <div className="df-news-meta">
                    <span className="df-news-sym">{n.symbol.replace(".NS", "")}</span>
                    {n.publisher && <span>{n.publisher}</span>}
                    {n.published_at && <span>{timeAgo(n.published_at)}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sector Summary */}
      {hasSectors && (
        <div className="df-section">
          <h3 className="df-section-title">Sector Overview</h3>
          <div className="df-sectors">
            {Object.entries(feed.sector_summary).map(([sector, data]) => (
              <div key={sector} className="df-sector-card">
                <div className="df-sector-name">{sector}</div>
                <div className="df-sector-stats">
                  {data.avg_change_pct != null && (
                    <span className={`df-sector-change ${data.avg_change_pct >= 0 ? "up" : "down"}`}>
                      {data.avg_change_pct >= 0 ? "+" : ""}{data.avg_change_pct.toFixed(2)}%
                    </span>
                  )}
                  <span>Anomaly: {data.max_anomaly}</span>
                </div>
                <div className="df-sector-stocks">
                  {data.stocks.map(s => s.symbol.replace(".NS", "")).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Changes from Pipeline */}
      {hasChanges && (
        <div className="df-section">
          <h3 className="df-section-title">
            Recent Changes Detected <span className="count">{feed.recent_changes.length}</span>
          </h3>
          <div className="df-changes">
            {(feed.recent_changes ?? []).map((c, i) => (
              <div key={i} className="df-change-item">
                <span className={`df-change-sev ${c.severity}`} />
                <span className="df-change-sym">{c.symbol.replace(".NS", "")}</span>
                <span className="df-change-detail">{c.detail}</span>
                {c.timestamp && <span className="df-change-time">{timeAgo(c.timestamp)}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
