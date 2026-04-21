"""
Deep analysis of UI Input fields vs Training Script columns
Checks for exact alignment between schemas.py and train.py
"""

from typing import Dict, List, Set

import pandas as pd

# UI Input Fields from schemas.py
UI_FIELDS = {
    "AC": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "ac_tonnage",
            "ac_star_rating",
            "num_ac_units",
            "ac_type",
            "ac_usage_pattern",
            "ac_hours_per_day",
        ],
    },
    "Fridge": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "fridge_capacity_liters",
            "fridge_age_years",
            "fridge_star_rating",
            "fridge_type",
            "fridge_hours_per_day",
        ],
    },
    "Washing Machine": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "wm_capacity_kg",
            "wm_star_rating",
            "wm_type",
            "wm_cycles_per_week",
        ],
    },
    "Ceiling Fan": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "num_ceiling_fans",
            "fan_star_rating",
            "fan_type",
            "fan_hours_per_day",
        ],
    },
    "Television": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "tv_size_inches",
            "num_televisions",
            "tv_type",
            "tv_hours_per_day",
        ],
    },
    "Water Heater": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "water_heater_capacity_liters",
            "water_heater_type",
            "water_heater_usage_hours",
        ],
    },
    "Water Pump": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": ["water_pump_hp", "water_pump_usage_hours_per_day"],
    },
    "Lighting": {
        "base": ["season", "location_type", "n_occupants"],
        "specific": [
            "num_units",
            "light_hours_per_day",
            "num_led_lights",
            "num_cfl_bulbs",
            "num_tube_lights",
        ],
    },
}

# Training Features from train.py (updated version)
TRAINING_FEATURES = {
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
    "led_lights": ["n_occupants", "total_kwh_monthly"],
    "cfl_lights": ["n_occupants", "total_kwh_monthly"],
    "tube_lights": ["n_occupants", "total_kwh_monthly"],
}

# Field name mappings (UI field -> Dataset column name)
FIELD_MAPPINGS = {
    # AC
    "ac_tonnage": "ac_tonnage",
    "ac_star_rating": "ac_star_rating",
    "ac_type": "ac_type",
    "ac_usage_pattern": "ac_usage_pattern",
    # Fridge
    "fridge_capacity_liters": "fridge_capacity",  # MISMATCH
    "fridge_age_years": "fridge_age",  # MISMATCH
    "fridge_type": "fridge_type",
    # Fan
    "num_ceiling_fans": "num_fans",  # MISMATCH
    "fan_type": "fan_type",
    # TV
    "tv_size_inches": "tv_size",  # MISMATCH
    "tv_type": "television_type",  # MISMATCH
    # Washing Machine
    "wm_type": "wm_type",
    "wm_cycles_per_week": "wm_cycles_per_week",
    # Water Pump
    "water_pump_hp": "water_pump_hp",
}


