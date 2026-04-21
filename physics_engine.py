class PhysicsEngine:
    """
    Handles definitive Watt-Hour calculations based on appliance specifications.
    This is the "Truth" layer that adheres to physics laws.
    """

    @staticmethod
    def _get_float(d, key, default):
        val = d.get(key, default)
        if val == "unknown" or val is None:
            return default
        try:
            return float(val)
        except:
            return default

    @classmethod
    def calculate_watts(cls, name, d):
        """Standard Physics Wattage Calculation"""
        watts = 100  # Fallback

        if name == "ac":
            tons = cls._get_float(d, "ac_tonnage", 1.5)
            star = cls._get_float(d, "ac_star_rating", 3)
            # Prevent star rating > 5 or < 1 causing weird math? No, formula handles it.
            watts = tons * 1200 * (1 + (5 - star) * 0.1)

        elif name == "fridge":
            cap = cls._get_float(d, "fridge_capacity", 250)
            age = cls._get_float(d, "fridge_age", 5)
            star = cls._get_float(d, "fridge_star_rating", 3)
            # DEBUG: Print to confirm logic usage
            # print(f"DEBUG: Fridge Physics - Star: {star}, Capacity: {cap}, Age: {age}")

            # Base watts + 2% degradation per year + Star Rating Impact (5 star = 20% less base)
            # Base 150W for 3-star. 5-star ~120W. 1-star ~180W.
            base_watts = (cap / 250) * 150
            efficiency_factor = (
                1 + (3 - star) * 0.15
            )  # 5-star -> 0.7 (30% less), 1-star -> 1.3 (30% more)
            watts = base_watts * efficiency_factor * (1 + (age * 0.02))

        elif name == "ceiling_fan":
            fan_type = d.get("fan_type", "standard")
            if fan_type == "bldc":
                watts = 30  # BLDC Energy Saver
            else:
                watts = 75  # Standard Fan

        elif name == "television":
            size = cls._get_float(d, "tv_size_inches", 43)
            watts = size * 2.5  # Approx 100W for 43 inch, 140W for 55 inch

        elif name == "washing_machine":
            watts = 500  # Watts per cycle equivalent

        elif name == "water_pump":
            hp = cls._get_float(d, "water_pump_hp", 1.0)
            watts = hp * 746

        elif name == "water_heater":
            watts = 2000  # 2kW Geyser

        elif name == "iron":
            watts = 1000  # Standard Iron

        elif name == "kettle":
            watts = 1500

        elif name == "induction":
            watts = 2000

        elif name == "desktop":
            watts = 250

        elif name == "microwave":
            watts = 1200
        elif name == "mixer":
            watts = 750
        elif name == "rice_cooker":
            watts = 600
        elif name == "toaster":
            watts = 800
        elif name == "food_processor":
            watts = 600
        elif name == "laptop":
            watts = 60
        elif name == "hair_dryer":
            watts = 1200
        elif name == "vacuum":
            watts = 1400
        elif name == "led_lights":
            watts = 9
        elif name == "cfl_lights":
            watts = 18
        elif name == "tube_lights":
            watts = 40

        return watts
