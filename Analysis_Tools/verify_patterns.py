import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("\n" + "=" * 70)
print("USAGE PATTERN vs EFFECTIVE HOURS VERIFICATION")
print("=" * 70)

# AC
print("\n1. AIR CONDITIONER:")
print(
    df[df["has_ac"] == 1][["ac_usage_pattern", "ac_real_effective_hours"]]
    .groupby("ac_usage_pattern")["ac_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Fridge
print("\n2. REFRIGERATOR:")
print(
    df[df["has_refrigerator"] == 1][
        ["refrigerator_usage_pattern", "fridge_real_effective_hours"]
    ]
    .groupby("refrigerator_usage_pattern")["fridge_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Television
print("\n3. TELEVISION:")
print(
    df[df["has_television"] == 1][
        ["television_usage_pattern", "television_real_effective_hours"]
    ]
    .groupby("television_usage_pattern")["television_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Iron
print("\n4. IRON:")
print(
    df[df["has_iron"] == 1][["iron_usage_pattern", "iron_real_effective_hours"]]
    .groupby("iron_usage_pattern")["iron_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Kettle
print("\n5. ELECTRIC KETTLE:")
print(
    df[df["has_electric_kettle"] == 1][
        ["kettle_usage_pattern", "kettle_real_effective_hours"]
    ]
    .groupby("kettle_usage_pattern")["kettle_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Water Pump
print("\n6. WATER PUMP:")
print(
    df[df["has_water_pump"] == 1][
        ["pump_usage_pattern", "water_pump_real_effective_hours"]
    ]
    .groupby("pump_usage_pattern")["water_pump_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

# Geyser
print("\n7. WATER HEATER (GEYSER):")
print(
    df[df["has_water_heater"] == 1][
        ["geyser_usage_pattern", "water_heater_real_effective_hours"]
    ]
    .groupby("geyser_usage_pattern")["water_heater_real_effective_hours"]
    .agg(["count", "mean", "min", "max"])
    .round(2)
)

print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)
