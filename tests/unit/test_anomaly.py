import os
import sys

# Add parent dir to path to import backend modules (3 levels up)
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from anomaly_engine import AnomalyEngine
from predictor import get_predictor


def test_anomaly_detection():
    print("🚨 TESTING ANOMALY DETECTION LOGIC (RETRY) 🚨")
    predictor = get_predictor()
    predictor.preload_all_models()

    def prep(d):
        d["total_kwh_monthly"] = 500
        return [d]

    # 1. TEST USAGE ANOMALIES (Behavior)
    print("\n[TestCase 1] Geyser Running 4 Hours (Critical > 3h)")
    # CORRECT INPUT KEY: 'geyser_hours_per_day'
    res = predictor.predict("geyser", prep({"geyser_hours_per_day": 4.0}))

    anom = res["insights"]["anomaly"]
    print(f"   Output Status: {anom['status']}")
    print(f"   Output Message: {anom['message']}")

    if anom["status"] == "Usage_Anomaly" and "Geyser running > 3h" in anom["message"]:
        print("   ✅ PASS")
    else:
        print("   ❌ FAIL (Val: " + str(res["insights"]["predicted_hours"]) + ")")

    # 2. TEST NORMAL CASE
    print("\n[TestCase 2] Geyser Normal (1 Hour)")
    res = predictor.predict("geyser", prep({"geyser_hours_per_day": 1.0}))
    anom = res["insights"]["anomaly"]
    print(f"   Output Status: {anom['status']}")

    if anom["status"] == "Normal":
        print("   ✅ PASS")
    else:
        print("   ❌ FAIL")

    # 3. TEST EFFICIENCY ANOMALIES (Health)
    print("\n[TestCase 3] Direct Method Check (Health Critical)")
    chk = AnomalyEngine.check_anomalies("ac", 1.3, 8.0)
    print(f"   Input: Eff=1.3. Output: {chk['status']}")

    if chk["status"] == "efficiency_critical":
        print("   ✅ PASS")
    else:
        print("   ❌ FAIL")


if __name__ == "__main__":
    test_anomaly_detection()
