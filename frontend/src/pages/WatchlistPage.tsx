import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Watchlist } from "../types/api";
import "./WatchlistPage.css";

function normalizeSymbol(input: string): string {
  const trimmed = input.trim().toUpperCase();
  if (!trimmed) return trimmed;
  return trimmed.includes(".") ? trimmed : `${trimmed}.NS`;
}

export function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    api
      .getWatchlist()
      .then(setWatchlist)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add stock");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (symbol: string) => {
    const updated = await api.removeStock(symbol);
    setWatchlist(updated);
  };

  return (
    <div className="watchlist-page">
      <form className="add-stock-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Add a symbol, e.g. TCS or RELIANCE.NS"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={adding || !input.trim()}>
          {adding ? "Adding..." : "+ Add stock"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}

      {watchlist && watchlist.stocks.length === 0 && (
        <p className="status-text">No stocks yet. Try adding TCS, RELIANCE, or HDFCBANK.</p>
      )}

      <ul className="watchlist-list">
        {watchlist?.stocks.map((s) => (
          <li key={s.symbol}>
            <span>{s.symbol}</span>
            <button className="remove-btn" onClick={() => handleRemove(s.symbol)}>
              Remove
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
