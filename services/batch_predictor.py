"""
Batch Predictor Service
Single prediction loop for all appliances - no spam, no redundancy.
"""

from typing import Any, Dict, List

import pandas as pd


class BatchPredictor:
    """Handles batch prediction for multiple appliances in ONE loop"""

    def __init__(self, predictor_instance):
        """
        Args:
            predictor_instance: The AppliancePredictor from predictor.py
        """
        self.predictor = predictor_instance

    def predict_batch(
        self, user_context: Dict[str, Any], appliance_inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ONE loop, all predictions.

        ⚠️ No API calls inside loop
        ⚠️ No learning inside loop
        ⚠️ No logging spam

        Args:
            user_context: Shared household context
            appliance_inputs: Dict of {appliance_name: inputs}

        Returns:
            List of prediction results
        """
        results = []

        for appliance_name, inputs in appliance_inputs.items():
            # Merge context with appliance-specific inputs
            combined_data = {**user_context, **inputs}

            # Single prediction call
            result = self.predictor.predict(name=appliance_name, data=[combined_data])

            # Structure result
            results.append(
                {
                    "appliance": appliance_name,
                    "kwh": result.get("prediction", 0),
                    "insights": result.get("insights", {}),
                    "source": result.get("insights", {}).get("source", "unknown"),
                }
            )

        return results

    def calculate_total_kwh(self, results: List[Dict[str, Any]]) -> float:
        """Calculate total predicted consumption"""
        return sum(r["kwh"] for r in results)

    def group_by_source(self, results: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group appliances by prediction source (User Hours vs Inferred Physics)"""
        grouped = {"User Hours": [], "Inferred Physics": [], "Physics": []}

        for r in results:
            source = r.get("source", "Physics")
            if source in grouped:
                grouped[source].append(r)
            else:
                grouped["Physics"].append(r)

        return grouped
