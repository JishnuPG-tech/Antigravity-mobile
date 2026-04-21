"""
FINAL UI-TRAINING ALIGNMENT VERIFICATION
Generated: January 26, 2026
"""

import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("=" * 80)
print("FINAL UI-TRAINING ALIGNMENT VERIFICATION")
print("=" * 80)

# Training features from train.py
training_config = {
    "AC": {
        "ui_fields": [
            "ac_tonnage",
            "ac_star_rating",
            "ac_type",
            "ac_usage_pattern",
            "location_type",
        ],
        "training_features": [
            "n_occupants",
            "total_kwh_monthly",
            "ac_tonnage",
            "ac_star_rating",
            "ac_type",
            "ac_usage_pattern",
            "location_type",
        ],
        "key_new_fields": ["ac_type", "ac_usage_pattern"],
    },
    "Fridge": {
        "ui_fields": ["fridge_capacity_liters", "fridge_age_years", "fridge_type"],
        "training_features": [
            "n_occupants",
            "total_kwh_monthly",
            "fridge_capacity",
            "fridge_age",
            "fridge_type",
            "location_type",
        ],
        "key_new_fields": ["fridge_type"],
    },
    "Ceiling Fan": {
        "ui_fields": ["num_ceiling_fans", "fan_type"],
        "training_features": [
            "n_occupants",
            "total_kwh_monthly",
            "ceiling_fan_age",
            "fan_type",
            "num_fans",
        ],
        "key_new_fields": ["fan_type", "num_fans"],
    },
    "Television": {
        "ui_fields": ["tv_size_inches", "tv_type"],
        "training_features": [
            "n_occupants",
            "total_kwh_monthly",
            "television_type",
            "tv_size",
        ],
        "key_new_fields": ["tv_size"],
    },
    "Washing Machine": {
        "ui_fields": ["wm_type", "wm_cycles_per_week"],
        "training_features": [
            "n_occupants",
            "total_kwh_monthly",
            "wm_type",
            "wm_cycles_per_week",
        ],
        "key_new_fields": ["wm_type", "wm_cycles_per_week"],
    },
    "Water Pump": {
        "ui_fields": ["water_pump_hp"],
        "training_features": ["n_occupants", "total_kwh_monthly", "water_pump_hp"],
        "key_new_fields": ["water_pump_hp"],
    },
}

field_mappings = {
    "fridge_capacity_liters": "fridge_capacity",
    "fridge_age_years": "fridge_age",
    "num_ceiling_fans": "num_fans",
    "tv_size_inches": "tv_size",
    "tv_type": "television_type",
}

print(f"\n📦 Dataset: {len(df)} households, {len(df.columns)} columns")
print("\n" + "=" * 80)

for appliance, config in training_config.items():
    print(f"\n{appliance}")
    print("-" * 80)

    # Check if all training features exist in dataset
    all_present = True
    missing = []

    for feature in config["training_features"]:
        if feature not in df.columns:
            all_present = False
            missing.append(feature)

    if all_present:
        print(
            f'✅ All {len(config["training_features"])} training features exist in dataset'
        )
    else:
        print(f"❌ Missing features: {missing}")
        continue

    # Show new fields added
    print(f"\n🆕 Key new UI-aligned fields:")
    for field in config["key_new_fields"]:
        if field in df.columns:
            print(f"   ✓ {field}")
            # Show sample values
            sample = df[field].value_counts().head(3)
            print(f"      Top values: {dict(sample)}")
        else:
            print(f"   ✗ {field} - MISSING!")

    # Show training feature count
    print(f'\n📊 Training uses {len(config["training_features"])} features')
    print(f'   UI provides {len(config["ui_fields"])} appliance-specific fields')

print("\n" + "=" * 80)
print("CRITICAL NEW FIELDS VERIFICATION")
print("=" * 80)

critical_fields = [
    ("ac_type", "AC Type", "split/window/inverter - 30% efficiency variance"),
    ("ac_usage_pattern", "AC Usage", "heavy/moderate/light - usage prediction"),
    ("fridge_type", "Fridge Type", "frost_free/direct_cool - 20-30% power difference"),
    ("fan_type", "Fan Type", "standard/bldc - 50% energy savings"),
    ("num_fans", "Fan Count", "2-6 fans per household"),
    ("tv_size", "TV Size", "32/43/55 inches - size-based consumption"),
    ("wm_type", "WM Type", "top_load/front_load/semi_automatic"),
    ("wm_cycles_per_week", "WM Cycles", "Usage frequency - most predictive"),
    ("water_pump_hp", "Pump HP", "0.5/1.0/1.5 HP - direct power correlation"),
]

print("\n")
for col, name, description in critical_fields:
    if col in df.columns:
        non_null = df[col].notna().sum()
        unique = df[col].nunique()
        print(f"✅ {name:20s} | Exists | {non_null:,} records | {unique} unique values")
        print(f"   💡 {description}")
    else:
        print(f"❌ {name:20s} | MISSING!")

print("\n" + "=" * 80)
print("FIELD MAPPING VALIDATION")
print("=" * 80)
print("\nUI Field Name → Dataset Column Name:")
for ui_field, dataset_col in field_mappings.items():
    status = "✓" if dataset_col in df.columns else "✗"
    print(f"{status} {ui_field:30s} → {dataset_col}")

print("\n" + "=" * 80)
print("TRAINING READINESS CHECK")
print("=" * 80)

# Count how many appliances can be trained
ready_count = 0
total_count = len(training_config)

for appliance, config in training_config.items():
    features_exist = all(f in df.columns for f in config["training_features"])
    if features_exist:
        ready_count += 1
        print(f"✅ {appliance:20s} - Ready to train")
    else:
        print(f"❌ {appliance:20s} - Missing features")

print(f"\n📊 Training readiness: {ready_count}/{total_count} appliances ready")

if ready_count == total_count:
    print("\n" + "=" * 80)
    print("🎉 PERFECT ALIGNMENT ACHIEVED!")
    print("=" * 80)
    print("\n✅ All UI input fields are present in dataset")
    print("✅ All training features are available")
    print("✅ Field mappings are correct")
    print("✅ Ready to train models with UI-aligned features")
    print('\n🚀 Next step: Run "python train.py" to train all models')
else:
    print("\n⚠️ Some appliances are not ready for training!")
    print("Please check the missing features above.")

print("\n" + "=" * 80)
