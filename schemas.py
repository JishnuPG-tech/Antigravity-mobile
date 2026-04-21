from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, validator


# --- Base Models ---
class BaseApplianceInput(BaseModel):
    season: str = Field(
        "monsoon",
        description="Current season (summer, monsoon, winter)",
        pattern="^(summer|monsoon|winter)$",
    )
    location_type: str = Field(
        "urban", description="Location type (urban, rural)", pattern="^(urban|rural)$"
    )
    n_occupants: int = Field(
        4, ge=1, le=10, description="Number of people in the household"
    )


# --- Specific Appliance Models ---


class ACInput(BaseApplianceInput):
    ac_tonnage: float = Field(..., ge=0.5, le=5.0)
    ac_star_rating: int = Field(..., ge=1, le=5)
    num_ac_units: int = Field(1, ge=1)
    ac_type: str = Field(..., pattern="^(split|window|inverter)$")
    ac_age_years: str = Field("unknown", description="Age of AC unit")
    ac_usage_pattern: str = Field(
        "moderate", pattern="^(heavy|moderate|light|rare|short|long|night)$"
    )
    ac_hours_per_day: float = Field(..., ge=0, le=24)
    ac_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class FridgeInput(BaseApplianceInput):
    fridge_capacity_liters: float = Field(..., ge=50, le=1000)
    fridge_age_years: Union[float, str] = Field(
        ..., description="Age in years (numeric) or range (e.g., '3-5', '10+', '<1')"
    )
    fridge_star_rating: int = Field(..., ge=1, le=5)
    fridge_type: Literal["frost_free", "direct_cool", "side_by_side"]
    refrigerator_usage_pattern: Literal["manual", "light", "normal", "always"] = (
        "always"
    )
    fridge_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class WashingMachineInput(BaseApplianceInput):
    wm_capacity_kg: float = Field(..., ge=2, le=20)
    wm_star_rating: int = Field(..., ge=1, le=5)
    wm_type: Literal["top_load", "front_load", "semi_automatic"]
    wm_cycles_per_week: float = Field(..., ge=0, le=50)
    washing_machine_hours: Optional[float] = Field(
        None, ge=0, le=24
    )  # Explicit override


class CeilingFanInput(BaseApplianceInput):
    num_ceiling_fans: int = Field(..., ge=1)
    fan_type: Optional[Literal["standard", "bldc", "high_speed"]] = "standard"
    fan_usage_pattern: Literal["rarely", "few", "most", "all"] = "most"
    ceiling_fan_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class LightingInput(BaseApplianceInput):
    count: Optional[int] = Field(None, ge=1, alias="num_units")

    # Pattern fields
    num_led_lights: Optional[int] = None
    led_lights_usage_pattern: Optional[
        Literal["evening", "morning_evening", "most", "all"]
    ] = "evening"
    led_lights_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override

    num_cfl_bulbs: Optional[int] = None
    cfl_lights_usage_pattern: Optional[
        Literal["evening", "morning_evening", "most", "all"]
    ] = "evening"
    cfl_lights_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override

    num_tube_lights: Optional[int] = None
    tube_lights_usage_pattern: Optional[
        Literal["evening", "morning_evening", "most", "all"]
    ] = "evening"
    tube_lights_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class TelevisionInput(BaseApplianceInput):
    tv_size_inches: float = Field(..., ge=10, le=100)
    num_televisions: int = Field(1, ge=1)
    television_type: Literal["LED", "LCD", "CRT", "OLED", "QLED"]
    television_usage_pattern: Literal["light", "moderate", "heavy", "always"] = (
        "moderate"
    )
    television_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class WaterHeaterInput(BaseApplianceInput):
    water_heater_capacity_liters: float = Field(..., ge=1, le=100)
    water_heater_type: Literal["instant", "storage", "gas", "solar"]
    geyser_usage_pattern: Literal["minimal", "light", "moderate", "heavy"] = "light"
    water_heater_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class WaterPumpInput(BaseApplianceInput):
    water_pump_hp: float = Field(..., ge=0.5, le=5.0)
    pump_usage_pattern: Literal[
        "minimal", "light", "moderate", "heavy", "rare", "normal", "frequent"
    ] = "moderate"
    water_pump_hours: Optional[float] = Field(None, ge=0, le=24)  # Explicit override


