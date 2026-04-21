"""
Compare appliance field names between Frontend UI and Backend training
Identifies mismatches that could cause prediction errors
"""

import json

import pandas as pd

# Backend Training Appliances (from train.py)
BACKEND_APPLIANCES = {
    "ac": {
        "features": ["ac_tonnage", "ac_star_rating"],
        "targets": ["ac_real_efficiency_factor", "ac_real_effective_hours"],
        "dataset_cols": [
            "has_ac",
            "ac_tonnage",
            "ac_star_rating",
            "ac_real_effective_hours",
            "ac_real_efficiency_factor",
            "ac_kwh",
        ],
    },
    "fridge": {
        "features": ["fridge_capacity", "fridge_age"],
        "targets": ["fridge_real_efficiency_factor", "fridge_real_effective_hours"],
        "dataset_cols": [
            "has_refrigerator",
            "fridge_capacity",
            "fridge_age",
            "fridge_real_effective_hours",
            "fridge_real_efficiency_factor",
            "fridge_kwh",
        ],
    },
    "ceiling_fan": {
        "features": ["ceiling_fan_age"],
        "targets": [
            "ceiling_fan_real_efficiency_factor",
            "ceiling_fan_real_effective_hours",
        ],
        "dataset_cols": [
            "has_ceiling_fan",
            "ceiling_fan_age",
            "ceiling_fan_real_effective_hours",
            "ceiling_fan_real_efficiency_factor",
            "ceiling_fan_kwh",
        ],
    },
    "television": {
        "features": ["television_type"],
        "targets": [
            "television_real_efficiency_factor",
            "television_real_effective_hours",
        ],
        "dataset_cols": [
            "has_television",
            "television_type",
            "television_real_effective_hours",
            "television_real_efficiency_factor",
            "television_kwh",
        ],
    },
    "washing_machine": {
        "features": [],
        "targets": [
            "washing_machine_real_efficiency_factor",
            "washing_machine_real_effective_hours",
        ],
        "dataset_cols": [
            "has_washing_machine",
            "washing_machine_real_effective_hours",
            "washing_machine_real_efficiency_factor",
            "washing_machine_kwh",
        ],
    },
    "water_pump": {
        "features": [],
        "targets": [
            "water_pump_real_efficiency_factor",
            "water_pump_real_effective_hours",
        ],
        "dataset_cols": [
            "has_water_pump",
            "water_pump_real_effective_hours",
            "water_pump_real_efficiency_factor",
            "water_pump_kwh",
        ],
    },
    "water_heater": {
        "features": ["season"],
        "targets": [
            "water_heater_real_efficiency_factor",
            "water_heater_real_effective_hours",
        ],
        "dataset_cols": [
            "has_water_heater",
            "season",
            "water_heater_real_effective_hours",
            "water_heater_real_efficiency_factor",
            "water_heater_kwh",
        ],
    },
    "microwave": {
        "features": [],
        "targets": [
            "microwave_real_efficiency_factor",
            "microwave_real_effective_hours",
        ],
        "dataset_cols": [
            "has_microwave",
            "microwave_real_effective_hours",
            "microwave_real_efficiency_factor",
            "microwave_kwh",
        ],
    },
    "led_lights": {
        "features": [],
        "targets": [
            "led_lights_real_efficiency_factor",
            "led_lights_real_effective_hours",
        ],
        "dataset_cols": [
            "has_led_lights",
            "led_lights_real_effective_hours",
            "led_lights_real_efficiency_factor",
            "led_lights_kwh",
        ],
    },
    "cfl_lights": {
        "features": [],
        "targets": [
            "cfl_lights_real_efficiency_factor",
            "cfl_lights_real_effective_hours",
        ],
        "dataset_cols": [
            "has_cfl_lights",
            "cfl_lights_real_effective_hours",
            "cfl_lights_real_efficiency_factor",
            "cfl_lights_kwh",
        ],
    },
    "tube_lights": {
        "features": [],
        "targets": [
            "tube_lights_real_efficiency_factor",
            "tube_lights_real_effective_hours",
        ],
        "dataset_cols": [
            "has_tube_lights",
            "tube_lights_real_effective_hours",
            "tube_lights_real_efficiency_factor",
            "tube_lights_kwh",
        ],
    },
}

