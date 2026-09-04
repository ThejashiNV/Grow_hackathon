from app.services import scoring


def test_price_anomaly_scales_with_volatility_not_fixed_threshold():
    # Same 2% move: huge for a low-vol stock, unremarkable for a high-vol one.
    stable_score, stable_z = scoring.price_anomaly(change_pct=2.0, volatility_30d=0.005)
    volatile_score, volatile_z = scoring.price_anomaly(change_pct=2.0, volatility_30d=0.04)

    assert stable_score > volatile_score
    assert abs(stable_z) > abs(volatile_z)


def test_price_anomaly_handles_missing_data():
    score, z = scoring.price_anomaly(None, 0.01)
    assert score == 0.0
    assert z is None


def test_volume_anomaly_log_normalized():
    at_normal, ratio = scoring.volume_anomaly(volume=1_000_000, average_volume_20d=1_000_000)
    assert at_normal == 0.0
    assert ratio == 1.0

    double, ratio2 = scoring.volume_anomaly(volume=2_000_000, average_volume_20d=1_000_000)
    quadruple, ratio4 = scoring.volume_anomaly(volume=4_000_000, average_volume_20d=1_000_000)
    # log2(4) = 2x log2(2): score should double, not quadruple.
    assert quadruple == round(double * 2, 1)


def test_volume_anomaly_missing_data():
    score, ratio = scoring.volume_anomaly(None, 1_000_000)
    assert score == 0.0
    assert ratio is None


def test_sector_relative_score_zero_when_moving_with_sector():
    score = scoring.sector_relative_score(change_pct=-2.8, sector_change_pct=-2.8)
    assert score == 0.0


def test_sector_relative_score_high_when_diverging():
    score = scoring.sector_relative_score(change_pct=-2.8, sector_change_pct=-4.6)
    assert score > 0


def test_compute_surprise_weights_sum_to_one():
    assert scoring.PRICE_WEIGHT + scoring.VOLUME_WEIGHT + scoring.SECTOR_WEIGHT == 1.0


def test_compute_attention_confidence_dampens_score():
    high_conf = scoring.compute_attention(surprise=90, impact=80, confidence=95)
    low_conf = scoring.compute_attention(surprise=90, impact=80, confidence=40)
    assert high_conf > low_conf


def test_is_meaningful_gate():
    assert scoring.is_meaningful(scoring.ATTENTION_THRESHOLD) is True
    assert scoring.is_meaningful(scoring.ATTENTION_THRESHOLD - 0.1) is False


def test_compute_confidence_penalizes_missing_data():
    full, factors_full = scoring.compute_confidence(
        has_price=True, has_volume=True, has_sector=True, headline_count=3, is_stale=False
    )
    degraded, factors_degraded = scoring.compute_confidence(
        has_price=True, has_volume=False, has_sector=False, headline_count=0, is_stale=True
    )
    assert full == 100.0
    assert degraded < full
    assert "Volume data unavailable" in factors_degraded
