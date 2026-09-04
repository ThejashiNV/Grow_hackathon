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


class PatternDiscovery(BaseModel):
    pattern_type: str
    description: str
    confidence: float
    observations: int
    period_analyzed: str
    details: dict | None = None


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


class ExpectedVsActual(BaseModel):
    description: str
    historical_avg_move: float
    historical_observations: int
    current_move: float | None = None
    deviation: str


class StockIntelligence(BaseModel):
    symbol: str
    company_name: str | None = None
    sector: str | None = None
    data_start: str | None = None
    data_end: str | None = None
    total_trading_days: int = 0
    current_price: float | None = None

    horizons: list[HorizonAnalysis] = []
    anomalous_moves: list[AnomalousMove] = []
    patterns: list[PatternDiscovery] = []
    regime_changes: list[RegimeChange] = []
    rare_events: list[RareEvent] = []
    expected_vs_actual: list[ExpectedVsActual] = []

    generated_at: str = ""
    data_source: str = "yfinance"
    confidence_note: str = ""
