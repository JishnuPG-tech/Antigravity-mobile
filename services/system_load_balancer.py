"""
System Load Balancer Service
Caps system load at realistic levels and redistributes excess proportionally.
"""

from typing import Any, Dict, List


class SystemLoadBalancer:
    """Handles realistic system load calculation and excess redistribution"""

    # Configuration
    MAX_SYSTEM_LOAD_PERCENTAGE = 0.15  # 15% maximum for believability
    MIN_SYSTEM_LOAD_PERCENTAGE = 0.05  # 5% minimum (standby devices exist)

    # Redistribution weights (which appliances get excess)
    REDISTRIBUTION_WEIGHTS = {
        "fridge": 0.35,  # Fridge runs 24/7, gets most excess
        "ceiling_fan": 0.30,  # Fans often underestimated
        "led_light": 0.20,  # Lights usage varies
        "ac": 0.10,  # AC gets some
        "television": 0.05,  # TV gets minimal
    }

    @classmethod
    def calculate_balanced_load(
        cls,
        actual_kwh: float,
        predicted_total: float,
        results_list: List[Dict[str, Any]],
    ) -> tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Calculate system load with realistic cap and redistribute excess.

        Args:
            actual_kwh: Actual monthly consumption
            predicted_total: Sum of all predicted appliances
            results_list: List of prediction results

        Returns:
            (system_load, adjusted_results, balancing_info)
        """
        # Calculate raw system load
        raw_system_load = max(0, actual_kwh - predicted_total)
        raw_percentage = (raw_system_load / actual_kwh * 100) if actual_kwh > 0 else 0

        # Cap system load at maximum realistic level
        max_allowed_load = actual_kwh * cls.MAX_SYSTEM_LOAD_PERCENTAGE
        system_load = min(raw_system_load, max_allowed_load)

        # Calculate excess that needs redistribution
        excess_kwh = raw_system_load - system_load

        balancing_info = {
            "raw_system_load": raw_system_load,
            "raw_percentage": raw_percentage,
            "capped_system_load": system_load,
            "capped_percentage": (
                (system_load / actual_kwh * 100) if actual_kwh > 0 else 0
            ),
            "excess_redistributed": excess_kwh,
            "redistribution_applied": excess_kwh > 0,
        }

        # If no excess, return as-is
        if excess_kwh <= 0:
            return system_load, results_list, balancing_info

        # Redistribute excess proportionally to key appliances
        redistributed_results = []
        redistribution_details = {}

        for r in results_list:
            appliance = r["appliance"]
            original_kwh = r["kwh"]

            # Calculate redistribution amount based on weights
            weight = cls.REDISTRIBUTION_WEIGHTS.get(appliance, 0)
            redistribution_amount = excess_kwh * weight

            # Add to appliance consumption
            new_kwh = original_kwh + redistribution_amount

            redistributed_results.append(
                {
                    **r,
                    "kwh": new_kwh,
                    "original_kwh": original_kwh,
                    "redistributed_kwh": redistribution_amount,
                }
            )

            if redistribution_amount > 0:
                redistribution_details[appliance] = redistribution_amount

        balancing_info["redistribution_details"] = redistribution_details

        return system_load, redistributed_results, balancing_info

    @classmethod
    def get_system_load_explanation(
        cls, percentage: float, location_type: str = "urban"
    ) -> str:
        """Get human-readable explanation for system load"""
        if percentage < 5:
            return "Very low system load - excellent appliance coverage"
        elif percentage <= 10:
            if location_type == "rural":
                return "Normal background consumption (standby devices, voltage fluctuations)"
            else:
                return (
                    "Normal background consumption (chargers, routers, standby devices)"
                )
        elif percentage <= 15:
            if location_type == "rural":
                return "Typical rural system load (pump losses, voltage fluctuation, standby devices)"
            else:
                return "Typical urban system load (inverter, CCTV, unmodeled devices)"
        else:
            # Shouldn't happen after capping, but just in case
            return f"High system load ({percentage:.1f}%) - indicates unmodeled devices or measurement variance"
