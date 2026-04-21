import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("=" * 80)
print("DATASET COLUMN NAME VERIFICATION")
print("=" * 80)

# Training features used in train.py
training_features = {
    "Common": ["n_occupants", "location_type", "season"],
    "AC": ["ac_tonnage", "ac_star_rating", "ac_type", "ac_usage_pattern"],
    "Fridge": ["fridge_capacity", "fridge_age", "fridge_type"],
    "Fan": ["fan_type", "num_fans"],
    "TV": ["television_type", "tv_size"],
    "WM": ["wm_type", "wm_cycles_per_week"],
    "Pump": ["water_pump_hp"],
}

print("\n✅ Checking if training features exist in dataset:\n")

all_exist = True
for category, features in training_features.items():
    print(f"{category}:")
    for feat in features:
        exists = feat in df.columns
        status = "✅" if exists else "❌"
        print(f"   {status} {feat}")
        if not exists:
            all_exist = False
    print()

if all_exist:
    print("=" * 80)
    print("✅ ALL TRAINING FEATURES EXIST IN DATASET!")
    print("=" * 80)
else:
    print("=" * 80)
    print("❌ SOME FEATURES MISSING - CHECK COLUMN NAMES")
    print("=" * 80)
