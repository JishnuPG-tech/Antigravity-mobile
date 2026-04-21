import json
import os
import sys

import pandas as pd

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predictor import AppliancePredictor


def verify_all_overrides():
    predictor = AppliancePredictor()
    # Preload to ensure we are testing the actual loaded models
    predictor.preload_all_models()

    appliances = [
        "ac",
        "fridge",
        "washing_machine",
        "water_heater",
        "water_pump",
        "ceiling_fan",
        "led_lights",
        "cfl_lights",
        "tube_lights",
        "television",
        "desktop",
        "laptop",
        "mixer",
        "microwave",
        "kettle",
        "induction",
        "rice_cooker",
        "toaster",
        "food_processor",
        "iron",
        "hair_dryer",
        "vacuum",
    ]

    print("\n" + "=" * 60)
    print("      VERIFYING USER OVERRIDE LOGIC FOR ALL APPLIANCES")
    print("=" * 60 + "\n")

    input_hours = 10.0
    failures = []

    # Standard context to avoid 'missing features' errors
    base_context = {
        "n_occupants": 4,
        "total_kwh_monthly": 150,
        "location_type": "urban",
        "season": "summer",
    }

    for app in appliances:
        # Construct input with explicit user hours
        inp = base_context.copy()
        inp[f"{app}_hours"] = input_hours  # Key expected by override logic

        # Add minimal dummy props to avoid basic physics crashes if any
        inp[f"{app}_age"] = "unknown"

        try:
            # Main.py mapping simulation
            # Note: main.py maps 'geyser' -> 'water_heater', etc.
            # But here we use the keys expected by predictor.predict()
            # Predictor expects mapped names (e.g. 'water_heater') OR frontend names?
            # Predictor.predict() handles mapping. passing 'geyser' maps to 'water_heater'.
            # Let's test with the names we used in the list above.

            # Map for list compatibility if needed (e.g. 'geyser' in frontend, 'water_heater' in backend)
            # We will use the backend model names for direct testing stability,
            # but note that 'predictor.predict' has a mapping block (lines 152+).

            test_name = app
            if app == "water_heater":
                test_name = "geyser"  # Simulator frontend
            if app == "ceiling_fan":
                test_name = "fan"

            # Run prediction
            result = predictor.predict(test_name, [inp])

            predicted_hours = result["insights"]["predicted_hours"]
            source = result["insights"]["source"]

            # Check if hours match user input
            if abs(predicted_hours - input_hours) < 0.1:
                print(
                    f"✅ {app.ljust(20)} | Input: {input_hours}h -> Used: {predicted_hours}h | Source: {source}"
                )
            else:
                print(
                    f"❌ {app.ljust(20)} | Input: {input_hours}h -> Used: {predicted_hours}h | Source: {source}"
                )
                failures.append(app)

        except Exception as e:
            print(f"⚠️ {app.ljust(20)} | CRASHED: {str(e)}")
            failures.append(app)

    print("\n" + "=" * 60)
    if not failures:
        print("🎉 ALL SYSTEMS GO: Every appliance respects User Input Hours!")
    else:
        print(f"🚨 FAILURES DETECTED: {len(failures)} appliances ignored input.")
        print(failures)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    verify_all_overrides()
