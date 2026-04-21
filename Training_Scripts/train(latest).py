"""
Training Demo Script with Visualization
This is the "Teacher" with built-in graph generation.
It trains the AI and automatically generates training accuracy/loss graphs.
"""

import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping

# Ensure Model Directory Exists
if not os.path.exists("models"):
    os.makedirs("models")
if not os.path.exists("training_graphs"):
    os.makedirs("training_graphs")


def load_data():
    if not os.path.exists("kerala_smartwatt_ai.csv"):
        print("❌ Dataset not found! Run newdataset.py first.")
        return None
    return pd.read_csv("kerala_smartwatt_ai.csv")


def build_multi_output_model(input_dim):
    """
    This is the Brain Architecture.
    Shared layers → Split heads for Efficiency and Hours
    """
    inputs = keras.Input(shape=(input_dim,))

    # Shared Representation
    x = layers.Dense(128, activation="relu")(inputs)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(64, activation="relu")(x)

    # --- HEAD 1: EFFICIENCY FACTOR ---
    eff_branch = layers.Dense(32, activation="relu")(x)
    eff_output = layers.Dense(1, name="efficiency")(eff_branch)

    # --- HEAD 2: EFFECTIVE HOURS ---
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


# Store all training results and histories for final graphs
all_results = []
all_histories = []