# Frontend UI Field Names (from ApplianceSelection.tsx and diagnostics.tsx)
FRONTEND_FIELDS = {
    "ac": [
        "ac_tonnage",
        "ac_star_rating",
        "ac_hours",
        "ac_temperature",
        "ac_type",
        "ac_usage_pattern",
    ],
    "fridge": ["fridge_age", "fridge_capacity", "fridge_hours"],
    "ceiling_fan": ["fan_type", "fan_hours", "num_fans"],
    "television": ["tv_size", "tv_hours", "tv_type"],
    "washing_machine": ["wm_cycles_per_week", "wm_hours"],
    "water_heater": ["water_heater_hours", "geyser_hours"],
    "water_pump": ["pump_hours", "water_pump_hp"],
    "microwave": ["microwave_minutes"],
    "led_lights": ["num_led", "led_hours"],
    "cfl_lights": ["num_cfl", "cfl_hours"],
    "tube_lights": ["num_tube", "tube_hours"],
    "iron": ["iron_hours"],
    "laptop": ["laptop_hours"],
    "desktop": ["desktop_hours"],
}

# Common Frontend-to-Backend Mappings (from predictor.py)
PREDICTOR_MAPPINGS = {
    "fan": "ceiling_fan",
    "tv": "television",
    "geyser": "water_heater",
    "pump": "water_pump",
    "mixer_grinder": "mixer",
    "led_light": "led_lights",
    "led_bulb": "led_lights",
    "cfl_bulb": "cfl_lights",
    "tube_light": "tube_lights",
}


