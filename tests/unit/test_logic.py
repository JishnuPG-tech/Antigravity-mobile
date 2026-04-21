import os
import sys

import pytest

# Add parent dir to path to import backend modules
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from predictor import get_predictor


@pytest.fixture(scope="module")
def predictor():
    pred = get_predictor()
    pred.preload_all_models()
    return pred


def _prep(d, bill):
    defaults = {
        "n_occupants": 4,
        "location_type": "urban",
        "season": "summer",
        "total_kwh_monthly": bill,
    }
    # Merge d into defaults
    full = defaults.copy()
    full.update(d)
    return [full]


# --- BASIC LOGIC TESTS ---


def test_ac_physics_logic(predictor):
    """Verify 5-Star AC consumes less than 3-Star AC for same hours"""
    bill = 500

    # 3-Star Case
    res_3star = predictor.predict(
        "ac",
        _prep({"ac_hours_per_day": 8, "ac_star_rating": 3, "ac_tonnage": 1.5}, bill),
    )["prediction"]

    # 5-Star Case
    res_5star = predictor.predict(
        "ac",
        _prep({"ac_hours_per_day": 8, "ac_star_rating": 5, "ac_tonnage": 1.5}, bill),
    )["prediction"]

    assert (
        res_5star < res_3star
    ), f"5-Star AC ({res_5star}) should consume less than 3-Star ({res_3star})"


def test_fridge_age_logic(predictor):
    """Verify Old Fridge (10+ yrs) consumes more than New Fridge"""
    bill = 300

    # New Fridge
    res_new = predictor.predict(
        "fridge", _prep({"fridge_capacity": 250, "fridge_age": 2}, bill)
    )["prediction"]

    # Old Fridge
    res_old = predictor.predict(
        "fridge", _prep({"fridge_capacity": 250, "fridge_age": 15}, bill)
    )["prediction"]

    assert (
        res_old > res_new
    ), f"Old Fridge ({res_old}) should consume more than New ({res_new})"


def test_fan_bldc_logic(predictor):
    """Verify BLDC Fan consumes significantly less than Standard"""
    bill = 300

    # Standard Fan (75W)
    res_std = predictor.predict(
        "ceiling_fan", _prep({"fan_type": "standard", "fan_hours": 10}, bill)
    )["prediction"]

    # BLDC Fan (30W)
    res_bldc = predictor.predict(
        "ceiling_fan", _prep({"fan_type": "bldc", "fan_hours": 10}, bill)
    )["prediction"]

    # Expected: Standard ~750Wh, BLDC ~300Wh (Prediction is kWh/month -> /1000 * 30)
    # Actually, prediction returns TOTAL kWh for the period (usually monthly).
    # Since inputs are usually scaled, let's just assert relative order.

    assert (
        res_bldc < res_std * 0.6
    ), f"BLDC ({res_bldc}) should be < 60% of Standard ({res_std})"


# --- ROBUSTNESS TESTS ---


def test_missing_keys_fallback(predictor):
    """Verify predictor handles missing keys without crashing"""
    # Empty details
    res = predictor.predict("ac", _prep({}, 500))
    assert (
        res["prediction"] >= 0
    ), "Should return valid prediction even with empty input"


def test_zero_bill_handling(predictor):
    """Verify behavior when total bill is 0 (unlikely but possible boundary)"""
    res = predictor.predict("ac", _prep({"ac_hours_per_day": 5}, 0))
    assert isinstance(res["prediction"], (int, float))


def test_extreme_usage_inputs(predictor):
    """Verify reasonable caps or non-crash on extreme inputs"""
    # 25 hours per day (impossible)
    res = predictor.predict("ac", _prep({"ac_hours_per_day": 25}, 500))
    assert res["prediction"] > 0