def plot_averaged_training_curves():
    """
    Generate Figure 2.1.2: Averaged Training Curves Across All 22 Models

    Shows training/validation loss and MAE over epochs (averaged across all models).
    This demonstrates overall model convergence - exactly what Figure 2.1.2 needs.
    """
    if not all_histories:
        print("⚠️ No training histories to plot")
        return

    # Find minimum epoch count (models stopped at different epochs due to EarlyStopping)
    min_epochs = min(len(h.history["loss"]) for h in all_histories)
    print(
        f"\n   ℹ️ Averaging across {len(all_histories)} models up to {min_epochs} epochs (shortest training)"
    )

    # Average training metrics across all models (truncate to min_epochs)
    avg_loss = np.mean([h.history["loss"][:min_epochs] for h in all_histories], axis=0)
    avg_val_loss = np.mean(
        [h.history["val_loss"][:min_epochs] for h in all_histories], axis=0
    )
    avg_mae = np.mean(
        [h.history["efficiency_mae"][:min_epochs] for h in all_histories], axis=0
    )
    avg_val_mae = np.mean(
        [h.history["val_efficiency_mae"][:min_epochs] for h in all_histories], axis=0
    )

    epochs = range(1, len(avg_loss) + 1)

    # Calculate statistics
    initial_loss = avg_loss[0]
    final_loss = avg_loss[-1]
    final_mae = avg_mae[-1]
    loss_reduction = (initial_loss - final_loss) / initial_loss * 100

    # Create Figure 2.1.2
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Figure 2.1.2: Neural Network Training Performance (Averaged Across 22 Models)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # LEFT: Loss Curves
    axes[0].plot(
        epochs,
        avg_loss,
        label="Training Loss",
        linewidth=2.5,
        color="#3b82f6",
        marker="o",
        markersize=3,
    )
    axes[0].plot(
        epochs,
        avg_val_loss,
        label="Validation Loss",
        linewidth=2.5,
        color="#f59e0b",
        marker="s",
        markersize=3,
    )
    axes[0].set_title("Training & Validation Loss", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Epoch", fontsize=11)
    axes[0].set_ylabel("Loss (MSE)", fontsize=11)
    axes[0].legend(fontsize=10)
    axes[0].grid(True, alpha=0.3, linestyle="--")

    # RIGHT: Accuracy Curves (MAE)
    axes[1].plot(
        epochs,
        avg_mae,
        label="Training MAE",
        linewidth=2.5,
        color="#10b981",
        marker="o",
        markersize=3,
    )
    axes[1].plot(
        epochs,
        avg_val_mae,
        label="Validation MAE",
        linewidth=2.5,
        color="#ef4444",
        marker="s",
        markersize=3,
    )
    axes[1].set_title("Prediction Accuracy (MAE)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Epoch", fontsize=11)
    axes[1].set_ylabel("Mean Absolute Error", fontsize=11)
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()

    # Save as Figure 2.1.2
    graph_path = "training_graphs/figure_2.1.2_training_curves.png"
    plt.savefig(graph_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    # Print comprehensive statistics
    print("\n" + "=" * 70)
    print("📊 FIGURE 2.1.2 - TRAINING STATISTICS (Averaged Across 22 Models)")
    print("=" * 70)
    print(f"\n🔄 LOSS (MSE):")
    print(f"   • Initial Training Loss (Epoch 1):      {initial_loss:.4f}")
    print(f"   • Final Training Loss (Epoch {len(epochs)}):       {final_loss:.4f}")
    print(
        f"   • Final Validation Loss (Epoch {len(epochs)}):     {avg_val_loss[-1]:.4f}"
    )
    print(f"   • Loss Reduction:                        {loss_reduction:.1f}%")

    print(f"\n✅ ACCURACY (MAE - Lower is Better):")
    print(f"   • Final Training MAE:                    {final_mae:.4f}")
    print(f"   • Final Validation MAE:                  {avg_val_mae[-1]:.4f}")
    print(
        f"   • Train-Val Gap:                         {abs(final_mae - avg_val_mae[-1]):.4f}"
    )

    if abs(final_mae - avg_val_mae[-1]) < 0.02:
        print(f"   • Overfitting Status:                    ✅ No overfitting detected")
    else:
        print(f"   • Overfitting Status:                    ⚠️ Minor gap present")

    print(f"\n📈 CONVERGENCE:")
    print(f"   • Average Epochs Trained:                {len(epochs)}")
    print(f"   • Total Models:                          {len(all_histories)}")
    print(f"   • Models Used EarlyStopping:             Yes (Patience=10)")
    print("=" * 70)

    print(f"\n✅ FIGURE 2.1.2 SAVED: {graph_path}")
    print("   📊 Left Panel: Training & Validation Loss over Epochs")
    print("   📊 Right Panel: MAE Accuracy over Epochs")
    print("   📊 Graph shows model convergence and learning effectiveness\n")


def plot_comprehensive_comparison_graphs():
    """
    Generate TWO professional graphs for academic report:
    Graph 1: Bar Chart - MAE Efficiency across all models
    Graph 2: Dual-Line Chart - Efficiency vs Hours MAE comparison
    """
    if not all_results:
        print("⚠️ No training results to plot")
        return

    appliances = [r["appliance"] for r in all_results]
    mae_eff = [r["mae_efficiency"] for r in all_results]
    mae_hours = [r["mae_hours"] for r in all_results]

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=300)
    fig.suptitle(
        "SmartWatt AI: Model Performance Comparison Across All 22 Appliances",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # GRAPH 1: Bar Chart - MAE Efficiency
    colors = plt.cm.viridis([i / len(appliances) for i in range(len(appliances))])
    bars = ax1.bar(
        range(len(appliances)), mae_eff, color=colors, edgecolor="black", linewidth=0.5
    )
    ax1.set_xticks(range(len(appliances)))
    ax1.set_xticklabels(
        [a.replace("_", " ").title() for a in appliances],
        rotation=90,
        ha="right",
        fontsize=8,
    )
    ax1.set_ylabel("MAE (Efficiency Factor)", fontsize=11, fontweight="bold")
    ax1.set_title(
        "Efficiency Prediction Error by Appliance",
        fontsize=13,
        fontweight="bold",
        pad=10,
    )
    ax1.grid(True, alpha=0.3, axis="y")
    ax1.set_ylim(0, max(mae_eff) * 1.15)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, mae_eff)):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=6,
            rotation=0,
        )

    # GRAPH 2: Dual-Line Chart - Efficiency vs Hours MAE
    x_pos = range(len(appliances))
    line1 = ax2.plot(
        x_pos,
        mae_eff,
        marker="o",
        markersize=6,
        linewidth=2,
        label="Efficiency MAE",
        color="#2E7D32",
    )
    line2 = ax2.plot(
        x_pos,
        mae_hours,
        marker="s",
        markersize=6,
        linewidth=2,
        label="Hours MAE",
        color="#F57C00",
    )

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(
        [a.replace("_", " ").title() for a in appliances],
        rotation=90,
        ha="right",
        fontsize=8,
    )
    ax2.set_ylabel("MAE", fontsize=11, fontweight="bold")
    ax2.set_title(
        "Efficiency vs Hours Prediction Error Comparison",
        fontsize=13,
        fontweight="bold",
        pad=10,
    )
    ax2.legend(loc="upper left", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, max(max(mae_eff), max(mae_hours)) * 1.15)

    # Add average performance line
    avg_eff = sum(mae_eff) / len(mae_eff)
    avg_hours = sum(mae_hours) / len(mae_hours)
    ax2.axhline(
        y=avg_eff,
        color="#2E7D32",
        linestyle="--",
        alpha=0.5,
        linewidth=1.5,
        label=f"Avg Efficiency MAE: {avg_eff:.3f}",
    )
    ax2.axhline(
        y=avg_hours,
        color="#F57C00",
        linestyle="--",
        alpha=0.5,
        linewidth=1.5,
        label=f"Avg Hours MAE: {avg_hours:.2f}",
    )
    ax2.legend(loc="upper left", fontsize=9, framealpha=0.9)

    plt.tight_layout()

    # Save graph
    graph_path = "training_graphs/model_performance_comparison.png"
    plt.savefig(graph_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\n✅ COMPREHENSIVE COMPARISON GRAPHS SAVED: {graph_path}")
    print(f"   📊 Graph 1: MAE Efficiency Bar Chart (All 22 Models)")
    print(f"   📊 Graph 2: Efficiency vs Hours Dual-Line Comparison")
    print(f"   📈 Average Efficiency MAE: {avg_eff:.4f}")
    print(f"   📈 Average Hours MAE: {avg_hours:.2f}")
    plt.close()


def train_appliance_model(df, app_name, target_cols, features):
    print(f"\n🎓 Training Model for: {app_name.upper()}")

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
        df_app = df.copy()

    if len(df_app) < 100:
        print(f"⚠️ Not enough data for {app_name} (n={len(df_app)})")
        return

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

    # Split
    X_train, X_test, y_eff_train, y_eff_test, y_hours_train, y_hours_test = (
        train_test_split(X, y_eff, y_hours, test_size=0.2, random_state=42)
    )

    # Build & Train
    model = build_multi_output_model(X.shape[1])

    # Define Early Stopping
    early_stopping = EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True, verbose=1
    )

    print(f"   Training on {len(X_train)} samples with EarlyStopping (Patience=10)...")
    history = model.fit(
        X_train,
        {"efficiency": y_eff_train, "hours": y_hours_train},
        validation_data=(X_test, {"efficiency": y_eff_test, "hours": y_hours_test}),
        epochs=120,  # Increased from 30 to allow full convergence
        batch_size=32,
        callbacks=[early_stopping],
        verbose=1,  # Show progress
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

    # Store history for averaged training curves (Figure 2.1.2)
    all_histories.append(history)

    # Return results for comparison graph
    return {
        "appliance": app_name,
        "mae_efficiency": results[3],
        "mae_hours": results[4],
    }


def run_training():
    df = load_data()
    if df is None:
        return

    # Train just AC model as demo (you can add more appliances)
    print("\n" + "=" * 60)
    print(" SMARTWATT AI TRAINING DEMO WITH VISUALIZATION")
    print("=" * 60)

    # Train all 22 appliance models
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

    for name, prefix, feats in tasks:
        result = train_appliance_model(
            df,
            name,
            target_cols=[
                f"{prefix}_real_efficiency_factor",
                f"{prefix}_real_effective_hours",
            ],
            features=feats,
        )
        if result:
            all_results.append(result)

    # Generate Figure 2.1.2: Averaged training curves over epochs
    plot_averaged_training_curves()

    # Generate comprehensive comparison graphs (bonus analysis)
    plot_comprehensive_comparison_graphs()

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print(f"📊 Trained {len(all_results)} models successfully")
    print("📊 Figure 2.1.2: training_graphs/figure_2.1.2_training_curves.png")
    print("📊 Comparison: training_graphs/model_performance_comparison.png")
    print("=" * 60)


if __name__ == "__main__":
    run_training()
