"""
Shared Physics Constants for SmartWatt Hybrid 0
This file is the "Ground Truth".
When the AI feels unsure (or for simple devices like Irons),
it checks this file to know the correct Wattage.
"""

PHYSICS_DEFAULTS = {
    # MAJOR APPLIANCES
    "ac": {
        "reference_watts": 1000,  # Per Ton (e.g. 1.5 Ton = 1500W base)
        "default_hours": 8,
    },
    "fridge": {
        "reference_watts": 40,  # Baseline active draw (approx for 250L) - scaling handled by logic
        "default_hours": 24,
    },
    "washing_machine": {
        "reference_watts": 500,  # Average cycle power
        "default_hours": 1.0,  # Per day approx (derived from cycles)
    },
    "water_heater": {"reference_watts": 2000, "default_hours": 1.5},
    "water_pump": {"reference_watts": 746, "default_hours": 0.5},  # 1 HP
    "television": {
        "reference_watts": 100,  # Approx for 43-50 inch LED
        "default_hours": 4,
    },
    # LIGHTING & FANS
    "ceiling_fan": {"reference_watts": 75, "default_hours": 12},
    "led_light": {"reference_watts": 10, "default_hours": 6},
    "tube_light": {"reference_watts": 40, "default_hours": 6},
    "cfl_bulb": {"reference_watts": 20, "default_hours": 6},
    # KITCHEN
    "microwave": {"reference_watts": 1200, "default_hours": 0.3},
    "mixer_grinder": {"reference_watts": 750, "default_hours": 0.5},
    "kettle": {"reference_watts": 1500, "default_hours": 0.2},
    "induction": {"reference_watts": 1500, "default_hours": 1.0},  # Variable 1200-2000
    "rice_cooker": {"reference_watts": 700, "default_hours": 0.5},
    # OTHER
    "desktop": {"reference_watts": 200, "default_hours": 4},
    "laptop": {"reference_watts": 50, "default_hours": 4},
    "iron": {"reference_watts": 1000, "default_hours": 0.2},
}
