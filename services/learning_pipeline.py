"""
Learning Pipeline Service
Fires ONCE after totals are computed - real AI-inferred physics learning.
"""

from typing import Any, Dict

from services.bias_adjuster import BiasAdjuster


class LearningPipeline:
    """Handles self-learning from prediction gaps"""

    # Learning configuration
    LEARNING_RATE = 0.1  # 10% adjustment per iteration
    MIN_BIAS = 0.5  # Don't go below 50% efficiency
    MAX_BIAS = 1.5  # Don't go above 150% efficiency
    GAP_THRESHOLD = 5.0  # Only learn if gap > 5 kWh

    @classmethod
    def learn_from_gap(
        cls,
        user_id: str,
        actual_kwh: float,
        predicted_total: float,
        current_bias: float,
    ) -> Dict[str, Any]:
        """
        Learning fires ONCE after full batch prediction.

        This is real AI-inferred physics learning.

        Args:
            user_id: User identifier
            actual_kwh: Actual monthly consumption
            predicted_total: Sum of all predicted kWh
            current_bias: Current efficiency bias

        Returns:
            Learning result dict with new bias and metadata
        """
        # Calculate prediction gap
        gap = actual_kwh - predicted_total
        gap_percentage = (gap / actual_kwh * 100) if actual_kwh > 0 else 0

        # Check if learning needed
        if abs(gap) < cls.GAP_THRESHOLD:
            return {
                "learning_applied": False,
                "reason": f"Gap too small ({gap:.2f} kWh < {cls.GAP_THRESHOLD} threshold)",
                "current_bias": current_bias,
                "new_bias": current_bias,
                "gap_kwh": gap,
                "gap_percentage": gap_percentage,
            }

        # Calculate new bias using gradient descent approach
        # If gap > 0: under-predicting, increase bias
        # If gap < 0: over-predicting, decrease bias
        adjustment = (gap / actual_kwh) * cls.LEARNING_RATE
        new_bias = current_bias + adjustment

        # Apply safety bounds
        new_bias = max(cls.MIN_BIAS, min(new_bias, cls.MAX_BIAS))

        # Save updated bias
        BiasAdjuster.save_user_bias(user_id, new_bias)

        return {
            "learning_applied": True,
            "reason": f"Gap {gap:.2f} kWh ({gap_percentage:.1f}%) exceeds threshold",
            "current_bias": current_bias,
            "new_bias": new_bias,
            "gap_kwh": gap,
            "gap_percentage": gap_percentage,
            "adjustment": adjustment,
        }

    @classmethod
    def should_trigger_learning(cls, actual_kwh: float) -> bool:
        """Check if we have enough data to trigger learning"""
        return actual_kwh > 0
