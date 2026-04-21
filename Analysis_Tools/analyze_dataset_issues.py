import numpy as np
import pandas as pd

df = pd.read_csv("kerala_smartwatt_ai.csv")

print("=" * 80)
print("DATASET ISSUE ANALYSIS")
print("=" * 80)

print("\n1. AC AGE VALUES (Date Formatting Issue?)")
print("-" * 80)
print(df["ac_age_years"].value_counts())
print(f"\nSample AC age values: {df['ac_age_years'].unique()[:10]}")

print("\n2. AC USAGE PATTERN FOR NON-AC HOUSEHOLDS")
print("-" * 80)
print(f"Total households: {len(df)}")
print(f"Has AC (has_ac=1): {df['has_ac'].sum()}")
print(f"No AC (has_ac=0): {(df['has_ac']==0).sum()}")
print(f"\nPattern distribution for NO-AC households:")
print(df[df["has_ac"] == 0]["ac_usage_pattern"].value_counts())

print("\n3. SAMPLE NON-AC HOUSEHOLD DATA")
print("-" * 80)
print(
    df[df["has_ac"] == 0][
        [
            "has_ac",
            "ac_age_years",
            "ac_type",
            "ac_usage_pattern",
            "ac_real_effective_hours",
            "ac_kwh",
        ]
    ].head(15)
)

print("\n4. CHECKING OTHER APPLIANCES FOR SIMILAR ISSUES")
print("-" * 80)

# Check refrigerator
print("\nREFRIGERATOR:")
print(f"Has fridge: {df['has_refrigerator'].sum()}")
print(f"No fridge: {(df['has_refrigerator']==0).sum()}")
non_fridge_patterns = df[df["has_refrigerator"] == 0][
    "refrigerator_usage_pattern"
].value_counts()
print(f"Non-fridge pattern distribution:\n{non_fridge_patterns[:5]}")

# Check television
print("\nTELEVISION:")
print(f"Has TV: {df['has_television'].sum()}")
print(f"No TV: {(df['has_television']==0).sum()}")
non_tv_patterns = df[df["has_television"] == 0][
    "television_usage_pattern"
].value_counts()
print(f"Non-TV pattern distribution:\n{non_tv_patterns[:5]}")

# Check iron
print("\nIRON:")
print(f"Has iron: {df['has_iron'].sum()}")
print(f"No iron: {(df['has_iron']==0).sum()}")
non_iron_patterns = df[df["has_iron"] == 0]["iron_usage_pattern"].value_counts()
print(f"Non-iron pattern distribution:\n{non_iron_patterns[:5]}")

print("\n5. CHECKING FOR ZERO VALUES WITH NON-ZERO PATTERNS")
print("-" * 80)
issues = df[
    (df["has_ac"] == 0)
    & (df["ac_usage_pattern"] != "unknown")
    & (df["ac_usage_pattern"] != "none")
]
print(f"AC: {len(issues)} households without AC but have usage_pattern assigned")

issues_fridge = df[
    (df["has_refrigerator"] == 0)
    & (df["refrigerator_usage_pattern"] != "unknown")
    & (df["refrigerator_usage_pattern"] != "none")
]
print(
    f"Fridge: {len(issues_fridge)} households without fridge but have usage_pattern assigned"
)

issues_tv = df[
    (df["has_television"] == 0)
    & (df["television_usage_pattern"] != "unknown")
    & (df["television_usage_pattern"] != "none")
]
print(f"TV: {len(issues_tv)} households without TV but have usage_pattern assigned")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
