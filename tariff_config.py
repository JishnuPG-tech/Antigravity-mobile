"""
KSEB Tariff Configuration (2024-25)
===================================
Centralized configuration for KSEB Basic Tariff rates.
Update this file when rate changes occur.
Methods: Telescopic (<= 250 units) and Non-Telescopic (> 250 units).
"""

# --- TELESCOPIC SLAB RATES ---
# Applied when monthly average consumption is <= 250 units
# Format: (Limit, Rate_Per_Unit)
TELESCOPIC_SLABS = [
    (50, 3.25),  # First 50 units: ₹3.25/unit
    (50, 4.05),  # Next 50 (51-100): ₹4.05/unit
    (50, 5.10),  # Next 50 (101-150): ₹5.10/unit
    (50, 6.95),  # Next 50 (151-200): ₹6.95/unit
    (50, 8.20),  # Next 50 (201-250): ₹8.20/unit
]

# --- NON-TELESCOPIC FLAT RATES ---
# Applied when monthly average consumption is > 250 units
# Format: (Limit, Rate_Per_Unit)
FLAT_RATE_SLABS = [
    (
        300,
        6.40,
    ),  # 0-300 units: ₹6.40/unit (applied to ENTIRE consumption if applicable logic, but usually tiered in non-telescopic too?
    # KSEB Non-telescopic usually means:
    # 0-300 @ 6.40
    # 0-350 @ 7.25 (Total volume driven)
    # Notes: The previous implementation treated these as "SLABS" but the logic iteration suggests they might be "Block Slab" or "Flat Rate".
    # Re-checking logic in kseb_tariff.py:
    # It iterates `FLAT_RATE_SLABS`.
    # If logic is: for limit, rate in slabs: check if total <= limit return total * rate?
    # No, `kseb_tariff.py` (line 100+) implements a specific logic.
    # Let's preserve the existing data structure exactly as found in kseb_tariff.py used by the logic.
    (300, 6.40),  # Up to 300
    (350, 7.25),  # Up to 350
    (400, 7.60),  # Up to 400
    (500, 7.90),  # Up to 500
    (float("inf"), 8.80),  # Above 500
]

# --- FUEL SURCHARGE MECHANISM (FSM) ---
# Floating rate adjusted quarterly
FSM_RATE = 0.13
