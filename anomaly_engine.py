class AnomalyEngine:
    """
    Diagnoses Health (Efficiency) and Behavior (Usage) Anomalies.
    """

    @staticmethod
    def check_anomalies(name, eff, hours):
        status = "Normal"
        msg = ""
        type = "None"

        # 1. USAGE ANOMALIES (Behavior)
        usage_thresholds = {
            "water_heater": (3.0, "Critical: Geyser running > 3h/day!"),
            "water_pump": (2.0, "Warning: Pump running > 2h/day"),
            "ac": (16.0, "Notice: High AC Usage (>16h)"),
            "led_lights": (14.0, "Notice: Lights on > 14h"),
            "iron": (1.0, "Warning: Iron Box usage high"),
        }

        if name in usage_thresholds:
            thresh, warn_msg = usage_thresholds[name]
            if hours > thresh:
                status = "Usage_Anomaly"
                msg = warn_msg
                type = "Behavior"

        # 2. EFFICIENCY ANOMALIES (Health Check)
        # If a machine is consuming 25% more power than it should, it's sick.
        if eff > 1.25:
            status = "efficiency_critical"
            msg = f"CRITICAL: {name} is consuming 25% more power than rated! Check for service."
            type = "Health"
        elif eff > 1.15 and status != "efficiency_critical":
            status = "efficiency_warning"
            msg = f"Warning: {name} efficiency is degrading (15% loss)."
            type = "Health"

        return {"status": status, "message": msg, "type": type}
