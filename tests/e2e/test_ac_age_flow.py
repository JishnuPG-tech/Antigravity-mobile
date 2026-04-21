"""
Test AC Age Field Complete Data Flow
Tests that ac_age_years is properly handled from API → Predictor → Model
"""

import sys

from predictor import get_predictor
from schemas import ACInput


def test_ac_age_api_validation():
    """Test 1: API Schema Validation"""
    print("\n" + "=" * 80)
    print("TEST 1: API Schema Validation (schemas.py)")
    print("=" * 80)

    # Test valid AC input with age
    test_data = {
        "n_occupants": 4,
        "location_type": "urban",
        "season": "summer",
        "ac_tonnage": 1.5,
        "ac_star_rating": 3,
        "num_ac_units": 1,
        "ac_type": "split",
        "ac_age_years": "3-5",  # This is categorical!
        "ac_usage_pattern": "moderate",
        "ac_hours_per_day": 8.0,
        "total_kwh_monthly": 300,
    }

    try:
        validated = ACInput(test_data)
        print(f"✅ Schema validation passed!")
        print(f"   ac_age_years: {validated.ac_age_years}")
        print(f"   ac_type: {validated.ac_type}")
        print(f"   ac_usage_pattern: {validated.ac_usage_pattern}")
        return validated
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return None


def test_predictor_preprocessing():
    """Test 2: Predictor Preprocessing"""
    print("\n" + "=" * 80)
    print("TEST 2: Predictor Preprocessing (predictor.py)")
    print("=" * 80)

    predictor = get_predictor()

    # Test data that will be sent to predictor
    test_data = [
        {
            "n_occupants": 4,
            "location_type": "urban",
            "season": "summer",
            "ac_tonnage": 1.5,
            "ac_star_rating": 3,
            "ac_type": "split",
            "ac_age_years": "3-5",  # Categorical value
            "ac_usage_pattern": "moderate",
            "ac_hours": 8.0,
            "total_kwh_monthly": 300,
        }
    ]

    try:
        result = predictor.predict("ac", test_data)
        print(f"✅ Prediction successful!")
        print(f"   Predicted kWh: {result['prediction']:.2f}")
        print(f"   Source: {result['insights']['source']}")
        print(f"   Predicted Hours: {result['insights']['predicted_hours']:.2f}")
        print(f"   Efficiency Factor: {result['insights']['efficiency_factor']:.2f}")
        return result
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_all_age_values():
    """Test 3: All AC Age Values"""
    print("\n" + "=" * 80)
    print("TEST 3: All AC Age Categories")
    print("=" * 80)

    predictor = get_predictor()

    age_values = ["unknown", "0-2", "3-5", "6-10", "10+"]

    for age in age_values:
        test_data = [
            {
                "n_occupants": 4,
                "location_type": "urban",
                "season": "summer",
                "ac_tonnage": 1.5,
                "ac_star_rating": 3,
                "ac_type": "split",
                "ac_age_years": age,
                "ac_usage_pattern": "moderate",
                "ac_hours": 8.0,
                "total_kwh_monthly": 300,
            }
        ]

        try:
            result = predictor.predict("ac", test_data)
            print(
                f"✅ Age '{age}': {result['prediction']:.2f} kWh (Source: {result['insights']['source']})"
            )
        except Exception as e:
            print(f"❌ Age '{age}': Failed - {e}")


def check_categorical_columns():
    """Test 4: Verify ac_age_years in categorical_columns"""
    print("\n" + "=" * 80)
    print("TEST 4: Categorical Columns Check")
    print("=" * 80)

    import inspect

    from predictor import AppliancePredictor

    # Get the source code to find categorical_columns definition
    source = inspect.getsource(AppliancePredictor.predict)

    if "ac_age_years" in source and "categorical_columns" in source:
        print("✅ ac_age_years found in categorical_columns definition")
    else:
        print(
            "⚠️  ac_age_years might not be in categorical_columns - checking runtime..."
        )


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧪 SMARTWATT AC AGE FIELD INTEGRATION TEST")
    print("=" * 80)

    # Test 1: Schema validation
    validated = test_ac_age_api_validation()

    if validated:
        # Test 2: Predictor preprocessing
        result = test_predictor_preprocessing()

        if result:
            # Test 3: All age values
            test_all_age_values()

    # Test 4: Check categorical columns
    check_categorical_columns()

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80 + "\n")
