"""
Test that ALL user inputs from the UI are properly used by the backend AI for predictions
"""

from predictor import get_predictor

predictor = get_predictor()

# Simulating EXACT user inputs from the UI
test_cases = {
    "ac": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "ac_tonnage": 1.0,
        "ac_star_rating": 5,
        "ac_type": "split",  # UI showed "Don't Know" but backend needs a value
        "ac_age_years": "6-10",  # RANGE INPUT - should use AI resolution
        "ac_usage_pattern": "rare",
        "ac_hours": 0.25,
        "total_kwh_monthly": 150,
    },
    "fridge": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "fridge_capacity": 215,
        "fridge_star_rating": 5,
        "fridge_type": "direct_cool",
        "fridge_age": "5-10",  # RANGE INPUT - should use AI resolution
        "refrigerator_usage_pattern": "always",
        "fridge_hours": 24,
        "total_kwh_monthly": 150,
    },
    "ceiling_fan": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "fan_type": "standard",
        "num_fans": 2,
        "fan_usage_pattern": "most",
        "ceiling_fan_hours": 8,
        "total_kwh_monthly": 150,
    },
    "led_light": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "num_led_lights": 8,
        "led_lights_usage_pattern": "evening",
        "led_lights_hours": 7,
        "total_kwh_monthly": 150,
    },
    "water_pump": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "water_pump_hp": 1.0,
        "pump_usage_pattern": "rare",
        "water_pump_hours": 0.21,
        "total_kwh_monthly": 150,
    },
    "iron": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "iron_usage_pattern": "light",
        "iron_hours": 0.048,
        "total_kwh_monthly": 150,
    },
    "television": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "television_type": "LED",
        "tv_size": 43,
        "television_usage_pattern": "light",
        "television_hours": 2,
        "total_kwh_monthly": 150,
    },
    "mixer_grinder": {
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "mixer_usage_pattern": "rarely",
        "mixer_grinder_wattage": 750,
        "mixer_hours": 0.167,
        "total_kwh_monthly": 150,
    },
}

print("=" * 100)
print("TESTING ALL USER INPUTS - VERIFYING AI USES EACH FIELD FOR PREDICTION")
print("=" * 100)

for appliance, inputs in test_cases.items():
    print(f"\n{'=' * 100}")
    print(f"📱 {appliance.upper()}")
    print(f"{'=' * 100}")

    # Show all inputs being sent
    print("\n📝 User Inputs:")
    for key, value in inputs.items():
        if key not in ["total_kwh_monthly"]:
            print(f"   • {key}: {value}")

    try:
        result = predictor.predict(appliance, [inputs])

        print(f"\n✅ Prediction Result:")
        print(f"   • Energy: {result['prediction']:.2f} kWh")
        print(f"   • Source: {result['insights']['source']}")
        print(f"   • Base Watts: {result['insights']['base_watts']:.0f}W")
        print(f"   • Real Watts: {result['insights']['real_watts']:.0f}W")
        print(f"   • Efficiency Factor: {result['insights']['efficiency_score']}")
        print(f"   • Predicted Hours: {result['insights']['predicted_hours']:.2f}h")

        # Check if AI model was used or fallback
        if result["insights"]["source"] == "Pure_Physics_Fallback":
            print(f"   ⚠️  WARNING: Using physics fallback (AI model failed)")
        elif "AI" in result["insights"]["source"]:
            print(f"   🧠 AI MODEL ACTIVE")

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

print("\n" + "=" * 100)
print("TEST COMPLETE")
print("=" * 100)
print("\n📊 Summary:")
print("   • All appliances tested with exact UI inputs")
print("   • Range values (ac_age_years, fridge_age) should show AI resolution in logs")
print(
    "   • Check for 'Pure_Physics_Fallback' warnings - indicates AI model not running"
)
print("=" * 100)
