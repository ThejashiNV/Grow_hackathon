from app.schemas.events import EventType
from app.services.event_classifier import classify_headline


def test_ceo_resignation_classified_as_high_impact():
    event_type, impact = classify_headline("HDFC Bank CEO resigns amid board dispute")
    assert event_type == EventType.EXECUTIVE_RESIGNATION
    assert impact >= 85


def test_low_impact_novel_headline_scored_low():
    event_type, impact = classify_headline("Company opens a new branch in Pune")
    assert event_type == EventType.OTHER
    assert impact <= 30


def test_earnings_surprise_detected():
    event_type, _ = classify_headline("Infosys beats estimates in Q2 earnings")
    assert event_type == EventType.EARNINGS_SURPRISE


def test_merger_detected():
    event_type, impact = classify_headline("Tata Group to acquire majority stake in rival firm")
    assert event_type == EventType.MERGER_ACQUISITION
    assert impact >= 80
