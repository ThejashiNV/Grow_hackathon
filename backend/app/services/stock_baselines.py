"""Stock-specific behavior baselines.

Computes per-stock normal ranges for volatility, volume, daily moves, and
correlation patterns. These baselines let us say "this is unusual FOR THIS
STOCK" rather than applying generic thresholds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StockBaseline:
    symbol: str
    normal_daily_vol_ann: float  # annualized volatility (normal)
    normal_volume_median: float
    normal_volume_p90: float
    normal_daily_range_pct: float  # median |return|
    normal_daily_range_p95: float  # 95th pctile |return|
    volume_clustering_score: float  # autocorrelation of volume
    return_persistence: float  # autocorrelation of returns (momentum vs mean-revert)
    gap_frequency: float  # fraction of days with >2σ gaps
    regime_label: str  # NORMAL / ELEVATED / UNUSUAL / EXTREME
    volatility_percentile: float  # current vol vs 1Y distribution


def compute_stock_baseline(
    symbol: str,
    closes: np.ndarray,
    volumes: np.ndarray,
) -> StockBaseline | None:
    n = len(closes)
    if n < 60:
        return None

    returns = np.diff(closes) / closes[:-1]
    abs_returns = np.abs(returns)

    ann_vol = float(np.std(returns[-252:] if n > 252 else returns)) * np.sqrt(252)

    vol_series = volumes[1:]
    vol_median = float(np.median(vol_series[-60:]))
    vol_p90 = float(np.percentile(vol_series[-60:], 90))

    med_abs_ret = float(np.median(abs_returns[-252:] if len(abs_returns) > 252 else abs_returns)) * 100
    p95_abs_ret = float(np.percentile(abs_returns[-252:] if len(abs_returns) > 252 else abs_returns, 95)) * 100

    vol_autocorr = _autocorrelation(vol_series[-60:]) if len(vol_series) >= 60 else 0.0
    ret_autocorr = _autocorrelation(returns[-60:]) if len(returns) >= 60 else 0.0

    recent_window = returns[-252:] if len(returns) > 252 else returns
    sigma = float(np.std(recent_window))
    gap_count = int(np.sum(np.abs(recent_window) > 2 * sigma))
    gap_freq = gap_count / len(recent_window)

    recent_vol = float(np.std(returns[-20:]) * np.sqrt(252)) if len(returns) >= 20 else ann_vol
    vol_1y = returns[-252:] if len(returns) > 252 else returns
    rolling_vols = []
    for i in range(20, len(vol_1y) + 1):
        rv = float(np.std(vol_1y[i - 20:i]) * np.sqrt(252))
        rolling_vols.append(rv)

    if rolling_vols:
        vol_pctile = float(np.searchsorted(np.sort(rolling_vols), recent_vol) / len(rolling_vols) * 100)
    else:
        vol_pctile = 50.0

    if vol_pctile >= 95:
        regime = "EXTREME"
    elif vol_pctile >= 80:
        regime = "UNUSUAL"
    elif vol_pctile >= 60:
        regime = "ELEVATED"
    else:
        regime = "NORMAL"

    return StockBaseline(
        symbol=symbol,
        normal_daily_vol_ann=round(ann_vol * 100, 2),
        normal_volume_median=round(vol_median, 0),
        normal_volume_p90=round(vol_p90, 0),
        normal_daily_range_pct=round(med_abs_ret, 3),
        normal_daily_range_p95=round(p95_abs_ret, 3),
        volume_clustering_score=round(vol_autocorr, 3),
        return_persistence=round(ret_autocorr, 3),
        gap_frequency=round(gap_freq, 4),
        regime_label=regime,
        volatility_percentile=round(vol_pctile, 1),
    )


def _autocorrelation(series: np.ndarray, lag: int = 1) -> float:
    if len(series) < lag + 10:
        return 0.0
    x = series[:-lag]
    y = series[lag:]
    mx = np.mean(x)
    my = np.mean(y)
    num = float(np.sum((x - mx) * (y - my)))
    den = float(np.sqrt(np.sum((x - mx) ** 2) * np.sum((y - my) ** 2)))
    if den < 1e-10:
        return 0.0
    return num / den
