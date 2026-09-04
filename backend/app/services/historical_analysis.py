"""Historical market data analysis — pure computation, no I/O.

All public functions operate on numpy arrays of dates, closes, and volumes.
"""

from __future__ import annotations

from datetime import datetime as dt

import numpy as np

from app.schemas.intelligence import (
    AnomalousMove,
    ExpectedVsActual,
    HorizonAnalysis,
    PatternDiscovery,
    RareEvent,
    RegimeChange,
)
from app.services.historical_events import find_nearby_events

HORIZON_SPECS: list[tuple[str, int]] = [
    ("1W", 5),
    ("2W", 10),
    ("1M", 21),
    ("3M", 63),
    ("6M", 126),
    ("1Y", 252),
    ("2Y", 504),
    ("5Y", 1260),
]


# ── Multi-horizon analysis ────────────────────────────────────────────


def compute_horizons(
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
) -> list[HorizonAnalysis]:
    n = len(closes)
    if n < 6:
        return []

    all_returns = np.diff(closes) / closes[:-1]
    overall_sigma = float(np.std(all_returns)) if len(all_returns) > 1 else 0.01
    overall_avg_vol = float(np.mean(volumes)) if len(volumes) > 0 else None

    results: list[HorizonAnalysis] = []
    for label, days in HORIZON_SPECS:
        if n < days + 1:
            continue

        wc = closes[-days:]
        wv = volumes[-days:]
        wd = dates[-days:]

        ret = (wc[-1] / wc[0] - 1) * 100
        wr = np.diff(wc) / wc[:-1]
        vol = float(np.std(wr) * np.sqrt(252) * 100) if len(wr) > 1 else 0.0

        cummax = np.maximum.accumulate(wc)
        max_dd = float(np.min((wc - cummax) / cummax * 100))

        avg_vol = float(np.mean(wv)) if len(wv) > 0 else None
        vol_ratio = (
            avg_vol / overall_avg_vol
            if avg_vol and overall_avg_vol and overall_avg_vol > 0
            else None
        )

        large_count = int(np.sum(np.abs(wr) > 2 * overall_sigma))

        expected_move = vol / 100 / np.sqrt(252) * np.sqrt(days) if vol > 0 else 0.01
        normalized = ret / 100 / expected_move if expected_move > 0 else 0.0
        if normalized > 0.5:
            trend = "bullish"
        elif normalized < -0.5:
            trend = "bearish"
        else:
            trend = "sideways"
        momentum = float(np.clip(normalized * 50, -100, 100))

        results.append(
            HorizonAnalysis(
                period=label,
                trading_days=len(wc),
                start_date=wd[0],
                end_date=wd[-1],
                start_price=round(float(wc[0]), 2),
                end_price=round(float(wc[-1]), 2),
                return_pct=round(ret, 2),
                annualized_volatility=round(vol, 2),
                max_drawdown_pct=round(max_dd, 2),
                avg_daily_volume=round(avg_vol, 0) if avg_vol else None,
                volume_vs_baseline=round(vol_ratio, 2) if vol_ratio else None,
                large_move_count=large_count,
                trend=trend,
                momentum_score=round(momentum, 1),
            )
        )

    return results


# ── Anomalous move detection ──────────────────────────────────────────


