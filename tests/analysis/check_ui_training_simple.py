"""
Simple UI to Training Column Mapping Validator (No emojis)
"""

import pandas as pd

# Updated training features
TRAINING_FEATURES = {
    "ac": [
        "n_occupants",
        "season",
        "location_type",
        "ac_tonnage",
        "ac_star_rating",
        "ac_type",
        "ac_usage_pattern",
    ],
    "fridge": [
        "n_occupants",
        "season",
        "location_type",
        "fridge_capacity",
        "fridge_age",
        "fridge_star_rating",
        "fridge_type",
    ],
    "ceiling_fan": ["n_occupants", "season", "location_type", "fan_type", "num_fans"],
    "television": [
        "n_occupants",
        "season",
        "location_type",
        "television_type",
        "tv_size",
    ],
    "washing_machine": [
        "n_occupants",
        "season",
        "location_type",
        "wm_type",
        "wm_capacity",
        "wm_star_rating",
        "wm_cycles_per_week",
    ],
    "water_pump": ["n_occupants", "season", "location_type", "water_pump_hp"],
    "water_heater": [
        "n_occupants",
        "season",
        "location_type",
        "water_heater_type",
        "water_heater_capacity",
    ],
    "iron": ["n_occupants", "season", "location_type"],
    "kettle": ["n_occupants", "season", "location_type"],
    "induction": ["n_occupants", "season", "location_type"],
    "desktop": ["n_occupants", "season", "location_type"],
    "microwave": ["n_occupants", "season", "location_type"],
    "mixer": ["n_occupants", "season", "location_type"],
    "rice_cooker": ["n_occupants", "season", "location_type"],
    "toaster": ["n_occupants", "season", "location_type"],
    "food_processor": ["n_occupants", "season", "location_type"],
    "laptop": ["n_occupants", "season", "location_type"],
    "hair_dryer": ["n_occupants", "season", "location_type"],
    "vacuum": ["n_occupants", "season", "location_type"],
    "led_lights": ["n_occupants", "season", "location_type"],
    "cfl_lights": ["n_occupants", "season", "location_type"],
    "tube_lights": ["n_occupants", "season", "location_type"],
}

# UI fields (excluding hours, patterns, total_units)
UI_IMPORTANT_FIELDS = {
    "ac": [
        "n_occupants",
        "season",
        "location_type",
        "ac_star",
        "ac_tonnage",
        "ac_type",
    ],
    "fridge": [
        "n_occupants",
        "season",
        "location_type",
        "fridge_star",
        "fridge_capacity",
        "fridge_type",
        "fridge_age",
    ],
    "washing_machine": [
        "n_occupants",
        "season",
        "location_type",
        "wm_type",
        "wm_capacity",
        "wm_star",
    ],
    "water_heater": [
        "n_occupants",
        "season",
        "location_type",
        "geyser_type",
        "geyser_capacity",
    ],
    "ceiling_fan": ["n_occupants", "season", "location_type", "fan_type", "num_fans"],
    "television": ["n_occupants", "season", "location_type", "tv_type", "tv_size"],
    "water_pump": ["n_occupants", "season", "location_type", "pump_hp"],
}

# Mapping UI field names to dataset column names
FIELD_MAPPING = {
    "ac_star": "ac_star_rating",
    "fridge_star": "fridge_star_rating",
    "wm_star": "wm_star_rating",
    "geyser_type": "water_heater_type",
    "geyser_capacity": "water_heater_capacity",
    "tv_type": "television_type",
    "pump_hp": "water_pump_hp",
}


def check_mapping():
    print("=" * 80)
    print("UI TO TRAINING MAPPING VALIDATION (UPDATED)")
    print("=" * 80)

    # Check dataset
    try:
        df = pd.read_csv("kerala_smartwatt_ai.csv")
        dataset_cols = set(df.columns)
    except:
        print("[ERROR] Cannot load dataset")
        return

    total_ok = 0
    total_missing = 0

    for appliance, ui_fields in UI_IMPORTANT_FIELDS.items():
        print(f"\n{'='*80}")
        print(f"[{appliance.upper()}]")
        print(f"{'='*80}")

        training_fields = TRAINING_FEATURES.get(appliance, [])

        print(f"\nUI Fields: {len(ui_fields)}")
        print(f"Training Fields: {len(training_fields)}")

        for ui_field in ui_fields:
            # Map UI field to dataset column
            dataset_field = FIELD_MAPPING.get(ui_field, ui_field)

            # Check if in training
            if dataset_field in training_fields or ui_field in training_fields:
                print(f"  [OK] {ui_field:25s} -> {dataset_field:30s}")
                total_ok += 1
            else:
                print(f"  [MISSING] {ui_field:25s} -> {dataset_field:30s}")
                total_missing += 1

        # Check for extra training fields
        ui_mapped = set([FIELD_MAPPING.get(f, f) for f in ui_fields])
        extra = set(training_fields) - ui_mapped
        if extra:
            print(f"\n  [EXTRA IN TRAINING]: {extra}")

    # Base field usage
    print(f"\n{'='*80}")
    print("[BASE FIELDS USAGE]")
    print(f"{'='*80}")

    for base_field in ["n_occupants", "season", "location_type"]:
        count = sum(1 for feats in TRAINING_FEATURES.values() if base_field in feats)
        print(f"  {base_field:20s}: {count}/22 models")

    # Summary
    print(f"\n{'='*80}")
    print("[SUMMARY]")
    print(f"{'='*80}")
    print(f"Total UI Fields Checked: {total_ok + total_missing}")
    print(f"Mapped Correctly: {total_ok}")
    print(f"Missing from Training: {total_missing}")

    if total_missing == 0:
        print("\n[SUCCESS] ALL UI FIELDS MAPPED TO TRAINING!")
    else:
        print(f"\n[WARNING] {total_missing} fields not in training")

    print("=" * 80)


if __name__ == "__main__":
    check_mapping()
