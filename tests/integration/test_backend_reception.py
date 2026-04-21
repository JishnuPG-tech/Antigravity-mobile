"""
Backend Data Reception Validation Script
Tests if backend correctly receives and processes UI data
"""

import json

import requests

# Backend URL (adjust if needed)
BASE_URL = "http://localhost:8000"


def test_backend_data_reception():
    print("=" * 80)
    print("BACKEND DATA RECEPTION VALIDATION")
    print("=" * 80)

    # Test 1: Health Check
    print("\n[TEST 1] Health Check")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Backend is running: {response.json()}")
        else:
            print(f"[FAIL] Backend returned status {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] Cannot connect to backend: {e}")
        print("\nMake sure backend is running:")
        print("  cd Backend")
        print("  uvicorn main:app --reload")
        return

    # Test 2: AC Prediction with all UI fields
    print("\n[TEST 2] AC Prediction - All UI Fields")
    print("-" * 80)

    ac_request = {
        "appliance_name": "air_conditioner",
        "total_bill": 500,
        "details": {
            # Base fields (from HouseholdInfo)
            "n_occupants": 4,
            "season": "summer",
            "location_type": "urban",
            # AC specific fields (from UsageDetails)
            "ac_tonnage": 1.5,
            "ac_star_rating": 5,
            "num_ac_units": 1,
            "ac_type": "inverter",
            "ac_usage_pattern": "moderate",
            "ac_hours_per_day": 6,
        },
    }

    print(f"Request payload:")
    print(json.dumps(ac_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict-appliance", json=ac_request, timeout=10
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"\n[OK] AC Prediction received: {result.get('prediction')} kWh")
            else:
                print(
                    f"\n[WARN] Prediction returned with status: {result.get('status')}"
                )
        else:
            print(f"\n[FAIL] Request failed with status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

    # Test 3: Fridge Prediction
    print("\n[TEST 3] Fridge Prediction - All UI Fields")
    print("-" * 80)

    fridge_request = {
        "appliance_name": "refrigerator",
        "total_bill": 500,
        "details": {
            # Base fields
            "n_occupants": 4,
            "season": "monsoon",
            "location_type": "rural",
            # Fridge specific fields
            "fridge_capacity_liters": 240,
            "fridge_age_years": 3,
            "fridge_star_rating": 4,
            "fridge_type": "frost_free",
            "fridge_hours_per_day": 24,
        },
    }

    print(f"Request payload:")
    print(json.dumps(fridge_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict-appliance", json=fridge_request, timeout=10
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(
                    f"\n[OK] Fridge Prediction received: {result.get('prediction')} kWh"
                )
        else:
            print(f"\n[FAIL] Request failed")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

    # Test 4: Washing Machine with cycles_per_week
    print("\n[TEST 4] Washing Machine - wm_cycles_per_week")
    print("-" * 80)

    wm_request = {
        "appliance_name": "washing_machine",
        "total_bill": 500,
        "details": {
            "n_occupants": 4,
            "season": "monsoon",
            "location_type": "urban",
            "wm_capacity_kg": 7.0,
            "wm_star_rating": 4,
            "wm_type": "front_load",
            "wm_cycles_per_week": 4,
        },
    }

    print(f"Request payload:")
    print(json.dumps(wm_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict-appliance", json=wm_request, timeout=10
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"\n[OK] WM Prediction received: {result.get('prediction')} kWh")
        else:
            print(f"\n[FAIL] Request failed")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

    # Test 5: Water Heater (Geyser) with type and capacity
    print("\n[TEST 5] Water Heater - type and capacity")
    print("-" * 80)

    geyser_request = {
        "appliance_name": "water_heater",
        "total_bill": 500,
        "details": {
            "n_occupants": 4,
            "season": "winter",
            "location_type": "urban",
            "water_heater_capacity_liters": 15,
            "water_heater_type": "storage",
            "water_heater_usage_hours": 2,
        },
    }

    print(f"Request payload:")
    print(json.dumps(geyser_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict-appliance", json=geyser_request, timeout=10
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(
                    f"\n[OK] Water Heater Prediction received: {result.get('prediction')} kWh"
                )
        else:
            print(f"\n[FAIL] Request failed")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

    # Test 6: Missing Required Field
    print("\n[TEST 6] Validation Test - Missing Required Field")
    print("-" * 80)

    invalid_request = {
        "appliance_name": "air_conditioner",
        "total_bill": 500,
        "details": {
            "n_occupants": 4,
            "season": "summer",
            # Missing: location_type, ac_tonnage, ac_type, etc.
        },
    }

    print(f"Request payload (intentionally incomplete):")
    print(json.dumps(invalid_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict-appliance", json=invalid_request, timeout=10
        )

        print(f"\nResponse status: {response.status_code}")
        result = response.json()
        print(f"Response body:")
        print(json.dumps(result, indent=2))

        if result.get("status") == "error":
            print(f"\n[OK] Backend correctly rejected invalid request")
        else:
            print(f"\n[WARN] Backend should have rejected this request")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print("""
Key Checks:
1. Backend health endpoint responding
2. AC prediction with all 7 UI fields (including season, location_type)
3. Fridge prediction with all 7 UI fields
4. Washing Machine with wm_cycles_per_week
5. Water Heater with type and capacity
6. Validation for missing fields

Expected Behavior:
- Backend should accept all UI fields from schemas.py
- Pydantic should validate field types and patterns
- Models should receive: n_occupants, season, location_type + specific fields
- Invalid requests should be rejected with error message
    """)
    print("=" * 80)


if __name__ == "__main__":
    test_backend_data_reception()
