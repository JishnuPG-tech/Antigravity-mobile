import json
import os
import sys

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictor import AppliancePredictor


def run_regression():
    print("=" * 60)
    print("WARNING: Regression Test Started")
    print("=" * 60)

    # Load Baseline
    baseline_path = os.path.join(os.path.dirname(__file__), "regression_baseline.json")
    if not os.path.exists(baseline_path):
        print("❌ Baseline file not found!")
        sys.exit(1)

    with open(baseline_path, "r") as f:
        baseline = json.load(f)

    # Initialize Predictor
    predictor = AppliancePredictor(models_dir="models")

    # Map friendly names to predictor methods (simplified map)
    method_map = {
        "ac": predictor.predict_ac,
        "fridge": predictor.predict_fridge,
        "ceiling_fan": predictor.predict_ceiling_fan,
    }

    passed = 0
    failed = 0

    print(
        f"{'ID':<20} | {'Appliance':<12} | {'Prediction':<10} | {'Expected':<12} | {'Status':<10}"
    )
    print("-" * 80)

    for case in baseline:
        app_name = case["appliance"]
        if app_name not in method_map:
            print(f"⚠️ Skipper: {case['id']} (No method mapped)")
            continue

        try:
            # Run Prediction
            func = method_map[app_name]
            res = func(case["input"], case["bill"])
            val = res["prediction"]

            # Check Range
            min_exp, max_exp = case["expected_range"]

            status = "✅ PASS"
            if val < min_exp or val > max_exp:
                status = "❌ FAIL"
                failed += 1
            else:
                passed += 1

            print(
                f"{case['id']:<20} | {app_name:<12} | {val:<10.2f} | {min_exp}-{max_exp:<12} | {status}"
            )

        except Exception as e:
            print(
                f"{case['id']:<20} | {app_name:<12} | {'ERROR':<10} | {'-':<12} | ❌ {str(e)}"
            )
            failed += 1

    print("-" * 80)
    print(f"SUMMARY: Passed: {passed} | Failed: {failed} | Total: {passed + failed}")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_regression()
