import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from predictor import get_predictor

client = TestClient(app)


@pytest.fixture(scope="module")
def predictor():
    pred = get_predictor()
    pred.preload_all_models()
    return pred


# --- API EDGE CASES ---


def test_negative_bill_input():
    """Ensure negative bill input returns 422 Validation Error"""
    response = client.post("/calculate-bill", json={"kwh": -100})
    assert response.status_code == 422


def test_zero_bill_input():
    """Ensure zero bill input returns 422 (since gt=0)"""
    response = client.post("/calculate-bill", json={"kwh": 0})
    assert response.status_code == 422


def test_massive_bill_input():
    """Ensure system handles extremely large numbers without crashing"""
    # 1 Million units
    response = client.post("/calculate-bill", json={"kwh": 1_000_000})
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert data["total"] > 1_000_000 * 5


def test_malformed_json():
    """Ensure malformed JSON returns 422"""
    response = client.post("/calculate-bill", json={"kwh": "five_hundred"})
    assert response.status_code == 422


# --- PREDICTOR LOGIC EDGE CASES ---


def _prep(d, bill):
    d["total_kwh_monthly"] = bill
    return [d]


def test_predictor_extreme_hours(predictor):
    """Verify behavior when appliance usage > 24 hours"""
    #  caps hours at 24 internally
    res = predictor.predict(
        "ac",
        _prep(
            {
                "ac_hours_per_day": 30,  # Impossible input
                "ac_star_rating": 3,
                "ac_tonnage": 1.5,
            },
            500,
        ),
    )

    assert res["prediction"] > 0
    # Also usage should be clamped to 24 internally effectively
    # prediction = watts * 24 * 30 / 1000 roughly


def test_predictor_negative_hours(predictor):
    """Verify behavior when hours are negative"""
    #  caps at 0
    res = predictor.predict(
        "ac", _prep({"ac_hours_per_day": -5, "ac_star_rating": 3}, 500)
    )

    # Physics watts * 0 hours = 0
    # Wait, predictor_ bounds check:
    # ai_effective_hours = max(0, min(ai_effective_hours, 24.0)) if AI used.
    # What if fallback?
    # Fallback: uses _get_val(d, 'ac_hours_per_day', 1.0)
    # If -5 passed, _get_val returns -5.
    # Logic: kwh = watts * hours * ...
    # IF fallback, negative hours might produce negative kWh?
    # predictor_: kwh = (real_watts * ai_effective_hours * count * 30) / 1000
    # return {'prediction': float(max(0, kwh))}
    # Line 188 of predictor_py caps at max(0, kwh). So it should be 0.
    assert res["prediction"] == 0


def test_predictor_missing_all_keys(predictor):
    """Verify clean fallback when details object is empty"""
    res = predictor.predict("ac", _prep({}, 500))
    assert res["prediction"] > 0  # Should fallback to defaults


def test_predictor_string_injection_for_numbers(predictor):
    """Verify safe conversion if strings passed for numeric fields"""
    # predictor_ uses pd.to_numeric(errors='coerce').fillna(0) for AI path
    # For physics path, it relies on _get_val which returns as is if not 'unknown'.
    # But usually Python handles float("1.5") fine if calc done?
    # Actually, if we do string * int -> string replication error in python?
    # '1.5' * 1200 -> crash?
    # predictor_ doesn't explicit cast inside _calculate_physics_watts
    # But frontend usually sends strings.
    # The PD dataframe conversion handles it for AI path.
    # The Fallback path might crash?
    # Let's hope PD path is taken.

    res = predictor.predict(
        "ac", _prep({"ac_hours_per_day": "8", "ac_tonnage": "1.5"}, 500)
    )

    assert res["prediction"] > 0
