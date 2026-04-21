"""
FINAL DATA LEAKAGE CHECK - Verify no leaked features remain
"""

import re

print("=" * 80)
print("FINAL DATA LEAKAGE VERIFICATION")
print("=" * 80)

# Read the actual train.py file
with open("train.py", "r", encoding="utf-8") as f:
    content = f.read()

# Extract the tasks list
tasks_match = re.search(r"tasks = \[(.*?)\]", content, re.DOTALL)

if not tasks_match:
    print("❌ Could not find tasks list in train.py")
    exit(1)

tasks_content = tasks_match.group(1)

print("\n✅ Successfully extracted training configuration from train.py\n")

# Check for data leakage
leakage_indicators = [
    ("total_kwh_monthly", "CRITICAL - Target variable leakage"),
    ("_kwh", "Consumption data leakage"),
    ("_real_effective_hours", "Ground truth hours leakage"),
    ("_real_efficiency_factor", "Ground truth efficiency leakage"),
]

leakage_found = []

for indicator, description in leakage_indicators:
    if indicator in tasks_content:
        leakage_found.append((indicator, description))

if leakage_found:
    print("❌ DATA LEAKAGE STILL PRESENT!")
    print("=" * 80)
    for indicator, desc in leakage_found:
        print(f"   ⚠️  Found: {indicator} - {desc}")
    print("\n" + "=" * 80)
else:
    print("✅ NO DATA LEAKAGE DETECTED!")
    print("=" * 80)
    print("\n✓ No total_kwh_monthly found")
    print("✓ No _kwh columns found")
    print("✓ No _real_effective_hours found")
    print("✓ No _real_efficiency_factor found")

# Parse and display actual features
print("\n" + "=" * 80)
print("TRAINING FEATURES PER APPLIANCE")
print("=" * 80)

lines = tasks_content.strip().split("\n")
appliances = []

for line in lines:
    line = line.strip()
    if line.startswith("("):
        # Extract appliance name and features
        match = re.search(r"\('(\w+)',\s*'(\w+)',\s*\[(.*?)\]\)", line)
        if match:
            name = match.group(1)
            features_str = match.group(3)
            features = [f.strip().strip("'") for f in features_str.split(",")]
            appliances.append((name, features))

for name, features in appliances[:7]:  # Show main appliances
    print(f"\n{name.upper()}:")
    for feat in features:
        print(f"   • {feat}")

# Check ceiling_fan_age issue
print("\n" + "=" * 80)
print("ADDITIONAL CHECKS")
print("=" * 80)

ceiling_fan_features = next((f for n, f in appliances if n == "ceiling_fan"), None)
if ceiling_fan_features and "ceiling_fan_age" in ceiling_fan_features:
    print("\n⚠️  WARNING: ceiling_fan_age is used but NOT in UI")
    print("   Recommendation: Remove ceiling_fan_age or add to UI")
else:
    print("\n✅ ceiling_fan_age removed from training")

# Check if all features are UI-available
ui_available_features = [
    "n_occupants",
    "location_type",
    "season",
    "ac_tonnage",
    "ac_star_rating",
    "ac_type",
    "ac_usage_pattern",
    "fridge_capacity",
    "fridge_age",
    "fridge_type",
    "fan_type",
    "num_fans",
    "television_type",
    "tv_size",
    "wm_type",
    "wm_cycles_per_week",
    "water_pump_hp",
]

print("\n" + "=" * 80)
print("UI AVAILABILITY CHECK")
print("=" * 80)

all_ui_available = True
for name, features in appliances:
    unavailable = [f for f in features if f not in ui_available_features]
    if unavailable:
        print(f"\n❌ {name}: {unavailable} not available from UI")
        all_ui_available = False

if all_ui_available:
    print("\n✅ All training features are available from UI!")

print("\n" + "=" * 80)
if not leakage_found and all_ui_available:
    print("🎉 TRAINING SCRIPT IS PRODUCTION-READY!")
    print("=" * 80)
    print("\n✅ No data leakage")
    print("✅ All features from UI")
    print("✅ Models will work in production")
    print("\n🚀 Ready to train: python train.py")
else:
    print("⚠️  ISSUES DETECTED - Review above")
print("=" * 80)
