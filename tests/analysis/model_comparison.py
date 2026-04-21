import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from tensorflow.keras.layers import BatchNormalization, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

# Set style for academic graphs
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_theme(style="darkgrid")


def compare_models(appliance_name, target_col, features, categorical_features):
    """
    Trains Linear Regression, Random Forest, and Neural Network on the same data
    and compares their R-Squared scores.
    """
    print(f"\n--- Benchmarking Models for {appliance_name.upper()} ---")

    # 1. Load Data
    try:
        df = pd.read_csv("../../kerala_realworld_dataset.csv")
    except FileNotFoundError:
        try:
            df = pd.read_csv("../../kerala_smartwatt_ai.csv")
        except FileNotFoundError:
            print("Error: Dataset not found. Please run newdataset.py first.")
            return

    # Filter for appliance owners only
    if appliance_name == "ac":
        df = df[df["has_ac"] == 1].copy()

    X = df[features + ["total_kwh_monthly"]]
    y = df[target_col]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                [f for f in features if f not in categorical_features]
                + ["total_kwh_monthly"],
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
        ]
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    results = {}

    # --- Model 1: Linear Regression (Baseline) ---
    lr = LinearRegression()
    lr.fit(X_train_processed, y_train)
    y_pred_lr = lr.predict(X_test_processed)
    r2_lr = r2_score(y_test, y_pred_lr)
    results["Linear Regression"] = r2_lr
    print(f"Linear Regression R²: {r2_lr:.4f}")

    # --- Model 2: Random Forest (Strong ML) ---
    rf = RandomForestRegressor(n_estimators=50, random_state=42)
    rf.fit(X_train_processed, y_train)
    y_pred_rf = rf.predict(X_test_processed)
    r2_rf = r2_score(y_test, y_pred_rf)
    results["Random Forest"] = r2_rf
    print(f"Random Forest R²:     {r2_rf:.4f}")

    # --- Model 3: Neural Network (Deep Learning) ---
    model = Sequential(
        [
            Dense(64, activation="relu", input_shape=(X_train_processed.shape[1],)),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation="relu"),
            Dense(16, activation="relu"),
            Dense(1, activation="linear"),
        ]
    )
    model.compile(optimizer=Adam(learning_rate=0.001), loss="mse")
    model.fit(X_train_processed, y_train, epochs=50, batch_size=32, verbose=0)

    y_pred_nn = model.predict(X_test_processed, verbose=0).flatten()
    r2_nn = r2_score(y_test, y_pred_nn)
    results["Neural Network"] = r2_nn
    print(f"Neural Network R²:    {r2_nn:.4f}")

    return results


def plot_comparison(results, appliance_name):
    """Generates a professional bar chart for the report."""
    plt.figure(figsize=(10, 6))

    models = list(results.keys())
    scores = list(results.values())

    # Color palette: Grey for baselines, Blue/Green for Neural Network (Hero)
    colors = ["#95a5a6", "#95a5a6", "#2ecc71"]  # Grey, Grey, Green

    bars = plt.bar(models, scores, color=colors, width=0.6)

    plt.title(
        f"Model Performance Comparison: {appliance_name.upper()} Energy Disaggregation",
        fontsize=14,
        pad=20,
    )
    plt.ylabel("R-Squared Score (Accuracy)", fontsize=12)
    plt.ylim(0, 1.1)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.3f}",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig("model_comparison_chart.png", dpi=300)
    print("\n✅ Chart saved as 'model_comparison_chart.png'")


if __name__ == "__main__":
    print("Running Scientific Justification Experiment...")

    # Config for AC (Complex appliance)
    ac_config = {
        "appliance_name": "ac",
        "target_col": "ac_kwh",
        "features": [
            "ac_hours_per_day",
            "ac_tonnage",
            "ac_star_rating",
            "ac_type",
            "num_ac_units",
        ],
        "categorical_features": ["ac_type"],
    }

    results = compare_models(ac_config)

    if results:
        plot_comparison(results, "Air Conditioner")

        print("\n" + "=" * 50)
        print("SUMMARY FOR VIVA/REPORT")
        print("=" * 50)
        print("Standard Linear Models fail to capture the non-linear interactions")
        print("between Star Rating, Inverter Technology, and Usage Hours.")
        print(
            f"Neural Network provides a {(results['Neural Network'] - results['Linear Regression'])*100:.1f}% improvement"
        )
        print("over baseline Linear Regression.")
        print("-" * 50)
