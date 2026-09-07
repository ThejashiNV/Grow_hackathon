import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Watchlist, WatchlistIntelItem, RefreshStatus } from "../types/api";
import "./WatchlistPage.css";

function normalizeSymbol(input: string): string {
  const trimmed = input.trim().toUpperCase();
  if (!trimmed) return trimmed;
  return trimmed.includes(".") ? trimmed : `${trimmed}.NS`;
}

function ringClass(score: number) {
  if (score >= 70) return "high";
  if (score >= 40) return "med";
  return "low";
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function changeSeverityIcon(type: string) {
  if (type === "anomaly_change") return "⚠";
  if (type === "regime_change") return "⇄";
  if (type === "price_move") return "↕";
  if (type === "new_news") return "●";
  return "•";
}

export function WatchlistPage() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [intelItems, setIntelItems] = useState<WatchlistIntelItem[]>([]);
  const [totalNewChanges, setTotalNewChanges] = useState(0);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [wl, intel, status] = await Promise.all([
        api.getWatchlist(),
        api.getWatchlistIntelligence(),
        api.getRefreshStatus(),
      ]);
      setWatchlist(wl);
      setIntelItems(intel.items);
      setTotalNewChanges(intel.total_new_changes ?? 0);
      setRefreshStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const [intel, status] = await Promise.all([
          api.getWatchlistIntelligence(),
          api.getRefreshStatus(),
        ]);
        setIntelItems(intel.items);
        setTotalNewChanges(intel.total_new_changes ?? 0);
        setRefreshStatus(status);
      } catch { /* ignore */ }
    }, 120_000);
    return () => clearInterval(id);
  }, []);

  const handleMarkSeen = async () => {
    setMarking(true);
    try {
      await api.markIntelSeen();
      const intel = await api.getWatchlistIntelligence();
      setIntelItems(intel.items);
      setTotalNewChanges(intel.total_new_changes ?? 0);
    } catch { /* ignore */ }
    setMarking(false);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = normalizeSymbol(input);
    if (!symbol) return;
    setAdding(true);
    setError(null);
    try {
      const updated = await api.addStock(symbol);
      setWatchlist(updated);
      setInput("");
      api.getWatchlistIntelligence().then(r => {
        setIntelItems(r.items);
        setTotalNewChanges(r.total_new_changes ?? 0);
      }).catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add stock");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const updated = await api.removeStock(symbol);
      setWatchlist(updated);
      setIntelItems(prev => prev.filter(i => i.symbol !== symbol));
    } catch { /* ignore */ }
  };

  const handleRefresh = async (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRefreshing(symbol);
    try {
      await api.triggerRefresh(symbol);
      const intel = await api.getWatchlistIntelligence();
      setIntelItems(intel.items);
      setTotalNewChanges(intel.total_new_changes ?? 0);
    } catch { /* ignore */ }
    setRefreshing(null);
  };

  const openIntel = (symbol: string) => {
    navigate(`/intelligence?s=${encodeURIComponent(symbol)}`);
  };

  if (loading) {
    return (
      <div className="watchlist-page">
        <div className="wl-loading"><div className="wl-spinner" /> Loading intelligence...</div>
      </div>
    );
  }

  const itemsWithChanges = intelItems.filter(
    i => (i.changes_since_last_check?.length ?? 0) > 0 || i.never_seen
  );

  return (
    <div className="watchlist-page">
      {/* Header with pipeline status */}
      <div className="wl-header">
        <h2>Watchlist Intelligence</h2>
        <div className="wl-pipeline-status">
          <span className={`wl-pulse ${refreshStatus?.running ? "" : "offline"}`} />
          {refreshStatus?.running ? "LIVE" : "OFFLINE"}
          {refreshStatus?.last_run && ` · updated ${timeAgo(refreshStatus.last_run)}`}
          {refreshStatus && ` · ${refreshStatus.stocks_tracked} stocks`}
        </div>
      </div>

      {/* What Changed Banner */}
      {totalNewChanges > 0 && (
        <div className="wl-changes-banner">
          <div className="wl-changes-banner-left">
            <span className="wl-changes-count">{totalNewChanges}</span>
            <span className="wl-changes-label">
              {totalNewChanges === 1 ? "change" : "changes"} since your last check
            </span>
          </div>
          <button
            className="wl-mark-seen-btn"
            onClick={handleMarkSeen}
            disabled={marking}
          >
            {marking ? "Marking..." : "Mark all reviewed"}
          </button>
        </div>
      )}

      {/* Portfolio Stats */}
      {intelItems.length > 0 && (
        <div className="wl-stats-bar">
          <div className="wl-stat">
            <span className="wl-stat-value">{intelItems.length}</span>
            <span className="wl-stat-label">Stocks</span>
          </div>
          <div className="wl-stat">
            <span className={`wl-stat-value ${(() => {
              const changes = intelItems.filter(i => i.change_pct != null).map(i => i.change_pct!);
              const avg = changes.length > 0 ? changes.reduce((a, b) => a + b, 0) / changes.length : 0;
              return avg >= 0 ? "up" : "down";
            })()}`}>
              {(() => {
                const changes = intelItems.filter(i => i.change_pct != null).map(i => i.change_pct!);
                const avg = changes.length > 0 ? changes.reduce((a, b) => a + b, 0) / changes.length : 0;
                return `${avg >= 0 ? "+" : ""}${avg.toFixed(2)}%`;
              })()}
            </span>
            <span className="wl-stat-label">Avg Change</span>
          </div>
          <div className="wl-stat">
            <span className={`wl-stat-value ${(() => {
              const max = Math.max(...intelItems.map(i => i.anomaly_score));
              return max >= 70 ? "alert" : max >= 40 ? "warn" : "";
            })()}`}>
              {Math.round(Math.max(...intelItems.map(i => i.anomaly_score)))}
            </span>
            <span className="wl-stat-label">Peak Anomaly</span>
          </div>
          <div className="wl-stat">
            <span className="wl-stat-value">
              {intelItems.filter(i => i.status === "high_anomaly" || i.status === "event_detected").length}
            </span>
            <span className="wl-stat-label">Active Signals</span>
          </div>
          <div className="wl-stat">
            <span className="wl-stat-value">
              {intelItems.reduce((sum, i) => sum + i.news_count, 0)}
            </span>
            <span className="wl-stat-label">News Items</span>
          </div>
        </div>
      )}

      {/* Add stock */}
      <form className="wl-add-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Add symbol (e.g. TCS, RELIANCE, HDFCBANK)"
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <button type="submit" disabled={adding || !input.trim()}>
          {adding ? "Adding..." : "+ Add"}
        </button>
      </form>
      {error && <p className="wl-error">{error}</p>}

      {/* Empty state */}
      {watchlist && watchlist.stocks.length === 0 && (
        <div className="wl-empty">
          <p>No stocks in your watchlist yet.</p>
          <p>Add TCS, RELIANCE, or HDFCBANK to start tracking intelligence.</p>
        </div>
      )}

      {/* Intelligence cards grid */}
      <div className="wl-grid">
        {intelItems.map(item => {
          const changeCount = item.changes_since_last_check?.length ?? 0;
          const hasChanges = changeCount > 0 || item.never_seen;

          return (
            <div
              key={item.symbol}
              className={`wl-card status-${item.status}${hasChanges ? " has-changes" : ""}`}
              onClick={() => openIntel(item.symbol)}
            >
              {/* Change badge */}
              {hasChanges && (
                <div className="wl-change-badge">
                  {item.never_seen ? "NEW" : `${changeCount} new`}
                </div>
              )}

              <div className="wl-card-main">
                <div className="wl-card-header">
                  <span className="wl-symbol">{item.symbol.replace(".NS", "")}</span>
                  {item.sector && <span className="wl-sector-badge">{item.sector}</span>}
                </div>
                {item.company_name && (
                  <span className="wl-company">{item.company_name}</span>
                )}

                <div className="wl-signals">
                  {(item.signals ?? []).map((sig, i) => {
                    let cls = "wl-signal";
                    if (sig.includes("Anomaly")) cls += " anomaly";
                    else if (sig.includes("Regime")) cls += " regime";
                    else if (sig.includes("news")) cls += " news";
                    else if (sig.includes("Price")) {
                      cls += " price";
                      if (sig.includes("-")) cls += " down";
                    }
                    return <span key={i} className={cls}>{sig}</span>;
                  })}
                </div>

                {/* Inline changes since last check */}
                {changeCount > 0 && (
                  <div className="wl-inline-changes">
                    {item.changes_since_last_check.slice(0, 3).map((c, i) => (
                      <div key={i} className={`wl-inline-change ${c.severity}`}>
                        <span className="wl-ic-icon">{changeSeverityIcon(c.type)}</span>
                        <span className="wl-ic-text">{c.detail}</span>
                      </div>
                    ))}
                    {changeCount > 3 && (
                      <div className="wl-inline-change-more">+{changeCount - 3} more</div>
                    )}
                  </div>
                )}

                {item.freshness && (
                  <div className="wl-freshness">
                    <span className={`wl-freshness-dot ${item.freshness.cache_hit ? "stale" : "fresh"}`} />
                    {item.freshness.cache_hit ? "cached" : "fresh"}
                    {item.freshness.intelligence_generated_at && ` · ${timeAgo(item.freshness.intelligence_generated_at)}`}
                  </div>
                )}

                <div className="wl-card-actions">
                  <button
                    className="wl-btn-sm"
                    onClick={e => handleRefresh(item.symbol, e)}
                    disabled={refreshing === item.symbol}
                  >
                    {refreshing === item.symbol ? "..." : "Refresh"}
                  </button>
                  <button className="wl-btn-sm danger" onClick={e => handleRemove(item.symbol, e)}>
                    Remove
                  </button>
                </div>
              </div>

              <div className="wl-card-right">
                {item.current_price != null && (
                  <span className="wl-price">{"₹"}{item.current_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</span>
                )}
                {item.change_pct != null && (
                  <span className={`wl-change ${item.change_pct >= 0 ? "up" : "down"}`}>
                    {item.change_pct >= 0 ? "+" : ""}{item.change_pct.toFixed(2)}%
                  </span>
                )}
                <div className="wl-anomaly-ring">
                  <span className={`wl-ring ${ringClass(item.anomaly_score)}`}>
                    {Math.round(item.anomaly_score)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}

        {/* Show watchlist stocks that haven't loaded intel yet */}
        {watchlist?.stocks
          .filter(s => !intelItems.some(i => i.symbol === s.symbol))
          .map(s => (
            <div key={s.symbol} className="wl-card status-normal" onClick={() => openIntel(s.symbol)}>
              <div className="wl-card-main">
                <div className="wl-card-header">
                  <span className="wl-symbol">{s.symbol.replace(".NS", "")}</span>
                </div>
                <span className="wl-company">Loading intelligence...</span>
              </div>
              <div className="wl-card-right">
                <div className="wl-spinner" />
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
