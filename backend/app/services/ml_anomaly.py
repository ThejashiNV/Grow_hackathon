"""ML-based multi-signal anomaly detection engine.

Uses an ensemble of statistical and ML methods to detect anomalous behavior.
Every anomaly score comes with an explanation of WHY it's anomalous.
Pure computation — no I/O.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AnomalySignal:
    name: str
    score: float  # 0-100
    z_score: float
    description: str
    weight: float = 1.0


@dataclass
class AnomalyResult:
    date: str
    composite_score: float  # 0-100
    signals: list[AnomalySignal] = field(default_factory=list)
    explanation: str = ""
    is_anomalous: bool = False


def detect_anomalies_ml(
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
    sector_closes: np.ndarray | None = None,
    market_closes: np.ndarray | None = None,
    lookback: int = 5,
) -> list[AnomalyResult]:
    """Run ensemble anomaly detection on the most recent `lookback` trading days.

    Returns anomaly results for each of the last `lookback` days, scored 0-100
    with full signal decomposition.
    """
    n = len(closes)
    if n < 60:
        return []

    returns = np.diff(closes) / closes[:-1]
    vol_series = volumes[1:]  # align with returns
    dates_aligned = dates[1:]

    results: list[AnomalyResult] = []

    for offset in range(min(lookback, len(returns))):
        idx = len(returns) - 1 - offset
        if idx < 30:
            continue

        day_date = dates_aligned[idx]
        signals: list[AnomalySignal] = []

        # Signal 1: Return z-score (robust, using median/MAD)
        window_returns = returns[max(0, idx - 252):idx]
        ret_signal = _return_anomaly(returns[idx], window_returns)
        signals.append(ret_signal)

        # Signal 2: Volume anomaly
        window_volumes = vol_series[max(0, idx - 60):idx]
        vol_signal = _volume_anomaly(vol_series[idx], window_volumes)
        signals.append(vol_signal)

        # Signal 3: Volatility regime (recent vs baseline)
        vol_regime_signal = _volatility_regime(returns, idx)
        signals.append(vol_regime_signal)

        # Signal 4: Price-volume divergence
        pv_signal = _price_volume_divergence(returns[idx], vol_series[idx], window_returns, window_volumes)
        signals.append(pv_signal)

        # Signal 5: Momentum break
        momentum_signal = _momentum_break(closes, idx + 1)
        signals.append(momentum_signal)

        # Signal 6: Sector-relative anomaly
        if sector_closes is not None and len(sector_closes) > idx + 1:
            sector_signal = _sector_relative_anomaly(returns, idx, sector_closes)
            signals.append(sector_signal)

        # Signal 7: Market-relative anomaly
        if market_closes is not None and len(market_closes) > idx + 1:
            market_signal = _market_relative_anomaly(returns, idx, market_closes)
            signals.append(market_signal)

        # Signal 8: Gap detection
        if idx + 1 < len(closes):
            gap_signal = _gap_anomaly(closes, idx + 1, window_returns)
            if gap_signal.score > 10:
                signals.append(gap_signal)

        # Signal 9: Isolation Forest score
        iso_signal = _isolation_forest_score(returns, vol_series, idx)
        signals.append(iso_signal)

        # Signal 10: Change-point detection (CUSUM-like)
        cp_signal = _change_point_signal(returns, idx)
        if cp_signal.score > 10:
            signals.append(cp_signal)

        # Signal 11: Return-volume correlation break
        corr_signal = _correlation_break(returns, vol_series, idx)
        if corr_signal.score > 10:
            signals.append(corr_signal)

        # Composite score: weighted average with emphasis on strongest signals
        composite = _compute_composite(signals)

        explanation = _build_explanation(signals, composite)

        results.append(AnomalyResult(
            date=day_date,
            composite_score=round(composite, 1),
            signals=signals,
            explanation=explanation,
            is_anomalous=composite >= 60,
        ))

    results.reverse()
    return results


def _return_anomaly(current_return: float, window_returns: np.ndarray) -> AnomalySignal:
    """Robust z-score using median absolute deviation."""
    if len(window_returns) < 20:
        return AnomalySignal("return", 0, 0, "Insufficient history", 2.0)

    median = float(np.median(window_returns))
    mad = float(np.median(np.abs(window_returns - median)))
    if mad < 1e-10:
        mad = float(np.std(window_returns))
    if mad < 1e-10:
        return AnomalySignal("return", 0, 0, "No variance in returns", 2.0)

    z = (current_return - median) / (mad * 1.4826)
    score = min(100, abs(z) * 20)
    direction = "above" if current_return > 0 else "below"
    pct = current_return * 100

    desc = f"Return {pct:+.2f}% is {abs(z):.1f}σ {direction} normal"
    return AnomalySignal("return", round(score, 1), round(z, 2), desc, 2.0)


def _volume_anomaly(current_vol: float, window_volumes: np.ndarray) -> AnomalySignal:
    if len(window_volumes) < 10 or current_vol <= 0:
        return AnomalySignal("volume", 0, 0, "Insufficient volume data", 1.5)

    median_vol = float(np.median(window_volumes))
    if median_vol <= 0:
        return AnomalySignal("volume", 0, 0, "Zero baseline volume", 1.5)

    ratio = current_vol / median_vol
    log_ratio = float(np.log2(max(ratio, 0.01)))
    z = log_ratio / 0.5 if log_ratio > 0 else log_ratio / 0.3

    score = min(100, max(0, abs(z) * 15))
    desc = f"Volume {ratio:.1f}× median"
    if ratio > 2:
        desc += " — significantly elevated"
    elif ratio < 0.5:
        desc += " — unusually low"

    return AnomalySignal("volume", round(score, 1), round(z, 2), desc, 1.5)


def _volatility_regime(returns: np.ndarray, idx: int) -> AnomalySignal:
    if idx < 60:
        return AnomalySignal("volatility_regime", 0, 0, "Insufficient history", 1.0)

    recent_vol = float(np.std(returns[max(0, idx - 10):idx + 1]))
    baseline_vol = float(np.std(returns[max(0, idx - 252):idx]))

    if baseline_vol < 1e-10:
        return AnomalySignal("volatility_regime", 0, 0, "Zero baseline volatility", 1.0)

    ratio = recent_vol / baseline_vol
    z = (ratio - 1.0) / 0.3

    score = min(100, max(0, abs(z) * 15))
    desc = f"10d volatility is {ratio:.1f}× the 1Y baseline"
    if ratio > 1.5:
        desc += " — volatility spike"
    elif ratio < 0.5:
        desc += " — unusually calm"

    return AnomalySignal("volatility_regime", round(score, 1), round(z, 2), desc, 1.0)


def _price_volume_divergence(
    current_return: float,
    current_vol: float,
    window_returns: np.ndarray,
    window_volumes: np.ndarray,
) -> AnomalySignal:
    if len(window_returns) < 20 or len(window_volumes) < 20:
        return AnomalySignal("price_volume", 0, 0, "Insufficient data", 0.8)

    median_vol = float(np.median(window_volumes))
    if median_vol <= 0:
        return AnomalySignal("price_volume", 0, 0, "Zero baseline volume", 0.8)

    ret_z = abs(current_return) / max(float(np.std(window_returns)), 1e-10)
    vol_ratio = current_vol / median_vol

    if ret_z > 1.5 and vol_ratio < 0.8:
        score = min(80, ret_z * 15)
        desc = "Large price move on low volume — potential thin-market anomaly"
        z = ret_z
    elif ret_z < 0.5 and vol_ratio > 2.0:
        score = min(60, vol_ratio * 10)
        desc = "High volume without significant price move — possible accumulation/distribution"
        z = vol_ratio
    else:
        score = 0
        desc = "Price-volume relationship normal"
        z = 0

    return AnomalySignal("price_volume", round(score, 1), round(z, 2), desc, 0.8)


def _momentum_break(closes: np.ndarray, idx: int) -> AnomalySignal:
    if idx < 22:
        return AnomalySignal("momentum", 0, 0, "Insufficient history", 1.0)

    sma_20 = float(np.mean(closes[idx - 20:idx]))
    sma_50 = float(np.mean(closes[max(0, idx - 50):idx])) if idx >= 50 else sma_20
    current = float(closes[idx - 1])

    if sma_20 <= 0:
        return AnomalySignal("momentum", 0, 0, "Zero SMA", 1.0)

    deviation_20 = (current - sma_20) / sma_20
    cross = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0

    z = deviation_20 / 0.03

    score = 0
    desc = "Momentum normal"

    if abs(deviation_20) > 0.05:
        score = min(70, abs(deviation_20) * 500)
        direction = "above" if deviation_20 > 0 else "below"
        desc = f"Price {abs(deviation_20) * 100:.1f}% {direction} 20d SMA"

    if idx >= 50 and abs(cross) > 0.03:
        score = max(score, min(50, abs(cross) * 500))
        if cross > 0 and deviation_20 < -0.02:
            desc += " — divergence from uptrend"
            score = min(80, score + 20)

    return AnomalySignal("momentum", round(score, 1), round(z, 2), desc, 1.0)


def _sector_relative_anomaly(
    stock_returns: np.ndarray,
    idx: int,
    sector_closes: np.ndarray,
) -> AnomalySignal:
    if len(sector_closes) < idx + 2:
        return AnomalySignal("sector_relative", 0, 0, "Insufficient sector data", 1.2)

    sector_returns = np.diff(sector_closes) / sector_closes[:-1]
    if len(sector_returns) <= idx:
        return AnomalySignal("sector_relative", 0, 0, "Sector data too short", 1.2)

    relative = stock_returns[idx] - sector_returns[idx]

    window_start = max(0, idx - 252)
    rel_window = stock_returns[window_start:idx] - sector_returns[window_start:idx]
    if len(rel_window) < 20:
        return AnomalySignal("sector_relative", 0, 0, "Insufficient relative history", 1.2)

    rel_std = float(np.std(rel_window))
    if rel_std < 1e-10:
        return AnomalySignal("sector_relative", 0, 0, "Zero sector-relative variance", 1.2)

    z = relative / rel_std
    score = min(100, abs(z) * 18)
    pct = relative * 100

    if abs(z) > 2:
        desc = f"Stock diverged {pct:+.2f}% from sector ({abs(z):.1f}σ) — company-specific signal"
    else:
        desc = f"Sector-relative move normal ({pct:+.2f}%)"

    return AnomalySignal("sector_relative", round(score, 1), round(z, 2), desc, 1.2)


def _market_relative_anomaly(
    stock_returns: np.ndarray,
    idx: int,
    market_closes: np.ndarray,
) -> AnomalySignal:
    if len(market_closes) < idx + 2:
        return AnomalySignal("market_relative", 0, 0, "Insufficient market data", 0.8)

    market_returns = np.diff(market_closes) / market_closes[:-1]
    if len(market_returns) <= idx:
        return AnomalySignal("market_relative", 0, 0, "Market data too short", 0.8)

    relative = stock_returns[idx] - market_returns[idx]

    window_start = max(0, idx - 252)
    rel_window = stock_returns[window_start:idx] - market_returns[window_start:idx]
    if len(rel_window) < 20:
        return AnomalySignal("market_relative", 0, 0, "Insufficient data", 0.8)

    rel_std = float(np.std(rel_window))
    if rel_std < 1e-10:
        return AnomalySignal("market_relative", 0, 0, "Zero variance", 0.8)

    z = relative / rel_std
    score = min(100, abs(z) * 15)
    pct = relative * 100
    desc = f"Market-relative move {pct:+.2f}% ({abs(z):.1f}σ)"

    return AnomalySignal("market_relative", round(score, 1), round(z, 2), desc, 0.8)


def _gap_anomaly(closes: np.ndarray, idx: int, window_returns: np.ndarray) -> AnomalySignal:
    if idx < 2:
        return AnomalySignal("gap", 0, 0, "No gap data", 0.6)

    gap = (closes[idx] - closes[idx - 1]) / closes[idx - 1]
    sigma = float(np.std(window_returns)) if len(window_returns) > 10 else 0.02
    if sigma < 1e-10:
        sigma = 0.02

    z = gap / sigma
    score = min(80, max(0, (abs(z) - 1.5) * 20))
    direction = "up" if gap > 0 else "down"
    desc = f"Gap {direction} {abs(gap) * 100:.2f}% ({abs(z):.1f}σ)"

    return AnomalySignal("gap", round(score, 1), round(z, 2), desc, 0.6)


def _isolation_forest_score(
    returns: np.ndarray,
    volumes: np.ndarray,
    idx: int,
) -> AnomalySignal:
    """Simplified isolation forest using random splits on multiple features."""
    if idx < 60:
        return AnomalySignal("isolation_forest", 0, 0, "Insufficient data", 1.0)

    window_start = max(0, idx - 252)
    window_end = idx + 1

    wr = returns[window_start:window_end]
    wv = volumes[window_start:window_end]

    if len(wr) < 30:
        return AnomalySignal("isolation_forest", 0, 0, "Too few points", 1.0)

    features = np.column_stack([
        wr,
        np.abs(wr),
        wv / (np.median(wv) + 1e-10),
        np.convolve(np.abs(wr), np.ones(5) / 5, mode='same'),
    ])

    current_point = features[-1]
    historical = features[:-1]

    n_trees = 50
    n_features = features.shape[1]
    rng = np.random.RandomState(42)
    depths = []

    for _ in range(n_trees):
        depth = 0
        subset = historical.copy()
        for d in range(10):
            if len(subset) <= 1:
                break
            feat_idx = rng.randint(0, n_features)
            feat_min = subset[:, feat_idx].min()
            feat_max = subset[:, feat_idx].max()
            if feat_max - feat_min < 1e-15:
                break
            split = rng.uniform(feat_min, feat_max)
            if current_point[feat_idx] <= split:
                subset = subset[subset[:, feat_idx] <= split]
            else:
                subset = subset[subset[:, feat_idx] > split]
            depth += 1
        depths.append(depth)

    avg_depth = float(np.mean(depths))
    n_samples = len(historical)
    expected_depth = 2.0 * (np.log(n_samples) + 0.5772) - 2.0 * (n_samples - 1) / n_samples if n_samples > 1 else 1.0

    anomaly_score_raw = 2.0 ** (-avg_depth / max(expected_depth, 1.0))
    score = min(100, max(0, (anomaly_score_raw - 0.5) * 200))

    desc = f"Isolation score {anomaly_score_raw:.2f}"
    if score > 50:
        desc += " — multi-feature anomaly detected"

    z = (anomaly_score_raw - 0.5) / 0.15

    return AnomalySignal("isolation_forest", round(score, 1), round(z, 2), desc, 1.0)


def _compute_composite(signals: list[AnomalySignal]) -> float:
    if not signals:
        return 0.0

    total_weight = sum(s.weight for s in signals)
    if total_weight <= 0:
        return 0.0

    weighted_sum = sum(s.score * s.weight for s in signals)
    base = weighted_sum / total_weight

    top_signals = sorted(signals, key=lambda s: s.score, reverse=True)[:3]
    top_avg = float(np.mean([s.score for s in top_signals]))

    composite = 0.6 * base + 0.4 * top_avg

    high_count = sum(1 for s in signals if s.score >= 50)
    if high_count >= 3:
        composite = min(100, composite * 1.15)
    if high_count >= 5:
        composite = min(100, composite * 1.1)

    return min(100.0, composite)


def _build_explanation(signals: list[AnomalySignal], composite: float) -> str:
    active = [s for s in signals if s.score >= 25]
    if not active:
        return "No significant anomalies detected."

    active.sort(key=lambda s: s.score, reverse=True)

    parts = []
    for s in active[:5]:
        parts.append(f"• {s.description}")

    header = f"ANOMALY SCORE: {composite:.0f}/100"
    if composite >= 80:
        header += " — HIGHLY ANOMALOUS"
    elif composite >= 60:
        header += " — SIGNIFICANT ANOMALY"
    elif composite >= 40:
        header += " — MODERATE ANOMALY"

    return header + "\n" + "\n".join(parts)


def _change_point_signal(returns: np.ndarray, idx: int) -> AnomalySignal:
    """Detects regime shifts using a CUSUM-like statistic on returns."""
    if idx < 60:
        return AnomalySignal("change_point", 0, 0, "Insufficient history", 0.8)

    pre = returns[max(0, idx - 40):idx - 10]
    post = returns[max(0, idx - 10):idx + 1]

    if len(pre) < 20 or len(post) < 5:
        return AnomalySignal("change_point", 0, 0, "Insufficient data", 0.8)

    pre_mean = float(np.mean(pre))
    pre_std = float(np.std(pre))
    post_mean = float(np.mean(post))

    if pre_std < 1e-10:
        return AnomalySignal("change_point", 0, 0, "Zero pre-period variance", 0.8)

    shift = abs(post_mean - pre_mean) / pre_std

    pre_vol = float(np.std(pre))
    post_vol = float(np.std(post))
    vol_shift = post_vol / max(pre_vol, 1e-10)

    combined = shift + max(0, (vol_shift - 1.5)) * 2
    score = min(100, max(0, combined * 20))

    desc = f"Mean shift {shift:.1f}σ, volatility ratio {vol_shift:.1f}×"
    if score > 40:
        desc += " — potential regime change"

    z = shift

    return AnomalySignal("change_point", round(score, 1), round(z, 2), desc, 0.8)


def _correlation_break(
    returns: np.ndarray,
    volumes: np.ndarray,
    idx: int,
) -> AnomalySignal:
    """Detects breakdown in the return-volume correlation pattern."""
    if idx < 60:
        return AnomalySignal("correlation_break", 0, 0, "Insufficient history", 0.6)

    baseline_start = max(0, idx - 252)
    baseline_end = max(0, idx - 20)
    recent_start = max(0, idx - 20)

    bl_ret = returns[baseline_start:baseline_end]
    bl_vol = volumes[baseline_start + 1:baseline_end + 1]
    rc_ret = returns[recent_start:idx + 1]
    rc_vol = volumes[recent_start + 1:idx + 2]

    min_len = min(len(bl_ret), len(bl_vol))
    if min_len < 30:
        return AnomalySignal("correlation_break", 0, 0, "Insufficient baseline", 0.6)
    bl_ret = bl_ret[:min_len]
    bl_vol = bl_vol[:min_len]

    min_recent = min(len(rc_ret), len(rc_vol))
    if min_recent < 5:
        return AnomalySignal("correlation_break", 0, 0, "Insufficient recent data", 0.6)
    rc_ret = rc_ret[:min_recent]
    rc_vol = rc_vol[:min_recent]

    bl_corr = _pearson_corr(np.abs(bl_ret), bl_vol)
    rc_corr = _pearson_corr(np.abs(rc_ret), rc_vol)

    corr_change = abs(bl_corr - rc_corr)
    score = min(80, max(0, (corr_change - 0.3) * 150))

    desc = f"|Return|-volume correlation: baseline {bl_corr:.2f} → recent {rc_corr:.2f}"
    if score > 30:
        desc += " — correlation regime break"

    z = corr_change / 0.2

    return AnomalySignal("correlation_break", round(score, 1), round(z, 2), desc, 0.6)


def _pearson_corr(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 5:
        return 0.0
    mx, my = np.mean(x), np.mean(y)
    num = float(np.sum((x - mx) * (y - my)))
    den = float(np.sqrt(np.sum((x - mx) ** 2) * np.sum((y - my) ** 2)))
    if den < 1e-10:
        return 0.0
    return num / den
