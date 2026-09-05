"""Tests for the ML anomaly detection engine."""

import numpy as np
import pytest

from app.services.ml_anomaly import (
    AnomalyResult,
    detect_anomalies_ml,
    _return_anomaly,
    _volume_anomaly,
    _volatility_regime,
    _compute_composite,
    AnomalySignal,
)


class TestReturnAnomaly:
    def test_normal_return(self):
        rng = np.random.RandomState(42)
        window = rng.normal(0, 0.01, 252)
        signal = _return_anomaly(0.005, window)
        assert signal.score < 40

    def test_extreme_return(self):
        rng = np.random.RandomState(42)
        window = rng.normal(0, 0.01, 252)
        signal = _return_anomaly(0.05, window)
        assert signal.score >= 60
        assert "above" in signal.description

    def test_negative_extreme(self):
        rng = np.random.RandomState(42)
        window = rng.normal(0, 0.01, 252)
        signal = _return_anomaly(-0.06, window)
        assert signal.score >= 60
        assert "below" in signal.description


class TestVolumeAnomaly:
    def test_normal_volume(self):
        window = np.full(60, 1_000_000.0)
        signal = _volume_anomaly(1_100_000, window)
        assert signal.score < 20

    def test_high_volume(self):
        window = np.full(60, 1_000_000.0)
        signal = _volume_anomaly(5_000_000, window)
        assert signal.score >= 30
        assert "elevated" in signal.description


class TestVolatilityRegime:
    def test_stable_regime(self):
        rng = np.random.RandomState(42)
        returns = rng.normal(0, 0.01, 300)
        signal = _volatility_regime(returns, 299)
        assert signal.score < 40

    def test_spike_regime(self):
        rng = np.random.RandomState(42)
        returns = rng.normal(0, 0.01, 300)
        returns[-10:] = rng.normal(0, 0.04, 10)
        signal = _volatility_regime(returns, 299)
        assert signal.score >= 30


class TestComposite:
    def test_all_low(self):
        signals = [AnomalySignal("a", 10, 0.5, "", 1.0), AnomalySignal("b", 5, 0.2, "", 1.0)]
        assert _compute_composite(signals) < 30

    def test_one_high(self):
        signals = [
            AnomalySignal("a", 90, 4.0, "", 2.0),
            AnomalySignal("b", 10, 0.5, "", 1.0),
        ]
        assert _compute_composite(signals) >= 40

    def test_multiple_high_boost(self):
        signals = [
            AnomalySignal("a", 70, 3.0, "", 1.0),
            AnomalySignal("b", 65, 2.8, "", 1.0),
            AnomalySignal("c", 60, 2.5, "", 1.0),
        ]
        result = _compute_composite(signals)
        assert result >= 60


class TestDetectAnomaliesMl:
    def test_basic_run(self):
        rng = np.random.RandomState(42)
        n = 300
        dates = [f"2023-{(i // 21) + 1:02d}-{(i % 21) + 1:02d}" for i in range(n)]
        closes = 100 + np.cumsum(rng.normal(0, 1, n))
        closes = np.maximum(closes, 10)
        volumes = rng.uniform(500_000, 2_000_000, n)

        results = detect_anomalies_ml(dates, closes, volumes, lookback=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        for r in results:
            assert isinstance(r, AnomalyResult)
            assert 0 <= r.composite_score <= 100

    def test_spike_detected(self):
        rng = np.random.RandomState(42)
        n = 300
        closes = 100 + np.cumsum(rng.normal(0, 0.5, n))
        closes = np.maximum(closes, 10)
        closes[-1] = closes[-2] * 1.10  # 10% spike
        volumes = np.full(n, 1_000_000.0)
        volumes[-1] = 8_000_000  # 8x volume

        dates = [f"2023-{(i // 21) + 1:02d}-{(i % 21) + 1:02d}" for i in range(n)]
        results = detect_anomalies_ml(dates, closes, volumes, lookback=1)
        assert len(results) == 1
        assert results[0].composite_score >= 50

    def test_insufficient_data(self):
        results = detect_anomalies_ml(
            ["2023-01-01"] * 20,
            np.arange(20, dtype=np.float64) + 100,
            np.full(20, 1e6),
        )
        assert results == []


class TestCompanyIntel:
    def test_curated_profile(self):
        from app.services.company_intel import CURATED_COMPANIES, get_search_terms

        profile = dict(CURATED_COMPANIES["RELIANCE.NS"])
        profile["symbol"] = "RELIANCE.NS"
        terms = get_search_terms(profile)
        assert "Reliance" in terms or "Reliance Industries Ltd" in terms
        assert "Jio" in terms

    def test_search_terms_dedup(self):
        from app.services.company_intel import get_search_terms

        profile = {
            "name": "Test Corp",
            "symbol": "TEST.NS",
            "aliases": ["Test Corp"],
            "subsidiaries": ["Sub1"],
        }
        terms = get_search_terms(profile)
        assert len(terms) == len(set(terms))


class TestBenchmarkService:
    def test_relative_returns(self):
        from app.services.benchmark_service import compute_relative_returns

        rng = np.random.RandomState(42)
        stock = 100.0 + np.cumsum(rng.normal(0.001, 0.01, 50))
        bench = 1000.0 + np.cumsum(rng.normal(0.0005, 0.008, 50))
        result = compute_relative_returns(stock, bench)
        assert "stock_return_pct" in result
        assert "outperformance_pct" in result
        assert "correlation" in result

    def test_short_data(self):
        from app.services.benchmark_service import compute_relative_returns

        result = compute_relative_returns(np.array([100.0]), np.array([1000.0]))
        assert result == {}
