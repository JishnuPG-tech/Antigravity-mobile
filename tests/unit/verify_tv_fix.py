import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from predictor import get_predictor
from routers.appliances import map_schema_to_training_columns


def test_tv_prediction():
    print("Testing TV Prediction with Mapping...")

    predictor = get_predictor()

    input_details = {
        "total_kwh_monthly": 150,
        "n_occupants": 3,
        "season": "monsoon",
        "location_type": "rural",
        "television_hours": 2,
        "television_usage_pattern": "light",
        "tv_size_inches": 43,
        "num_televisions": 1,
        "television_type": "LED",
    }

    print(f"Input Details: {input_details}")

    mapped_data = map_schema_to_training_columns(input_details)
    print(f"Mapped Data: {mapped_data}")

    if "tv_hours" in mapped_data:
        print("✅ 'tv_hours' found in mapped data.")
        print(f"   Value: {mapped_data['tv_hours']}")
    else:
        print("❌ 'tv_hours' MISSING in mapped data!")

    result = predictor.predict("television", [mapped_data])

    with open("test_result.txt", "w") as f:
        f.write("\n--- Prediction Results ---\n")
        f.write(f"Prediction: {result['prediction']} kWh\n")
        f.write(f"Efficiency Score: {result['insights']['efficiency_score']}\n")
        f.write(f"Predicted Hours: {result['insights']['predicted_hours']}\n")
        f.write(f"Source: {result['insights']['source']}\n")
        f.write(f"Anomaly: {result['insights']['anomaly']}\n")

        if result["insights"]["anomaly"]["status"] == "Normal":
            f.write("\n✅ TEST PASSED: No Critical Fault.\n")
        else:
            f.write(f"\n❌ TEST FAILED: {result['insights']['anomaly']['message']}\n")

    print("Test complete. Check test_result.txt")


if __name__ == "__main__":
    test_tv_prediction()
