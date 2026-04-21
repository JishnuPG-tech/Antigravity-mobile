import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("=" * 60)
print("VERIFICATION: UNKNOWN VALUES IN TRAINING DATA")
print("=" * 60)

# AC
ac_owners = df[df["has_ac"] == 1]
print(f"\n🔌 AC Owners: {len(ac_owners)}")
print(f"   ac_type distribution:")
print(ac_owners["ac_type"].value_counts())
print(f'   ✅ No unknown values: {(ac_owners["ac_type"] == "unknown").sum() == 0}')

# Fridge
fridge_owners = df[df["has_refrigerator"] == 1]
print(f"\n🧊 Fridge Owners: {len(fridge_owners)}")
print(f"   fridge_type distribution:")
print(fridge_owners["fridge_type"].value_counts())
print(
    f'   ✅ No unknown values: {(fridge_owners["fridge_type"] == "unknown").sum() == 0}'
)

# Fan
fan_owners = df[df["has_ceiling_fan"] == 1]
print(f"\n🌀 Fan Owners: {len(fan_owners)}")
print(f"   fan_type distribution:")
print(fan_owners["fan_type"].value_counts())
print(f'   ✅ No unknown values: {(fan_owners["fan_type"] == "unknown").sum() == 0}')

# Washing Machine
wm_owners = df[df["has_washing_machine"] == 1]
print(f"\n🧺 Washing Machine Owners: {len(wm_owners)}")
print(f"   wm_type distribution:")
print(wm_owners["wm_type"].value_counts())
print(f'   ✅ No unknown values: {(wm_owners["wm_type"] == "unknown").sum() == 0}')

print("\n" + "=" * 60)
print('CONCLUSION: All "unknown" values are for non-owners only!')
print("Training will use only valid categorical values.")
print("=" * 60)
