"""
Comprehensive UI to Training Column Mapping Validator
Checks that all UI input fields (except hours and total_units) are used in training
"""

import json

import pandas as pd

# Training feature lists from train.py (UPDATED)
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

# UI Fields from usageForms.ts (excluding hours and total_units)
UI_FIELDS = {
    "refrigerator": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["fridge_star", "fridge_capacity", "fridge_type", "fridge_age"],
        "excluded": ["refrigerator_hours", "refrigerator_pattern"],
    },
    "air_conditioner": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["ac_star", "ac_tonnage", "ac_type", "ac_age"],
        "excluded": [
            "ac_hours",
            "ac_pattern",
            "ac_usage_pattern",
        ],  # ac_usage_pattern is DERIVED from pattern
    },
    "washing_machine": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["wm_type", "wm_capacity", "wm_star", "wm_age"],
        "excluded": [
            "wm_hours",
            "wm_pattern",
            "wm_cycles_per_week",
        ],  # wm_cycles_per_week is DERIVED
    },
    "geyser": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["geyser_type", "geyser_capacity", "geyser_age"],
        "excluded": ["geyser_hours", "geyser_pattern"],
    },
    "fans": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["fan_type"],
        "excluded": [
            "fan_hours",
            "fan_pattern",
            "num_fans",
        ],  # num_fans from household info
    },
    "tv": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["tv_type", "tv_size"],
        "excluded": ["tv_hours", "tv_pattern"],
    },
    "pump": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["pump_hp"],
        "excluded": ["pump_hours", "pump_pattern"],
    },
    "mixer": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["mixer_hours", "mixer_pattern"],
    },
    "microwave": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["microwave_hours", "microwave_pattern"],
    },
    "kettle": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["kettle_hours", "kettle_pattern"],
    },
    "induction": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["induction_hours", "induction_pattern"],
    },
    "rice_cooker": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["rice_cooker_hours", "rice_cooker_pattern"],
    },
    "toaster": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["toaster_hours", "toaster_pattern"],
    },
    "food_processor": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["food_processor_hours", "food_processor_pattern"],
    },
    "led_lights": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["led_hours", "led_pattern"],
    },
    "cfl_lights": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["cfl_hours", "cfl_pattern"],
    },
    "tube_lights": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["tube_hours", "tube_pattern"],
    },
    "desktop": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["desktop_hours", "desktop_pattern"],
    },
    "laptop": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["laptop_hours", "laptop_pattern"],
    },
    "iron": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["iron_hours", "iron_pattern"],
    },
    "hair_dryer": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["hair_dryer_hours", "hair_dryer_pattern"],
    },
    "vacuum": {
        "base": ["n_occupants", "season", "location_type"],
        "excluded": ["vacuum_hours", "vacuum_pattern"],
    },
}

# Field name mappings (UI key -> Dataset column name)
FIELD_MAPPINGS = {
    # AC
    "ac_star": "ac_star_rating",
    "ac_age": "ac_age",  # NOT used in training (excluded)
    # Fridge
    "fridge_star": "fridge_star_rating",  # NOT used in training
    "fridge_capacity": "fridge_capacity",
    "fridge_age": "fridge_age",
    # Washing Machine
    "wm_star": "wm_star_rating",  # NOT used in training
    "wm_capacity": "wm_capacity",  # NOT used in training
    "wm_age": "wm_age",  # NOT used in training
    # Geyser (water_heater)
    "geyser_type": "water_heater_type",
    "geyser_capacity": "water_heater_capacity",
    "geyser_age": "water_heater_age",
    # TV
    "tv_type": "television_type",
    # Pump
    "pump_hp": "water_pump_hp",
    # Fan
    "num_fans": "num_fans",
}


