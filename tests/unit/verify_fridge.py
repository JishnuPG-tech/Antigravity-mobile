import os
import sys

import pandas as pd

# Add Backend to path
sys.path.append(os.getcwd())

from predictor import get_predictor


# --- THE "FRIDGE POLICE" TEST ---
# Users often lie. They say they use the Fridge "24 hours".
# If we believed them, the bill would be huge!
# The AI knows better. It knows a Fridge cycles on/off (Duty Cycle).
# This test checks if the "Detective" correctly catches this lie.
def test_fridge():
    p = get_predictor()

    # Payload simulating Frontend sending 24h usage
    details = [
        {
            "fridge_hours": 24,
            "fridge_capacity": 250,
            "fridge_age": 5,
            "total_kwh_monthly": 150,
        }
    ]

    print("--- Testing Fridge Logic ---")
    res = p.predict("fridge", details)
    pred_kwh = res["prediction"]
    insights = res["insights"]

    print(f"Input Hours: 24")
    print(f"Predicted kWh: {pred_kwh:.2f}")
    print(f"Effective Hours Used: {insights['predicted_hours']}")
    print(f"Real Watts: {insights['real_watts']}")

    if pred_kwh < 60:
        print("✅ PASS: Duty Cycle Applied correctly.")
    else:
        print("❌ FAIL: Still predicting jet-engine usage.")


if __name__ == "__main__":
    test_fridge()
