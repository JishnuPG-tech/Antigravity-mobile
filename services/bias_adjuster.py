"""
Bias Adjuster Service
Applies efficiency bias ONCE after all predictions complete.
"""

import json
import os
from typing import Any, Dict, List


class BiasAdjuster:
    """Applies user-specific efficiency bias to predictions"""

    BIAS_FILE = "user_biases.json"

    @classmethod
    def load_user_bias(cls, user_id: str) -> float:
        """Load user's efficiency bias (default 1.0)"""
        if not os.path.exists(cls.BIAS_FILE):
            return 1.0

        try:
            with open(cls.BIAS_FILE, "r") as f:
                biases = json.load(f)
                return biases.get(user_id, 1.0)
        except:
            return 1.0

    @classmethod
    def save_user_bias(cls, user_id: str, bias: float):
        """Save updated bias to file"""
        biases = {}

        if os.path.exists(cls.BIAS_FILE):
            try:
                with open(cls.BIAS_FILE, "r") as f:
                    biases = json.load(f)
            except:
                pass

        biases[user_id] = bias

        with open(cls.BIAS_FILE, "w") as f:
            json.dump(biases, f, indent=2)

    @classmethod
    def apply_bias_to_results(
        cls, results: List[Dict[str, Any]], user_id: str
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Apply efficiency bias ONCE to all results.

        ✔ Predict first
        ✔ Adjust once
        ✔ Then move on

        Args:
            results: List of prediction results
            user_id: User identifier

        Returns:
            (adjusted_results, bias_applied)
        """
        # Load bias ONCE
        efficiency_bias = cls.load_user_bias(user_id)

        # Apply to all results
        for r in results:
            r["kwh"] *= efficiency_bias
            r["bias_applied"] = efficiency_bias

        return results, efficiency_bias
