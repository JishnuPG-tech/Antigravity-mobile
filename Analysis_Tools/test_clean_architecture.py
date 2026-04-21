"""
Test script to demonstrate new clean batch prediction architecture
"""

import json

import requests

# Test data - household with multiple appliances
test_request = {
    "requests": [
        {
            "appliance_name": "ac",
            "total_bill": 150.0,
            "details": {
                "num_people": 3,
                "season": "monsoon",
                "ac_tonnage": 1.5,
                "ac_star": 3,
                "ac_hours": 6,
            },
        },
        {
            "appliance_name": "fridge",
            "total_bill": 150.0,
            "details": {
                "num_people": 3,
                "season": "monsoon",
                "fridge_capacity_liters": 250,
                "fridge_age_years": 5,
                "fridge_star": 4,
            },
        },
        {
            "appliance_name": "ceiling_fan",
            "total_bill": 150.0,
            "details": {
                "num_people": 3,
                "season": "monsoon",
                "num_ceiling_fans": 4,
                "fan_hours": 12,
            },
        },
        {
            "appliance_name": "led_light",
            "total_bill": 150.0,
            "details": {
                "num_people": 3,
                "season": "monsoon",
                "num_led": 10,
                "led_hours": 5,
            },
        },
        {
            "appliance_name": "television",
            "total_bill": 150.0,
            "details": {
                "num_people": 3,
                "season": "monsoon",
                "tv_size_inches": 43,
                "tv_type": "LED",
                "tv_pattern": "moderate",
            },
        },
    ]
}

print("=" * 80)
print("TESTING NEW CLEAN BATCH PREDICTION ARCHITECTURE")
print("=" * 80)
print(f"\nSending batch request with {len(test_request['requests'])} appliances...")
print()

# Make request
response = requests.post("http://localhost:8000/predict-all", json=test_request)

if response.status_code == 200:
    results = response.json()
    print("\n" + "=" * 80)
    print("API RESPONSE RECEIVED")
    print("=" * 80)

    total_kwh = 0
    for appliance, data in results.items():
        kwh = data.get("prediction", 0)
        total_kwh += kwh
        source = data.get("insights", {}).get("source", "Unknown")
        print(f"{appliance:20}: {kwh:6.2f} kWh ({source})")

    print("-" * 80)
    print(f"{'TOTAL':20}: {total_kwh:6.2f} kWh")
    print("=" * 80)
else:
    print(f"Error: {response.status_code}")
    print(response.text)

print("\n\nCheck the backend console for CLEAN LOGGING OUTPUT!")
