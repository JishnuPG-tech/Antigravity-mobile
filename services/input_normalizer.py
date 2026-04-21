"""
Input Normalizer Service
Extracts and normalizes user context and appliance inputs ONCE per request.
"""

from typing import Any, Dict, List


class InputNormalizer:
    """Normalizes batch prediction inputs into clean structure"""

    @staticmethod
    def normalize_batch_request(batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts user context once and builds appliance inputs dict.

        Args:
            batch_data: Raw request data from API

        Returns:
            {
                "user_context": {...},
                "appliance_inputs": {...}
            }
        """
        # Extract common user context ONCE
        user_context = {
            "total_kwh_monthly": batch_data.get("total_kwh_monthly", 0),
            "n_occupants": batch_data.get("n_occupants", 3),
            "season": batch_data.get("season", "monsoon"),
            "location_type": batch_data.get("location_type", "urban"),
            "house_type": batch_data.get("house_type", "apartment"),
        }

        # Build appliance-specific inputs dict
        appliance_inputs = {}
        requests = batch_data.get("requests", [])

        for req in requests:
            appliance_name = req.get("appliance_name")
            details = req.get("details", {})

            # Store appliance-specific params
            appliance_inputs[appliance_name] = {
                **details,  # All appliance-specific fields
                "_user_context": user_context,  # Reference to shared context
            }

        return {"user_context": user_context, "appliance_inputs": appliance_inputs}

    @staticmethod
    def extract_household_features(user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract household-level features for AI models"""
        return {
            "num_people": user_context.get("n_occupants", 3),
            "season": user_context.get("season", "monsoon"),
            "location_type": user_context.get("location_type", "urban"),
            "house_type": user_context.get("house_type", "apartment"),
            "total_monthly_kwh": user_context.get("total_kwh_monthly", 0),
        }