def detect_anomalous_moves(
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
    top_n: int = 20,
) -> list[AnomalousMove]:
    n = len(closes)
    if n < 30:
        return []

    returns = np.diff(closes) / closes[:-1]
    sigma = float(np.std(returns))
    if sigma < 1e-10:
        return []

    avg_vol = float(np.mean(volumes)) if len(volumes) > 0 else None

    anomalies: list[AnomalousMove] = []
    for i in range(len(returns)):
        z = abs(returns[i]) / sigma
        if z < 2.0:
            continue

        idx = i + 1  # the day the return materialised
        day_vol = int(volumes[idx]) if idx < len(volumes) else None
        vr = (day_vol / avg_vol) if day_vol and avg_vol and avg_vol > 0 else None

        def _post(days_ahead: int) -> float | None:
            t = idx + days_ahead
            if t < n:
                return round((closes[t] / closes[idx] - 1) * 100, 2)
            return None

        nearby = find_nearby_events(dates[idx])
        event_label = nearby[0]["title"] if nearby else None

        anomalies.append(
            AnomalousMove(
                date=dates[idx],
                close=round(float(closes[idx]), 2),
                change_pct=round(float(returns[i]) * 100, 2),
                volume=day_vol,
                volume_ratio=round(vr, 2) if vr else None,
                direction="up" if returns[i] > 0 else "down",
                magnitude_sigma=round(z, 2),
                return_1d=_post(1),
                return_1w=_post(5),
                return_2w=_post(10),
                return_1m=_post(21),
                associated_event=event_label,
            )
        )

    anomalies.sort(key=lambda a: a.magnitude_sigma, reverse=True)
    return anomalies[:top_n]


# ── Pattern detection ─────────────────────────────────────────────────


def detect_patterns(
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
) -> list[PatternDiscovery]:
    n = len(closes)
    if n < 60:
        return []

    returns = np.diff(closes) / closes[:-1]
    period_str = f"{dates[0]} to {dates[-1]}"
    patterns: list[PatternDiscovery] = []

    _detect_day_of_week(dates[1:], returns, period_str, patterns)
    _detect_monthly(dates[1:], returns, period_str, patterns)
    _detect_vol_clustering(returns, period_str, patterns)
    _detect_large_move_freq(returns, period_str, patterns)
    _detect_volume_patterns(volumes, period_str, patterns)

    return patterns


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _detect_day_of_week(
    dates: list[str],
    returns: np.ndarray,
    period_str: str,
    out: list[PatternDiscovery],
) -> None:
    weekdays = np.array([dt.strptime(d, "%Y-%m-%d").weekday() for d in dates])
    significant: list[dict] = []
    for day in range(5):
        mask = weekdays == day
        dr = returns[mask]
        if len(dr) < 20:
            continue
        mean_r = float(np.mean(dr))
        std_r = float(np.std(dr))
        if std_r < 1e-10:
            continue
        t = mean_r / (std_r / np.sqrt(len(dr)))
        if abs(t) > 2.0:
            significant.append(
                {
                    "day": _DAY_NAMES[day],
                    "avg_return_pct": round(mean_r * 100, 3),
                    "t_stat": round(t, 2),
                    "observations": int(len(dr)),
                }
            )
    if not significant:
        return
    best = max(significant, key=lambda x: abs(x["t_stat"]))
    direction = "positive" if best["avg_return_pct"] > 0 else "negative"
    out.append(
        PatternDiscovery(
            pattern_type="day_of_week",
            description=(
                f"{best['day']}s show statistically significant {direction} "
                f"average returns ({best['avg_return_pct']:.3f}%)"
            ),
            confidence=min(1.0, abs(best["t_stat"]) / 4.0),
            observations=best["observations"],
            period_analyzed=period_str,
            details={"days": significant},
        )
    )


def _detect_monthly(
    dates: list[str],
    returns: np.ndarray,
    period_str: str,
    out: list[PatternDiscovery],
) -> None:
    months = np.array([dt.strptime(d, "%Y-%m-%d").month for d in dates])
    significant: list[dict] = []
    for m in range(1, 13):
        mask = months == m
        mr = returns[mask]
        if len(mr) < 10:
            continue
        mean_r = float(np.mean(mr))
        std_r = float(np.std(mr))
        if std_r < 1e-10:
            continue
        t = mean_r / (std_r / np.sqrt(len(mr)))
        if abs(t) > 2.0:
            significant.append(
                {
                    "month": _MONTH_NAMES[m],
                    "avg_return_pct": round(mean_r * 100, 3),
                    "t_stat": round(t, 2),
                    "observations": int(len(mr)),
                }
            )
    if not significant:
        return
    best = max(significant, key=lambda x: abs(x["t_stat"]))
    direction = "positive" if best["avg_return_pct"] > 0 else "negative"
    out.append(
        PatternDiscovery(
            pattern_type="monthly_seasonality",
            description=(
                f"{best['month']} shows statistically significant {direction} "
                f"average returns ({best['avg_return_pct']:.3f}%)"
            ),
            confidence=min(1.0, abs(best["t_stat"]) / 4.0),
            observations=best["observations"],
            period_analyzed=period_str,
            details={"months": significant},
        )
    )


