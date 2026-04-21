import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")
print(f"Total columns: {len(df.columns)}")

new_cols = [
    "ac_type",
    "ac_usage_pattern",
    "fan_type",
    "fridge_type",
    "num_fans",
    "tv_size",
    "water_pump_hp",
    "wm_cycles_per_week",
    "wm_type",
]

print("\n🔍 Checking new columns:")
for col in new_cols:
    status = "✅ FOUND" if col in df.columns else "❌ MISSING"
    print(f"  {col:25s} {status}")

print(f"\n📊 First few rows of new columns:")
found_cols = [col for col in new_cols if col in df.columns]
if found_cols:
    print(df[found_cols].head())
else:
    print("  No new columns found!")
