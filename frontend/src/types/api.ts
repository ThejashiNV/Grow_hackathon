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