def _detect_vol_clustering(
    returns: np.ndarray,
    period_str: str,
    out: list[PatternDiscovery],
) -> None:
    if len(returns) < 60:
        return
    sq = returns**2
    mean_sq = np.mean(sq)
    denom = np.sum((sq - mean_sq) ** 2)
    if denom < 1e-20:
        return
    numer = np.sum((sq[1:] - mean_sq) * (sq[:-1] - mean_sq))
    autocorr = float(numer / denom)
    se = 1.0 / np.sqrt(len(sq))
    z = autocorr / se
    if abs(z) > 2.0 and autocorr > 0.1:
        out.append(
            PatternDiscovery(
                pattern_type="volatility_clustering",
                description=(
                    f"Volatility clustering detected (autocorrelation {autocorr:.2f}). "
                    "Large moves tend to follow large moves."
                ),
                confidence=min(1.0, abs(z) / 5.0),
                observations=len(sq),
                period_analyzed=period_str,
                details={"autocorrelation": round(autocorr, 3), "z_stat": round(z, 2)},
            )
        )


def _detect_large_move_freq(
    returns: np.ndarray,
    period_str: str,
    out: list[PatternDiscovery],
) -> None:
    sigma = float(np.std(returns))
    if sigma < 1e-10:
        return
    large_mask = np.abs(returns) > 2 * sigma
    count = int(np.sum(large_mask))
    if count < 3:
        return
    total = len(returns)
    freq = total / count
    mid = total // 2
    first_half = int(np.sum(large_mask[:mid]))
    second_half = int(np.sum(large_mask[mid:]))
    trend = "stable"
    if second_half > first_half * 1.5 and second_half > 3:
        trend = "increasing"
    elif first_half > second_half * 1.5 and first_half > 3:
        trend = "decreasing"
    desc = f"Large moves (>2σ) occur approximately every {freq:.0f} trading days"
    if trend != "stable":
        desc += f" — frequency is {trend} recently"
    out.append(
        PatternDiscovery(
            pattern_type="large_move_frequency",
            description=desc,
            confidence=min(1.0, count / 20.0),
            observations=count,
            period_analyzed=period_str,
            details={
                "total_large_moves": count,
                "avg_interval_days": round(freq, 1),
                "frequency_trend": trend,
                "first_half_count": first_half,
                "second_half_count": second_half,
            },
        )
    )


def _detect_volume_patterns(
    volumes: np.ndarray,
    period_str: str,
    out: list[PatternDiscovery],
) -> None:
    if len(volumes) < 60:
        return
    avg_vol = float(np.mean(volumes))
    if avg_vol < 1:
        return
    high_mask = volumes > 2 * avg_vol
    high_count = int(np.sum(high_mask))
    if high_count < 3:
        return
    freq = len(volumes) / high_count
    recent_avg = float(np.mean(volumes[-21:])) if len(volumes) >= 21 else float(np.mean(volumes))
    ratio = recent_avg / avg_vol
    desc = (
        f"High-volume days (>2× average) occur every ~{freq:.0f} days "
        f"({high_count} occurrences)"
    )
    if ratio > 1.3:
        desc += f". Recent volume is {ratio:.1f}× the historical average"
    elif ratio < 0.7:
        desc += f". Recent volume is only {ratio:.1f}× the historical average"
    out.append(
        PatternDiscovery(
            pattern_type="volume_behavior",
            description=desc,
            confidence=min(1.0, high_count / 15.0),
            observations=high_count,
            period_analyzed=period_str,
            details={
                "high_volume_days": high_count,
                "avg_interval_days": round(freq, 1),
                "recent_vs_historical_ratio": round(ratio, 2),
            },
        )
    )


