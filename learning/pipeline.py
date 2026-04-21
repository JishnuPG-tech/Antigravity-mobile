import logging

from .core import Learner
from .memory import HouseholdMemory

logger = logging.getLogger("LearningPipeline")


class LearningPipeline:
    def __init__(self):
        self.memory = HouseholdMemory()
        self.learner = Learner()

    def get_context_bias(self, context: dict) -> float:
        """
        Called BEFORE prediction.
        Returns the efficiency multiplier to apply (e.g., 1.05).
        """
        pid = self.memory.get_profile_hash(context)
        profile = self.memory.get_profile(pid)
        return profile.get("efficiency_bias", 1.0)

    def learn(
        self,
        context: dict,
        predicted_total: float,
        actual_bill: float,
        confidence: float = 80.0,
    ):
        """
        Called AFTER prediction.
        Updates the profile based on the gap.
        Args:
            confidence: 0-100 score indicating how sure the AI was about the breakdown.
        """
        pid = self.memory.get_profile_hash(context)
        profile = self.memory.get_profile(pid)

        updates = self.learner.calculate_updates(
            profile, predicted_total, actual_bill, confidence
        )

        if updates:
            # Update sample count
            updates["sample_count"] = profile.get("sample_count", 0) + 1

            logger.info(
                f"LEARNING [{pid}]: Gap={actual_bill - predicted_total:.1f}. "
                f"Bias {profile.get('efficiency_bias', 1.0):.3f} -> {updates.get('efficiency_bias'):.3f}"
            )

            self.memory.update_profile(pid, updates)


# Singleton
pipeline = LearningPipeline()


def get_pipeline():
    return pipeline
