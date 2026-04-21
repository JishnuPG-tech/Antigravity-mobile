import json
import os
import shutil
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# 1. Environment Setup
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
load_dotenv()

import tensorflow as tf
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# Machine Learning & Deep Learning Libraries
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import BatchNormalization, Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

# Supabase Configuration
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get(
    "SUPABASE_URL"
)
SUPABASE_KEY = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get(
    "SUPABASE_KEY"
)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials not found in environment variables.")
    print(
        "Please set SUPABASE_URL and SUPABASE_KEY (or NEXT_PUBLIC_...) in your .env file or environment."
    )
    exit(1)

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create directories for models and backups
if not os.path.exists("models"):
    os.makedirs("models")
if not os.path.exists("models/backups"):
    os.makedirs("models/backups")
if not os.path.exists("training_data"):
    os.makedirs("training_data")
if not os.path.exists("training_logs"):
    os.makedirs("training_logs")

# Training History File
TRAINING_HISTORY_FILE = "training_logs/training_history.json"
PERFORMANCE_LOG_CSV = "training_logs/model_performance_log.csv"


def load_training_history():
    """Load training history from JSON file."""
    if os.path.exists(TRAINING_HISTORY_FILE):
        with open(TRAINING_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_training_history(history):
    """Save training history to JSON file."""
    with open(TRAINING_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def backup_existing_model(appliance_name):
    """Backup existing model files before training new one."""
    model_path = f"models/{appliance_name}_model.keras"
    preprocessor_path = f"models/{appliance_name}_preprocessor.pkl"

    if os.path.exists(model_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"models/backups/{appliance_name}"
        os.makedirs(backup_dir, exist_ok=True)

        shutil.copy2(model_path, f"{backup_dir}/model_{timestamp}.keras")
        if os.path.exists(preprocessor_path):
            shutil.copy2(
                preprocessor_path, f"{backup_dir}/preprocessor_{timestamp}.pkl"
            )

        print(f"  📦 Backed up existing model to {backup_dir}/")
        return True
    return False


def compare_models(appliance_name, new_metrics, old_metrics=None):
    """
    Compare new model with old model performance.
    Returns True if new model is better.
    """
    if old_metrics is None:
        print(f"  ✨ First model for {appliance_name} - Auto-accepting")
        return True

    # Compare based on multiple metrics
    mae_improvement = (
        (old_metrics["mae"] - new_metrics["mae"]) / old_metrics["mae"]
    ) * 100
    r2_improvement = (
        (new_metrics["r2"] - old_metrics.get("r2", 0))
        / max(old_metrics.get("r2", 0.01), 0.01)
    ) * 100

    print(f"\n  📊 Performance Comparison:")
    print(
        f"     MAE: {old_metrics['mae']:.3f} → {new_metrics['mae']:.3f} ({mae_improvement:+.1f}%)"
    )
    print(
        f"     R²:  {old_metrics.get('r2', 0):.3f} → {new_metrics['r2']:.3f} ({r2_improvement:+.1f}%)"
    )

    # Decision logic: Accept if MAE improved OR R2 improved significantly
    if new_metrics["mae"] < old_metrics["mae"] or new_metrics["r2"] > old_metrics.get(
        "r2", 0
    ):
        print(f"  ✅ New model is BETTER - Accepting")
        return True
    else:
        print(f"  ❌ Old model is BETTER - Keeping existing")
        return False


def restore_backup_model(appliance_name):
    """Restore the most recent backup if new model is worse."""
    backup_dir = f"models/backups/{appliance_name}"
    if not os.path.exists(backup_dir):
        return False

    backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("model_")])
    if not backups:
        return False

    latest_backup = backups[-1]
    timestamp = latest_backup.replace("model_", "").replace(".keras", "")

    shutil.copy2(
        f"{backup_dir}/model_{timestamp}.keras", f"models/{appliance_name}_model.keras"
    )
    shutil.copy2(
        f"{backup_dir}/preprocessor_{timestamp}.pkl",
        f"models/{appliance_name}_preprocessor.pkl",
    )

    print(f"  ↩️  Restored previous model from backup")
    return True


def log_performance_to_csv(appliance_name, metrics, accepted):
    """Log model performance to CSV for analysis."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "appliance": appliance_name,
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "r2": metrics["r2"],
        "samples": metrics["samples"],
        "accepted": accepted,
    }

    df_new = pd.DataFrame([log_entry])

    if os.path.exists(PERFORMANCE_LOG_CSV):
        df_existing = pd.read_csv(PERFORMANCE_LOG_CSV)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(PERFORMANCE_LOG_CSV, index=False)
    else:
        df_new.to_csv(PERFORMANCE_LOG_CSV, index=False)


def export_training_data_to_csv(df, filename="training_data/latest_training_data.csv"):
    """Export the current training dataset to CSV for analysis."""
    df.to_csv(filename, index=False)
    print(f"\n💾 Training data exported to: {filename}")
    print(f"   Total records: {len(df)}")
    print(f"   File size: {os.path.getsize(filename) / 1024:.1f} KB")


def fetch_training_data():
    """
    Fetches all data from the smartwatt_training table.
    Extracts ACTUAL vs PREDICTED kWh and calculates prediction errors for self-learning.
    """
    print("🔄 Connecting to Supabase...")
    try:
        # Fetch all rows (Supabase limits to 1000 by default, using range for more if needed)
        # For now, assuming < 1000 rows or simple fetch is enough.
        # For production with >1000 rows, you'd need pagination.
        response = supabase.table("smartwatt_training").select("*").execute()
        data = response.data

        if not data:
            print("⚠️ No data found in 'smartwatt_training' table.")
            return None

        df = pd.DataFrame(data)
        print(f"✅ Successfully fetched {len(df)} training records from Supabase.")

        # === DEBUG: Check what's in final_breakdown ===
        print(f"\n🔍 DEBUG: Checking final_breakdown column...")
        print(f"   Column exists: {'final_breakdown' in df.columns}")
        if "final_breakdown" in df.columns:
            non_null = df["final_breakdown"].notna().sum()
            print(f"   Non-null final_breakdown: {non_null}/{len(df)}")
            if non_null > 0:
                # Show first non-null sample
                first_result = df[df["final_breakdown"].notna()].iloc[0][
                    "final_breakdown"
                ]
                print(f"   Sample type: {type(first_result)}")
                if isinstance(first_result, str):
                    print(f"   Sample (first 200 chars): {first_result[:200]}...")
                elif isinstance(first_result, dict):
                    print(f"   Sample keys: {list(first_result.keys())}")

        # === SELF-LEARNING: EXTRACT ACTUAL VS PREDICTED kWh ===
        print("\n🧮 Calculating Prediction Errors for Self-Learning...")

        # Use dedicated columns directly (much faster than JSON parsing)
        print("   ✅ Using dedicated input_kwh and predicted_kwh columns")
        df["actual_kwh"] = df["input_kwh"].fillna(0)
        df["predicted_total_kwh"] = df["predicted_kwh"].fillna(0)

        # Debug: Show sample of what was extracted
        samples_with_predictions = df[df["predicted_total_kwh"] > 0]
        print(f"   Found {len(samples_with_predictions)} records with predictions")
        if len(samples_with_predictions) > 0:
            sample_row = samples_with_predictions.iloc[0]
            print(
                f"   Sample: Actual={sample_row.get('actual_kwh', 0):.1f} kWh, Predicted={sample_row.get('predicted_total_kwh', 0):.1f} kWh"
            )

        # Calculate Prediction Error (Core of Self-Learning)
        df["prediction_error"] = df["actual_kwh"] - df["predicted_total_kwh"]
        df["error_percentage"] = (
            (df["prediction_error"] / df["actual_kwh"]) * 100
        ).fillna(0)

        # Absolute error for filtering
        df["abs_error_percentage"] = df["error_percentage"].abs()

        # Print Error Statistics
        valid_predictions = df[df["predicted_total_kwh"] > 0]
        if len(valid_predictions) > 0:
            print(f"\n📊 Error Analysis:")
            print(f"   Total Samples: {len(df)}")
            print(f"   With Predictions: {len(valid_predictions)}")
            print(
                f"   Average Error: {valid_predictions['prediction_error'].mean():.2f} kWh"
            )
            print(
                f"   Average Error %: {valid_predictions['error_percentage'].abs().mean():.2f}%"
            )
            print(
                f"   Median Error %: {valid_predictions['error_percentage'].abs().median():.2f}%"
            )
            print(
                f"   Max Over-prediction: {valid_predictions['prediction_error'].min():.2f} kWh"
            )
            print(
                f"   Max Under-prediction: {valid_predictions['prediction_error'].max():.2f} kWh"
            )

            # Count accuracy tiers
            high_accuracy = len(
                valid_predictions[valid_predictions["abs_error_percentage"] <= 10]
            )
            medium_accuracy = len(
                valid_predictions[
                    (valid_predictions["abs_error_percentage"] > 10)
                    & (valid_predictions["abs_error_percentage"] <= 20)
                ]
            )
            low_accuracy = len(
                valid_predictions[valid_predictions["abs_error_percentage"] > 20]
            )

            print(f"\n   Accuracy Tiers:")
            print(
                f"   ✅ High (<10% error): {high_accuracy} samples ({high_accuracy/len(valid_predictions)*100:.1f}%)"
            )
            print(
                f"   ⚠️  Medium (10-20%): {medium_accuracy} samples ({medium_accuracy/len(valid_predictions)*100:.1f}%)"
            )
            print(
                f"   ❌ Low (>20% error): {low_accuracy} samples ({low_accuracy/len(valid_predictions)*100:.1f}%)"
            )

            # === DETAILED ACTUAL VS PREDICTED COMPARISON ===
            print(f"\n" + "=" * 80)
            print(f"📋 ACTUAL vs PREDICTED COMPARISON (All Records)")
            print(f"=" * 80)
            print(
                f"{'ID':<8} {'Actual kWh':<12} {'Predicted kWh':<15} {'Error':<10} {'Error %':<10} {'Status':<15}"
            )
            print(f"-" * 80)

            for idx, row in valid_predictions.iterrows():
                record_id = (
                    row.get("id", idx)[:8]
                    if isinstance(row.get("id"), str)
                    else str(idx)[:8]
                )
                actual = row["actual_kwh"]
                predicted = row["predicted_total_kwh"]
                error = row["prediction_error"]
                error_pct = row["error_percentage"]
                abs_error_pct = row["abs_error_percentage"]

                # Determine status
                if abs_error_pct <= 10:
                    status = "✅ High Acc"
                elif abs_error_pct <= 20:
                    status = "⚠️  Medium Acc"
                else:
                    status = "❌ Low Acc"

                # Format error percentage as string with % symbol
                error_pct_str = f"{error_pct:.1f}%"
                print(
                    f"{record_id:<8} {actual:<12.1f} {predicted:<15.1f} {error:<10.1f} {error_pct_str:<10} {status:<15}"
                )

            print(f"=" * 80)
            print(
                f"Summary: {high_accuracy} excellent, {medium_accuracy} good, {low_accuracy} needs improvement"
            )
            print(f"=" * 80 + "\n")

        print(f"\n✅ Successfully fetched {len(df)} training records from Supabase.")

        # --- DATA TRANSFORMATION: EXTRACT PER-APPLIANCE TARGETS ---
        print("\n🔍 Extracting per-appliance consumption targets...")

        # Helper to extract kwh from final_breakdown predictions
        def extract_appliance_kwh(row, appliance_key):
            """Extract predicted kWh for specific appliance"""
            try:
                results = row.get("final_breakdown")
                if not results:
                    return 0.0

                # Handle JSON string (Supabase returns JSONB as string sometimes)
                if isinstance(results, str):
                    import json

                    results = json.loads(results)

                if not isinstance(results, dict):
                    return 0.0

                predictions = results.get("predictions", {})
                return float(predictions.get(appliance_key, 0.0))
            except:
                return 0.0

        # Calculate CORRECTION RATIO for each appliance
        # This is the KEY to self-learning: actual/predicted ratio
        def calculate_correction_ratio(row, appliance_key):
            """
            Calculate how much the model needs to adjust.
            If predicted = 100 kWh and actual total suggests 120 kWh needed,
            then correction_ratio = 1.2 (need to predict 20% higher)
            """
            try:
                appliance_pred = extract_appliance_kwh(row, appliance_key)
                if appliance_pred == 0:
                    return 1.0  # No prediction, no correction needed

                total_pred = row.get("predicted_total_kwh", 0)
                actual = row.get("actual_kwh", 0)

                if total_pred == 0 or actual == 0:
                    return 1.0

                # Global correction factor: actual/predicted
                global_factor = actual / total_pred

                # Apply to this appliance (proportional correction)
                return global_factor
            except:
                return 1.0

        # Map of training target columns to JSON keys (matching your ai_results structure)
        target_map = {
            "ac_kwh": "ac",
            "refrigerator_kwh": "fridge",
            "washing_machine_kwh": "washing_machine",
            "water_heater_kwh": "water_heater",
            "water_pump_kwh": "water_pump",
            "television_kwh": "television",
            "ceiling_fans_kwh": "ceiling_fan",
            "led_lights_kwh": "led_light",
            "tube_lights_kwh": "tube_light",
            "cfl_bulbs_kwh": "cfl_bulb",
            "mixer_grinder_kwh": "mixer_grinder",
            "microwave_kwh": "microwave",
            "desktop_kwh": "desktop",
            "laptop_kwh": "laptop",
            "iron_kwh": "iron",
            "kettle_kwh": "kettle",
            "induction_kwh": "induction",
            "rice_cooker_kwh": "rice_cooker",
        }

        for col, key in target_map.items():
            # Original predicted value
            df[col] = df.apply(lambda row: extract_appliance_kwh(row, key), axis=1)

            # SELF-LEARNING: Corrected target (what model SHOULD have predicted)
            correction_col = f"{col}_corrected"
            df[correction_col] = df.apply(
                lambda row: extract_appliance_kwh(row, key)
                * calculate_correction_ratio(row, key),
                axis=1,
            )

        print(f"✅ Extracted {len(target_map)} appliance types with correction ratios")

        # --- EXTRACT FEATURES FROM APPLIANCE_USAGE ---
        print("\n📋 Extracting features from appliance_usage JSON...")

        def extract_feature(row, feature_key):
            try:
                usage = row.get("appliance_usage")
                if not usage:
                    return 0.0

                # Handle JSON string (Supabase returns JSONB as string sometimes)
                if isinstance(usage, str):
                    import json

                    usage = json.loads(usage)

                if isinstance(usage, list):
                    return 0.0  # Handle legacy list format if any

                # Check direct key match
                if feature_key in usage:
                    return usage[feature_key]

                # Fallback: hours_per_day -> hours (frontend saves as _hours)
                if feature_key.endswith("_hours_per_day"):
                    short_key = feature_key.replace("_hours_per_day", "_hours")
                    if short_key in usage:
                        return usage[short_key]

                return usage.get(feature_key, 0.0)
            except:
                return 0.0

        # List of all possible feature columns needed for training
        all_features = [
            "ac_hours_per_day",
            "ac_tonnage",
            "ac_star_rating",
            "num_ac_units",
            "ac_category",
            "ac_min_hours",
            "ac_max_hours",
            "fridge_capacity_liters",
            "fridge_age_years",
            "fridge_star_rating",
            "fridge_category",
            "fridge_min_hours",
            "fridge_max_hours",
            "wm_cycles_per_week",
            "wm_capacity_kg",
            "wm_star_rating",
            "wm_category",
            "wm_min_hours",
            "wm_max_hours",
            "water_heater_usage_hours",
            "water_heater_capacity_liters",
            "geyser_category",
            "geyser_min_hours",
            "geyser_max_hours",
            "water_pump_usage_hours_per_day",
            "water_pump_hp",
            "pump_category",
            "pump_min_hours",
            "pump_max_hours",
            "tv_hours_per_day",
            "tv_size_inches",
            "num_televisions",
            "tv_category",
            "tv_min_hours",
            "tv_max_hours",
            "mixer_grinder_usage_minutes_per_day",
            "mixer_grinder_wattage",
            "mixer_category",
            "mixer_min_hours",
            "mixer_max_hours",
            "microwave_usage_minutes_per_day",
            "microwave_capacity_liters",
            "microwave_category",
            "microwave_min_hours",
            "microwave_max_hours",
            "desktop_hours_per_day",
            "desktop_category",
            "desktop_min_hours",
            "desktop_max_hours",
            "laptop_hours_per_day",
            "laptop_category",
            "laptop_min_hours",
            "laptop_max_hours",
            "iron_hours_per_day",
            "iron_category",
            "iron_min_hours",
            "iron_max_hours",
            "kettle_hours_per_day",
            "kettle_category",
            "kettle_min_hours",
            "kettle_max_hours",
            "induction_hours_per_day",
            "induction_category",
            "induction_min_hours",
            "induction_max_hours",
            "rice_cooker_hours_per_day",
            "rice_cooker_category",
            "rice_cooker_min_hours",
            "rice_cooker_max_hours",
            "num_ceiling_fans",
            "fan_hours_per_day",
            "fan_star_rating",
            "fan_category",
            "fan_min_hours",
            "fan_max_hours",
            "num_led_lights",
            "light_hours_per_day",
            "led_category",
            "led_min_hours",
            "led_max_hours",
            "num_tube_lights",
            "tube_category",
            "tube_min_hours",
            "tube_max_hours",
            "num_cfl_bulbs",
            "cfl_category",
            "cfl_min_hours",
            "cfl_max_hours",
            "toaster_hours_per_day",
            "toaster_category",
            "toaster_min_hours",
            "toaster_max_hours",
            "food_processor_hours_per_day",
            "food_processor_category",
            "food_processor_min_hours",
            "food_processor_max_hours",
            "hair_dryer_hours_per_day",
            "hair_dryer_category",
            "hair_dryer_min_hours",
            "hair_dryer_max_hours",
            "vacuum_hours_per_day",
            "vacuum_category",
            "vacuum_min_hours",
            "vacuum_max_hours",
        ]

        # Extract all features
        print(f"\n📋 Extracting features from appliance_usage JSON...")

        # Build a dict to batch-add columns (avoids DataFrame fragmentation)
        feature_data = {}
        for feat in all_features:
            # If column already exists in top-level (e.g. from SQL schema), prefer it
            if feat not in df.columns:
                feature_data[feat] = df.apply(
                    lambda row: extract_feature(row, feat), axis=1
                )

        # Add all new columns at once to avoid fragmentation
        if feature_data:
            feature_df = pd.DataFrame(feature_data, index=df.index)
            df = pd.concat([df, feature_df], axis=1)

        print(f"✅ Extracted {len(all_features)} feature columns")
        print(f"   Total columns in dataset: {len(df.columns)}")

        return df
    except Exception as e:
        print(f"❌ Error fetching data from Supabase: {e}")
        return None


def build_and_train_model(
    df, appliance_name, target_col, filter_col, numeric_features, categorical_features
):
    """
    Generic function with SELF-LEARNING: builds, trains, compares, and selects best model.
    NOW USES CORRECTED TARGETS based on actual vs predicted errors!
    """
    print(f"\n" + "=" * 60)
    print(f"TRAINING MODEL FOR: {appliance_name.upper()}")
    print(f"=" * 60)

    # --- Step A: Data Preparation with SELF-LEARNING ---
    # Use CORRECTED target if available (learned from actual vs predicted)
    corrected_target_col = f"{target_col}_corrected"

    if corrected_target_col in df.columns:
        print(f"🎓 Using SELF-LEARNING corrected targets from actual user data!")
        actual_target = corrected_target_col
    else:
        print(f"📊 Using original targets (no correction data available yet)")
        actual_target = target_col

    # Check if required columns exist
    missing_cols = [
        col
        for col in numeric_features + categorical_features + [target_col]
        if col not in df.columns
    ]
    if missing_cols:
        print(f"⚠️ Skipping {appliance_name}: Missing columns in data: {missing_cols}")
        return

    # 1. Filter: Only learn from homes that HAVE this appliance
    print(f"🔍 Filtering for {appliance_name}...")
    if filter_col:
        if filter_col not in df.columns:
            print(f"   {filter_col} missing. Using {target_col} > 0")
            appliance_df = df[df[target_col] > 0].copy()
        else:
            appliance_df = df[df[filter_col] == 1].copy()
    else:
        appliance_df = df[df[target_col] > 0].copy()

    # SELF-LEARNING: Filter out samples with extreme errors (outliers that would harm training)
    if "abs_error_percentage" in appliance_df.columns:
        before_filter = len(appliance_df)
        appliance_df = appliance_df[
            appliance_df["abs_error_percentage"] <= 100
        ].copy()  # Remove >100% errors
        if len(appliance_df) < before_filter:
            print(
                f"   🧹 Filtered out {before_filter - len(appliance_df)} extreme outlier samples"
            )

    print(f"   {appliance_name} samples: {len(appliance_df)}")

    if len(appliance_df) < 10:
        print(
            f"⚠️ Skipping {appliance_name}: Not enough data samples ({len(appliance_df)}). Need at least 10."
        )
        return

    # 2. Features: Always include total_kwh_monthly (bi_monthly_kwh / 2) if available
    if "total_kwh_monthly" not in appliance_df.columns:
        if "bi_monthly_kwh" in appliance_df.columns:
            appliance_df["total_kwh_monthly"] = appliance_df["bi_monthly_kwh"] / 2
        else:
            print(
                f"⚠️ Skipping {appliance_name}: 'bi_monthly_kwh' column missing for context."
            )
            return

    features = numeric_features + categorical_features + ["total_kwh_monthly"]

    # Fill NaNs with 0 or appropriate defaults to prevent crashes
    appliance_df[numeric_features] = appliance_df[numeric_features].fillna(0)
    for cat in categorical_features:
        appliance_df[cat] = appliance_df[cat].fillna("unknown")

    X = appliance_df[features]
    y = appliance_df[actual_target]  # Use corrected target!

    # Show learning statistics
    if actual_target != target_col:
        original_avg = appliance_df[target_col].mean()
        corrected_avg = appliance_df[actual_target].mean()
        adjustment_pct = (
            ((corrected_avg - original_avg) / original_avg * 100)
            if original_avg > 0
            else 0
        )
        print(
            f"   📈 Learning Adjustment: {adjustment_pct:+.1f}% (Original: {original_avg:.1f} → Corrected: {corrected_avg:.1f} kWh)"
        )

    print(f"   Training samples: {len(X)}")

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # --- Step B: Preprocessing ---
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features + ["total_kwh_monthly"]),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
        ]
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    # --- SELF-LEARNING: Backup existing model ---
    had_old_model = backup_existing_model(appliance_name)

    # Save NEW Preprocessor (temporary - will be kept or restored based on performance)
    joblib.dump(preprocessor, f"models/{appliance_name}_preprocessor_temp.pkl")

    # --- Step C: Neural Network Architecture ---
    model = Sequential(
        [
            Dense(64, activation="relu", input_shape=(X_train_processed.shape[1],)),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation="relu"),
            BatchNormalization(),
            Dropout(0.15),
            Dense(16, activation="relu"),
            Dense(1, activation="linear"),
        ]
    )

    model.compile(
        optimizer=Adam(learning_rate=0.001), loss="mean_squared_error", metrics=["mae"]
    )

    early_stop = EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True, verbose=0
    )

    # --- Step D: Training ---
    print("🧠 Neural Network is learning...")
    history = model.fit(
        X_train_processed,
        y_train,
        validation_data=(X_test_processed, y_test),
        epochs=100,
        batch_size=32,
        verbose=0,
        callbacks=[early_stop],
    )

    # --- Step E: Evaluation ---
    y_pred = model.predict(X_test_processed, verbose=0).flatten()
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    new_metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "samples": len(X_train),
        "timestamp": datetime.now().isoformat(),
    }

    print(f"📈 New Model Performance: MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r2:.3f}")

    # --- SELF-LEARNING: Compare with old model ---
    training_history = load_training_history()
    old_metrics = training_history.get(appliance_name, {}).get("best_metrics")

    should_accept = compare_models(appliance_name, new_metrics, old_metrics)

    if should_accept:
        # Save NEW model as the current best
        model.save(f"models/{appliance_name}_model.keras")

        # Move temp preprocessor to final location
        os.rename(
            f"models/{appliance_name}_preprocessor_temp.pkl",
            f"models/{appliance_name}_preprocessor.pkl",
        )

        # Update training history
        training_history[appliance_name] = {
            "best_metrics": new_metrics,
            "training_history": training_history.get(appliance_name, {}).get(
                "training_history", []
            )
            + [new_metrics],
            "last_trained": datetime.now().isoformat(),
        }
        save_training_history(training_history)

        print(f"✅ Model SAVED successfully")
    else:
        # Restore old model
        if had_old_model:
            restore_backup_model(appliance_name)
            os.remove(f"models/{appliance_name}_preprocessor_temp.pkl")
        print(f"⏮️  Kept existing model (better performance)")

    # Log to CSV for analysis
    log_performance_to_csv(appliance_name, new_metrics, should_accept)


def main():
    print("\n" + "=" * 70)
    print(" 🎓 SELF-LEARNING AI TRAINING SYSTEM")
    print(" 📊 Learning from ACTUAL vs PREDICTED kWh errors")
    print("=" * 70)

    # 1. Fetch Data with Error Calculations
    df = fetch_training_data()
    if df is None:
        return

    # Check if we have enough data to train
    valid_samples = len(df[df["predicted_total_kwh"] > 0])
    if valid_samples < 10:
        print(
            f"\n⚠️ Not enough data to train (only {valid_samples} samples with predictions)"
        )
        print("   Need at least 10 user predictions to start self-learning.")
        print(
            "   Continue using the system - training will happen automatically as data accumulates!"
        )
        return

    print(
        f"\n✅ Found {valid_samples} samples with predictions - starting self-learning!"
    )

    # 2. Train All Models with SELF-LEARNING
    # Note: We map the Supabase columns to the expected feature names.

    # --- MAJOR APPLIANCES ---
    build_and_train_model(
        df,
        "ac",
        "ac_kwh",
        "has_ac",
        [
            "ac_hours_per_day",
            "ac_tonnage",
            "ac_star_rating",
            "num_ac_units",
            "ac_min_hours",
            "ac_max_hours",
        ],
        ["ac_type", "ac_category"],
    )
    build_and_train_model(
        df,
        "fridge",
        "refrigerator_kwh",
        "has_refrigerator",
        [
            "fridge_capacity_liters",
            "fridge_age_years",
            "fridge_star_rating",
            "fridge_min_hours",
            "fridge_max_hours",
        ],
        ["fridge_type", "fridge_category"],
    )
    build_and_train_model(
        df,
        "washing_machine",
        "washing_machine_kwh",
        "has_washing_machine",
        [
            "wm_cycles_per_week",
            "wm_capacity_kg",
            "wm_star_rating",
            "wm_min_hours",
            "wm_max_hours",
        ],
        ["wm_type", "wm_category"],
    )
    build_and_train_model(
        df,
        "water_heater",
        "water_heater_kwh",
        "has_water_heater",
        [
            "water_heater_usage_hours",
            "water_heater_capacity_liters",
            "geyser_min_hours",
            "geyser_max_hours",
        ],
        ["water_heater_type", "geyser_category"],
    )
    build_and_train_model(
        df,
        "water_pump",
        "water_pump_kwh",
        "has_water_pump",
        [
            "water_pump_usage_hours_per_day",
            "water_pump_hp",
            "pump_min_hours",
            "pump_max_hours",
        ],
        ["pump_category"],
    )
    build_and_train_model(
        df,
        "television",
        "television_kwh",
        "has_television",
        [
            "tv_hours_per_day",
            "tv_size_inches",
            "num_televisions",
            "tv_min_hours",
            "tv_max_hours",
        ],
        ["tv_type", "tv_category"],
    )

    # --- KITCHEN & SMALL APPLIANCES ---
    build_and_train_model(
        df,
        "mixer_grinder",
        "mixer_grinder_kwh",
        "has_mixer_grinder",
        [
            "mixer_grinder_usage_minutes_per_day",
            "mixer_grinder_wattage",
            "mixer_min_hours",
            "mixer_max_hours",
        ],
        ["mixer_category"],
    )
    build_and_train_model(
        df,
        "microwave",
        "microwave_kwh",
        "has_microwave",
        [
            "microwave_usage_minutes_per_day",
            "microwave_capacity_liters",
            "microwave_min_hours",
            "microwave_max_hours",
        ],
        ["microwave_category"],
    )

    # --- COOLING & LIGHTING ---
    build_and_train_model(
        df,
        "ceiling_fan",
        "ceiling_fans_kwh",
        None,
        [
            "num_ceiling_fans",
            "fan_hours_per_day",
            "fan_star_rating",
            "fan_min_hours",
            "fan_max_hours",
        ],
        ["fan_category"],
    )
    build_and_train_model(
        df,
        "led_light",
        "led_lights_kwh",
        None,
        ["num_led_lights", "light_hours_per_day", "led_min_hours", "led_max_hours"],
        ["led_category"],
    )
    build_and_train_model(
        df,
        "tube_light",
        "tube_lights_kwh",
        None,
        ["num_tube_lights", "light_hours_per_day", "tube_min_hours", "tube_max_hours"],
        ["tube_category"],
    )
    build_and_train_model(
        df,
        "cfl_bulb",
        "cfl_bulbs_kwh",
        None,
        ["num_cfl_bulbs", "light_hours_per_day", "cfl_min_hours", "cfl_max_hours"],
        ["cfl_category"],
    )

    # --- NEW APPLIANCES ---
    build_and_train_model(
        df,
        "desktop",
        "desktop_kwh",
        "has_computer",
        ["desktop_hours_per_day", "desktop_min_hours", "desktop_max_hours"],
        ["desktop_category"],
    )
    build_and_train_model(
        df,
        "laptop",
        "laptop_kwh",
        "has_laptop",
        ["laptop_hours_per_day", "laptop_min_hours", "laptop_max_hours"],
        ["laptop_category"],
    )
    build_and_train_model(
        df,
        "iron",
        "iron_kwh",
        "has_iron",
        ["iron_hours_per_day", "iron_min_hours", "iron_max_hours"],
        ["iron_category"],
    )
    build_and_train_model(
        df,
        "kettle",
        "kettle_kwh",
        "has_electric_kettle",
        ["kettle_hours_per_day", "kettle_min_hours", "kettle_max_hours"],
        ["kettle_category"],
    )
    build_and_train_model(
        df,
        "induction",
        "induction_kwh",
        "has_induction",
        ["induction_hours_per_day", "induction_min_hours", "induction_max_hours"],
        ["induction_category"],
    )
    build_and_train_model(
        df,
        "rice_cooker",
        "rice_cooker_kwh",
        "has_rice_cooker",
        ["rice_cooker_hours_per_day", "rice_cooker_min_hours", "rice_cooker_max_hours"],
        ["rice_cooker_category"],
    )
    build_and_train_model(
        df,
        "toaster",
        "toaster_kwh",
        "has_toaster",
        ["toaster_hours_per_day", "toaster_min_hours", "toaster_max_hours"],
        ["toaster_category"],
    )
    build_and_train_model(
        df,
        "food_processor",
        "food_processor_kwh",
        "has_food_processor",
        [
            "food_processor_hours_per_day",
            "food_processor_min_hours",
            "food_processor_max_hours",
        ],
        ["food_processor_category"],
    )
    build_and_train_model(
        df,
        "hair_dryer",
        "hair_dryer_kwh",
        "has_hair_dryer",
        ["hair_dryer_hours_per_day", "hair_dryer_min_hours", "hair_dryer_max_hours"],
        ["hair_dryer_category"],
    )
    build_and_train_model(
        df,
        "vacuum",
        "vacuum_kwh",
        "has_vacuum",
        ["vacuum_hours_per_day", "vacuum_min_hours", "vacuum_max_hours"],
        ["vacuum_category"],
    )

    # --- Export Training Data ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_training_data_to_csv(df, f"training_data/training_data_{timestamp}.csv")
    export_training_data_to_csv(
        df, "training_data/latest_training_data.csv"
    )  # Always keep latest

    print("\n" + "=" * 70)
    print(" 🎓 SELF-LEARNING TRAINING SESSION COMPLETE")
    print("=" * 70)
    print(f"\n📊 Training Logs:")
    print(f"   - History: {TRAINING_HISTORY_FILE}")
    print(f"   - Performance CSV: {PERFORMANCE_LOG_CSV}")
    print(f"   - Model Backups: models/backups/")
    print("=" * 70)


if __name__ == "__main__":
    main()
