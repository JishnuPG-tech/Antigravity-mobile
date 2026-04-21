import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import  PREDICTOR
from predictor import get_predictor


def run_verification():
    print("🚀 STARTING COMPREHENSIVE HYBRID LOGIC VERIFICATION ( ENGINE) 🚀")
    print("=" * 60)

    predictor = get_predictor()
    predictor.preload_all_models()

    # Context Variable (The User's Total Bill)
    LOW_BILL = 150  # kWh
    HIGH_BILL = 800  # kWh

    # Helper to format input
    def prep(details, bill):
        d = details.copy()
        d["total_kwh_monthly"] = bill
        return [d]

    # ---------------------------------------------------------
    # 1. FRIDGE VERIFICATION (Testing Manual Logic fix)
    # ---------------------------------------------------------
    print("\n🥶 1. REFRIGERATOR TEST (Testing Manual Logic fix)")
    print("-" * 50)

    # Case A: Unknown / Default (AI)
    fridge_default = {
        "fridge_capacity": 250,
        "fridge_star": 3,
        # No hours/pattern provided
    }
    pred_def = predictor.predict("fridge", prep(fridge_default, LOW_BILL))["prediction"]

    # Case B: Manual Pattern (12 Hours) (AI - Mixed)
    fridge_manual = {
        "fridge_capacity": 250,
        "fridge_star": 3,
        "fridge_hours_per_day": 12,
    }
    pred_manual = predictor.predict("fridge", prep(fridge_manual, LOW_BILL))[
        "prediction"
    ]

    # Case C: Physics Exact (12 Hours)
    # 250L 3-Star approx 40W active.
    physics_exact = (40 * 12 * 30) / 1000

    print(f"   • Scenario: Bill {LOW_BILL} kWh")
    print(f"   • [AI Default] (24h assumed):        {pred_def:.2f} kWh")
    print(f"   • [AI Manual]  (12h pattern input):  {pred_manual:.2f} kWh")
    print(f"   • [Physics]    (12h calculation):    {physics_exact:.2f} kWh")

    # ---------------------------------------------------------
    # 2. AC VERIFICATION (Testing Pattern & Bill Context)
    # ---------------------------------------------------------
    print("\n❄️ 2. AC TEST (Testing Context Awareness)")
    print("-" * 50)

    ac_inputs = {
        "ac_tonnage": 1.5,
        "ac_star_rating": 3,  #  uses 'ac_star_rating' key
        "ac_usage_pattern": "moderate",  # Default
    }

    # High Bill Context
    pred_ac_high = predictor.predict("ac", prep(ac_inputs, HIGH_BILL))["prediction"]
    # Low Bill Context
    pred_ac_low = predictor.predict("ac", prep(ac_inputs, LOW_BILL))["prediction"]

    print(f"   • Input: 1.5 Ton, 3 Star, Moderate Pattern")
    print(f"   • [AI High Bill Context]: {pred_ac_high:.2f} kWh")
    print(f"   • [AI Low Bill Context]:  {pred_ac_low:.2f} kWh")

    # ---------------------------------------------------------
    # 3. WASHING MACHINE (Testing Cycles Fix)
    # ---------------------------------------------------------
    print("\n🧺 3. WASHING MACHINE TEST (Testing Cycles Fix)")
    print("-" * 50)

    wm_default = {"wm_capacity": 7.0, "wm_cycles_per_week": 4}  # Standard
    wm_high = {"wm_capacity": 7.0, "wm_cycles_per_week": 10}  # User specific

    pred_wm_def = predictor.predict("washing_machine", prep(wm_default, LOW_BILL))[
        "prediction"
    ]
    pred_wm_high = predictor.predict("washing_machine", prep(wm_high, LOW_BILL))[
        "prediction"
    ]

    print(f"   • [AI Default] (4 cycles): {pred_wm_def:.2f} kWh")
    print(f"   • [AI High]    (10 cycles):{pred_wm_high:.2f} kWh")

    # ---------------------------------------------------------
    # 4. LIGHTING (Testing Key Fix / Hybrid Enforcement)
    # ---------------------------------------------------------
    print("\n💡 4. LIGHTING TEST (Testing Hybrid Enforcement)")
    print("-" * 50)

    led_default = {"num_led": 10, "led_light_hours_per_day": 6}
    #  expects 'led_lights_hours_per_day' or matches 'led_light' key from frontend?
    # Predictor  logic uses `f'{name}_hours_per_day` fallback if AI fails, but AI uses features.
    # We should ensure input keys match training or are mapped.
    # Let's pass 'led_light_hours_per_day' and check.

    try:
        pred_led = predictor.predict("led_light", prep(led_default, LOW_BILL))[
            "prediction"
        ]
        print(f"   • [AI Prediction]: {pred_led:.2f} kWh")
    except Exception as e:
        print(f"   • [ERROR]: {e}")

    print("=" * 60)
    print("✅ VERIFICATION COMPLETE")


if __name__ == "__main__":
    run_verification()