def analyze_alignment():
    print("=" * 80)
    print("DEEP ANALYSIS: UI INPUTS vs TRAINING FEATURES")
    print("=" * 80)

    # Load actual dataset columns
    try:
        df = pd.read_csv("kerala_smartwatt_ai.csv")
        dataset_cols = set(df.columns)
        print(f"\n✅ Dataset loaded: {len(dataset_cols)} columns found\n")
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}\n")
        dataset_cols = set()

    issues = []

    # AC Analysis
    print("\n" + "─" * 80)
    print("🔌 AC (Air Conditioner)")
    print("─" * 80)
    ui_ac = UI_FIELDS["AC"]["base"] + UI_FIELDS["AC"]["specific"]
    train_ac = TRAINING_FEATURES["ac"]

    print(f"UI sends {len(ui_ac)} fields:")
    for field in ui_ac:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_ac else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_ac and field not in [
            "season",
            "num_ac_units",
            "ac_hours_per_day",
        ]:
            issues.append(
                f"AC: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_ac)} features: {train_ac}")

    # Fridge Analysis
    print("\n" + "─" * 80)
    print("🧊 Fridge (Refrigerator)")
    print("─" * 80)
    ui_fridge = UI_FIELDS["Fridge"]["base"] + UI_FIELDS["Fridge"]["specific"]
    train_fridge = TRAINING_FEATURES["fridge"]

    print(f"UI sends {len(ui_fridge)} fields:")
    for field in ui_fridge:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_fridge else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_fridge and field not in [
            "season",
            "fridge_star_rating",
            "fridge_hours_per_day",
        ]:
            issues.append(
                f"Fridge: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_fridge)} features: {train_fridge}")

    # Ceiling Fan Analysis
    print("\n" + "─" * 80)
    print("🌀 Ceiling Fan")
    print("─" * 80)
    ui_fan = UI_FIELDS["Ceiling Fan"]["base"] + UI_FIELDS["Ceiling Fan"]["specific"]
    train_fan = TRAINING_FEATURES["ceiling_fan"]

    print(f"UI sends {len(ui_fan)} fields:")
    for field in ui_fan:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_fan else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_fan and field not in [
            "season",
            "location_type",
            "fan_star_rating",
            "fan_hours_per_day",
        ]:
            issues.append(
                f"Fan: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_fan)} features: {train_fan}")

    # Television Analysis
    print("\n" + "─" * 80)
    print("📺 Television")
    print("─" * 80)
    ui_tv = UI_FIELDS["Television"]["base"] + UI_FIELDS["Television"]["specific"]
    train_tv = TRAINING_FEATURES["television"]

    print(f"UI sends {len(ui_tv)} fields:")
    for field in ui_tv:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_tv else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_tv and field not in [
            "season",
            "location_type",
            "num_televisions",
            "tv_hours_per_day",
        ]:
            issues.append(
                f"TV: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_tv)} features: {train_tv}")

    # Washing Machine Analysis
    print("\n" + "─" * 80)
    print("🧺 Washing Machine")
    print("─" * 80)
    ui_wm = (
        UI_FIELDS["Washing Machine"]["base"] + UI_FIELDS["Washing Machine"]["specific"]
    )
    train_wm = TRAINING_FEATURES["washing_machine"]

    print(f"UI sends {len(ui_wm)} fields:")
    for field in ui_wm:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_wm else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_wm and field not in [
            "season",
            "location_type",
            "wm_capacity_kg",
            "wm_star_rating",
        ]:
            issues.append(
                f"WM: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_wm)} features: {train_wm}")

    # Water Pump Analysis
    print("\n" + "─" * 80)
    print("💧 Water Pump")
    print("─" * 80)
    ui_pump = UI_FIELDS["Water Pump"]["base"] + UI_FIELDS["Water Pump"]["specific"]
    train_pump = TRAINING_FEATURES["water_pump"]

    print(f"UI sends {len(ui_pump)} fields:")
    for field in ui_pump:
        status = (
            "✓"
            if field in dataset_cols or FIELD_MAPPINGS.get(field) in dataset_cols
            else "✗"
        )
        mapped = FIELD_MAPPINGS.get(field, field)
        used_in_training = "USED" if mapped in train_pump else "NOT USED"
        print(f"  {status} {field:35s} -> {mapped:25s} [{used_in_training}]")
        if mapped not in train_pump and field not in [
            "season",
            "location_type",
            "water_pump_usage_hours_per_day",
        ]:
            issues.append(
                f"Pump: UI field '{field}' (maps to '{mapped}') not used in training"
            )

    print(f"\nTraining uses {len(train_pump)} features: {train_pump}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)

    if issues:
        print(f"\n⚠️  Found {len(issues)} alignment issues:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i:2d}. {issue}")
    else:
        print(
            "\n✅ Perfect alignment! All UI fields are properly mapped and used in training."
        )

    # Check dataset columns
    print("\n" + "=" * 80)
    print("🗂️  DATASET COLUMN CHECK")
    print("=" * 80)

    required_training_cols = set()
    for feats in TRAINING_FEATURES.values():
        required_training_cols.update(feats)

    missing_cols = required_training_cols - dataset_cols
    if missing_cols:
        print(f"\n❌ Missing {len(missing_cols)} required columns in dataset:")
        for col in sorted(missing_cols):
            print(f"  • {col}")
        print("\n⚠️  You need to regenerate the dataset with: python newdataset.py")
    else:
        print("\n✅ All training features exist in the dataset!")


if __name__ == "__main__":
    analyze_alignment()
