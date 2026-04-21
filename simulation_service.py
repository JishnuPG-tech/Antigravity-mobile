from typing import Any, Dict, List


class SimulationService:
    """
    Handles 'What-If' scenarios for energy optimization.
    Each check is independently wrapped to prevent one failure from silencing others.
    """

    @staticmethod
    def safe_int(val, default=0):
        try:
            if not val:
                return default
            s = str(val).split(" ")[0].split("-")[0]
            return int(float(s))
        except:
            return default

    @staticmethod
    def safe_float(val, default=0.0):
        try:
            if not val:
                return default
            s = str(val).split(" ")[0]
            return float(s)
        except:
            return default

    @classmethod
    def run_simulation(
        cls, details: Dict[str, Any], bill_total: float, model_callback
    ) -> List[Dict[str, Any]]:
        """
        Runs all what-if simulations independently.
        Each check has its own try/except so a broken model call never blocks others.
        Returns a list of insight dicts with title, saved_kwh, description.
        """
        insights = []
        d = details
        bill = bill_total

        # --- 1. AC STAR RATING UPGRADE ---
        try:
            ac_star = cls.safe_int(d.get("ac_star"), 0)
            if ac_star > 0 and ac_star < 5:
                curr = model_callback("air_conditioner", d, bill).get("prediction", 0)
                sim_d = {**d, "ac_star": 5}
                sim_pred = model_callback("air_conditioner", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 2:
                    insights.append(
                        {
                            "title": f"Upgrade to 5-Star AC",
                            "saved_kwh": round(saved, 1),
                            "description": f"Switching your {ac_star}-star AC to a 5-star model could save ~{round(saved)} kWh per month.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] AC insight error: {e}")

        # --- 2. REDUCE AC DAILY HOURS ---
        try:
            ac_hours = cls.safe_float(d.get("ac_hours"), 0)
            if ac_hours > 4:
                curr = model_callback("air_conditioner", d, bill).get("prediction", 0)
                sim_d = {**d, "ac_hours": max(2, ac_hours - 2)}
                sim_pred = model_callback("air_conditioner", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 2:
                    insights.append(
                        {
                            "title": "Reduce AC Usage by 2 Hours",
                            "saved_kwh": round(saved, 1),
                            "description": f"Cutting AC from {round(ac_hours)}h to {round(max(2, ac_hours-2))}h/day could save ~{round(saved)} kWh monthly.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] AC hours insight error: {e}")

        # --- 3. OLD FRIDGE REPLACEMENT ---
        try:
            fridge_age = d.get("fridge_age", "")
            fridge_age_int = cls.safe_int(fridge_age, 0)
            # Check string keys like '10+' as well
            is_old_fridge = fridge_age_int >= 10 or str(fridge_age).startswith("10")
            if is_old_fridge:
                curr = model_callback("refrigerator", d, bill).get("prediction", 0)
                sim_d = {**d, "fridge_age": 2}
                sim_pred = model_callback("refrigerator", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 2:
                    insights.append(
                        {
                            "title": "Replace Old Refrigerator",
                            "saved_kwh": round(saved, 1),
                            "description": f"Your old fridge is inefficient. A new energy-efficient model could save ~{round(saved)} kWh monthly.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] Fridge insight error: {e}")

        # --- 4. BLDC FAN UPGRADE ---
        try:
            fan_type = str(d.get("fan_type", "")).lower()
            num_fans = cls.safe_int(d.get("num_fans"), 0)
            if fan_type not in ("bldc",) and num_fans > 0:
                curr = model_callback("ceiling_fan", d, bill).get("prediction", 0)
                sim_d = {**d, "fan_type": "bldc"}
                sim_pred = model_callback("ceiling_fan", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 2:
                    insights.append(
                        {
                            "title": "Switch to BLDC Fans",
                            "saved_kwh": round(saved, 1),
                            "description": f"Replacing your {num_fans} standard fan(s) with BLDC models saves ~{round(saved)} kWh monthly (60% less power).",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] Fan insight error: {e}")

        # --- 5. GEYSER USAGE REDUCTION ---
        try:
            geyser_hours = cls.safe_float(d.get("geyser_hours"), 0)
            if geyser_hours > 0.5:
                curr = model_callback("water_heater", d, bill).get("prediction", 0)
                sim_d = {**d, "geyser_hours": 0.5}
                sim_pred = model_callback("water_heater", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 1:
                    insights.append(
                        {
                            "title": "Limit Geyser to 30 min/day",
                            "saved_kwh": round(saved, 1),
                            "description": "Reducing geyser usage to 30 mins/day saves energy without sacrificing comfort.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] Geyser insight error: {e}")

        # --- 6. TV HOURS REDUCTION ---
        try:
            tv_hours = cls.safe_float(d.get("tv_hours"), 0)
            if tv_hours > 5:
                curr = model_callback("television", d, bill).get("prediction", 0)
                sim_d = {**d, "tv_hours": 3}
                sim_pred = model_callback("television", sim_d, bill).get(
                    "prediction", 0
                )
                saved = curr - sim_pred
                if saved > 1:
                    insights.append(
                        {
                            "title": "Reduce TV Watching by 2 Hours",
                            "saved_kwh": round(saved, 1),
                            "description": f"Cutting TV from {round(tv_hours)}h to 3h/day could save ~{round(saved)} kWh monthly.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] TV insight error: {e}")

        # --- 7. UPGRADE TO LED LIGHTS ---
        try:
            # If cfl or tube lights are present, recommend LEDs
            cfl_hours = cls.safe_float(d.get("cfl_hours"), 0)
            tube_hours = cls.safe_float(d.get("tube_hours"), 0)
            if cfl_hours > 2 or tube_hours > 2:
                # CFL ~15W vs LED ~7W: 50% saving
                total_hours = max(cfl_hours, tube_hours)
                # Rough estimate: 4 lights at 15W → 7W difference = 32W saving × hours × 30 / 1000
                estimated_save = round(4 * 0.008 * total_hours * 30, 1)
                if estimated_save > 1:
                    insights.append(
                        {
                            "title": "Switch CFL/Tube Lights to LED",
                            "saved_kwh": estimated_save,
                            "description": f"LEDs use 50–60% less power than CFL/tube lights. Est. saving: ~{estimated_save} kWh/month.",
                        }
                    )
        except Exception as e:
            print(f"[Simulation] LED insight error: {e}")

        # --- 8. WASHING MACHINE — COLD WASH TIP ---
        try:
            wm_pattern = str(d.get("wm_pattern", "")).lower()
            wm_cycles = cls.safe_float(d.get("wm_cycles_per_week"), 0)
            if wm_cycles >= 5 or wm_pattern in ("heavy", "very_heavy"):
                insights.append(
                    {
                        "title": "Use Cold Water Wash Cycles",
                        "saved_kwh": round(
                            wm_cycles * 0.5 * 4, 1
                        ),  # ~0.5 kWh saved per hot→cold wash
                        "description": "Switching to cold water wash for most loads saves ~0.5 kWh per cycle and extends fabric life.",
                    }
                )
        except Exception as e:
            print(f"[Simulation] WM insight error: {e}")

        return insights
