import type { AskResponse, AttentionResponse, ChangeBundle, DailyFeed, DemoScenario, HistoryResponse, RefreshStatus, StockIntelligence, Watchlist, WatchlistIntelItem } from "../types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  services: {
    mongodb: string;
    redis: string;
    chroma: string;
  };
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),

  getWatchlist: () => request<Watchlist>("/api/watchlist"),
  addStock: (symbol: string) =>
    request<Watchlist>("/api/watchlist/stocks", {
      method: "POST",
      body: JSON.stringify({ symbol }),
    }),
  removeStock: (symbol: string) =>
    request<Watchlist>(`/api/watchlist/stocks/${encodeURIComponent(symbol)}`, {
      method: "DELETE",
    }),

  getAttention: () => request<AttentionResponse>("/api/attention"),
  getChanges: () => request<ChangeBundle[]>("/api/changes"),
  getChangeBundle: (symbol: string) => request<ChangeBundle>(`/api/changes/${encodeURIComponent(symbol)}`),
  markSeen: (symbol: string) => request(`/api/stocks/${encodeURIComponent(symbol)}/seen`, { method: "POST" }),

  ask: (symbol: string, question: string) =>
    request<AskResponse>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ symbol, question }),
    }),

  getDemoScenarios: () =>
    request<{ demo_mode: boolean; scenarios: DemoScenario[] }>("/api/demo/scenarios"),

  getHistory: (filter: string = "all") =>
    request<HistoryResponse>(`/api/history?filter=${encodeURIComponent(filter)}`),

  getIntelligence: (symbol: string, refresh = false) =>
    request<StockIntelligence>(
      `/api/intelligence/${encodeURIComponent(symbol)}${refresh ? "?refresh=true" : ""}`
    ),

  getWatchlistIntelligence: () =>
    request<{ items: WatchlistIntelItem[] }>("/api/intelligence-summary"),

  getRefreshStatus: () =>
    request<RefreshStatus>("/api/refresh-status"),

  triggerRefresh: (symbol: string) =>
    request<{ refreshed: boolean; symbol: string }>(`/api/refresh/${encodeURIComponent(symbol)}`, { method: "POST" }),

  getDailyFeed: () =>
    request<DailyFeed>("/api/daily-feed"),

  markIntelSeen: () =>
    request<{ marked: number; seen_at: string }>("/api/intel-seen", { method: "POST" }),
};
