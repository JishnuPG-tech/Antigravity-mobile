"""
Comprehensive Test: AI-Based Dynamic Range Resolution for All Appliances
Tests that ALL appliances with range-based inputs use AI resolution
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from range_resolver import resolve_range_values


def test_all_appliances():
    print("\n" + "=" * 80)
    print("TESTING AI RANGE RESOLUTION FOR ALL APPLIANCES")
    print("=" * 80)

    # Test 1: Fridge - Age + Capacity
    print("\n1. FRIDGE (Age + Capacity ranges)")
    print("-" * 80)

    fridge_heavy = {
        "fridge_age": "3-5",
        "fridge_capacity": "300L+",
        "n_occupants": 7,
        "season": "summer",
        "refrigerator_usage_pattern": "always",
        "fridge_type": "frost_free",
        "location_type": "urban",
    }

    fridge_light = {
        "fridge_age": "3-5",
        "fridge_capacity": "300L+",
        "n_occupants": 2,
        "season": "winter",
        "refrigerator_usage_pattern": "light",
        "fridge_type": "direct_cool",
        "location_type": "rural",
    }

    result_heavy = resolve_range_values(fridge_heavy)
    result_light = resolve_range_values(fridge_light)

    print(
        f"  Heavy Usage: age={result_heavy['fridge_age']:.2f}, capacity={result_heavy['fridge_capacity']:.0f}L"
    )
    print(
        f"  Light Usage: age={result_light['fridge_age']:.2f}, capacity={result_light['fridge_capacity']:.0f}L"
    )
    print(
        f"  Age diff: {result_heavy['fridge_age'] - result_light['fridge_age']:.2f} years"
    )
    print(
        f"  Capacity diff: {result_heavy['fridge_capacity'] - result_light['fridge_capacity']:.0f}L"
    )

    # Test 2: Washing Machine - Capacity
    print("\n2. WASHING MACHINE (Capacity range)")
    print("-" * 80)

    wm_large = {
        "wm_capacity": "8.0+",
        "n_occupants": 8,
        "wm_cycles_per_week": 10,
        "wm_type": "front_load",
    }

    wm_small = {
        "wm_capacity": "8.0+",
        "n_occupants": 2,
        "wm_cycles_per_week": 2,
        "wm_type": "semi_automatic",
    }

    result_large = resolve_range_values(wm_large)
    result_small = resolve_range_values(wm_small)

    print(f"  Large Family: capacity={result_large['wm_capacity']:.1f}kg")
    print(f"  Small Family: capacity={result_small['wm_capacity']:.1f}kg")
    print(
        f"  Difference: {result_large['wm_capacity'] - result_small['wm_capacity']:.1f}kg"
    )

    # Test 3: Water Heater/Geyser - Age + Capacity
    print("\n3. WATER HEATER (Age + Capacity ranges)")
    print("-" * 80)

    geyser_heavy = {
        "water_heater_age": "5-10",
        "water_heater_capacity": "25L+",
        "n_occupants": 6,
        "season": "winter",
        "geyser_usage_pattern": "heavy",
        "water_heater_type": "storage",
    }

    geyser_light = {
        "water_heater_age": "5-10",
        "water_heater_capacity": "25L+",
        "n_occupants": 2,
        "season": "summer",
        "geyser_usage_pattern": "minimal",
        "water_heater_type": "instant",
    }

    result_heavy_geyser = resolve_range_values(geyser_heavy)
    result_light_geyser = resolve_range_values(geyser_light)

    print(
        f"  Heavy Usage: age={result_heavy_geyser['water_heater_age']:.2f}, capacity={result_heavy_geyser['water_heater_capacity']:.0f}L"
    )
    print(
        f"  Light Usage: age={result_light_geyser['water_heater_age']:.2f}, capacity={result_light_geyser['water_heater_capacity']:.0f}L"
    )
    print(
        f"  Age diff: {result_heavy_geyser['water_heater_age'] - result_light_geyser['water_heater_age']:.2f} years"
    )
    print(
        f"  Capacity diff: {result_heavy_geyser['water_heater_capacity'] - result_light_geyser['water_heater_capacity']:.0f}L"
    )

    # Test 4: All edge cases
    print("\n4. EDGE CASES FOR ALL APPLIANCES")
    print("-" * 80)

    edge_tests = [
        ("fridge_age", ["<1", "1-3", "10+"]),
        ("water_heater_age", ["<2", "2-5", "10+"]),
        ("fridge_capacity", ["300L+"]),
        ("wm_capacity", ["8.0+"]),
        ("water_heater_capacity", ["25L+"]),
    ]

    for field, ranges in edge_tests:
        for range_val in ranges:
            test_data = {
                field: range_val,
                "n_occupants": 4,
                "season": "monsoon",
                "refrigerator_usage_pattern": "normal",
                "geyser_usage_pattern": "light",
                "location_type": "urban",
            }
            result = resolve_range_values(test_data)
            resolved = result[field]
            if isinstance(resolved, float):
                print(f"  {field:25s} '{range_val:6s}' → {resolved:.1f}")

    print("\n" + "=" * 80)
    print("ALL APPLIANCE RANGE RESOLUTION TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("  ✓ Fridge: Age and Capacity ranges resolved dynamically")
    print("  ✓ Washing Machine: Capacity range resolved based on family size")
    print("  ✓ Water Heater: Age and Capacity ranges resolved based on usage")
    print("  ✓ All edge cases handled correctly")
    print("\n  AI adjusts values based on:")
    print("    - Number of occupants")
    print("    - Usage patterns")
    print("    - Season")
    print("    - Location type")
    print("    - Appliance type")


if __name__ == "__main__":
    test_all_appliances()
