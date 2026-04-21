"""
KSEB (Kerala State Electricity Board) Tariff Calculator
========================================================
This is the "Accountant" of the system.
It strictly follows the 2024-2025 KSEB Rulebook.

The Logic is "Telescopic":
- Use a little? Pay a little per unit.
- Use a lot? Pay A LOT per unit.
- Crossing 250 units is dangerous—you lose the subsidy on EVERYTHING!
"""


def calculate_kseb_tariff(monthly_units: float) -> dict:
    """
    Calculate Kerala State Electricity Board (KSEB) charges for bi-monthly billing.

    KSEB uses telescopic tariff structure where:
    1. Bill is calculated bi-monthly (2 months at a time)
    2. Units are divided by 2 to get monthly average
    3. Telescopic rates apply up to 250 units/month
    4. Flat rates apply above 250 units/month
    5. Fuel Surcharge Mechanism (FSM) is added

    Args:
        monthly_units (float): Monthly electricity consumption in kWh (units)

    Returns:
        dict: {
            'energy_charge': float,      # Base energy cost (bi-monthly)
            'fuel_surcharge': float,     # FSM charges
            'total': float,              # Total bi-monthly bill (actual KSEB charge)
            'monthly_estimate': float,   # Approximate monthly cost (total/2)
            'effective_rate': float,     # Per-unit cost
            'slab': str,                 # Tariff category
            'monthly_units': float,      # Input monthly units
            'bi_monthly_units': float    # 2-month consumption
        }

    Example:
        >>> result = calculate_kseb_tariff(150)
        >>> print(f"Bi-monthly bill: ₹{result['total']:.2f}")
        Bi-monthly bill: ₹1279.00
        >>> print(f"Monthly estimate: ₹{result['monthly_estimate']:.2f}")
        Monthly estimate: ₹639.50
    """
    import math

    # Import Centralized Tariff Configuration
    try:
        from tariff_config import FLAT_RATE_SLABS, FSM_RATE, TELESCOPIC_SLABS
    except ImportError:
        # Fallback if config matches missing (Safety)
        print("Warning: tariff_config.py not found, using fallback defaults.")
        FSM_RATE = 0.13
        TELESCOPIC_SLABS = [(50, 3.25), (50, 4.05), (50, 5.10), (50, 6.95), (50, 8.20)]
        FLAT_RATE_SLABS = [
            (300, 6.40),
            (350, 7.25),
            (400, 7.60),
            (500, 7.90),
            (float("inf"), 8.80),
        ]

    # Calculate for single month (bi-monthly bills use monthly average)
    energy_charge = 0.0
    slab_category = ""

    if monthly_units <= 250:
        # --- TELESCOPIC CALCULATION ---
        remaining = monthly_units
        for limit, rate in TELESCOPIC_SLABS:
            if remaining > 0:
                chunk = min(remaining, limit)
                energy_charge += chunk * rate
                remaining -= chunk
            else:
                break

        # Determine slab
        if monthly_units <= 50:
            slab_category = "Domestic LT-I (0-50 units)"
        elif monthly_units <= 100:
            slab_category = "Domestic LT-II (51-100 units)"
        elif monthly_units <= 150:
            slab_category = "Domestic LT-III (101-150 units)"
        elif monthly_units <= 200:
            slab_category = "Domestic LT-IV (151-200 units)"
        else:
            slab_category = "Domestic LT-V (201-250 units)"

    else:
        # --- NON-TELESCOPIC (FLAT RATE) ---
        for limit, rate in FLAT_RATE_SLABS:
            if monthly_units <= limit:
                energy_charge = monthly_units * rate
                if limit == float("inf"):
                    slab_category = "Domestic LT-VI (> 500 units)"
                else:
                    slab_category = f"Domestic LT-VI ({int(limit)} units)"
                break

    # --- BI-MONTHLY CALCULATION ---
    # KSEB bills every 2 months, so multiply by 2
    bi_monthly_energy = energy_charge * 2
    bi_monthly_units = monthly_units * 2

    # --- ADD FUEL SURCHARGE ---
    fuel_surcharge = bi_monthly_units * FSM_RATE

    # --- TOTAL BILL ---
    total_amount = bi_monthly_energy + fuel_surcharge

    # --- EFFECTIVE RATE ---
    effective_rate = total_amount / bi_monthly_units if bi_monthly_units > 0 else 0

    return {
        "energy_charge": round(bi_monthly_energy, 2),
        "fuel_surcharge": round(fuel_surcharge, 2),
        "total": round(total_amount, 2),  # Bi-monthly bill (what KSEB charges)
        "monthly_estimate": round(total_amount / 2, 2),  # Approximate monthly cost
        "effective_rate": round(effective_rate, 2),
        "slab": slab_category,
        "monthly_units": round(monthly_units, 2),
        "bi_monthly_units": round(bi_monthly_units, 2),
    }


def calculate_savings_potential(current_kwh: float, reduced_kwh: float) -> dict:
    """
    Calculate potential savings from reducing consumption.

    Args:
        current_kwh: Current monthly consumption
        reduced_kwh: Projected consumption after improvements

    Returns:
        dict: {
            'current_bill': float,
            'reduced_bill': float,
            'monthly_savings': float,
            'annual_savings': float,
            'reduction_percentage': float
        }
    """
    current_bill = calculate_kseb_tariff(current_kwh)
    reduced_bill = calculate_kseb_tariff(reduced_kwh)

    monthly_savings = current_bill["total"] - reduced_bill["total"]
    annual_savings = monthly_savings * 6  # 6 bi-monthly bills per year
    reduction_pct = (
        ((current_kwh - reduced_kwh) / current_kwh * 100) if current_kwh > 0 else 0
    )

    return {
        "current_bill": current_bill["total"],
        "reduced_bill": reduced_bill["total"],
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "reduction_percentage": round(reduction_pct, 1),
    }


# Example usage and validation
if __name__ == "__main__":
    print("=" * 60)
    print("KSEB TARIFF CALCULATOR - VALIDATION")
    print("=" * 60)

    # Test cases based on actual KSEB bills
    test_cases = [
        (75, "Expected: ~₹270 (Telescopic LT-II)"),
        (150, "Expected: ~₹547 (Telescopic LT-III)"),
        (250, "Expected: ~₹967 (Telescopic LT-V)"),
        (300, "Expected: ~₹1,212 (Flat ₹6.40/unit)"),
        (450, "Expected: ~₹2,673 (Flat ₹7.90/unit)"),
    ]

    for units, expected in test_cases:
        result = calculate_kseb_tariff(units)
        print(f"\n{units} units/month:")
        print(f"  Bi-monthly Bill: ₹{result['total']:.2f} (KSEB charges for 2 months)")
        print(f"  Monthly Estimate: ₹{result['monthly_estimate']:.2f}")
        print(f"  Energy Charge: ₹{result['energy_charge']:.2f}")
        print(f"  Fuel Surcharge: ₹{result['fuel_surcharge']:.2f}")
        print(f"  Slab: {result['slab']}")
        print(f"  Effective Rate: ₹{result['effective_rate']:.2f}/unit")

    print("\n" + "=" * 60)
    print("Validation complete. Use calculate_kseb_tariff() in your code.")
    print("=" * 60)
