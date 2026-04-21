import logging

logging.basicConfig(level=logging.INFO)

from range_resolver import resolve_range_values

# Test heavy usage
heavy_data = {
    "fridge_age": "3-5",
    "n_occupants": 7,
    "season": "summer",
    "refrigerator_usage_pattern": "always",
    "fridge_type": "frost_free",
    "location_type": "urban",
}

print("Heavy Usage Test:")
result_heavy = resolve_range_values(heavy_data)
print(f"  Input: 3-5")
print(f"  Output: {result_heavy['fridge_age']}")

# Test light usage
light_data = {
    "fridge_age": "3-5",
    "n_occupants": 2,
    "season": "winter",
    "refrigerator_usage_pattern": "light",
    "fridge_type": "direct_cool",
    "location_type": "rural",
}

print("\nLight Usage Test:")
result_light = resolve_range_values(light_data)
print(f"  Input: 3-5")
print(f"  Output: {result_light['fridge_age']}")

print(
    f"\nDifference: {result_heavy['fridge_age'] - result_light['fridge_age']:.2f} years"
)
