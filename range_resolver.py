"""
AI-Based Dynamic Range Resolver
Intelligently selects specific values within ranges based on user context
Instead of fixed averages, uses predictive logic to choose optimal values
"""

from typing import Dict, Optional, Tuple

import numpy as np


class RangeResolver:
    """
    Resolves range-based values (e.g., "3-5" years) to specific values
    based on contextual factors like usage patterns, location, season, etc.
    """

    @staticmethod
    def parse_range(value: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse range strings into (min, max) tuples
        Examples:
            "3-5" → (3.0, 5.0)
            "10+" → (10.0, None)
            "<1" → (None, 1.0)
            "5" → (5.0, 5.0)
        """
        value = str(value).strip()

        # Handle ranges: "3-5"
        if "-" in value and not value.startswith("<"):
            parts = value.split("-")
            try:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return (min_val, max_val)
            except:
                return (None, None)

        # Handle "10+" format
        elif "+" in value:
            try:
                base = float(value.replace("+", "").strip())
                return (base, None)  # Open-ended range
            except:
                return (None, None)

        # Handle "<1" format
        elif "<" in value:
            try:
                max_val = float(value.replace("<", "").strip())
                return (None, max_val)
            except:
                return (None, None)

        # Single value
        else:
            try:
                val = float(value)
                return (val, val)
            except:
                return (None, None)

    @staticmethod
    def resolve_geyser_age(age_str: str, context: Dict) -> float:
        """Dynamically resolve water heater/geyser age"""
        min_age, max_age = RangeResolver.parse_range(age_str)

        if min_age is None and max_age is None:
            return 3.0
        if min_age is not None and max_age is not None and min_age == max_age:
            return min_age
        if max_age is None:
            return min_age + 2.0
        if min_age is None:
            return max_age * 0.5

        bias_score = 0.5

        # Usage pattern (40% weight)
        usage_pattern = context.get("geyser_usage_pattern", "light")
        usage_weight = {"minimal": 0.2, "light": 0.4, "moderate": 0.6, "heavy": 0.8}
        bias_score += (usage_weight.get(usage_pattern, 0.5) - 0.5) * 0.4

        # Season (25% weight)
        season = context.get("season", "monsoon")
        if season == "winter":
            bias_score += 0.15  # More usage in winter
        elif season == "summer":
            bias_score -= 0.1  # Less usage in summer

        # Occupants (20% weight)
        occupants = context.get("n_occupants", 4)
        if occupants >= 6:
            bias_score += 0.1
        elif occupants <= 2:
            bias_score -= 0.05

        # Type (15% weight)
        geyser_type = context.get("water_heater_type", "storage")
        if geyser_type == "instant":
            bias_score += 0.05  # More complex, more wear

        bias_score = max(0.0, min(1.0, bias_score))
        resolved_age = min_age + (max_age - min_age) * bias_score

        logger.info(
            f"🧠 AI Range Resolver (geyser_age): '{age_str}' → {resolved_age:.2f} years (bias: {bias_score:.2f})"
        )
        return round(resolved_age, 2)

    @staticmethod
    def resolve_fridge_age(age_str: str, context: Dict) -> float:
        """
        Dynamically resolve fridge age based on usage context

        Logic:
        - Heavy usage + urban + summer → closer to max (more wear)
        - Light usage + rural + winter → closer to min (less wear)
        - Consider occupants (more people = more wear)
        """
        min_age, max_age = RangeResolver.parse_range(age_str)

        # Handle edge cases
        if min_age is None and max_age is None:
            return 3.0  # Default fallback

        if min_age is not None and max_age is not None and min_age == max_age:
            return min_age  # Single value, no range

        # Handle open-ended ranges
        if max_age is None:  # "10+"
            return min_age + 2.0  # Default: 10+ → 12

        if min_age is None:  # "<1"
            return max_age * 0.5  # Default: <1 → 0.5

        # Calculate bias factors (0.0 to 1.0, where 1.0 = max wear)
        bias_score = 0.5  # Start neutral

        # Factor 1: Usage pattern (30% weight)
        usage_pattern = context.get("refrigerator_usage_pattern", "normal")
        usage_weight = {
            "manual": 0.2,  # Low wear (not always on)
            "light": 0.35,  # Below average
            "normal": 0.5,  # Average
            "always": 0.8,  # High wear (always running)
        }
        bias_score += (usage_weight.get(usage_pattern, 0.5) - 0.5) * 0.3

        # Factor 2: Location (20% weight)
        location = context.get("location_type", "urban")
        if location == "urban":
            bias_score += 0.1  # Urban = more power fluctuations, more wear
        else:
            bias_score -= 0.05  # Rural = more stable, less wear

        # Factor 3: Season (20% weight)
        season = context.get("season", "monsoon")
        season_weight = {
            "summer": 0.15,  # High wear (compressor works harder)
            "monsoon": 0.0,  # Neutral
            "winter": -0.1,  # Low wear (easier cooling)
        }
        bias_score += season_weight.get(season, 0.0)

        # Factor 4: Occupants (15% weight)
        occupants = context.get("n_occupants", 4)
        if occupants >= 6:
            bias_score += 0.1  # More people = more door openings
        elif occupants <= 2:
            bias_score -= 0.05  # Fewer people = less usage

        # Factor 5: Fridge type (15% weight)
        fridge_type = context.get("fridge_type", "frost_free")
        if fridge_type == "frost_free":
            bias_score += 0.05  # More complex, more wear
        elif fridge_type == "direct_cool":
            bias_score -= 0.05  # Simpler, less wear

        # Clamp bias score to [0.0, 1.0]
        bias_score = max(0.0, min(1.0, bias_score))

        # Calculate final age using bias
        # bias=0.0 → min_age, bias=1.0 → max_age, bias=0.5 → average
        resolved_age = min_age + (max_age - min_age) * bias_score

        # Log for debugging
        logger.info(
            f"🧠 AI Range Resolver: '{age_str}' → {resolved_age:.2f} years (bias: {bias_score:.2f})"
        )

        return round(resolved_age, 2)

    @staticmethod
    def resolve_generic_range(value_str: str, field_name: str, context: Dict) -> float:
        """
        Generic range resolver for any numeric field
        Uses simpler heuristics when specific logic not available
        """
        min_val, max_val = RangeResolver.parse_range(value_str)

        # Handle edge cases
        if min_val is None and max_val is None:
            return 0.0  # Default fallback

        if min_val is not None and max_val is not None and min_val == max_val:
            return min_val

        # Handle open-ended ranges
        if max_val is None:  # "10+"
            return min_val + 2.0

        if min_val is None:  # "<1"
            return max_val * 0.5

        # Use simple bias based on general factors
        bias_score = 0.5

        # Higher usage → closer to max
        usage_keys = [k for k in context.keys() if "usage" in k or "pattern" in k]
        for key in usage_keys:
            val = str(context.get(key, "")).lower()
            if "heavy" in val or "always" in val or "high" in val:
                bias_score += 0.1
            elif "light" in val or "minimal" in val or "low" in val:
                bias_score -= 0.1

        # More occupants → closer to max (more usage)
        occupants = context.get("n_occupants", 4)
        if occupants >= 6:
            bias_score += 0.05
        elif occupants <= 2:
            bias_score -= 0.05

        # Clamp and calculate
        bias_score = max(0.0, min(1.0, bias_score))
        resolved_val = min_val + (max_val - min_val) * bias_score

        logger.info(
            f"🧠 AI Range Resolver ({field_name}): '{value_str}' → {resolved_val:.2f} (bias: {bias_score:.2f})"
        )

        return round(resolved_val, 2)


# Import logger after class definition
import logging

logger = logging.getLogger(__name__)


def resolve_range_values(data: Dict) -> Dict:
    """
    Main entry point: Automatically resolves all range-based values in input data
    """
    resolved_data = data.copy()
    resolver = RangeResolver()

    # AC age (uses training column name: ac_age_years)
    if "ac_age_years" in resolved_data:
        age_val = resolved_data["ac_age_years"]
        if isinstance(age_val, str) and (
            "-" in age_val or "+" in age_val or "<" in age_val
        ):
            # Resolve AC age based on usage context
            min_age, max_age = resolver.parse_range(age_val)
            if min_age is not None or max_age is not None:
                bias = 0.5
                usage = data.get("ac_usage_pattern", "moderate")
                if usage in ["heavy", "long"]:
                    bias += 0.3
                elif usage in ["rare", "short"]:
                    bias -= 0.2
                if data.get("season") == "summer":
                    bias += 0.1
                if data.get("n_occupants", 4) >= 6:
                    bias += 0.1
                bias = max(0.0, min(1.0, bias))

                if max_age is None:
                    resolved_age = min_age + 2.0
                elif min_age is None:
                    resolved_age = max_age * 0.5
                else:
                    resolved_age = min_age + (max_age - min_age) * bias

                resolved_data["ac_age_years"] = round(resolved_age, 2)
                logger.info(
                    f"🧠 AI Range Resolver (ac_age_years): '{age_val}' → {resolved_age:.2f} years (bias: {bias:.2f})"
                )

    # Fridge age (uses training column name: fridge_age)
    if "fridge_age" in resolved_data:
        age_val = resolved_data["fridge_age"]
        if isinstance(age_val, str) and (
            "-" in age_val or "+" in age_val or "<" in age_val
        ):
            resolved_data["fridge_age"] = resolver.resolve_fridge_age(age_val, data)

    # Geyser/Water heater age
    if "water_heater_age" in resolved_data:
        age_val = resolved_data["water_heater_age"]
        if isinstance(age_val, str) and (
            "-" in age_val or "+" in age_val or "<" in age_val
        ):
            resolved_data["water_heater_age"] = resolver.resolve_geyser_age(
                age_val, data
            )

    # Fridge capacity (300L+)
    if "fridge_capacity" in resolved_data:
        val = resolved_data["fridge_capacity"]
        if isinstance(val, str):
            # Extract numeric value first
            import re

            match = re.match(r"(\d+)", val)
            if match and "+" in val:
                # Has + symbol, apply AI resolution
                min_val = float(match.group(1))
                occupants = data.get("n_occupants", 4)
                usage = data.get("refrigerator_usage_pattern", "normal")
                bias = 0.5
                if occupants >= 6:
                    bias += 0.2
                elif occupants <= 2:
                    bias -= 0.1
                if usage == "always":
                    bias += 0.1
                bias = max(0.0, min(1.0, bias))
                resolved_data["fridge_capacity"] = min_val + (100 * bias)
                logger.info(
                    f"🧠 AI Range Resolver (fridge_capacity): '{val}' → {resolved_data['fridge_capacity']:.0f}L (bias: {bias:.2f})"
                )
            elif match:
                # Just a number with unit, extract it
                resolved_data["fridge_capacity"] = float(match.group(1))

    # WM capacity (8.0 kg+)
    if "wm_capacity" in resolved_data:
        val = resolved_data["wm_capacity"]
        if isinstance(val, str):
            import re

            match = re.match(r"(\d+\.?\d*)", val)
            if match and "+" in val:
                min_val = float(match.group(1))
                occupants = data.get("n_occupants", 4)
                cycles = data.get("wm_cycles_per_week", 5)
                bias = 0.5
                if occupants >= 6:
                    bias += 0.2
                if cycles >= 7:
                    bias += 0.15
                bias = max(0.0, min(1.0, bias))
                resolved_data["wm_capacity"] = min_val + (2.0 * bias)
                logger.info(
                    f"🧠 AI Range Resolver (wm_capacity): '{val}' → {resolved_data['wm_capacity']:.1f}kg (bias: {bias:.2f})"
                )
            elif match:
                resolved_data["wm_capacity"] = float(match.group(1))

    # Geyser capacity (25L+)
    if "water_heater_capacity" in resolved_data:
        val = resolved_data["water_heater_capacity"]
        if isinstance(val, str):
            import re

            match = re.match(r"(\d+)", val)
            if match and "+" in val:
                min_val = float(match.group(1))
                occupants = data.get("n_occupants", 4)
                usage = data.get("geyser_usage_pattern", "light")
                bias = 0.5
                if occupants >= 6:
                    bias += 0.2
                if usage == "heavy":
                    bias += 0.15
                bias = max(0.0, min(1.0, bias))
                resolved_data["water_heater_capacity"] = min_val + (10 * bias)
                logger.info(
                    f"🧠 AI Range Resolver (water_heater_capacity): '{val}' → {resolved_data['water_heater_capacity']:.0f}L (bias: {bias:.2f})"
                )
            elif match:
                resolved_data["water_heater_capacity"] = float(match.group(1))

    return resolved_data


if __name__ == "__main__":
    # Test the resolver
    print("\n" + "=" * 80)
    print("🧪 TESTING AI-BASED RANGE RESOLVER")
    print("=" * 80)

    # Test Case 1: Heavy usage scenario
    print("\n1️⃣ Heavy Usage Scenario (should bias toward MAX)")
    print("-" * 80)
    heavy_context = {
        "fridge_age": "3-5",  # Using training column name
        "n_occupants": 7,
        "location_type": "urban",
        "season": "summer",
        "refrigerator_usage_pattern": "always",
        "fridge_type": "frost_free",
    }
    resolved = resolve_range_values(heavy_context)
    print(f"Input: {heavy_context['fridge_age']}")
    print(f"Output: {resolved['fridge_age']} years")
    print(f"Expected: Closer to 5.0 (heavy usage)")

    # Test Case 2: Light usage scenario
    print("\n2️⃣ Light Usage Scenario (should bias toward MIN)")
    print("-" * 80)
    light_context = {
        "fridge_age": "3-5",
        "n_occupants": 2,
        "location_type": "rural",
        "season": "winter",
        "refrigerator_usage_pattern": "light",
        "fridge_type": "direct_cool",
    }
    resolved = resolve_range_values(light_context)
    print(f"Input: {light_context['fridge_age']}")
    print(f"Output: {resolved['fridge_age']} years")
    print(f"Expected: Closer to 3.0 (light usage)")

    # Test Case 3: Neutral scenario
    print("\n3️⃣ Neutral Scenario (should be near AVERAGE)")
    print("-" * 80)
    neutral_context = {
        "fridge_age": "3-5",
        "n_occupants": 4,
        "location_type": "urban",
        "season": "monsoon",
        "refrigerator_usage_pattern": "normal",
        "fridge_type": "frost_free",
    }
    resolved = resolve_range_values(neutral_context)
    print(f"Input: {neutral_context['fridge_age']}")
    print(f"Output: {resolved['fridge_age']} years")
    print(f"Expected: Close to 4.0 (average)")

    # Test Case 4: Edge cases
    print("\n4️⃣ Edge Cases")
    print("-" * 80)
    edge_cases = [
        ("10+", "Open-ended range"),
        ("<1", "Less than range"),
        ("1-3", "Different range"),
        ("5", "Single value"),
    ]

    for age_str, description in edge_cases:
        test_context = {
            "fridge_age": age_str,
            "n_occupants": 4,
            "refrigerator_usage_pattern": "normal",
        }
        resolved = resolve_range_values(test_context)
        resolved_val = resolved["fridge_age"]
        if isinstance(resolved_val, str):
            resolved_val = float(resolved_val)
        print(f"{age_str:6s} ({description:20s}) → {resolved_val:.2f} years")

    print("\n" + "=" * 80)
    print("✅ RANGE RESOLVER TEST COMPLETE")
    print("=" * 80)
