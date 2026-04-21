from typing import Any, Dict


class Learner:
    def __init__(self, learning_rate=0.05, max_bias_change=0.05):
        self.alpha = learning_rate
        self.limit = max_bias_change  # Max 5% change per step

    def calculate_updates(
        self,
        profile: Dict,
        predicted_total: float,
        actual_bill: float,
        confidence: float,
    ) -> Dict[str, Any]:
        """
        Core Learning Logic.
        Compare Prediction vs Bill.
        Return new parameters.
        confidence: 0-100
        """
        current_bias = profile.get("efficiency_bias", 1.0)

        # DYNAMIC LEARNING RATE
        # If High Confidence (>90%): Learn fast (we trust the data).
        # If Low Confidence (<70%): Learn slow (reduce noise).
        # Scale: 1.0 at 90%, 0.2 at 60%.

        confidence_factor = max(0.2, min(1.0, (confidence - 50) / 40))
        effective_alpha = self.alpha * confidence_factor

        # 1. Calculate Gap
        # Gap = Actual - Predicted
        gap = actual_bill - predicted_total

        updates = {}

        # 2. Safety Check: Is Gap reasonable?
        # If Gap is > 50% of bill, it might be a data entry error (e.g. 1500 instead of 150).
        # Ignore extreme outliers.
        if abs(gap) > (actual_bill * 0.6):
            return {}

        # 3. Allocation Strategy
        # We attribute 20% of the error to "Efficiency Bias" (Global Multiplier)
        # And 80% to "Background Load" (Constant Additive).

        # A. Efficiency Update
        # If predicted 100, actual 110. Gap +10.
        # We want predicted to rise.
        # Target change = 10 * 0.2 = 2 kWh.
        # Relative change = 2 / 100 = +2%.
        # New Bias = Old * (1 + 0.02 * Alpha).
        # Using simple EMA on the Bias Factor directly.

        # Determine direction
        direction = 1 if gap > 0 else -1

        # Update Bias
        # We nudge bias by LearningRate * Direction * Magnitude
        # But we Clamp magnitude.
        nudge = effective_alpha * (abs(gap) / max(1, predicted_total)) * direction
        nudge = max(-self.limit, min(self.limit, nudge))  # Clamp to +/- 5%

        new_bias = current_bias * (1 + nudge)

        # Hard Clamp on result (0.8 to 1.3) ~ +/- 20-30% global error correction limit
        new_bias = max(0.8, min(1.3, new_bias))

        updates["efficiency_bias"] = new_bias

        # B. Background Load Update
        # Remaining gap attributed here.
        # Ideally, we verify this against 'Unaccounted' logic.

        return updates
