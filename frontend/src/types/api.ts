export interface ScoreComponents {
  price_anomaly: number;
  price_z_score: number | null;
  volume_anomaly: number;
  volume_ratio: number | null;
  sector_relative_move: number;
  sector: string | null;
  sector_change_pct: number | null;
  headline_novelty: number;
  event_impact: number;
}

export interface ExplainChip {
  label: string;
  kind: "price" | "volume" | "sector" | "event" | "silence";
}

export interface ClassifiedEvent {
  event_id: string;
  symbol: string;
  event_type: string;
  title: string;
  summary: string | null;
  impact_score: number;
  novelty_score: number;
  source: string | null;
  link: string | null;
  timestamp: string;
  is_duplicate_of: string | null;
}

export interface ChangeBundle {
  symbol: string;
  company_name: string | null;
  price: number | null;
  previous_close: number | null;
  change_pct: number | null;
  normal_daily_move_pct: number | null;
  volume: number | null;
  average_volume_20d: number | null;
  components: ScoreComponents;
  surprise_score: number;
  impact_score: number;
  confidence_score: number;
  attention_score: number;
  sector_wide: boolean;
  events: ClassifiedEvent[];
  explain_chips: ExplainChip[];
  why_this: string;
  why_now: string;
  is_meaningful: boolean;
  as_of: string;
  is_delayed: boolean;
  data_ok: boolean;
  confidence_factors: string[];
  demo_label: string | null;
}

export interface DiffResult {
  symbol: string;
  has_prior_state: boolean;
  price_changed_since: number | null;
  new_event_ids: string[];
  score_changed_since: number | null;
  is_new_since_last_visit: boolean;
}

export interface AttentionItem {
  bundle: ChangeBundle;
  diff: DiffResult;
}

export interface AttentionResponse {
  items: AttentionItem[];
  meaningful_count: number;
  generated_at: string;
  empty_watchlist: boolean;
  demo_mode: boolean;
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  symbol: string;
}

export interface WatchlistStock {
  symbol: string;
  added_at: string;
}

export interface Watchlist {
  user_id: string;
  stocks: WatchlistStock[];
  updated_at: string;
}

export interface AskResponse {
  answer: string;
  evidence: string[];
  confidence: number;
  llm_generated: boolean;
}

export interface HistoryEntry {
  user_id: string;
  symbol: string;
  company_name: string | null;
  date_key: string;
  detected_at: string;
  seen_at: string | null;
  price: number | null;
  change_pct: number | null;
  attention_score: number;
  surprise_score: number;
  impact_score: number;
  explain_chips: ExplainChip[];
  top_headline: string | null;
  top_event_type: string | null;
  why_this: string;
  why_now: string;
  demo_label: string | null;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
  total: number;
}

// ── Market Intelligence ──────────────────────────────────────────────

export interface HorizonAnalysis {
  period: string;
  trading_days: number;
  start_date: string;
  end_date: string;
  start_price: number;
  end_price: number;
  return_pct: number;
  annualized_volatility: number;
  max_drawdown_pct: number;
  avg_daily_volume: number | null;
  volume_vs_baseline: number | null;
  large_move_count: number;
  trend: string;
  momentum_score: number;
  sector_return_pct: number | null;
  market_return_pct: number | null;
  relative_performance_pct: number | null;
}

export interface AnomalousMove {
  date: string;
  close: number;
  change_pct: number;
  volume: number | null;
  volume_ratio: number | null;
  direction: string;
  magnitude_sigma: number;
  return_1d: number | null;
  return_1w: number | null;
  return_2w: number | null;
  return_1m: number | null;
  associated_event: string | null;
  sector_return_pct: number | null;
  market_return_pct: number | null;
  abnormal_return_pct: number | null;
}

export interface PatternDiscovery {
  pattern_type: string;
  description: string;
  confidence: number;
  observations: number;
  period_analyzed: string;
  details: Record<string, unknown> | null;
  is_periodic: boolean;
  evidence_strength: string;
}

export interface RegimeChange {
  metric: string;
  current_value: number;
  baseline_value: number;
  ratio: number;
  description: string;
  period_compared: string;
}

export interface RareEvent {
  date: string;
  change_pct: number;
  description: string;
  recovery_days: number | null;
  severity: string;
  event_type: string | null;
  source: string | null;
}

export interface ExpectedVsActual {
  description: string;
  historical_avg_move: number;
  historical_observations: number;
  current_move: number | null;
  deviation: string;
  historical_median: number | null;
  historical_range_low: number | null;
  historical_range_high: number | null;
  similarity_score: number | null;
}

export interface AnomalySignal {
  name: string;
  score: number;
  z_score: number;
  description: string;
}

export interface MLAnomaly {
  date: string;
  composite_score: number;
  is_anomalous: boolean;
  explanation: string;
  signals: AnomalySignal[];
}

export interface NewsItem {
  news_id: string;
  title: string;
  summary: string;
  publisher: string | null;
  link: string | null;
  published_at: string | null;
  source: string;
  event_type: string;
  impact_score: number;
}

