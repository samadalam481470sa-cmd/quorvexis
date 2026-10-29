import pytest
from app.scoring import score_event

def test_critical_malware_score_is_bounded():
    result = score_event("malware_indicator", 100, 1000, 2000)
    assert result.score == 100 and result.band == "critical"
    assert any("velocity" in reason.lower() for reason in result.reasons)

def test_low_risk_event():
    result = score_event("configuration_drift", 5)
    assert result.score == 10 and result.band == "low"

@pytest.mark.parametrize("kind, severity", [("unknown", 50), ("auth_failure", -1), ("auth_failure", 101)])
def test_bad_input_is_rejected(kind, severity):
    with pytest.raises(ValueError):
        score_event(kind, severity)
