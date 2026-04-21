import os
import sys

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from predictor import AppliancePredictor


def verify_fix():
    predictor = AppliancePredictor()
    # No need to preload all, just load these two
    predictor._load_model("ceiling_fan")
    predictor._load_model("water_heater")

    # Test Ceiling Fan (Input Name: fan)
    inp_fan = {"fan_hours": 10.0, "n_occupants": 4, "total_kwh_monthly": 150}
    res_fan = predictor.predict("fan", [inp_fan])

    # Test Geyser (Input Name: geyser)
    inp_geyser = {
        "geyser_hours": 10.0,
        "n_occupants": 4,
        "total_kwh_monthly": 150,
        "season": "monsoon",
    }
    res_geyser = predictor.predict("geyser", [inp_geyser])

    print("\n--- RESULTS ---")
    print(
        f"Fan (Input 10h) -> Used: {res_fan['insights']['predicted_hours']}h | Source: {res_fan['insights']['source']}"
    )
    print(
        f"Geyser (Input 10h) -> Used: {res_geyser['insights']['predicted_hours']}h | Source: {res_geyser['insights']['source']}"
    )

    if (
        res_fan["insights"]["predicted_hours"] == 10.0
        and res_geyser["insights"]["predicted_hours"] == 10.0
    ):
        print("✅ FIX VERIFIED: Keys are now robust!")
    else:
        print("❌ STILL FAILING")


if __name__ == "__main__":
    verify_fix()
