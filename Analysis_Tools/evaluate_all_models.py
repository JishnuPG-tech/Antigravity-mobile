"""
Evaluate All Models Script
Loads all 22 trained models and generates a detailed performance report.
"""

import os

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow import keras


def load_data():
    if not os.path.exists("kerala_smartwatt_ai.csv"):
        print("❌ Dataset not found!")
        return None
    return pd.read_csv("kerala_smartwatt_ai.csv")


def evaluate_models():
    df = load_data()
    if df is None:
        return

    # List of all 22 models to evaluate
    tasks = [
        (
            "ac",
            "ac",
            [
                "n_occupants",
                "season",
                "location_type",
                "ac_tonnage",
                "ac_star_rating",
                "ac_type",
                "ac_age_years",
                "ac_usage_pattern",
            ],
        ),
        (
            "fridge",
            "fridge",
            [
                "n_occupants",
                "season",
                "location_type",
                "fridge_capacity",
                "fridge_age",
                "fridge_star_rating",
                "fridge_type",
                "refrigerator_usage_pattern",
            ],
        ),
        (
            "ceiling_fan",
            "ceiling_fan",
            [
                "n_occupants",
                "season",
                "location_type",
                "fan_type",
                "num_fans",
                "fan_usage_pattern",
            ],
        ),
        (
            "television",
            "television",
            [
                "n_occupants",
                "season",
                "location_type",
                "television_type",
                "tv_size",
                "television_usage_pattern",
            ],
        ),
        (
            "washing_machine",
            "washing_machine",
            [
                "n_occupants",
                "season",
                "location_type",
                "wm_type",
                "wm_capacity",
                "wm_star_rating",
                "wm_cycles_per_week",
            ],
        ),
        (
            "water_pump",
            "water_pump",
            [
                "n_occupants",
                "season",
                "location_type",
                "water_pump_hp",
                "pump_usage_pattern",
            ],
        ),
        (
            "water_heater",
            "water_heater",
            [
                "n_occupants",
                "season",
                "location_type",
                "water_heater_type",
                "water_heater_capacity",
                "geyser_usage_pattern",
            ],
        ),
        (
            "iron",
            "iron",
            ["n_occupants", "season", "location_type", "iron_usage_pattern"],
        ),
        (
            "kettle",
            "kettle",
            ["n_occupants", "season", "location_type", "kettle_usage_pattern"],
        ),
        (
            "induction",
            "induction",
            ["n_occupants", "season", "location_type", "induction_usage_pattern"],
        ),
        (
            "desktop",
            "desktop",
            ["n_occupants", "season", "location_type", "desktop_usage_pattern"],
        ),
        (
            "microwave",
            "microwave",
            ["n_occupants", "season", "location_type", "microwave_usage_pattern"],
        ),
        (
            "mixer",
            "mixer",
            ["n_occupants", "season", "location_type", "mixer_usage_pattern"],
        ),
        (
            "rice_cooker",
            "rice_cooker",
            ["n_occupants", "season", "location_type", "rice_cooker_usage_pattern"],
        ),
        (
            "toaster",
            "toaster",
            ["n_occupants", "season", "location_type", "toaster_usage_pattern"],
        ),
        (
            "food_processor",
            "food_processor",
            ["n_occupants", "season", "location_type", "food_processor_usage_pattern"],
        ),
        (
            "laptop",
            "laptop",
            ["n_occupants", "season", "location_type", "laptop_usage_pattern"],
        ),
        (
            "hair_dryer",
            "hair_dryer",
            ["n_occupants", "season", "location_type", "hair_dryer_usage_pattern"],
        ),
        (
            "vacuum",
            "vacuum",
            ["n_occupants", "season", "location_type", "vacuum_usage_pattern"],
        ),
        (
            "led_lights",
            "led_lights",
            ["n_occupants", "season", "location_type", "led_lights_usage_pattern"],
        ),
        (
            "cfl_lights",
            "cfl_lights",
            ["n_occupants", "season", "location_type", "cfl_lights_usage_pattern"],
        ),
        (
            "tube_lights",
            "tube_lights",
            ["n_occupants", "season", "location_type", "tube_lights_usage_pattern"],
        ),
    ]

    results_data = []

    print(
        f"{'APPLIANCE':<20} | {'EFFICIENCY MAE':<15} | {'HOURS MAE':<10} | {'SAMPLES':<8}"
    )
    print("-" * 65)

    for name, prefix, feats in tasks:
        model_path = f"models/{name}_model.keras"
        preprocessor_path = f"models/{name}_preprocessor.pkl"

        if not os.path.exists(model_path) or not os.path.exists(preprocessor_path):
            print(f"⚠️ {name}: Model/Preprocessor not found")
            continue

        try:
            # Load artifacts
            model = keras.models.load_model(model_path)
            preprocessor = joblib.load(preprocessor_path)

            # Filter data
            if f"has_{name}" in df.columns:
                df_app = df[df[f"has_{name}"] == 1].copy()
            elif name == "fridge":
                df_app = df[df["has_refrigerator"] == 1].copy()
            elif name == "desktop":
                df_app = df[df["has_computer"] == 1].copy()
            elif name == "kettle":
                df_app = df[df["has_electric_kettle"] == 1].copy()
            elif name in [
                "microwave",
                "mixer",
                "rice_cooker",
                "toaster",
                "food_processor",
                "laptop",
                "hair_dryer",
                "vacuum",
            ]:
                df_app = df[df[f"has_{name}"] == 1].copy()
            elif name in ["led_lights", "cfl_lights", "tube_lights"]:
                df_app = df[df[f"has_{name}"] == 1].copy()
            else:
                df_app = df.copy()

            if len(df_app) == 0:
                print(f"⚠️ {name}: No data")
                continue

            # Prepare inputs/targets
            X = preprocessor.transform(df_app[feats])
            y_eff_true = df_app[f"{prefix}_real_efficiency_factor"].values
            y_hours_true = df_app[f"{prefix}_real_effective_hours"].values

            # Predict
            preds = model.predict(X, verbose=0)
            y_eff_pred = preds[0].flatten()
            y_hours_pred = preds[1].flatten()

            # Calculate Metrics
            mae_eff = mean_absolute_error(y_eff_true, y_eff_pred)
            mae_hours = mean_absolute_error(y_hours_true, y_hours_pred)

            # Additional logic to handle very large R2 errors if any
            r2_eff = r2_score(y_eff_true, y_eff_pred)
            r2_hours = r2_score(y_hours_true, y_hours_pred)

            print(
                f"{name:<20} | {mae_eff:<15.4f} | {mae_hours:<10.2f} | {len(df_app):<8}"
            )

            results_data.append(
                {
                    "Appliance": name.replace("_", " ").title(),
                    "Efficiency MAE": f"{mae_eff:.4f}",
                    "Hours MAE": f"{mae_hours:.2f}",
                    "Efficiency R²": f"{r2_eff:.3f}",
                    "Hours R²": f"{r2_hours:.3f}",
                    "Samples": len(df_app),
                }
            )

        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")

    # Save to Markdown
    with open("training_results_table.md", "w") as f:
        f.write("# SmartWatt AI Model Performance Report\n\n")
        f.write(
            "| Appliance | Efficiency MAE | Usage Hours MAE | Efficiency R² | Hours R² | Samples |\n"
        )
        f.write(
            "|-----------|----------------|-----------------|---------------|----------|---------|\n"
        )
        for r in results_data:
            f.write(
                f"| {r['Appliance']} | {r['Efficiency MAE']} | {r['Hours MAE']} | {r['Efficiency R²']} | {r['Hours R²']} | {r['Samples']} |\n"
            )

    print("\n✅ Report saved to training_results_table.md")


if __name__ == "__main__":
    evaluate_models()
