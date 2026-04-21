"""
This is the "Teacher".
It takes our fake simulated student data (from newdataset.py) and teaches the AI.
Instead of teaching it to just output one number (Bill), we teach it to understand TWO things:
1. How efficient is the appliance? (Is it old/rusty?)
2. How long is it really used? (Is the user fibbing about usage?)
"""

import os

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from tensorflow import keras
from tensorflow.keras import layers

# Ensure  Model Directory Exists
if not os.path.exists("models"):
    os.makedirs("models")


def load_data():
    if not os.path.exists("kerala_smartwatt_ai.csv"):
        print("❌ Dataset not found! Run newdataset.py first.")
        return None
    return pd.read_csv("kerala_smartwatt_ai.csv")


def build_multi_output_model(input_dim):
    """
    This is the Brain Architecture.
    Imagine a student sharing a brain (Shared Layers) but having two mouths (Split Heads).

    - The Shared Brain learns general concepts (e.g., "Big families use more power").
    - Head 1 (Efficiency) specializes in judging the health of the machine.
    - Head 2 (Hours) specializes in judging the behavior of the humans.
    """
    inputs = keras.Input(shape=(input_dim,))

    # Shared Representation
    x = layers.Dense(128, activation="relu")(inputs)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(64, activation="relu")(x)

    # --- HEAD 1: EFFICIENCY FACTOR ---
    # Target: 0.6 to 1.1 (Ratio)
    eff_branch = layers.Dense(32, activation="relu")(x)
    eff_output = layers.Dense(1, name="efficiency")(eff_branch)

    # --- HEAD 2: EFFECTIVE HOURS ---
    # Target: 0 to 24 (Hours)
    hours_branch = layers.Dense(32, activation="relu")(x)
    hours_output = layers.Dense(1, name="hours")(hours_branch)

    model = keras.Model(inputs=inputs, outputs=[eff_output, hours_output])

    model.compile(
        optimizer="adam",
        loss={"efficiency": "mse", "hours": "mse"},
        # Why weights?
        # Efficiency is a small number (0.6 - 1.1). Hours is a big number (0 - 24).
        # We shout louder about Efficiency (weight=10) so the AI pays attention to small changes.
        loss_weights={"efficiency": 10.0, "hours": 1.0},
        metrics={"efficiency": "mae", "hours": "mae"},
    )
    return model


def train_appliance_model(df, app_name, target_cols, features):
    print(f"\n Training  Model for: {app_name.upper()}")

    # Filter for owners
    if f"has_{app_name}" in df.columns:
        df_app = df[df[f"has_{app_name}"] == 1].copy()
    elif app_name == "fridge":
        df_app = df[df["has_refrigerator"] == 1].copy()
    elif app_name == "desktop":
        df_app = df[df["has_computer"] == 1].copy()
    elif app_name == "kettle":
        df_app = df[df["has_electric_kettle"] == 1].copy()
    elif app_name in [
        "microwave",
        "mixer",
        "rice_cooker",
        "toaster",
        "food_processor",
        "laptop",
        "hair_dryer",
        "vacuum",
    ]:
        df_app = df[df[f"has_{app_name}"] == 1].copy()
    elif app_name in ["led_lights", "cfl_lights", "tube_lights"]:
        df_app = df[df[f"has_{app_name}"] == 1].copy()
    else:
        df_app = df.copy()  # Fallback

    if len(df_app) < 100:
        print(f"⚠️ Not enough data for {app_name} (n={len(df_app)})")
        return

    # Prepare specific targets
    # Expecting cols like 'ac_real_efficiency_factor', 'ac_real_effective_hours'
    y_eff = df_app[f"{app_name}_real_efficiency_factor"]
    y_hours = df_app[f"{app_name}_real_effective_hours"]

    # Preprocessing
    # Separate numeric and categorical
    numeric_features = [f for f in features if df_app[f].dtype in ["int64", "float64"]]
    categorical_features = [f for f in features if df_app[f].dtype == "object"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    X = preprocessor.fit_transform(df_app[features])

    # Split
    X_train, X_test, y_eff_train, y_eff_test, y_hours_train, y_hours_test = (
        train_test_split(X, y_eff, y_hours, test_size=0.2, random_state=42)
    )

    # Build & Train
    model = build_multi_output_model(X.shape[1])

    history = model.fit(
        X_train,
        {"efficiency": y_eff_train, "hours": y_hours_train},
        validation_data=(X_test, {"efficiency": y_eff_test, "hours": y_hours_test}),
        epochs=30,  # Quick train for demo
        batch_size=32,
        verbose=0,
    )

    # Evaluate
    results = model.evaluate(
        X_test, {"efficiency": y_eff_test, "hours": y_hours_test}, verbose=0
    )
    print(
        f"   ✅ Trained. MAE Efficiency: {results[3]:.4f}, MAE Hours: {results[4]:.2f}"
    )

    # Save Artifacts
    model.save(f"models/{app_name}_model.keras")
    joblib.dump(preprocessor, f"models/{app_name}_preprocessor.pkl")
    print(f"   💾 Saved to models/{app_name}_model.keras")


def run_training():
    df = load_data()
    if df is None:
        return

    # List of models to train
    # Format: (name, target_prefix, features)
    # Updated to match UI fields exactly - ALL UI FIELDS USED (except hours/total_units)
    # All appliances now include usage patterns for AI-driven personalization
    tasks = [
        # MAJOR APPLIANCES - Use all UI collected fields + patterns
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
        # MISC APPLIANCES - Include base fields for context + patterns
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

    for name, prefix, feats in tasks:
        train_appliance_model(
            df,
            name,
            target_cols=[
                f"{prefix}_real_efficiency_factor",
                f"{prefix}_real_effective_hours",
            ],
            features=feats,
        )

    print("\n✅  Training Complete (7 Models)!")


if __name__ == "__main__":
    run_training()