# ── Regime analysis ───────────────────────────────────────────────────


def analyze_regime(
    closes: np.ndarray,
    volumes: np.ndarray,
) -> list[RegimeChange]:
    n = len(closes)
    if n < 60:
        return []

    returns = np.diff(closes) / closes[:-1]
    changes: list[RegimeChange] = []

    if n >= 252:
        recent_vol = float(np.std(returns[-21:]) * np.sqrt(252) * 100)
        baseline_vol = float(np.std(returns[-252:]) * np.sqrt(252) * 100)
        if baseline_vol > 0:
            ratio = recent_vol / baseline_vol
            if abs(ratio - 1.0) > 0.3:
                direction = "higher" if ratio > 1 else "lower"
                changes.append(
                    RegimeChange(
                        metric="volatility",
                        current_value=round(recent_vol, 1),
                        baseline_value=round(baseline_vol, 1),
                        ratio=round(ratio, 2),
                        description=(
                            f"Recent volatility ({recent_vol:.1f}%) is "
                            f"{ratio:.1f}× the 1-year baseline ({baseline_vol:.1f}%) "
                            f"— significantly {direction}"
                        ),
                        period_compared="30d vs 1Y",
                    )
                )

    if n >= 252 and len(volumes) >= 252:
        recent_avg = float(np.mean(volumes[-21:]))
        baseline_avg = float(np.mean(volumes[-252:]))
        if baseline_avg > 0:
            ratio = recent_avg / baseline_avg
            if abs(ratio - 1.0) > 0.3:
                direction = "higher" if ratio > 1 else "lower"
                changes.append(
                    RegimeChange(
                        metric="volume",
                        current_value=round(recent_avg, 0),
                        baseline_value=round(baseline_avg, 0),
                        ratio=round(ratio, 2),
                        description=(
                            f"Recent avg volume ({recent_avg:,.0f}) is "
                            f"{ratio:.1f}× the 1-year average ({baseline_avg:,.0f}) "
                            f"— {direction} than normal"
                        ),
                        period_compared="30d vs 1Y",
                    )
                )

    if n >= 252:
        recent_ret = (closes[-1] / closes[-22] - 1) * 100 if n >= 22 else 0
        yearly_ret = (closes[-1] / closes[-252] - 1) * 100
        avg_monthly = yearly_ret / 12
        if abs(avg_monthly) > 0.1:
            ratio = recent_ret / avg_monthly if avg_monthly != 0 else 0
            if abs(ratio) > 2 or (recent_ret * avg_monthly < 0 and abs(recent_ret) > 1):
                if recent_ret * avg_monthly < 0:
                    desc = (
                        f"Recent 30d return ({recent_ret:+.1f}%) has reversed direction "
                        f"from the 1Y trend (avg monthly: {avg_monthly:+.1f}%)"
                    )
                else:
                    desc = (
                        f"Recent 30d return ({recent_ret:+.1f}%) is "
                        f"{abs(ratio):.1f}× the average monthly pace ({avg_monthly:+.1f}%)"
                    )
                changes.append(
                    RegimeChange(
                        metric="momentum",
                        current_value=round(recent_ret, 2),
                        baseline_value=round(avg_monthly, 2),
                        ratio=round(ratio, 2),
                        description=desc,
                        period_compared="30d vs 1Y avg",
                    )
                )

    if n >= 252:
        yc = closes[-252:]
        cm = np.maximum.accumulate(yc)
        current_dd = float((yc[-1] - cm[-1]) / cm[-1] * 100)
        if current_dd < -5:
            max_dd = float(np.min((yc - cm) / cm * 100))
            avg_dd = float(np.mean((yc - cm) / cm * 100))
            changes.append(
                RegimeChange(
                    metric="drawdown",
                    current_value=round(current_dd, 2),
                    baseline_value=round(avg_dd, 2),
                    ratio=round(current_dd / avg_dd if avg_dd != 0 else 0, 2),
                    description=(
                        f"Currently in a {current_dd:.1f}% drawdown from 1Y high "
                        f"(max drawdown was {max_dd:.1f}%)"
                    ),
                    period_compared="current vs 1Y",
                )
            )

    return changes


