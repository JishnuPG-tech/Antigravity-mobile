"""
Enhanced Monte Carlo Simulation  (Multi-Output Targets - Kerala Context)
Author: SmartWatt Team
Date: 2025-12-11
Purpose: Generates dataset with 'Ground Truth' Efficiency and Effective Hours for Integrated Hybrid AI
"""

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class KeralaRealWorldSimulator:
    def __init__(self, n_households: int = 12000, random_seed: int = 42):
        self.n = n_households
        np.random.seed(random_seed)

        # --- KERALA CONTEXT VARIABLES ---
        # High Humidity -> Fans run longer
        # Voltage Fluctuation -> Rural areas have lower efficiency
        # Old Grid -> 10% transmission loss simulation

    def generate_demographics(self):
        data = {
            "household_id": [f"KL__{i}" for i in range(self.n)],
            "n_occupants": np.random.choice(
                [2, 3, 4, 5, 6], size=self.n, p=[0.1, 0.25, 0.40, 0.15, 0.1]
            ),
            "location_type": np.random.choice(
                ["urban", "rural"], size=self.n, p=[0.6, 0.4]
            ),
            "total_kwh_monthly": np.zeros(self.n),  # Will sum up later
        }
        return pd.DataFrame(data)

    def generate_ac_data(self, df):
        # 45% Penetration
        has_ac = np.random.random(self.n) < 0.45
        df["has_ac"] = has_ac.astype(int)

        # 1. Specs (What kind of AC do they have?)
        df["ac_tonnage"] = np.where(
            has_ac, np.random.choice([1.0, 1.5], size=self.n, p=[0.3, 0.7]), 0
        )
        df["ac_star_rating"] = np.where(
            has_ac, np.random.choice([3, 5], size=self.n, p=[0.6, 0.4]), 0
        )

        # New Field: ac_age_years (Integrated from add_ac_age.py)
        df["ac_age_years"] = np.where(
            has_ac,
            np.random.choice(
                ["0-2", "3-5", "6-10", "10+"], size=self.n, p=[0.20, 0.35, 0.30, 0.15]
            ),
            "unknown",
        )

        # UI Fields: ac_type, ac_usage_pattern
        df["ac_type"] = np.where(
            has_ac,
            np.random.choice(
                ["split", "window", "inverter"], size=self.n, p=[0.6, 0.2, 0.2]
            ),
            "unknown",
        )
        df["ac_usage_pattern"] = np.where(
            has_ac,
            np.random.choice(
                ["heavy", "moderate", "light"], size=self.n, p=[0.2, 0.5, 0.3]
            ),
            "none",
        )

        # 2. BEHAVIOR (The 'Secret' Human Factor)
        # Generate hours based on usage pattern (AI learns this correlation)
        # In Kerala, humidity makes AC run longer than expected
        base_hours = np.where(
            df["ac_usage_pattern"] == "light",
            np.random.uniform(2, 6, self.n),
            np.where(
                df["ac_usage_pattern"] == "moderate",
                np.random.uniform(6, 10, self.n),
                np.where(
                    df["ac_usage_pattern"] == "heavy",
                    np.random.uniform(10, 14, self.n),
                    0,
                ),
            ),
        )

        # Kerala humidity factor (compressor works harder)
        humidity_factor = np.random.normal(
            1.15, 0.05, self.n
        )  # 15% extra load due to humidity
        df["ac_real_effective_hours"] = np.where(
            has_ac, base_hours * humidity_factor, 0
        )

        # 3. EFFICIENCY (The 'Wear and Tear' Factor)
        # Rural areas often suffer from voltage drops.
        # A low voltage supply makes the AC compressor struggle, reducing efficiency by ~10%.
        efficiency = np.random.normal(
            0.95, 0.05, self.n
        )  # Most ACs work at 95% optimal efficiency
        rural_mask = (df["location_type"] == "rural") & has_ac
        efficiency[rural_mask] -= 0.10  # Penalty for rural grid quality
        df["ac_real_efficiency_factor"] = np.where(has_ac, efficiency.clip(0.6, 1.1), 0)

        # 4. The Physics Calculation (Ground Truth)
        # Physics Formula: Watts = Tons * 1200 / Efficiency
        watts = (df["ac_tonnage"] * 1200) * (1 + (5 - df["ac_star_rating"]) * 0.1)

        # If efficiency is low (e.g., 0.8), power consumption goes UP.
        # It's an inverse relationship: Worse Efficiency = Higher Bill.
        watts = watts / df["ac_real_efficiency_factor"]

        # Final Bill Calculation: (Watts * Hours * 30 days) / 1000 to get units (kWh)
        df["ac_kwh"] = (watts * df["ac_real_effective_hours"] * 30) / 1000
        return df

    def generate_fridge_data(self, df):
        # 95% Penetration
        has_fridge = np.random.random(self.n) < 0.95
        df["has_refrigerator"] = has_fridge.astype(int)

        # Specs
        df["fridge_capacity"] = np.where(
            has_fridge, np.random.choice([190, 260], size=self.n), 0
        )
        df["fridge_age"] = np.where(
            has_fridge, np.random.choice([2, 5, 10], size=self.n, p=[0.3, 0.4, 0.3]), 0
        )
        df["fridge_star_rating"] = np.where(
            has_fridge,
            np.random.choice([2, 3, 4, 5], size=self.n, p=[0.2, 0.3, 0.3, 0.2]),
            0,
        )

        # UI Fields: fridge_type
        df["fridge_type"] = np.where(
            has_fridge,
            np.random.choice(["frost_free", "direct_cool"], size=self.n, p=[0.7, 0.3]),
            "unknown",
        )

        # BEHAVIOR: AI Pattern Learning
        df["refrigerator_usage_pattern"] = np.where(
            has_fridge,
            np.random.choice(
                ["manual", "light", "normal", "always"],
                size=self.n,
                p=[0.05, 0.10, 0.20, 0.65],
            ),
            "unknown",
        )

        # Pattern-based hour ranges
        pattern_hours_map = {
            "manual": np.random.uniform(8, 14, self.n),  # Turn off at night
            "light": np.random.uniform(14, 18, self.n),  # Off during low usage
            "normal": np.random.uniform(18, 22, self.n),  # Mostly on
            "always": np.full(self.n, 24.0),  # 24/7 operation
        }
        hours = np.zeros(self.n)
        for pattern, hours_range in pattern_hours_map.items():
            hours = np.where(
                df["refrigerator_usage_pattern"] == pattern, hours_range, hours
            )

        df["fridge_real_effective_hours"] = np.where(has_fridge, hours, 0)

        # EFFICIENCY:
        # In the hot Kerala climate, rubber seals on fridges degrade faster.
        # An old fridge leaks cold air, making the motor run longer. We deduct 4% efficiency per year.
        eff = np.ones(self.n)
        eff -= df["fridge_age"] * 0.04
        df["fridge_real_efficiency_factor"] = np.where(
            has_fridge, eff.clip(0.5, 1.0), 0
        )

        # Calculation
        watts = (df["fridge_capacity"] / 250) * 200  # Baseline
        watts = watts / df["fridge_real_efficiency_factor"]
        df["fridge_kwh"] = (watts * df["fridge_real_effective_hours"] * 30) / 1000
        return df

    def generate_fan_data(self, df):
        # 98% Penetration (Essential in Kerala)
        df["has_ceiling_fan"] = (np.random.random(self.n) < 0.98).astype(int)

        # UI Fields: fan_type, num_fans
        df["fan_type"] = np.where(
            df["has_ceiling_fan"],
            np.random.choice(["standard", "bldc"], size=self.n, p=[0.8, 0.2]),
            "unknown",
        )
        df["num_fans"] = np.where(
            df["has_ceiling_fan"],
            np.random.choice(
                [2, 3, 4, 5, 6], size=self.n, p=[0.1, 0.25, 0.35, 0.2, 0.1]
            ),
            0,
        )

        # BEHAVIOR: AI Pattern Learning
        df["fan_usage_pattern"] = np.where(
            df["has_ceiling_fan"],
            np.random.choice(
                ["rarely", "few", "most", "all"],
                size=self.n,
                p=[0.05, 0.20, 0.50, 0.25],
            ),
            "unknown",
        )

        # Pattern-based hour ranges (Kerala humidity = high usage)
        pattern_hours_map = {
            "rarely": np.random.uniform(2, 5, self.n),  # AC users
            "few": np.random.uniform(5, 10, self.n),  # Few rooms
            "most": np.random.uniform(10, 16, self.n),  # Most rooms
            "all": np.random.uniform(16, 22, self.n),  # All rooms all day
        }
        base_hours = np.zeros(self.n)
        for pattern, hours_range in pattern_hours_map.items():
            base_hours = np.where(
                df["fan_usage_pattern"] == pattern, hours_range, base_hours
            )

        # Humidity boost (Kerala climate)
        humidity_boost = np.random.normal(1.2, 0.1, self.n)
        df["ceiling_fan_real_effective_hours"] = np.where(
            df["has_ceiling_fan"], (base_hours * humidity_boost).clip(2, 24), 0
        )

        # EFFICIENCY: Old fans get slow/power hungry
        df["ceiling_fan_age"] = np.random.choice(
            [2, 5, 10, 15], size=self.n, p=[0.2, 0.3, 0.3, 0.2]
        )
        eff = np.ones(self.n) - (df["ceiling_fan_age"] * 0.01)  # 1% drop/year
        df["ceiling_fan_real_efficiency_factor"] = np.where(
            df["has_ceiling_fan"], eff.clip(0.7, 1.0), 0
        )

        # Power calculation
        watts = 75 / df["ceiling_fan_real_efficiency_factor"]
        df["ceiling_fan_kwh"] = (
            watts * df["ceiling_fan_real_effective_hours"] * df["num_fans"] * 30
        ) / 1000
        return df

    def generate_tv_data(self, df):
        # 95% Penetration
        df["has_television"] = (np.random.random(self.n) < 0.95).astype(int)

        # BEHAVIOR: The "Serial" factor.
        # In Kerala households, evening TV serials and news are a staple.
        # We assume 4-6 hours of usage is standard usage.
        # Generate usage patterns first (light/moderate/heavy/always)
        df["television_usage_pattern"] = np.where(
            df["has_television"],
            np.random.choice(
                ["light", "moderate", "heavy", "always"],
                size=self.n,
                p=[0.25, 0.45, 0.25, 0.05],
            ),
            "none",
        )

        # Generate hours based on pattern + household context (AI will learn this correlation)
        base_hours = np.where(
            df["television_usage_pattern"] == "light",
            np.random.uniform(1, 3, self.n),
            np.where(
                df["television_usage_pattern"] == "moderate",
                np.random.uniform(3, 5, self.n),
                np.where(
                    df["television_usage_pattern"] == "heavy",
                    np.random.uniform(5, 8, self.n),
                    np.where(
                        df["television_usage_pattern"] == "always",
                        np.random.uniform(8, 12, self.n),
                        0,
                    ),
                ),
            ),
        )

        # Add household context influence (more people = slightly more hours)
        occupant_factor = (
            1 + (df["n_occupants"] - 4) * 0.05
        )  # ±5% per person difference from 4
        hours = (base_hours * occupant_factor).clip(1, 14)

        df["television_real_effective_hours"] = np.where(df["has_television"], hours, 0)

        # Efficiency (LED vs CRT/LCD)
        df["television_type"] = np.random.choice(
            ["LED", "CRT", "LCD"], size=self.n, p=[0.7, 0.1, 0.2]
        )

        # UI Fields: tv_size
        df["tv_size"] = np.where(
            df["has_television"],
            np.random.choice([32, 43, 55], size=self.n, p=[0.4, 0.4, 0.2]),
            0,
        )

        base_watts = np.where(
            df["television_type"] == "LED",
            80,
            np.where(df["television_type"] == "LCD", 120, 150),
        )
        eff = np.ones(self.n)
        df["television_real_efficiency_factor"] = np.where(df["has_television"], eff, 0)
        df["television_kwh"] = (
            base_watts * df["television_real_effective_hours"] * 30
        ) / 1000
        return df

    def generate_wm_data(self, df):
        # 60% Penetration
        df["has_washing_machine"] = (np.random.random(self.n) < 0.60).astype(int)

        # UI Fields: wm_type, wm_capacity, wm_star_rating, wm_cycles_per_week
        df["wm_type"] = np.where(
            df["has_washing_machine"],
            np.random.choice(
                ["top_load", "front_load", "semi_automatic"],
                size=self.n,
                p=[0.5, 0.35, 0.15],
            ),
            "unknown",
        )
        df["wm_capacity"] = np.where(
            df["has_washing_machine"],
            np.random.choice([5, 6, 7, 8], size=self.n, p=[0.2, 0.3, 0.3, 0.2]),
            0,
        )
        df["wm_star_rating"] = np.where(
            df["has_washing_machine"],
            np.random.choice([2, 3, 4, 5], size=self.n, p=[0.2, 0.3, 0.3, 0.2]),
            0,
        )

        # BEHAVIOR: Cycles Per Week dependent on Occupants
        # 2 people -> 2 cycles/week
        # 4+ people -> 4-6 cycles/week
        cycles = (df["n_occupants"] * 1.2) + np.random.normal(0, 1, self.n)
        df["wm_cycles_per_week"] = np.where(
            df["has_washing_machine"], cycles.clip(1, 10), 0
        )
        df["washing_machine_real_effective_hours"] = df[
            "wm_cycles_per_week"
        ]  # Storing Cycles as "Hours" for simplicity in training

        # Efficiency
        df["washing_machine_real_efficiency_factor"] = 1.0

        base_kwh_per_cycle = 0.5  # Avg
        df["washing_machine_kwh"] = (
            base_kwh_per_cycle * df["washing_machine_real_effective_hours"] * 4.3
        )
        return df

    def generate_pump_data(self, df):
        # 70% Penetration (Well Water is common in Kerala)
        df["has_water_pump"] = (np.random.random(self.n) < 0.70).astype(int)

        # UI Fields: water_pump_hp
        df["water_pump_hp"] = np.where(
            df["has_water_pump"],
            np.random.choice([0.5, 1.0, 1.5], size=self.n, p=[0.3, 0.5, 0.2]),
            0,
        )

        # BEHAVIOR: AI Pattern Learning
        df["pump_usage_pattern"] = np.where(
            df["has_water_pump"],
            np.random.choice(
                ["minimal", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.15, 0.35, 0.40, 0.10],
            ),
            "unknown",
        )

        # Pattern-based minute ranges
        pattern_mins_map = {
            "minimal": np.random.uniform(10, 20, self.n),  # Municipal backup
            "light": np.random.uniform(20, 40, self.n),  # Occasional pumping
            "moderate": np.random.uniform(40, 70, self.n),  # Regular well usage
            "heavy": np.random.uniform(70, 120, self.n),  # Primary water source
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(df["pump_usage_pattern"] == pattern, mins, base_mins)

        # Occupancy influence (more people = more water)
        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.12
        hours = (base_mins * occupant_factor) / 60
        df["water_pump_real_effective_hours"] = np.where(
            df["has_water_pump"], hours.clip(0.15, 2.5), 0
        )

        # Efficiency (Old pumps are terrible)
        eff = np.random.normal(0.8, 0.1, self.n).clip(0.5, 1.0)
        df["water_pump_real_efficiency_factor"] = np.where(df["has_water_pump"], eff, 0)

        watts = (df["water_pump_hp"] * 746) / df[
            "water_pump_real_efficiency_factor"
        ]  # HP to Watts
        df["water_pump_kwh"] = (
            watts * df["water_pump_real_effective_hours"] * 30
        ) / 1000
        return df

    def generate_geyser_data(self, df):
        # 40% Penetration (Urban mainly)
        df["has_water_heater"] = (np.random.random(self.n) < 0.40).astype(int)

        # UI Fields: water_heater_type, water_heater_capacity
        df["water_heater_type"] = np.where(
            df["has_water_heater"],
            np.random.choice(
                ["instant", "storage", "gas", "solar"],
                size=self.n,
                p=[0.4, 0.4, 0.1, 0.1],
            ),
            "unknown",
        )
        df["water_heater_capacity"] = np.where(
            df["has_water_heater"],
            np.random.choice([10, 15, 25, 35], size=self.n, p=[0.3, 0.4, 0.2, 0.1]),
            0,
        )

        # BEHAVIOR: AI Pattern Learning + Seasonality
        df["season"] = np.random.choice(["summer", "monsoon", "winter"], size=self.n)

        df["geyser_usage_pattern"] = np.where(
            df["has_water_heater"],
            np.random.choice(
                ["minimal", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.20, 0.40, 0.30, 0.10],
            ),
            "unknown",
        )

        # Pattern-based hour ranges
        pattern_hours_map = {
            "minimal": np.random.uniform(0.2, 0.5, self.n),  # Quick showers
            "light": np.random.uniform(0.5, 1.0, self.n),  # 1-2 showers/day
            "moderate": np.random.uniform(1.0, 1.8, self.n),  # Regular family use
            "heavy": np.random.uniform(1.8, 3.0, self.n),  # Multiple long showers
        }
        base_hours = np.zeros(self.n)
        for pattern, hours_range in pattern_hours_map.items():
            base_hours = np.where(
                df["geyser_usage_pattern"] == pattern, hours_range, base_hours
            )

        # Season multiplier (winter = more hot water)
        season_factor = np.where(
            df["season"] == "summer", 0.5, np.where(df["season"] == "monsoon", 1.0, 2.0)
        )

        # Occupancy influence
        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.10

        hours = base_hours * season_factor * occupant_factor

        df["water_heater_real_effective_hours"] = np.where(
            df["has_water_heater"], hours, 0
        )
        df["water_heater_real_efficiency_factor"] = 1.0  # Static

        df["water_heater_kwh"] = (
            2000 * df["water_heater_real_effective_hours"] * 30
        ) / 1000
        return df

    def generate_misc_data(self, df):
        # 1. Iron Box (90% Penetration)
        df["has_iron"] = (np.random.random(self.n) < 0.90).astype(int)

        # Add usage pattern for iron
        df["iron_usage_pattern"] = np.where(
            df["has_iron"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.15, 0.50, 0.30, 0.05],
            ),
            "none",
        )

        # Generate hours based on pattern + household context
        base_hours = np.where(
            df["iron_usage_pattern"] == "rarely",
            np.random.uniform(0.08, 0.25, self.n),  # 5-15 min
            np.where(
                df["iron_usage_pattern"] == "light",
                np.random.uniform(0.25, 0.50, self.n),  # 15-30 min
                np.where(
                    df["iron_usage_pattern"] == "moderate",
                    np.random.uniform(0.50, 1.0, self.n),  # 30-60 min
                    np.where(
                        df["iron_usage_pattern"] == "heavy",
                        np.random.uniform(1.0, 2.0, self.n),
                        0,
                    ),
                ),
            ),
        )  # 1-2 hrs

        occupant_factor = (
            1 + (df["n_occupants"] - 4) * 0.10
        )  # More people = more clothes
        df["iron_real_effective_hours"] = np.where(
            df["has_iron"], (base_hours * occupant_factor).clip(0.08, 2.5), 0
        )
        df["iron_real_efficiency_factor"] = 1.0

        # 2. Electric Kettle (45%) - AI Pattern Learning
        df["has_electric_kettle"] = (np.random.random(self.n) < 0.45).astype(int)
        df["kettle_usage_pattern"] = np.where(
            df["has_electric_kettle"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.15, 0.35, 0.40, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(3, 8, self.n),  # Occasional tea/coffee
            "light": np.random.uniform(8, 15, self.n),  # 1-2 times/day
            "moderate": np.random.uniform(15, 25, self.n),  # 3-4 times/day
            "heavy": np.random.uniform(25, 40, self.n),  # Frequent use
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(df["kettle_usage_pattern"] == pattern, mins, base_mins)

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.06
        df["kettle_real_effective_hours"] = np.where(
            df["has_electric_kettle"],
            ((base_mins * occupant_factor) / 60).clip(0.05, 0.8),
            0,
        )
        df["kettle_real_efficiency_factor"] = 1.0

        # 3. Induction (65%) - AI Pattern Learning
        df["has_induction"] = (np.random.random(self.n) < 0.65).astype(int)
        df["induction_usage_pattern"] = np.where(
            df["has_induction"],
            np.random.choice(
                ["light", "moderate", "heavy", "very_heavy"],
                size=self.n,
                p=[0.25, 0.45, 0.25, 0.05],
            ),
            "unknown",
        )
        # Pattern-based hour ranges
        pattern_hours_map = {
            "light": np.random.uniform(0.3, 0.8, self.n),  # Backup cooking
            "moderate": np.random.uniform(0.8, 1.5, self.n),  # Regular use
            "heavy": np.random.uniform(1.5, 2.5, self.n),  # Primary cooking
            "very_heavy": np.random.uniform(2.5, 4.0, self.n),  # All meals
        }
        base_hours = np.zeros(self.n)
        for pattern, hours in pattern_hours_map.items():
            base_hours = np.where(
                df["induction_usage_pattern"] == pattern, hours, base_hours
            )

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.08
        df["induction_real_effective_hours"] = np.where(
            df["has_induction"], (base_hours * occupant_factor).clip(0.3, 4.5), 0
        )
        df["induction_real_efficiency_factor"] = 1.0

        # 4. PC/Desktop (55%)
        df["has_computer"] = (np.random.random(self.n) < 0.55).astype(int)

        # Add usage pattern for desktop
        df["desktop_usage_pattern"] = np.where(
            df["has_computer"],
            np.random.choice(
                ["light", "moderate", "heavy", "always"],
                size=self.n,
                p=[0.30, 0.40, 0.25, 0.05],
            ),
            "none",
        )

        # Generate hours based on pattern
        pc_hours = np.where(
            df["desktop_usage_pattern"] == "light",
            np.random.uniform(1, 2, self.n),
            np.where(
                df["desktop_usage_pattern"] == "moderate",
                np.random.uniform(3, 5, self.n),
                np.where(
                    df["desktop_usage_pattern"] == "heavy",
                    np.random.uniform(6, 10, self.n),
                    np.where(
                        df["desktop_usage_pattern"] == "always",
                        np.random.uniform(20, 24, self.n),
                        0,
                    ),
                ),
            ),
        )

        df["desktop_real_effective_hours"] = np.where(df["has_computer"], pc_hours, 0)
        df["desktop_real_efficiency_factor"] = 1.0

        # Calc kWh
        df["iron_kwh"] = (1000 * df["iron_real_effective_hours"] * 30) / 1000
        df["kettle_kwh"] = (1500 * df["kettle_real_effective_hours"] * 30) / 1000
        df["induction_kwh"] = (2000 * df["induction_real_effective_hours"] * 30) / 1000
        df["desktop_kwh"] = (250 * df["desktop_real_effective_hours"] * 30) / 1000

        return df

    def generate_kitchen_others(self, df):
        # Microwave (30%) - AI Pattern Learning
        df["has_microwave"] = (np.random.random(self.n) < 0.30).astype(int)
        df["microwave_usage_pattern"] = np.where(
            df["has_microwave"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.15, 0.40, 0.35, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(3, 8, self.n),  # Occasional reheating
            "light": np.random.uniform(8, 15, self.n),  # Few times/week
            "moderate": np.random.uniform(15, 25, self.n),  # Daily usage
            "heavy": np.random.uniform(25, 40, self.n),  # Multiple daily uses
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(
                df["microwave_usage_pattern"] == pattern, mins, base_mins
            )

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.05
        df["microwave_real_effective_hours"] = np.where(
            df["has_microwave"], ((base_mins * occupant_factor) / 60).clip(0.05, 0.8), 0
        )
        df["microwave_real_efficiency_factor"] = 1.0

        # Mixer (95%) - AI Pattern Learning
        df["has_mixer"] = (np.random.random(self.n) < 0.95).astype(int)
        df["mixer_usage_pattern"] = np.where(
            df["has_mixer"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.10, 0.30, 0.45, 0.15],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(5, 10, self.n),  # Occasional use
            "light": np.random.uniform(10, 20, self.n),  # Few times/week
            "moderate": np.random.uniform(20, 35, self.n),  # Daily grinding
            "heavy": np.random.uniform(35, 50, self.n),  # Heavy kitchen work
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(df["mixer_usage_pattern"] == pattern, mins, base_mins)

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.06
        df["mixer_real_effective_hours"] = np.where(
            df["has_mixer"], ((base_mins * occupant_factor) / 60).clip(0.08, 1.0), 0
        )
        df["mixer_real_efficiency_factor"] = 1.0

        # Rice Cooker (20%) - AI Pattern Learning
        df["has_rice_cooker"] = (np.random.random(self.n) < 0.20).astype(int)
        df["rice_cooker_usage_pattern"] = np.where(
            df["has_rice_cooker"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.15, 0.35, 0.40, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(15, 25, self.n),  # Once/twice a week
            "light": np.random.uniform(20, 30, self.n),  # Few times/week
            "moderate": np.random.uniform(30, 40, self.n),  # Daily cooking
            "heavy": np.random.uniform(40, 60, self.n),  # Multiple meals
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(
                df["rice_cooker_usage_pattern"] == pattern, mins, base_mins
            )

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.07
        df["rice_cooker_real_effective_hours"] = np.where(
            df["has_rice_cooker"],
            ((base_mins * occupant_factor) / 60).clip(0.25, 1.2),
            0,
        )
        df["rice_cooker_real_efficiency_factor"] = 1.0

        # Toaster (10%) - AI Pattern Learning
        df["has_toaster"] = (np.random.random(self.n) < 0.10).astype(int)
        df["toaster_usage_pattern"] = np.where(
            df["has_toaster"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.25, 0.40, 0.25, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(2, 5, self.n),  # Weekend breakfast
            "light": np.random.uniform(5, 10, self.n),  # Few times/week
            "moderate": np.random.uniform(10, 15, self.n),  # Daily breakfast
            "heavy": np.random.uniform(15, 25, self.n),  # Multiple daily use
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(
                df["toaster_usage_pattern"] == pattern, mins, base_mins
            )

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.04
        df["toaster_real_effective_hours"] = np.where(
            df["has_toaster"], ((base_mins * occupant_factor) / 60).clip(0.03, 0.5), 0
        )
        df["toaster_real_efficiency_factor"] = 1.0

        # Food Processor (15%) - AI Pattern Learning
        df["has_food_processor"] = (np.random.random(self.n) < 0.15).astype(int)
        df["food_processor_usage_pattern"] = np.where(
            df["has_food_processor"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.20, 0.40, 0.30, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(5, 10, self.n),  # Occasional prep
            "light": np.random.uniform(10, 18, self.n),  # Weekly usage
            "moderate": np.random.uniform(18, 30, self.n),  # Regular cooking
            "heavy": np.random.uniform(30, 45, self.n),  # Daily food prep
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(
                df["food_processor_usage_pattern"] == pattern, mins, base_mins
            )

        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.05
        df["food_processor_real_effective_hours"] = np.where(
            df["has_food_processor"],
            ((base_mins * occupant_factor) / 60).clip(0.08, 0.9),
            0,
        )
        df["food_processor_real_efficiency_factor"] = 1.0

        # Calc kWh
        df["microwave_kwh"] = (1200 * df["microwave_real_effective_hours"] * 30) / 1000
        df["mixer_kwh"] = (750 * df["mixer_real_effective_hours"] * 30) / 1000
        df["rice_cooker_kwh"] = (
            600 * df["rice_cooker_real_effective_hours"] * 30
        ) / 1000
        df["toaster_kwh"] = (800 * df["toaster_real_effective_hours"] * 30) / 1000
        df["food_processor_kwh"] = (
            600 * df["food_processor_real_effective_hours"] * 30
        ) / 1000
        return df

    def generate_personal_others(self, df):
        # Laptop (40%) - AI Pattern Learning
        df["has_laptop"] = (np.random.random(self.n) < 0.40).astype(int)
        df["laptop_usage_pattern"] = np.where(
            df["has_laptop"],
            np.random.choice(
                ["light", "moderate", "heavy", "always"],
                size=self.n,
                p=[0.30, 0.40, 0.25, 0.05],
            ),
            "unknown",
        )
        # Pattern-based hour ranges (work/study related)
        pattern_hours_map = {
            "light": np.random.uniform(1, 3, self.n),  # Light browsing
            "moderate": np.random.uniform(3, 6, self.n),  # Regular work
            "heavy": np.random.uniform(6, 12, self.n),  # Professional use
            "always": np.random.uniform(12, 20, self.n),  # WFH/Developers
        }
        base_hours = np.zeros(self.n)
        for pattern, hours in pattern_hours_map.items():
            base_hours = np.where(
                df["laptop_usage_pattern"] == pattern, hours, base_hours
            )

        # Occupancy influence: More people = more usage
        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.03
        df["laptop_real_effective_hours"] = np.where(
            df["has_laptop"], (base_hours * occupant_factor).clip(0.5, 20), 0
        )
        df["laptop_real_efficiency_factor"] = 1.0

        # Hair Dryer (20%) - AI Pattern Learning
        df["has_hair_dryer"] = (np.random.random(self.n) < 0.20).astype(int)
        df["hair_dryer_usage_pattern"] = np.where(
            df["has_hair_dryer"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.30, 0.40, 0.20, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(2, 5, self.n),  # Once/twice a week
            "light": np.random.uniform(5, 10, self.n),  # Few times a week
            "moderate": np.random.uniform(10, 20, self.n),  # Daily short use
            "heavy": np.random.uniform(20, 40, self.n),  # Daily long hair
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(
                df["hair_dryer_usage_pattern"] == pattern, mins, base_mins
            )

        # Occupancy influence (more family members = more usage)
        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.08
        df["hair_dryer_real_effective_hours"] = np.where(
            df["has_hair_dryer"],
            ((base_mins * occupant_factor) / 60).clip(0.03, 0.8),
            0,
        )
        df["hair_dryer_real_efficiency_factor"] = 1.0

        # Vacuum (15%) - AI Pattern Learning
        df["has_vacuum"] = (np.random.random(self.n) < 0.15).astype(int)
        df["vacuum_usage_pattern"] = np.where(
            df["has_vacuum"],
            np.random.choice(
                ["rarely", "light", "moderate", "heavy"],
                size=self.n,
                p=[0.20, 0.40, 0.30, 0.10],
            ),
            "unknown",
        )
        # Pattern-based minute ranges
        pattern_mins_map = {
            "rarely": np.random.uniform(5, 15, self.n),  # Once/twice a month
            "light": np.random.uniform(10, 20, self.n),  # Weekly cleaning
            "moderate": np.random.uniform(20, 40, self.n),  # 2-3 times/week
            "heavy": np.random.uniform(40, 60, self.n),  # Daily cleaning
        }
        base_mins = np.zeros(self.n)
        for pattern, mins in pattern_mins_map.items():
            base_mins = np.where(df["vacuum_usage_pattern"] == pattern, mins, base_mins)

        # Occupancy influence (larger households need more cleaning)
        occupant_factor = 1 + (df["n_occupants"] - 4) * 0.08
        df["vacuum_real_effective_hours"] = np.where(
            df["has_vacuum"], ((base_mins * occupant_factor) / 60).clip(0.08, 1.2), 0
        )
        df["vacuum_real_efficiency_factor"] = 1.0

        # Calc kWh
        df["laptop_kwh"] = (60 * df["laptop_real_effective_hours"] * 30) / 1000
        df["hair_dryer_kwh"] = (
            1200 * df["hair_dryer_real_effective_hours"] * 30
        ) / 1000
        df["vacuum_kwh"] = (1400 * df["vacuum_real_effective_hours"] * 30) / 1000
        return df

    def generate_lights_data(self, df):
        # AI Pattern Learning for all light types
        # LED (100% penetration)
        df["has_led_lights"] = 1
        df["led_lights_usage_pattern"] = np.random.choice(
            ["evening", "morning_evening", "most", "all"],
            size=self.n,
            p=[0.20, 0.45, 0.30, 0.05],
        )

        # Pattern-based hour ranges
        pattern_hours_map = {
            "evening": np.random.uniform(3, 5, self.n),  # Evening only
            "morning_evening": np.random.uniform(5, 8, self.n),  # Morning + Evening
            "most": np.random.uniform(8, 12, self.n),  # Most of day
            "all": np.random.uniform(12, 18, self.n),  # Nearly 24/7
        }
        led_hours = np.zeros(self.n)
        for pattern, hours_range in pattern_hours_map.items():
            led_hours = np.where(
                df["led_lights_usage_pattern"] == pattern, hours_range, led_hours
            )

        df["led_lights_real_effective_hours"] = led_hours
        df["led_lights_real_efficiency_factor"] = 1.0

        # CFL (50% penetration) - shares same pattern logic
        df["has_cfl_lights"] = (np.random.random(self.n) < 0.50).astype(int)
        df["cfl_lights_usage_pattern"] = np.where(
            df["has_cfl_lights"],
            df["led_lights_usage_pattern"],  # Same pattern as LED
            "unknown",
        )
        df["cfl_lights_real_effective_hours"] = np.where(
            df["has_cfl_lights"], led_hours, 0
        )
        df["cfl_lights_real_efficiency_factor"] = 1.0

        # Tube (60% penetration) - shares same pattern logic
        df["has_tube_lights"] = (np.random.random(self.n) < 0.60).astype(int)
        df["tube_lights_usage_pattern"] = np.where(
            df["has_tube_lights"],
            df["led_lights_usage_pattern"],  # Same pattern as LED
            "unknown",
        )
        df["tube_lights_real_effective_hours"] = np.where(
            df["has_tube_lights"], led_hours, 0
        )
        df["tube_lights_real_efficiency_factor"] = 1.0

        df["led_lights_kwh"] = (
            9 * df["led_lights_real_effective_hours"] * 5 * 30
        ) / 1000  # 5 LEDs avg
        df["cfl_lights_kwh"] = (
            18 * df["cfl_lights_real_effective_hours"] * 2 * 30
        ) / 1000
        df["tube_lights_kwh"] = (
            40 * df["tube_lights_real_effective_hours"] * 2 * 30
        ) / 1000
        return df

    def generate(self):
        df = self.generate_demographics()
        df = self.generate_ac_data(df)
        df = self.generate_fridge_data(df)
        df = self.generate_fan_data(df)
        df = self.generate_tv_data(df)
        df = self.generate_wm_data(df)
        df = self.generate_pump_data(df)
        df = self.generate_geyser_data(df)
        df = self.generate_misc_data(df)
        df = self.generate_kitchen_others(df)
        df = self.generate_personal_others(df)
        df = self.generate_lights_data(df)

        # Sum Total Predictor
        items = [
            "ac_kwh",
            "fridge_kwh",
            "ceiling_fan_kwh",
            "television_kwh",
            "washing_machine_kwh",
            "water_pump_kwh",
            "water_heater_kwh",
            "iron_kwh",
            "kettle_kwh",
            "induction_kwh",
            "desktop_kwh",
            "microwave_kwh",
            "mixer_kwh",
            "rice_cooker_kwh",
            "toaster_kwh",
            "food_processor_kwh",
            "laptop_kwh",
            "hair_dryer_kwh",
            "vacuum_kwh",
            "led_lights_kwh",
            "cfl_lights_kwh",
            "tube_lights_kwh",
        ]
        df["total_kwh_monthly"] = df[items].sum(axis=1) + np.random.normal(5, 2, self.n)

        return df


if __name__ == "__main__":
    sim = KeralaRealWorldSimulator()
    df = sim.generate()
    df.to_csv("kerala_smartwatt_ai.csv", index=False)
    print("✅  Dataset Generated: kerala_smartwatt_ai.csv")