def check_ui_training_alignment():
    """Check if all UI fields (except hours/total_units) are used in training"""

    print("=" * 80)
    print("UI TO TRAINING COLUMN MAPPING VALIDATION")
    print("=" * 80)
    print(
        "\nChecking: All UI input fields (except hours & total_units) are in training\n"
    )

    # Load dataset to verify column existence
    try:
        df = pd.read_csv("kerala_smartwatt_ai.csv")
        dataset_columns = set(df.columns)
    except:
        print("❌ Cannot load dataset")
        return

    results = []
    total_checks = 0
    passed_checks = 0
    warnings = []

    # Mapping from UI appliance names to training names
    UI_TO_TRAINING = {
        "refrigerator": "fridge",
        "air_conditioner": "ac",
        "washing_machine": "washing_machine",
        "geyser": "water_heater",
        "fans": "ceiling_fan",
        "tv": "television",
        "pump": "water_pump",
        "mixer": "mixer",
        "microwave": "microwave",
        "kettle": "kettle",
        "induction": "induction",
        "rice_cooker": "rice_cooker",
        "toaster": "toaster",
        "food_processor": "food_processor",
        "led_lights": "led_lights",
        "cfl_lights": "cfl_lights",
        "tube_lights": "tube_lights",
        "desktop": "desktop",
        "laptop": "laptop",
        "iron": "iron",
        "hair_dryer": "hair_dryer",
        "vacuum": "vacuum",
    }

    for ui_name, ui_fields_info in UI_FIELDS.items():
        training_name = UI_TO_TRAINING.get(ui_name, ui_name)

        if training_name not in TRAINING_FEATURES:
            warnings.append(f"⚠️  {ui_name} not in training script")
            continue

        print(f"\n{'='*80}")
        print(f"[CHECK] {ui_name.upper()} -> {training_name}")
        print(f"{'='*80}")

        training_features = set(TRAINING_FEATURES[training_name])

        # Collect all UI fields (base + specific)
        all_ui_fields = ui_fields_info.get("base", []) + ui_fields_info.get(
            "specific", []
        )
        excluded_fields = ui_fields_info.get("excluded", [])

        print(f"\n[UI FIELDS] Collected from user:")
        for field in all_ui_fields:
            print(f"   - {field}")

        print(f"\n[EXCLUDED] Hours/patterns fields:")
        for field in excluded_fields:
            print(f"   - {field}")

        print(f"\n[TRAINING] Features from train.py:")
        for field in training_features:
            print(f"   - {field}")

        # Check each UI field
        print(f"\n[MAPPING] Field mapping check:")
        for ui_field in all_ui_fields:
            total_checks += 1

            # Map UI field name to dataset column name
            dataset_field = FIELD_MAPPINGS.get(ui_field, ui_field)

            # Check if field is in training features
            if dataset_field in training_features:
                print(f"   [OK] {ui_field:30s} -> {dataset_field:30s} [IN TRAINING]")
                passed_checks += 1
            elif ui_field in training_features:
                print(f"   [OK] {ui_field:30s} -> {ui_field:30s} [IN TRAINING]")
                passed_checks += 1
            else:
                # Check if it's a valid exclusion (age, star_rating, capacity for some appliances)
                if any(x in ui_field for x in ["age", "star", "capacity"]):
                    print(
                        f"   [WARN] {ui_field:30s} -> {dataset_field:30s} [NOT IN TRAINING - Optional]"
                    )
                    warnings.append(
                        f"{ui_name}: {ui_field} not used in training (optional field)"
                    )
                else:
                    print(
                        f"   [FAIL] {ui_field:30s} -> {dataset_field:30s} [MISSING FROM TRAINING]"
                    )
                    results.append(
                        {
                            "appliance": ui_name,
                            "ui_field": ui_field,
                            "dataset_field": dataset_field,
                            "status": "MISSING",
                        }
                    )

        # Check for extra training features not in UI
        ui_field_set = set(all_ui_fields)
        for field in ui_fields_info.get("base", []):
            ui_field_set.add(field)

        extra_training = training_features - ui_field_set
        if extra_training:
            print(f"\n[WARN] Extra Training Features (not in UI):")
            for field in extra_training:
                if field not in [
                    "n_occupants",
                    "season",
                    "location_type",
                ]:  # Base fields
                    print(f"   - {field}")
                    warnings.append(f"{ui_name}: Training uses {field} but not in UI")

    # Summary
    print(f"\n{'='*80}")
    print("[SUMMARY] VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Checks: {total_checks}")
    print(f"[OK] Passed: {passed_checks}")
    print(f"[FAIL] Failed: {total_checks - passed_checks}")
    print(f"[WARN] Warnings: {len(warnings)}")

    if warnings:
        print(f"\n[WARNINGS]:")
        for w in warnings[:10]:  # Show first 10
            print(f"   - {w}")

    if results:
        print(f"\n[CRITICAL ISSUES]:")
        for r in results:
            print(
                f"   - {r['appliance']}: {r['ui_field']} -> {r['dataset_field']} MISSING"
            )

    # Specific important checks
    print(f"\n{'='*80}")
    print("[KEY CHECKS] KEY VALIDATIONS")
    print(f"{'='*80}")

    key_checks = [
        ("ac", "ac_type", "AC Type (split/window/inverter)"),
        ("ac", "ac_usage_pattern", "AC Usage Pattern"),
        ("fridge", "fridge_type", "Fridge Type (frost/direct)"),
        ("ceiling_fan", "fan_type", "Fan Type (standard/BLDC)"),
        ("television", "tv_size", "TV Size"),
        ("washing_machine", "wm_type", "WM Type (top/front/semi)"),
        ("washing_machine", "wm_cycles_per_week", "WM Cycles Per Week"),
        ("water_pump", "water_pump_hp", "Water Pump HP"),
        ("water_heater", "season", "Season (for water heater)"),
    ]

    for training_name, field, description in key_checks:
        if training_name in TRAINING_FEATURES:
            if field in TRAINING_FEATURES[training_name]:
                print(f"[OK] {description:40s} IN TRAINING")
            else:
                print(f"[FAIL] {description:40s} MISSING FROM TRAINING")

    # Check base fields
    print(f"\n{'='*80}")
    print("[BASE FIELDS] (All Appliances)")
    print(f"{'='*80}")

    base_fields = ["n_occupants", "season", "location_type"]
    for field in base_fields:
        usage_count = sum(
            1 for features in TRAINING_FEATURES.values() if field in features
        )
        print(f"   {field:20s}: Used in {usage_count}/{len(TRAINING_FEATURES)} models")

    print(f"\n{'='*80}")
    if passed_checks == total_checks:
        print("[SUCCESS] ALL UI FIELDS PROPERLY MAPPED TO TRAINING")
    else:
        print(
            f"[WARNING] {total_checks - passed_checks} UI FIELDS NOT MAPPED TO TRAINING"
        )
    print(f"{'='*80}\n")


if __name__ == "__main__":
    check_ui_training_alignment()