# ── Rare events ───────────────────────────────────────────────────────


def find_rare_events(
    dates: list[str],
    closes: np.ndarray,
) -> list[RareEvent]:
    n = len(closes)
    if n < 60:
        return []

    returns = np.diff(closes) / closes[:-1]
    sigma = float(np.std(returns))
    if sigma < 1e-10:
        return []

    events: list[RareEvent] = []
    for i in range(len(returns)):
        z = abs(returns[i]) / sigma
        if z < 3.0:
            continue
        idx = i + 1
        change_pct = round(float(returns[i]) * 100, 2)
        direction = "decline" if returns[i] < 0 else "surge"

        recovery_days = None
        if returns[i] < 0:
            pre = closes[i]
            for j in range(idx, min(idx + 63, n)):
                if closes[j] >= pre:
                    recovery_days = j - idx
                    break

        severity = "extreme" if z >= 4 else ("major" if z >= 3.5 else "notable")
        nearby = find_nearby_events(dates[idx])
        ctx = f" (near: {nearby[0]['title']})" if nearby else ""

        events.append(
            RareEvent(
                date=dates[idx],
                change_pct=change_pct,
                description=(
                    f"{severity.capitalize()} {direction} of {abs(change_pct):.1f}% "
                    f"({z:.1f}σ){ctx}"
                ),
                recovery_days=recovery_days,
                severity=severity,
            )
        )

    events.sort(key=lambda e: abs(e.change_pct), reverse=True)
    return events[:10]


# ── Expected vs. actual ───────────────────────────────────────────────


def compute_expected_vs_actual(
    anomalous_moves: list[AnomalousMove],
    closes: np.ndarray,
) -> list[ExpectedVsActual]:
    if len(anomalous_moves) < 3 or len(closes) < 30:
        return []

    results: list[ExpectedVsActual] = []
    for group, label in [
        ([m for m in anomalous_moves if m.direction == "up" and m.return_1w is not None], "positive shock"),
        ([m for m in anomalous_moves if m.direction == "down" and m.return_1w is not None], "negative shock"),
    ]:
        if len(group) < 3:
            continue
        avg_1w = float(np.mean([m.return_1w for m in group]))
        recent = group[0]
        if recent.return_1w is None:
            continue
        delta = recent.return_1w - avg_1w
        if abs(delta) < abs(avg_1w) * 0.3:
            dev = "inline"
        elif abs(recent.return_1w) < abs(avg_1w):
            dev = "muted"
        else:
            dev = "amplified"
        results.append(
            ExpectedVsActual(
                description=(
                    f"After a {label}, the 1-week aftermath historically averages "
                    f"{avg_1w:+.2f}%. The most recent {label} ({recent.date}) "
                    f"resulted in {recent.return_1w:+.2f}%."
                ),
                historical_avg_move=round(avg_1w, 2),
                historical_observations=len(group),
                current_move=recent.return_1w,
                deviation=dev,
            )
        )

    all_1w = [m for m in anomalous_moves if m.return_1w is not None]
    if len(all_1w) >= 5:
        avg_abs = float(np.mean([abs(m.return_1w) for m in all_1w]))
        avg_day = float(np.mean([abs(m.change_pct) for m in anomalous_moves]))
        results.append(
            ExpectedVsActual(
                description=(
                    f"After large moves (avg {avg_day:.1f}%), the average absolute "
                    f"1-week follow-through is {avg_abs:.2f}%."
                ),
                historical_avg_move=round(avg_abs, 2),
                historical_observations=len(all_1w),
                current_move=None,
                deviation="baseline",
            )
        )

    return results