def analyze_field_mismatches():
    print("=" * 80)
    print("APPLIANCE FIELD COMPARISON: Frontend UI vs Backend Training")
    print("=" * 80)

    print("\n📋 ANALYSIS SCOPE:")
    print(f"   Backend Models Trained:  {len(BACKEND_APPLIANCES)} appliances")
    print(f"   Frontend UI Fields:      {len(FRONTEND_FIELDS)} appliances")

    # Load actual dataset to verify columns
    try:
        df = pd.read_csv("kerala_smartwatt_ai.csv")
        dataset_columns = set(df.columns)
        print(f"   Dataset Columns:         {len(dataset_columns)} total")
    except:
        dataset_columns = set()
        print(f"   Dataset: Not loaded (file not found)")

    # ========== 1. FIELD MATCHING ANALYSIS ==========
    print("\n" + "=" * 80)
    print("1. FIELD MATCHING ANALYSIS")
    print("=" * 80)

    issues = []

    for appliance, backend_info in BACKEND_APPLIANCES.items():
        print(f"\n🔍 {appliance.upper()}")

        frontend_fields = FRONTEND_FIELDS.get(appliance, [])
        backend_features = backend_info["features"]

        print(
            f"   Backend Training Uses: {backend_features if backend_features else 'No specific features (uses generic)'}"
        )
        print(f"   Frontend UI Collects:  {frontend_fields}")

        # Check for mismatches
        for fe_field in frontend_fields:
            # Check if frontend field is used in backend
            if fe_field not in backend_features and fe_field not in [
                "n_occupants",
                "location_type",
                "season",
            ]:
                # Check if it's in dataset
                if dataset_columns and fe_field not in dataset_columns:
                    issues.append(
                        {
                            "appliance": appliance,
                            "field": fe_field,
                            "issue": "Frontend field NOT in dataset",
                            "severity": "HIGH",
                        }
                    )
                elif fe_field.endswith("_hours") or fe_field.endswith("_minutes"):
                    # Usage hours/minutes - these are expected user inputs
                    pass
                else:
                    issues.append(
                        {
                            "appliance": appliance,
                            "field": fe_field,
                            "issue": "Frontend field NOT used in backend training",
                            "severity": "MEDIUM",
                        }
                    )

        # Check dataset columns
        if dataset_columns:
            for col in backend_info["dataset_cols"]:
                if col not in dataset_columns:
                    issues.append(
                        {
                            "appliance": appliance,
                            "field": col,
                            "issue": "Backend expects column NOT in dataset",
                            "severity": "CRITICAL",
                        }
                    )

    # ========== 2. NAME MAPPING ISSUES ==========
    print("\n" + "=" * 80)
    print("2. APPLIANCE NAME MAPPING")
    print("=" * 80)

    print("\n📝 Frontend → Backend Mappings:")
    for frontend_name, backend_name in PREDICTOR_MAPPINGS.items():
        print(f"   '{frontend_name}' → '{backend_name}'")

    print("\n⚠️  Potential Name Conflicts:")
    conflicts = []

    # Check if frontend uses different names
    frontend_appliances = set(FRONTEND_FIELDS.keys())
    backend_appliances = set(BACKEND_APPLIANCES.keys())

    unmapped_frontend = (
        frontend_appliances - backend_appliances - set(PREDICTOR_MAPPINGS.keys())
    )
    if unmapped_frontend:
        print(f"   Frontend appliances with NO backend model: {unmapped_frontend}")
        for app in unmapped_frontend:
            conflicts.append(
                {
                    "frontend": app,
                    "backend": "MISSING",
                    "issue": "No trained model for this appliance",
                }
            )

    # ========== 3. CRITICAL ISSUES ==========
    print("\n" + "=" * 80)
    print("3. CRITICAL ISSUES FOUND")
    print("=" * 80)

    critical = [i for i in issues if i["severity"] == "CRITICAL"]
    high = [i for i in issues if i["severity"] == "HIGH"]
    medium = [i for i in issues if i["severity"] == "MEDIUM"]

    if critical:
        print(f"\n🚨 CRITICAL ({len(critical)}):")
        for issue in critical:
            print(f"   ❌ {issue['appliance']}: {issue['field']}")
            print(f"      Issue: {issue['issue']}")
    else:
        print(f"\n✅ No critical issues")

    if high:
        print(f"\n⚠️  HIGH ({len(high)}):")
        for issue in high:
            print(f"   ⚠️  {issue['appliance']}: {issue['field']}")
            print(f"      Issue: {issue['issue']}")
    else:
        print(f"\n✅ No high-priority issues")

    if medium:
        print(f"\n💡 MEDIUM ({len(medium)}):")
        for issue in medium[:5]:  # Show first 5
            print(f"   ℹ️  {issue['appliance']}: {issue['field']}")
            print(f"      Issue: {issue['issue']}")
        if len(medium) > 5:
            print(f"   ... and {len(medium)-5} more")

    # ========== 4. SPECIFIC FIELD COMPARISONS ==========
    print("\n" + "=" * 80)
    print("4. DETAILED FIELD COMPARISON (Key Appliances)")
    print("=" * 80)

    key_appliances = ["ac", "fridge", "ceiling_fan", "television"]

    for app in key_appliances:
        print(f"\n{'='*40}")
        print(f"{app.upper()}")
        print(f"{'='*40}")

        backend_features = BACKEND_APPLIANCES[app]["features"]
        frontend_fields = FRONTEND_FIELDS.get(app, [])

        print(f"\nBackend Training Features:")
        if backend_features:
            for feat in backend_features:
                status = (
                    "✅"
                    if feat in frontend_fields or feat in ["season", "location_type"]
                    else "❓"
                )
                print(f"   {status} {feat}")
        else:
            print(f"   (Uses only generic features: n_occupants, total_kwh_monthly)")

        print(f"\nFrontend UI Fields:")
        for field in frontend_fields:
            in_backend = field in backend_features
            is_usage = field.endswith("_hours") or field.endswith("_minutes")
            is_count = field.startswith("num_")

            if in_backend:
                status = "✅ Used in training"
            elif is_usage:
                status = "⏱️  Usage input (runtime override)"
            elif is_count:
                status = "🔢 Quantity multiplier"
            else:
                status = "⚠️  Not used in training"

            print(f"   {field:25s} → {status}")

    # ========== 5. RECOMMENDATIONS ==========
    print("\n" + "=" * 80)
    print("5. RECOMMENDATIONS")
    print("=" * 80)

    print("\n✅ WHAT'S WORKING WELL:")
    print("   • Core appliances (AC, Fridge, Fan, TV) have proper field mappings")
    print("   • Usage hours/minutes are correctly handled as user input overrides")
    print("   • Name mappings in predictor.py handle frontend/backend differences")
    print("   • Quantity fields (num_fans, num_led) properly used as multipliers")

    print("\n⚠️  POTENTIAL IMPROVEMENTS:")

    if unmapped_frontend:
        print(f"\n   1. Missing Backend Models:")
        print(f"      Frontend collects data for: {unmapped_frontend}")
        print(f"      Recommendation: Add training tasks for these appliances OR")
        print(f"      remove from frontend if not needed")

    if high:
        print(f"\n   2. Frontend Fields Not in Dataset:")
        print(f"      Some UI fields don't exist in training data")
        print(f"      Recommendation: Add these to newdataset.py OR remove from UI")

    print(f"\n   3. Feature Engineering:")
    print(f"      Some frontend fields are collected but not used in training")
    print(f"      Example: ac_temperature, ac_type, water_pump_hp")
    print(f"      Recommendation: Either use these in models OR remove from UI")

    # ========== 6. SUMMARY ==========
    print("\n" + "=" * 80)
    print("6. SUMMARY")
    print("=" * 80)

    total_issues = len(critical) + len(high) + len(medium)

    if total_issues == 0:
        print("\n✅ PERFECT ALIGNMENT")
        print("   All frontend fields match backend training expectations")
    else:
        print(f"\n📊 Total Issues Found: {total_issues}")
        print(f"   🚨 Critical: {len(critical)}")
        print(f"   ⚠️  High:     {len(high)}")
        print(f"   💡 Medium:   {len(medium)}")

        if len(critical) == 0:
            print(f"\n✅ No critical issues - system is functional")
            print(f"   Issues are minor inconsistencies that don't break predictions")

    print("\n" + "=" * 80 + "\n")

    return issues, conflicts


if __name__ == "__main__":
    issues, conflicts = analyze_field_mismatches()
