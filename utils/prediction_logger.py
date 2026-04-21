"""
Prediction Logger Utility
Clean, professional, exam-defensible logging format.
"""

from typing import Any, Dict, List


class PredictionLogger:
    """Professional logging for batch predictions"""

    @staticmethod
    def log_header(user_context: Dict[str, Any], num_appliances: int):
        """Log batch prediction header"""
        print("=" * 60)
        print("BATCH PREDICTION REQUEST")
        print(f"Appliances: {num_appliances}")
        print("=" * 60)
        print()
        print("User Context:")
        print(f"- Monthly kWh: {user_context.get('total_kwh_monthly', 0)}")
        print(f"- Occupants: {user_context.get('n_occupants', 3)}")
        print(f"- Season: {user_context.get('season', 'monsoon')}")
        print(f"- Location: {user_context.get('location_type', 'urban')}")
        print()

    @staticmethod
    def log_results(results: List[Dict[str, Any]], system_load: float = 0):
        """
        Log predictions in clean tabular format.

        Example output:
        ----------------------------------------
        Appliance Predictions
        ----------------------------------------
        AC              : 10.48 kWh (User Hours)
        Refrigerator    : 44.65 kWh (Inferred Physics)
        ...
        """
        print("-" * 60)
        print("Appliance Predictions")
        print("-" * 60)

        # Sort by consumption (highest first)
        sorted_results = sorted(results, key=lambda x: x["kwh"], reverse=True)

        for r in sorted_results:
            appliance = r["appliance"].replace("_", " ").title()
            kwh = r["kwh"]
            source = r.get("source", "Physics")

            # Format: "Appliance Name  : XX.XX kWh (Source)"
            print(f"{appliance:20}: {kwh:6.2f} kWh ({source})")

        if system_load > 0:
            print()
            print("-" * 60)
            print(f"System & Unaccounted Load: {system_load:.2f} kWh")

    @staticmethod
    def log_footer(
        total_kwh: float, bias_applied: float = None, learning_result: Dict = None
    ):
        """Log summary footer"""
        print("-" * 60)
        print()
        print(f"TOTAL: {total_kwh:.2f} kWh")

        if bias_applied and bias_applied != 1.0:
            print(f"🧠 Efficiency Bias Applied: {bias_applied:.2f}x")

        if learning_result and learning_result.get("learning_applied"):
            print(
                f"📚 Learning: Bias updated {learning_result['current_bias']:.2f} → {learning_result['new_bias']:.2f}"
            )
            print(
                f"   Gap: {learning_result['gap_kwh']:.2f} kWh ({learning_result['gap_percentage']:.1f}%)"
            )

        print("=" * 60)
        print()

    @staticmethod
    def log_compact_summary(
        user_context: Dict,
        num_appliances: int,
        results: List[Dict],
        system_load: float,
        total_kwh: float,
        bias_applied: float = None,
    ):
        """All-in-one compact logging"""
        PredictionLogger.log_header(user_context, num_appliances)
        PredictionLogger.log_results(results, system_load)
        PredictionLogger.log_footer(total_kwh, bias_applied)
