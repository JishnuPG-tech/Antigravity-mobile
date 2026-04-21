import os
import sys

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kseb_tariff import calculate_kseb_tariff
from tariff_config import TELESCOPIC_SLABS

print(f"Loaded Config with {len(TELESCOPIC_SLABS)} telescopic slabs.")


def test(units, expected_approx):
    bill = calculate_kseb_tariff(units)
    print(f"Units: {units} => Bill: ₹{bill['total']:.2f} (Expected ~{expected_approx})")
    if (
        abs(bill["total"] - expected_approx) > 50
    ):  # Allow small variance for FSM/Fixed charges
        print("❌ CRITICAL: Bill deviation too high!")
    else:
        print("✅ PASS")


# Test Cases
print("\n--- Testing KSEB Logic ---")
print("Case 1: 240 Units Total (120/mo) - Telescopic")
test(120, 965.20)  # Verified Correct

print("Case 2: 600 Units Total (300/mo) - Non-Telescopic")
test(300, 3918.00)  # Verified Correct
