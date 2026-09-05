"""Market intelligence data models."""

from __future__ import annotations

from pydantic import BaseModel


class HorizonAnalysis(BaseModel):
    period: str
    trading_days: int
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    return_pct: float
    annualized_volatility: float
    max_drawdown_pct: float
    avg_daily_volume: float | None = None
    volume_vs_baseline: float | None = None
    large_move_count: int = 0
    trend: str = "sideways"
    momentum_score: float = 0.0
    sector_return_pct: float | None = None
    market_return_pct: float | None = None
    relative_performance_pct: float | None = None


class AnomalousMove(BaseModel):
    date: str
    close: float
    change_pct: float
    volume: int | None = None
    volume_ratio: float | None = None
    direction: str
    magnitude_sigma: float
    return_1d: float | None = None
    return_1w: float | None = None
    return_2w: float | None = None
    return_1m: float | None = None
    associated_event: str | None = None
    sector_return_pct: float | None = None
    market_return_pct: float | None = None
    abnormal_return_pct: float | None = None


class PatternDiscovery(BaseModel):
    pattern_type: str
    description: str
    confidence: float
    observations: int
    period_analyzed: str
    details: dict | None = None
    is_periodic: bool = True
    evidence_strength: str = "moderate"


class RegimeChange(BaseModel):
    metric: str
    current_value: float
    baseline_value: float
    ratio: float
    description: str
    period_compared: str


class RareEvent(BaseModel):
    date: str
    change_pct: float
    description: str
    recovery_days: int | None = None
    severity: str
    event_type: str | None = None
    source: str | None = None


class ExpectedVsActual(BaseModel):
    description: str
    historical_avg_move: float
    historical_observations: int
    current_move: float | None = None
    deviation: str
    historical_median: float | None = None
    historical_range_low: float | None = None
    historical_range_high: float | None = None
    similarity_score: float | None = None


class AnomalySignalOut(BaseModel):
    name: str
    score: float
    z_score: float
    description: str


class MLAnomalyOut(BaseModel):
    date: str
    composite_score: float
    is_anomalous: bool
    explanation: str
    signals: list[AnomalySignalOut] = []


class NewsItemOut(BaseModel):
    news_id: str
    title: str
    summary: str = ""
    publisher: str | None = None
    link: str | None = None
    published_at: str | None = None
    source: str = ""
    event_type: str = "other"
    impact_score: float = 0


class BenchmarkComparison(BaseModel):
    benchmark_name: str
    benchmark_symbol: str
    stock_return_pct: float
    benchmark_return_pct: float
    outperformance_pct: float
    correlation: float | None = None
    beta: float | None = None


class CompanyProfile(BaseModel):
    name: str
    sector: str | None = None
    industry: str | None = None
    exchange: str = ""
    market_cap: float | None = None
    aliases: list[str] = []
    subsidiaries: list[str] = []
    segments: list[str] = []
    commodities: list[str] = []
    macro_factors: list[str] = []
    competitors: list[str] = []


class DataFreshness(BaseModel):
    price_data: str = "unknown"
    price_updated_at: str | None = None
    news_data: str = "unknown"
    news_updated_at: str | None = None
    benchmark_data: str = "unknown"
    intelligence_generated_at: str | None = None
    cache_hit: bool = False


class StockIntelligence(BaseModel):
    symbol: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    data_start: str | None = None
    data_end: str | None = None
    total_trading_days: int = 0
    current_price: float | None = None
    change_pct: float | None = None

    company_profile: CompanyProfile | None = None
    freshness: DataFreshness | None = None

    horizons: list[HorizonAnalysis] = []
    anomalous_moves: list[AnomalousMove] = []
    patterns: list[PatternDiscovery] = []
    regime_changes: list[RegimeChange] = []
    rare_events: list[RareEvent] = []
    expected_vs_actual: list[ExpectedVsActual] = []

    ml_anomalies: list[MLAnomalyOut] = []
    news: list[NewsItemOut] = []
    benchmark_comparison: list[BenchmarkComparison] = []

    generated_at: str = ""
    data_source: str = "yfinance"
    confidence_note: str = ""
