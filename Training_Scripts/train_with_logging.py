"""
Enhanced Training Script with History Logging
Runs actual training and saves history for visualization
"""

import json
import os

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from tensorflow import keras
from tensorflow.keras import layers

# Ensure directories exist
os.makedirs("models", exist_ok=True)
os.makedirs("training_logs", exist_ok=True)


def load_data():
    if not os.path.exists("kerala_smartwatt_ai.csv"):
        print("❌ Dataset not found! Run newdataset.py first.")
        return None
    return pd.read_csv("kerala_smartwatt_ai.csv")


def build_multi_output_model(input_dim):
    inputs = keras.Input(shape=(input_dim,))

    # Shared layers
    x = layers.Dense(128, activation="relu")(inputs)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(64, activation="relu")(x)

    # Efficiency head
    eff_branch = layers.Dense(32, activation="relu")(x)
    eff_output = layers.Dense(1, name="efficiency")(eff_branch)

    # Hours head
    hours_branch = layers.Dense(32, activation="relu")(x)
    hours_output = layers.Dense(1, name="hours")(hours_branch)

    model = keras.Model(inputs=inputs, outputs=[eff_output, hours_output])

    model.compile(
        optimizer="adam",
        loss={"efficiency": "mse", "hours": "mse"},
        loss_weights={"efficiency": 10.0, "hours": 1.0},
        metrics={"efficiency": "mae", "hours": "mae"},
    )
    return model


def train_single_appliance_with_logging(df, app_name="ac"):
    """Train a single appliance model and log the history"""
    print(f"\n🚀 Training {app_name.upper()} model with full logging...")

    # Filter data
    if app_name == "ac":
        df_app = df[df["has_ac"] == 1].copy()
        features = [
            "n_occupants",
            "season",
            "location_type",
            "ac_tonnage",
            "ac_star_rating",
            "ac_type",
            "ac_age_years",
            "ac_usage_pattern",
        ]
    elif app_name == "fridge":
        df_app = df[df["has_refrigerator"] == 1].copy()
        features = [
            "n_occupants",
            "season",
            "location_type",
            "fridge_capacity",
            "fridge_age",
            "fridge_star_rating",
            "fridge_type",
            "refrigerator_usage_pattern",
        ]
    else:
        print(f"❌ Appliance {app_name} not configured")
        return None

    print(f"   Dataset size: {len(df_app)} households")

    # Prepare targets
    y_eff = df_app[f"{app_name}_real_efficiency_factor"]
    y_hours = df_app[f"{app_name}_real_effective_hours"]

    # Preprocessing
    numeric_features = [f for f in features if df_app[f].dtype in ["int64", "float64"]]
    categorical_features = [f for f in features if df_app[f].dtype == "object"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    X = preprocessor.fit_transform(df_app[features])

    # Train/test split
    X_train, X_test, y_eff_train, y_eff_test, y_hours_train, y_hours_test = (
        train_test_split(X, y_eff, y_hours, test_size=0.2, random_state=42)
    )

    # Build model
    model = build_multi_output_model(X.shape[1])

    # Train with verbose output
    print(f"   Training for 30 epochs...")
    history = model.fit(
        X_train,
        {"efficiency": y_eff_train, "hours": y_hours_train},
        validation_data=(X_test, {"efficiency": y_eff_test, "hours": y_hours_test}),
        epochs=30,
        batch_size=32,
        verbose=1,
    )

    # Save history
    history_dict = {
        "loss": [float(x) for x in history.history["loss"]],
        "efficiency_loss": [float(x) for x in history.history["efficiency_loss"]],
        "hours_loss": [float(x) for x in history.history["hours_loss"]],
        "val_loss": [float(x) for x in history.history["val_loss"]],
        "val_efficiency_loss": [
            float(x) for x in history.history["val_efficiency_loss"]
        ],
        "val_hours_loss": [float(x) for x in history.history["val_hours_loss"]],
        "efficiency_mae": [float(x) for x in history.history["efficiency_mae"]],
        "hours_mae": [float(x) for x in history.history["hours_mae"]],
        "val_efficiency_mae": [float(x) for x in history.history["val_efficiency_mae"]],
        "val_hours_mae": [float(x) for x in history.history["val_hours_mae"]],
    }

    # Save to file
    with open(f"training_logs/{app_name}_training_history.json", "w") as f:
        json.dump(history_dict, f, indent=2)

    print(f"\n   ✅ Training complete!")
    print(f"   📊 Final metrics:")
    print(f"      Training Loss: {history_dict['loss'][-1]:.4f}")
    print(f"      Validation Loss: {history_dict['val_loss'][-1]:.4f}")
    print(f"      Efficiency MAE: {history_dict['val_efficiency_mae'][-1]:.4f}")
    print(f"      Hours MAE: {history_dict['val_hours_mae'][-1]:.2f}")
    print(f"   💾 History saved to training_logs/{app_name}_training_history.json")

    return history_dict


if __name__ == "__main__":
    df = load_data()
    if df is not None:
        # Train AC model as representative example
        history = train_single_appliance_with_logging(df, "ac")
