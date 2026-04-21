import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

new_cols = ["ac_type", "ac_usage_pattern", "fan_type", "fridge_type", "wm_type"]

print("=" * 60)
print('CHECKING FOR "UNKNOWN" VALUES IN NEW COLUMNS')
print("=" * 60)

for col in new_cols:
    print(f"\n📊 {col}:")
    print(df[col].value_counts())
    unknown_count = (df[col] == "unknown").sum()
    unknown_pct = (unknown_count / len(df)) * 100
    print(f"   ⚠️ Unknown: {unknown_count} ({unknown_pct:.1f}%)")
