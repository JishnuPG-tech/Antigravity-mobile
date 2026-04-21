import os
import sys

from fastapi.testclient import TestClient

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "SmartWatt (Hybrid AI + Physics) is Active",
    }


def test_calculate_bill_api():
    """Verify bill calculation endpoint"""
    payload = {"kwh": 500}  # Bi-monthly units
    response = client.post("/calculate-bill", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "monthly" in data
    assert "slab" in data
    assert data["total"] > 0


def test_calculate_bill_invalid_input():
    """Verify validation for negative units"""
    payload = {"kwh": -50}
    response = client.post("/calculate-bill", json=payload)

    # Pydantic validation error is usually 422 Unprocessable Entity
    assert response.status_code == 422


def test_predict_appliance_api_ac():
    """Verify AC prediction endpoint"""
    payload = {
        "appliance_name": "ac",
        "details": {
            "ac_hours_per_day": 8,
            "ac_star_rating": 3,
            "ac_tonnage": 1.5,
            "ac_type": "split",
            "ac_usage_pattern": "moderate",
            "n_occupants": 4,  # Context for AI
        },
        "total_bill": 500,
    }
    response = client.post("/predict-appliance", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prediction"] >= 0


def test_predict_appliance_api_fallback():
    """Verify unknown appliance fallback"""
    payload = {"appliance_name": "unknown_gadget", "details": {}, "total_bill": 500}
    response = client.post("/predict-appliance", json=payload)

    #  handles unknowns via internal physics fallback, returning success
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prediction"] > 0
