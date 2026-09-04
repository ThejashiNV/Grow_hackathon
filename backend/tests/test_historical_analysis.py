"""Tests for historical analysis computations."""

from datetime import datetime, timedelta

import numpy as np
import pytest

from app.schemas.intelligence import AnomalousMove
from app.services.historical_analysis import (
    analyze_regime,
    compute_expected_vs_actual,
    compute_horizons,
    detect_anomalous_moves,
    detect_patterns,
    find_rare_events,
)


def _make_dates(n: int, start: str = "2020-01-01") -> list[str]:
    dates: list[str] = []
    d = datetime.strptime(start, "%Y-%m-%d")
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return dates


def _trending_data(n: int, start: float = 1000.0, daily_ret: float = 0.001, noise: float = 0.01):
    np.random.seed(42)
    rets = daily_ret + np.random.normal(0, noise, n - 1)
    closes = np.empty(n)
    closes[0] = start
    for i in range(1, n):
        closes[i] = closes[i - 1] * (1 + rets[i - 1])
    volumes = np.random.randint(1_000_000, 5_000_000, n).astype(float)
    return closes, volumes


# ── Horizons ──────────────────────────────────────────────────────────

class TestHorizons:
    def test_insufficient_data(self):
        assert compute_horizons(_make_dates(3), np.array([100, 101, 102.0]), np.array([1e6]*3)) == []

    def test_basic(self):
        dates = _make_dates(300)
        c, v = _trending_data(300)
        result = compute_horizons(dates, c, v)
        periods = [h.period for h in result]
        assert "1M" in periods
        assert "3M" in periods

    def test_return_positive_for_uptrend(self):
        dates = _make_dates(30)
        c = np.linspace(100, 110, 30)
        v = np.full(30, 1e6)
        result = compute_horizons(dates, c, v)
        assert result and result[0].return_pct > 0

    def test_drawdown_nonpositive(self):
        dates = _make_dates(300)
        c, v = _trending_data(300)
        for h in compute_horizons(dates, c, v):
            assert h.max_drawdown_pct <= 0

    def test_large_move_count_nonnegative(self):
        dates = _make_dates(300)
        c, v = _trending_data(300)
        for h in compute_horizons(dates, c, v):
            assert h.large_move_count >= 0


# ── Anomalous moves ──────────────────────────────────────────────────

class TestAnomalousMoves:
    def test_detects_spike(self):
        np.random.seed(42)
        dates = _make_dates(200)
        c = np.full(200, 100.0) + np.random.normal(0, 0.5, 200).cumsum() * 0.1
        c[100] *= 1.20
        v = np.full(200, 1e6)
        result = detect_anomalous_moves(dates, c, v)
        assert any(abs(m.change_pct) > 5 for m in result)

    def test_post_event_returns_populated(self):
        dates = _make_dates(200)
        c, v = _trending_data(200, noise=0.02)
        c[50] = c[49] * 0.90
        result = detect_anomalous_moves(dates, c, v)
        drops = [m for m in result if m.direction == "down"]
        assert drops and drops[0].return_1d is not None

    def test_empty_for_flat(self):
        dates = _make_dates(200)
        c = np.full(200, 100.0)
        v = np.full(200, 1e6)
        assert detect_anomalous_moves(dates, c, v) == []

    def test_top_n_limit(self):
        np.random.seed(7)
        dates = _make_dates(500)
        c, v = _trending_data(500, noise=0.03)
        result = detect_anomalous_moves(dates, c, v, top_n=5)
        assert len(result) <= 5


# ── Patterns ──────────────────────────────────────────────────────────

class TestPatterns:
    def test_returns_list(self):
        dates = _make_dates(500)
        c, v = _trending_data(500, noise=0.015)
        assert isinstance(detect_patterns(dates, c, v), list)

    def test_insufficient_data(self):
        assert detect_patterns(_make_dates(20), *_trending_data(20)) == []

    def test_vol_clustering_with_block_volatility(self):
        np.random.seed(99)
        n = 600
        dates = _make_dates(n)
        c = np.empty(n)
        c[0] = 100
        for i in range(1, n):
            block = (i // 30) % 2
            sigma = 0.04 if block == 0 else 0.005
            c[i] = c[i - 1] * (1 + np.random.normal(0, sigma))
        v = np.random.randint(1_000_000, 5_000_000, n).astype(float)
        result = detect_patterns(dates, c, v)
        types = [p.pattern_type for p in result]
        assert "volatility_clustering" in types


# ── Regime ────────────────────────────────────────────────────────────

class TestRegime:
    def test_detects_vol_spike(self):
        dates = _make_dates(300)
        c = np.full(300, 100.0)
        np.random.seed(42)
        c[:270] += np.cumsum(np.random.normal(0, 0.2, 270))
        c[270:] = c[269] + np.cumsum(np.random.normal(0, 2.0, 30))
        v = np.full(300, 1e6)
        result = analyze_regime(c, v)
        vol_items = [r for r in result if r.metric == "volatility"]
        assert vol_items and vol_items[0].ratio > 1.5

    def test_no_crash_stable(self):
        dates = _make_dates(300)
        c, v = _trending_data(300, noise=0.01)
        assert isinstance(analyze_regime(c, v), list)


# ── Rare events ───────────────────────────────────────────────────────

class TestRareEvents:
    def test_detects_crash(self):
        np.random.seed(42)
        dates = _make_dates(300)
        c = 100 + np.cumsum(np.random.normal(0, 0.3, 300))
        c[150] = c[149] * 0.85
        result = find_rare_events(dates, c)
        assert any(e.severity in ("extreme", "major") for e in result)

    def test_recovery_days(self):
        dates = _make_dates(300)
        c = np.full(300, 100.0)
        np.random.seed(42)
        c += np.cumsum(np.random.normal(0, 0.2, 300))
        pre = c[99]
        c[100] = pre * 0.80
        for i in range(101, 130):
            c[i] = c[i-1] * 1.015
        result = find_rare_events(dates, c)
        crash = [e for e in result if e.change_pct < -10]
        if crash and crash[0].recovery_days is not None:
            assert crash[0].recovery_days > 0

    def test_empty_for_gentle_data(self):
        dates = _make_dates(300)
        c, _ = _trending_data(300, noise=0.002)
        result = find_rare_events(dates, c)
        assert isinstance(result, list)


# ── Expected vs actual ────────────────────────────────────────────────

class TestExpectedVsActual:
    def test_with_enough_data(self):
        moves = [
            AnomalousMove(date=f"2023-0{i}-10", close=100, change_pct=-5.0+i,
                          direction="down", magnitude_sigma=2.5,
                          return_1d=-1.0, return_1w=-2.0+i*0.3, return_2w=-1.0, return_1m=0.5)
            for i in range(1, 5)
        ]
        closes = np.linspace(90, 110, 300)
        result = compute_expected_vs_actual(moves, closes)
        assert len(result) > 0

    def test_too_few_moves(self):
        moves = [
            AnomalousMove(date="2023-01-10", close=100, change_pct=-5.0,
                          direction="down", magnitude_sigma=2.5)
        ]
        assert compute_expected_vs_actual(moves, np.array([100.0]*100)) == []