class KitchenApplianceInput(BaseApplianceInput):
    wattage: Optional[float] = None
    usage_minutes_per_day: Optional[float] = None
    usage_hours_per_day: Optional[float] = None
    kitchen_appliance_hours: Optional[float] = None  # Explicit override


class MixerInput(BaseApplianceInput):
    mixer_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "moderate"
    mixer_grinder_wattage: Optional[float] = 750
    mixer_hours: Optional[float] = Field(None, ge=0, le=24)


class MicrowaveInput(BaseApplianceInput):
    microwave_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    microwave_capacity_liters: Optional[float] = 20
    microwave_hours: Optional[float] = Field(None, ge=0, le=24)


class KettleInput(BaseApplianceInput):
    kettle_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    kettle_hours: Optional[float] = Field(None, ge=0, le=24)


class InductionInput(BaseApplianceInput):
    induction_usage_pattern: Literal["light", "moderate", "heavy", "very_heavy"] = (
        "moderate"
    )
    induction_hours: Optional[float] = Field(None, ge=0, le=24)


class RiceCookerInput(BaseApplianceInput):
    rice_cooker_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    rice_cooker_hours: Optional[float] = Field(None, ge=0, le=24)


class ToasterInput(BaseApplianceInput):
    toaster_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    toaster_hours: Optional[float] = Field(None, ge=0, le=24)


class FoodProcessorInput(BaseApplianceInput):
    food_processor_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = (
        "light"
    )
    food_processor_hours: Optional[float] = Field(None, ge=0, le=24)


class HairDryerInput(BaseApplianceInput):
    hair_dryer_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    hair_dryer_hours: Optional[float] = Field(None, ge=0, le=24)


class VacuumInput(BaseApplianceInput):
    vacuum_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    vacuum_hours: Optional[float] = Field(None, ge=0, le=24)


class IronInput(BaseApplianceInput):
    iron_usage_pattern: Literal["rarely", "light", "moderate", "heavy"] = "light"
    iron_hours: Optional[float] = Field(None, ge=0, le=24)


class DesktopInput(BaseApplianceInput):
    desktop_usage_pattern: Literal["light", "moderate", "heavy", "always"] = "moderate"
    desktop_hours: Optional[float] = Field(None, ge=0, le=24)


class LaptopInput(BaseApplianceInput):
    laptop_usage_pattern: Literal["light", "moderate", "heavy", "always"] = "moderate"
    laptop_hours: Optional[float] = Field(None, ge=0, le=24)


# --- Mapping Helper ---
# Maps frontend string "ac" -> ACInput class
MODEL_MAPPING = {
    "ac": ACInput,
    "fridge": FridgeInput,
    "refrigerator": FridgeInput,
    "washing_machine": WashingMachineInput,
    "ceiling_fan": CeilingFanInput,
    "fan": CeilingFanInput,
    "led_light": LightingInput,
    "cfl_bulb": LightingInput,
    "tube_light": LightingInput,
    "television": TelevisionInput,
    "tv": TelevisionInput,
    "water_heater": WaterHeaterInput,
    "geyser": WaterHeaterInput,
    "water_pump": WaterPumpInput,
    "pump": WaterPumpInput,
    "iron": IronInput,
    "desktop": DesktopInput,
    "laptop": LaptopInput,
    "mixer_grinder": MixerInput,
    "mixer": MixerInput,
    "microwave": MicrowaveInput,
    "kettle": KettleInput,
    "induction": InductionInput,
    "rice_cooker": RiceCookerInput,
    "toaster": ToasterInput,
    "food_processor": FoodProcessorInput,
    "hair_dryer": HairDryerInput,
    "vacuum": VacuumInput,
    # Fallbacks use generic KitchenApplianceInput
}
