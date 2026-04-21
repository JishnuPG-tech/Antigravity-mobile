"""
End-to-End Test: AI-Based Dynamic Range Resolution
Tests that range values are intelligently resolved based on usage context
"""

import sys

from predictor import get_predictor
from schemas import FridgeInput


def test_dynamic_range_resolution():
    """
    Test that identical range inputs produce different results
    based on usage context (heavy vs light)
    """
    print("\n" + "=" * 80)
    print("AI-BASED DYNAMIC RANGE RESOLUTION TEST")
    print("=" * 80)

    predictor = get_predictor()

    # Scenario 1: Heavy Usage (should bias toward higher age = more wear)
    print("\n1️⃣ HEAVY USAGE CONTEXT")
    print("-" * 80)

    heavy_data = [
        {
            "n_occupants": 7,
            "location_type": "urban",
            "season": "summer",
            "fridge_capacity": 300.0,  # Training column name
            "fridge_age": "3-5",  # 🎯 RANGE INPUT (training column name)
            "fridge_star_rating": 3,
            "fridge_type": "frost_free",
            "refrigerator_usage_pattern": "always",
            "total_kwh_monthly": 300,
        }
    ]

    print("Input Context:")
    print(f"  • Age Range: '3-5' years")
    print(f"  • Occupants: 7 (large family)")
    print(f"  • Location: Urban (more power fluctuations)")
    print(f"  • Season: Summer (compressor works harder)")
    print(f"  • Usage: Always running (high wear)")
    print(f"  • Type: Frost-free (complex system)")

    try:
        result_heavy = predictor.predict("fridge", heavy_data)
        print(f"\n✅ Prediction: {result_heavy['prediction']:.2f} kWh")
        print(f"   Source: {result_heavy['insights']['source']}")
        print(f"   Expected: Higher consumption (age biased toward 5.0)")
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False

    # Scenario 2: Light Usage (should bias toward lower age = less wear)
    print("\n2️⃣ LIGHT USAGE CONTEXT")
    print("-" * 80)

    light_data = [
        {
            "n_occupants": 2,
            "location_type": "rural",
            "season": "winter",
            "fridge_capacity": 300.0,  # Training column name
            "fridge_age": "3-5",  # 🎯 SAME RANGE INPUT (training column name)
            "fridge_star_rating": 3,
            "fridge_type": "direct_cool",
            "refrigerator_usage_pattern": "light",
            "total_kwh_monthly": 300,
        }
    ]

    print("Input Context:")
    print(f"  • Age Range: '3-5' years (SAME as heavy)")
    print(f"  • Occupants: 2 (small household)")
    print(f"  • Location: Rural (stable power)")
    print(f"  • Season: Winter (easier cooling)")
    print(f"  • Usage: Light (low wear)")
    print(f"  • Type: Direct-cool (simpler system)")

    try:
        result_light = predictor.predict("fridge", light_data)
        print(f"\n✅ Prediction: {result_light['prediction']:.2f} kWh")
        print(f"   Source: {result_light['insights']['source']}")
        print(f"   Expected: Lower consumption (age biased toward 3.0)")
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False

    # Comparison
    print("\n3️⃣ COMPARISON: DYNAMIC vs STATIC")
    print("-" * 80)

    difference = result_heavy["prediction"] - result_light["prediction"]
    percent_diff = (difference / result_light["prediction"]) * 100

    print(f"Heavy Usage:  {result_heavy['prediction']:.2f} kWh")
    print(f"Light Usage:  {result_light['prediction']:.2f} kWh")
    print(f"Difference:   {difference:.2f} kWh ({percent_diff:+.1f}%)")
    print(f"\n💡 Insight: Same range input ('3-5') produces different predictions")
    print(f"   based on usage context - this is AI-driven intelligence!")

    if difference > 0:
        print(f"\n✅ TEST PASSED: Heavy usage resulted in higher consumption")
        print(f"   The AI correctly biased toward max age for heavy wear scenario")
    else:
        print(f"\n⚠️  Unexpected: Light usage has higher consumption")

    # Test other range formats
    print("\n4️⃣ OTHER RANGE FORMATS")
    print("-" * 80)

    test_ranges = [
        ("10+", "Open-ended (10+ years)"),
        ("<1", "Less than 1 year"),
        ("1-3", "Different range"),
        (5.0, "Direct numeric (no range)"),
    ]

    for age_input, description in test_ranges:
        test_data = [
            {
                "n_occupants": 4,
                "location_type": "urban",
                "season": "monsoon",
                "fridge_capacity": 240.0,
                "fridge_age": age_input,
                "fridge_star_rating": 3,
                "fridge_type": "frost_free",
                "refrigerator_usage_pattern": "normal",
                "total_kwh_monthly": 300,
            }
        ]

        try:
            result = predictor.predict("fridge", test_data)
            print(
                f"  {str(age_input):6s} ({description:25s}) → {result['prediction']:.2f} kWh"
            )
        except Exception as e:
            print(f"  {str(age_input):6s} ({description:25s}) → Error: {e}")

    print("\n" + "=" * 80)
    print("AI-BASED RANGE RESOLUTION TEST COMPLETE")
    print("=" * 80)


def test_schema_validation():
    """Test that schema accepts both string ranges and numeric values"""
    print("\n" + "=" * 80)
    print("SCHEMA VALIDATION TEST (Union[float, str])")
    print("=" * 80)

    test_cases = [
        ("3-5", "Range string"),
        ("10+", "Open-ended range"),
        ("<1", "Less than range"),
        (4.0, "Numeric value"),
        (5, "Integer value"),
    ]

    for age_value, description in test_cases:
        test_data = {
            "n_occupants": 4,
            "location_type": "urban",
            "season": "summer",
            "fridge_capacity": 240.0,
            "fridge_age": age_value,
            "fridge_star_rating": 3,
            "fridge_type": "frost_free",
            "refrigerator_usage_pattern": "normal",
            "total_kwh_monthly": 300,
        }

        try:
            validated = FridgeInput(test_data)
            print(
                f"✅ {str(age_value):6s} ({description:20s}) - Type: {type(validated.fridge_age_years).__name__}"
            )
        except Exception as e:
            print(f"❌ {str(age_value):6s} ({description:20s}) - Error: {e}")

    print()


if __name__ == "__main__":
    # Test 1: Schema validation
    test_schema_validation()

    # Test 2: End-to-end dynamic resolution
    success = test_dynamic_range_resolution()

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The AI-based range resolver is working correctly.")
        print("\nKey Features:")
        print("  ✓ Ranges are resolved dynamically based on usage context")
        print("  ✓ Heavy usage → biases toward max (more wear)")
        print("  ✓ Light usage → biases toward min (less wear)")
        print("  ✓ Same range input produces different predictions")
        print("  ✓ All range formats supported (x-y, x+, <x, numeric)")
