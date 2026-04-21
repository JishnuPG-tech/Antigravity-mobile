"""
DATA LEAKAGE DETECTION IN TRAINING SCRIPT
Checks for features that would not be available at prediction time
"""

import pandas as pd

print("=" * 80)
print("DATA LEAKAGE ANALYSIS - TRAIN.PY")
print("=" * 80)

# Load dataset to understand available columns
df = pd.read_csv("../../kerala_smartwatt_ai.csv")

# Training features from train.py
training_config = {
    "ac": [
        "n_occupants",
        "total_kwh_monthly",
        "ac_tonnage",
        "ac_star_rating",
        "ac_type",
        "ac_usage_pattern",
        "location_type",
    ],
    "fridge": [
        "n_occupants",
        "total_kwh_monthly",
        "fridge_capacity",
        "fridge_age",
        "fridge_type",
        "location_type",
    ],
    "ceiling_fan": [
        "n_occupants",
        "total_kwh_monthly",
        "ceiling_fan_age",
        "fan_type",
        "num_fans",
    ],
    "television": ["n_occupants", "total_kwh_monthly", "television_type", "tv_size"],
    "washing_machine": [
        "n_occupants",
        "total_kwh_monthly",
        "wm_type",
        "wm_cycles_per_week",
    ],
    "water_pump": ["n_occupants", "total_kwh_monthly", "water_pump_hp"],
    "water_heater": ["n_occupants", "total_kwh_monthly", "season"],
}

# Features available at prediction time (from UI)
ui_available = {
    "ac": [
        "n_occupants",
        "location_type",
        "ac_tonnage",
        "ac_star_rating",
        "ac_type",
        "ac_usage_pattern",
        "season",
    ],
    "fridge": [
        "n_occupants",
        "location_type",
        "fridge_capacity_liters",
        "fridge_age_years",
        "fridge_type",
        "season",
    ],
    "ceiling_fan": [
        "n_occupants",
        "location_type",
        "num_ceiling_fans",
        "fan_type",
        "season",
    ],
    "television": [
        "n_occupants",
        "location_type",
        "tv_type",
        "tv_size_inches",
        "season",
    ],
    "washing_machine": [
        "n_occupants",
        "location_type",
        "wm_type",
        "wm_cycles_per_week",
        "season",
    ],
    "water_pump": ["n_occupants", "location_type", "water_pump_hp", "season"],
    "water_heater": ["n_occupants", "location_type", "season"],
}

# Map UI field names to dataset column names
field_mapping = {
    "fridge_capacity_liters": "fridge_capacity",
    "fridge_age_years": "fridge_age",
    "num_ceiling_fans": "num_fans",
    "tv_size_inches": "tv_size",
    "tv_type": "television_type",
}

print("\n🔍 CHECKING FOR DATA LEAKAGE")
print("=" * 80)

leakage_found = False
total_issues = 0

for appliance, train_features in training_config.items():
    print(f"\n📊 {appliance.upper()}")
    print("-" * 80)

    ui_fields = ui_available.get(appliance, [])
    # Map UI field names to dataset names
    ui_fields_mapped = [field_mapping.get(f, f) for f in ui_fields]

    print(f"Training uses: {train_features}")
    print(f"UI provides: {ui_fields}")

    # Check for leakage
    leakage_features = []

    for feature in train_features:
        # Check if feature is problematic
        if feature == "total_kwh_monthly":
            leakage_features.append(
                ("total_kwh_monthly", "CRITICAL - This is the target variable!")
            )
            leakage_found = True
        elif feature.endswith("_kwh"):
            leakage_features.append((feature, "Contains consumption data"))
            leakage_found = True
        elif "real_effective_hours" in feature:
            leakage_features.append((feature, "Contains ground truth hours"))
            leakage_found = True
        elif "real_efficiency_factor" in feature:
            leakage_features.append((feature, "Contains ground truth efficiency"))
            leakage_found = True
        elif feature not in ui_fields_mapped and feature not in [
            "n_occupants",
            "location_type",
            "season",
            "total_kwh_monthly",
        ]:
            # Feature used in training but not available from UI
            if feature == "ceiling_fan_age":
                # This is in dataset but not in UI
                leakage_features.append((feature, "WARNING - Not collected from UI"))

    if leakage_features:
        print(f"\n⚠️  POTENTIAL DATA LEAKAGE DETECTED:")
        for feat, reason in leakage_features:
            print(f"   ❌ {feat}: {reason}")
            total_issues += 1
    else:
        print(f"\n✅ No data leakage detected")

print("\n" + "=" * 80)
print("CRITICAL ISSUE: total_kwh_monthly")
print("=" * 80)

print("""
🚨 MAJOR DATA LEAKAGE DETECTED!

Problem: 'total_kwh_monthly' is used as a training feature

Why this is leakage:
- 'total_kwh_monthly' is the TOTAL consumption of the household
- It includes consumption from the very appliance we're trying to predict
- At prediction time, we DON'T know the total monthly consumption yet
- We're trying to PREDICT individual appliance consumption to calculate total

Example:
- Training: "Given total=300 kWh, AC uses 150 kWh" ✗ (Circular logic)
- Should be: "Given AC specs, predict AC uses 150 kWh" ✓

Impact:
- Models will perform artificially well in training
- Models will FAIL in production when total_kwh_monthly is unknown
- Predictions will be meaningless without this leaked information

Solution:
REMOVE 'total_kwh_monthly' from all training feature lists
""")

print("\n" + "=" * 80)
print("RECOMMENDED FIXES")
print("=" * 80)

print("""
1. REMOVE 'total_kwh_monthly' from all training features:
   ❌ BAD:  ['n_occupants', 'total_kwh_monthly', 'ac_tonnage', ...]
   ✅ GOOD: ['n_occupants', 'ac_tonnage', ...]

2. ADD 'ceiling_fan_age' to UI or remove from training:
   Option A: Add age field to UI schemas (RECOMMENDED)
   Option B: Remove from training features

3. Training features should ONLY include:
   - Household demographics (n_occupants, location_type, season)
   - Appliance specifications from UI (tonnage, type, capacity, etc.)
   - User behavior from UI (usage_pattern, cycles_per_week, etc.)

4. NEVER include in training:
   - total_kwh_monthly (target variable)
   - Any *_kwh columns (individual consumption)
   - Any *_real_effective_hours (ground truth)
   - Any *_real_efficiency_factor (ground truth)
""")

print("\n" + "=" * 80)
print(f"SUMMARY: {total_issues} data leakage issues found")
print("=" * 80)

if leakage_found:
    print("\n❌ DATA LEAKAGE DETECTED - Models will NOT work in production!")
    print("   Fix: Remove total_kwh_monthly from all training features")
else:
    print("\n✅ No critical data leakage detected")

print("\n" + "=" * 80)
