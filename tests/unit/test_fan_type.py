from predictor import get_predictor

predictor = get_predictor()

# Test BLDC (should be ~28W)
bldc_result = predictor.predict(
    "ceiling_fan",
    [
        {
            "n_occupants": 3,
            "season": "monsoon",
            "location_type": "rural",
            "fan_type": "bldc",
            "num_fans": 2,
            "fan_usage_pattern": "most",
            "ceiling_fan_hours": 8,
            "total_kwh_monthly": 150,
        }
    ],
)

# Test Standard (should be ~75W)
standard_result = predictor.predict(
    "ceiling_fan",
    [
        {
            "n_occupants": 3,
            "season": "monsoon",
            "location_type": "rural",
            "fan_type": "standard",
            "num_fans": 2,
            "fan_usage_pattern": "most",
            "ceiling_fan_hours": 8,
            "total_kwh_monthly": 150,
        }
    ],
)

print("=" * 80)
print("CEILING FAN TYPE COMPARISON")
print("=" * 80)
print("\nBLDC Fan (Energy Saver - 28W):")
print(f"  Prediction: {bldc_result['prediction']:.2f} kWh")
print(f"  Source: {bldc_result['insights']['source']}")
print(f"  Base Watts: {bldc_result['insights']['base_watts']:.0f}W")
print(f"  Real Watts: {bldc_result['insights']['real_watts']:.0f}W")
print(f"  Efficiency: {bldc_result['insights']['efficiency_score']}")

print("\nStandard Fan (Old - 75W):")
print(f"  Prediction: {standard_result['prediction']:.2f} kWh")
print(f"  Source: {standard_result['insights']['source']}")
print(f"  Base Watts: {standard_result['insights']['base_watts']:.0f}W")
print(f"  Real Watts: {standard_result['insights']['real_watts']:.0f}W")
print(f"  Efficiency: {standard_result['insights']['efficiency_score']}")

print("\n" + "=" * 80)
print(
    f"Difference: {standard_result['prediction'] - bldc_result['prediction']:.2f} kWh"
)
print(
    f"BLDC saves: {((standard_result['prediction'] - bldc_result['prediction']) / standard_result['prediction'] * 100):.1f}%"
)
print("=" * 80)
