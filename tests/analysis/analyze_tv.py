import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("\n" + "=" * 60)
print("TV CONSUMPTION ANALYSIS")
print("=" * 60)

print("\n[1] TV Usage Statistics:")
print(f"Average hours/day: {df['television_real_effective_hours'].mean():.1f}h")
print(f"Average kWh/day: {df['television_kwh'].mean() / 30:.2f}")
print(f"Average kWh/month: {df['television_kwh'].mean():.2f}")

print("\n[2] TV Size Distribution:")
print(df["tv_size"].value_counts())

print("\n[3] TV Type Distribution:")
print(df["television_type"].value_counts())

print("\n[4] Sample TV Data (first 10 rows):")
cols = [
    "tv_size",
    "television_type",
    "television_real_effective_hours",
    "television_kwh",
]
print(df[cols].head(10))

print("\n[5] Physics Calculation Check:")
print("For 43-inch LED TV:")
print(f"  Physics watts: 43 * 2.5 = {43 * 2.5:.0f}W")
print(f"  At 5 hours/day: {43 * 2.5 * 5 / 1000:.2f} kWh/day")
print(f"  Monthly: {43 * 2.5 * 5 * 30 / 1000:.2f} kWh/month")

print("\n" + "=" * 60)