export interface BenchmarkComparison {
  benchmark_name: string;
  benchmark_symbol: string;
  stock_return_pct: number;
  benchmark_return_pct: number;
  outperformance_pct: number;
  correlation: number | null;
  beta: number | null;
}

export interface CompanyProfile {
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string;
  market_cap: number | null;
  aliases: string[];
  subsidiaries: string[];
  segments: string[];
  commodities: string[];
  macro_factors: string[];
  competitors: string[];
}

export interface DataFreshness {
  price_data: string;
  price_updated_at: string | null;
  news_data: string;
  news_updated_at: string | null;
  benchmark_data: string;
  intelligence_generated_at: string | null;
  cache_hit: boolean;
}

export interface IntelChange {
  timestamp: string | null;
  type: string;
  detail: string;
  severity: string;
}

export interface WatchlistIntelItem {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  current_price: number | null;
  change_pct: number | null;
  status: string;
  anomaly_score: number;
  regime_alerts: string[];
  news_count: number;
  high_impact_news: number;
  signals: string[];
  freshness: DataFreshness | null;
  changes_since_last_check: IntelChange[];
  never_seen: boolean;
  last_seen_at: string | null;
  event_clusters: EventCluster[];
}

export interface ReactionWindow {
  window: string;
  days: number;
  stock_return_pct: number;
  market_return_pct: number | null;
  abnormal_return_pct: number | null;
  volume_ratio: number | null;
}

export interface HistoricalSimilar {
  date: string;
  event_description: string;
  stock_return_5d_pct: number;
  stock_return_20d_pct: number;
  severity: string;
}

export interface EventImpact {
  event_type: string;
  event_date: string | null;
  reactions: ReactionWindow[];
  historical_avg_reaction_5d: number | null;
  historical_avg_reaction_20d: number | null;
  similar_events: HistoricalSimilar[];
  historical_event_count: number;
}

export interface EventCluster {
  cluster_id: string;
  canonical_title: string;
  event_type: string;
  category: string;
  article_count: number;
  sources: string[];
  first_seen: string | null;
  last_seen: string | null;
  impact_score: number;
  severity: string;
  affected_symbols: string[];
  summary: string | null;
  event_impact: EventImpact | null;
}

export interface StockBaseline {
  normal_daily_vol_ann: number;
  normal_volume_median: number;
  normal_daily_range_pct: number;
  normal_daily_range_p95: number;
  volume_clustering_score: number;
  return_persistence: number;
  gap_frequency: number;
  regime_label: string;
  volatility_percentile: number;
}

export interface StockIntelligence {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  data_start: string | null;
  data_end: string | null;
  total_trading_days: number;
  current_price: number | null;
  change_pct: number | null;
  company_profile: CompanyProfile | null;
  freshness: DataFreshness | null;
  horizons: HorizonAnalysis[];
  anomalous_moves: AnomalousMove[];
  patterns: PatternDiscovery[];
  regime_changes: RegimeChange[];
  rare_events: RareEvent[];
  expected_vs_actual: ExpectedVsActual[];
  ml_anomalies: MLAnomaly[];
  stock_baseline: StockBaseline | null;
  news: NewsItem[];
  event_clusters: EventCluster[];
  benchmark_comparison: BenchmarkComparison[];
  generated_at: string;
  data_source: string;
  confidence_note: string;
}

// ── Refresh Pipeline ────────────────────────────────────────────────

export interface RefreshStatus {
  running: boolean;
  last_run: string | null;
  last_duration_sec: number | null;
  stocks_tracked: number;
  last_errors: string[];
  total_refreshes: number;
}

// ── Daily Feed ──────────────────────────────────────────────────────

export interface FeedAlert {
  type: string;
  symbol: string;
  company_name: string | null;
  score: number;
  detail: string;
  severity: string;
}

export interface FeedMover {
  symbol: string;
  company_name: string | null;
  change_pct: number;
  current_price: number | null;
  anomaly_score: number;
  direction: string;
}

export interface FeedNewsItem {
  symbol: string;
  title: string;
  publisher: string | null;
  published_at: string | null;
  impact_score: number;
  event_type: string;
  link: string | null;
}

export interface SectorSummary {
  stocks: { symbol: string; change_pct: number | null; anomaly_score: number }[];
  avg_change_pct: number | null;
  max_anomaly: number;
}

export interface RecentChange {
  symbol: string;
  timestamp: string | null;
  type: string;
  detail: string;
  severity: string;
}

export interface FeedEventCluster {
  symbol: string;
  cluster_id: string;
  canonical_title: string;
  event_type: string;
  category: string;
  article_count: number;
  impact_score: number;
  severity: string;
  affected_symbols: string[];
  first_seen: string | null;
  last_seen: string | null;
}

export interface DailyFeed {
  alerts: FeedAlert[];
  movers: FeedMover[];
  news_digest: FeedNewsItem[];
  event_clusters: FeedEventCluster[];
  sector_summary: Record<string, SectorSummary>;
  recent_changes: RecentChange[];
  refresh_status: RefreshStatus | null;
  generated_at: string | null;
}
