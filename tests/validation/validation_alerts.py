"""
Validation and Alert System for SmartWatt Energy Management Platform

This module provides intelligent validation for appliance usage patterns with:
1. Seasonal/contextual validation (e.g., AC usage in monsoon)
2. Appliance overuse detection (e.g., iron >1.25 hours/day)
3. Aggregate pattern diagnosis (e.g., single appliance dominance)

Each validation returns (severity, message) tuple or None.
Severity levels: 'info', 'warning', 'error'
"""

from datetime import datetime


def get_current_season():
    """
    Determine current season based on month.
    Returns: 'Summer', 'Monsoon', or 'Winter'
    """
    month = datetime.now().month

    if month in [3, 4, 5]:  # March, April, May
        return "Summer"
    elif month in [6, 7, 8, 9]:  # June-September
        return "Monsoon"
    else:  # October-February
        return "Winter"


def validate_seasonal_usage(appliance, hours, season=None):
    """
    Check if appliance usage is appropriate for current season.

    Args:
        appliance: Appliance key (e.g., 'ac', 'geyser')
        hours: Daily usage hours
        season: Override season (default: auto-detect)

    Returns:
        (severity, message) tuple or None
    """
    if season is None:
        season = get_current_season()

    # AC usage validation
    if appliance == "ac":
        if "Monsoon" in season and hours > 8:
            return (
                "warning",
                "High AC usage during monsoon season (>8 hours/day). Natural cooling is available!",
            )
        elif "Winter" in season and hours > 6:
            return (
                "warning",
                "High AC usage during winter (>6 hours/day). Consider using fans instead.",
            )

    # Geyser/Water Heater validation
    elif appliance == "geyser":
        if "Summer" in season and hours > 2:
            return (
                "info",
                "Consider solar heating in summer - Kerala's abundant sunlight can heat water naturally!",
            )

    # Water Pump validation
    elif appliance == "pump":
        if hours > 3:
            return (
                "warning",
                "Unusually high pump usage (>3 hours/day). Check for leaks or tank issues.",
            )

    # Refrigerator validation
    elif appliance == "fridge":
        if hours < 16:
            return (
                "warning",
                f"Refrigerators typically run 16-24 hours/day for proper cooling. You selected {hours:.1f} hours - are you sure?",
            )

    return None


def validate_appliance_overuse(appliance, hours):
    """
    Check if appliance usage exceeds typical household thresholds.

    Args:
        appliance: Appliance key
        hours: Daily usage hours

    Returns:
        (severity, message) tuple or None
    """
    # Define overuse thresholds
    thresholds = {
        "iron": (
            1.25,
            "warning",
            "Very high iron usage for a household (>1.25 hours/day). Commercial ironing?",
        ),
        "tv": (
            10,
            "info",
            "High screen time (>10 hours/day). Consider power-saving mode or auto-shutoff.",
        ),
        "mixer": (
            1.25,
            "warning",
            "Unusually high mixer usage (>1.25 hours/day) for typical households.",
        ),
        "microwave": (
            1.5,
            "warning",
            "High microwave usage (>1.5 hours/day). Typical households use <1 hour/day.",
        ),
        "fan": (
            18,
            "info",
            "Fans running most of the day (>18 hours). Normal for hot weather!",
        ),
        "led": (
            12,
            "info",
            "Lights on >12 hours/day. Consider daylight sensors or motion sensors.",
        ),
        "cfl": (
            12,
            "info",
            "Lights on >12 hours/day. Consider daylight sensors or motion sensors.",
        ),
        "tube": (
            12,
            "info",
            "Lights on >12 hours/day. Consider daylight sensors or motion sensors.",
        ),
    }

    if appliance in thresholds:
        threshold, severity, message = thresholds[appliance]
        if hours > threshold:
            return (severity, message)

    return None


def validate_aggregate_patterns(breakdown, total_kwh, correction_factor, raw_total):
    """
    Validate overall consumption patterns for inconsistencies.

    Args:
        breakdown: Dict of {appliance: kwh}
        total_kwh: Target total consumption from bill
        correction_factor: AI normalization factor
        raw_total: Total predicted usage before normalization

    Returns:
        List of (severity, message) tuples
    """
    alerts = []

    # 1. Single appliance dominance check (>70% of total)
    for appliance, kwh in breakdown.items():
        percentage = (kwh / total_kwh) * 100 if total_kwh > 0 else 0

        # Allow AC and Pump to dominate (they can legitimately be >70%)
        if percentage > 70 and appliance not in ["Air Conditioner", "Water Pump"]:
            alerts.append(
                (
                    "warning",
                    f"⚠️ {appliance} accounts for {percentage:.0f}% of total consumption. Please verify your inputs.",
                )
            )

    # 2. Correction factor validation
    if correction_factor > 3:
        alerts.append(
            (
                "error",
                f"❌ Predicted usage is much lower than your bill (adjustment factor: {correction_factor:.1f}x). Please review all appliance hours.",
            )
        )
    elif correction_factor < 0.5:
        alerts.append(
            (
                "error",
                f"❌ Predicted usage is much higher than your bill (adjustment factor: {correction_factor:.1f}x). Please review your usage hours.",
            )
        )
    elif correction_factor > 1.5:
        alerts.append(
            (
                "warning",
                f"⚠️ Significant upward adjustment needed ({correction_factor:.1f}x) to match your bill - some appliance hours may be underestimated.",
            )
        )
    elif correction_factor < 0.7:
        alerts.append(
            (
                "warning",
                f"⚠️ Significant downward adjustment needed ({correction_factor:.1f}x) to match your bill - some appliance hours may be overestimated.",
            )
        )

    # 3. Total raw prediction validation
    if total_kwh > 0:
        raw_percentage = (raw_total / total_kwh) * 100

        if raw_percentage < 10:
            alerts.append(
                (
                    "error",
                    f"❌ Total predicted usage is extremely low ({raw_percentage:.0f}% of your bill). Please check all appliance usage hours.",
                )
            )
        elif raw_percentage > 300:
            alerts.append(
                (
                    "error",
                    f"❌ Total predicted usage is extremely high ({raw_percentage:.0f}% of your bill). Please review all usage hours.",
                )
            )

    return alerts


def validate_logical_consistency(appliance, hours, details):
    """
    Check for logically impossible configurations.

    Args:
        appliance: Appliance key
        hours: Usage hours
        details: Full appliance details dict

    Returns:
        (severity, message) tuple or None
    """
    # Fan hours > 0 but num_fans = 0
    if appliance == "fan" and hours > 0:
        num_fans = details.get("num_fans", 0)
        if num_fans == 0:
            return (
                "error",
                "❌ Fan hours set but number of fans is 0. Please check your inputs.",
            )

    # LED hours > 0 but num_led = 0
    if appliance == "led" and hours > 0:
        num_led = details.get("num_led", 0)
        if num_led == 0:
            return (
                "error",
                "❌ LED light hours set but number of LED bulbs is 0. Please check your inputs.",
            )

    # CFL hours > 0 but num_cfl = 0
    if appliance == "cfl" and hours > 0:
        num_cfl = details.get("num_cfl", 0)
        if num_cfl == 0:
            return (
                "error",
                "❌ CFL light hours set but number of CFL bulbs is 0. Please check your inputs.",
            )

    # Tube light hours > 0 but num_tube = 0
    if appliance == "tube" and hours > 0:
        num_tube = details.get("num_tube", 0)
        if num_tube == 0:
            return (
                "error",
                "❌ Tube light hours set but number of tube lights is 0. Please check your inputs.",
            )

    return None
