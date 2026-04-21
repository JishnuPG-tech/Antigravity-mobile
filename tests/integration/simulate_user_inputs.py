import os
import sys

import numpy as np
import pandas as pd
from predictor import get_predictor

# Suppress TF logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def run_simulation():
    print("Initializing Predictor...")
    predictor = get_predictor()

    # Target Values from User
    TARGET_FRIDGE = 178.68
    TARGET_AC = 112.31
    BILL = 150  # User said 150 units bill

    print(f"\n--- Simulating FRIDGE (Target: ~{TARGET_FRIDGE}) ---")
    fridge_scenarios = []
    for age in [1, 3, 5, 10, 15]:
        for cap in [190, 240, 350]:
            for star in [1, 3, 5]:
                inputs = {
                    "fridge_capacity": cap,
                    "fridge_age": age,
                    "fridge_star": star,
                    "fridge_type": "double_door" if cap > 250 else "direct_cool",
                }
                res = predictor.predict_fridge(inputs, BILL)
                val = res["prediction"]
                if abs(val - TARGET_FRIDGE) < 20:  # Loose tolerance
                    print(f"MATCH FOUND: {inputs} => {val:.2f} kWh")

    print(f"\n--- Simulating AC (Target: ~{TARGET_AC}) ---")
    ac_scenarios = []
    for hours in [3, 4, 5, 6, 8]:
        for ton in [1.0, 1.5, 2.0]:
            for star in [3, 5]:
                inputs = {
                    "ac_hours": hours,
                    "ac_tonnage": ton,
                    "ac_star": star,
                    "ac_type": "split",
                }
                res = predictor.predict_ac(inputs, BILL)
                val = res["prediction"]
                if abs(val - TARGET_AC) < 15:
                    print(f"MATCH FOUND: {inputs} => {val:.2f} kWh")


if __name__ == "__main__":
    run_simulation()
