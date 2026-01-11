from scoring.deal_score import score_signal


def test_score_basic():
    sig = {
        "urgency": 0.9,
        "financial_distress": 0.8,
        "liquidity_estimate": 0.3,
        "confidence": 0.9,
    }
    out = score_signal(sig)
    assert out["score"] >= 0 and out["score"] <= 100
    assert "recommended_action" in out


def test_score_thresholds():
    high = {
        "urgency": 1.0,
        "financial_distress": 1.0,
        "liquidity_estimate": 1.0,
        "confidence": 1.0,
    }
    out = score_signal(high)
    assert out["recommended_action"] == "call_within_24h" or out["score"] >= 85
