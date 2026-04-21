"""
UI to Backend Field Mapping Checker
Validates that UI field names match backend schemas
"""

# UI field names (from usageForms.ts)
UI_FIELDS = {
    "ac": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["ac_star", "ac_tonnage", "ac_type", "ac_age"],
        "derived": ["ac_hours", "ac_pattern", "ac_usage_pattern"],
    },
    "fridge": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["fridge_star", "fridge_capacity", "fridge_type", "fridge_age"],
        "derived": ["fridge_hours", "fridge_pattern"],
    },
    "wm": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["wm_type", "wm_capacity", "wm_star", "wm_age"],
        "derived": ["wm_hours", "wm_pattern", "wm_cycles_per_week"],
    },
    "geyser": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["geyser_type", "geyser_capacity", "geyser_age"],
        "derived": ["geyser_hours", "geyser_pattern"],
    },
    "fan": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["fan_type", "num_fans"],
        "derived": ["fan_hours", "fan_pattern"],
    },
    "tv": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["tv_type", "tv_size"],
        "derived": ["tv_hours", "tv_pattern"],
    },
    "pump": {
        "base": ["n_occupants", "season", "location_type"],
        "specific": ["pump_hp"],
        "derived": ["pump_hours", "pump_pattern"],
    },
}

# Backend expected fields (from schemas.py)
BACKEND_SCHEMAS = {
    "ACInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": [
            "ac_tonnage",
            "ac_star_rating",
            "ac_type",
            "ac_usage_pattern",
            "ac_hours_per_day",
        ],
        "optional": ["num_ac_units"],
    },
    "FridgeInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": [
            "fridge_capacity_liters",
            "fridge_age_years",
            "fridge_star_rating",
            "fridge_type",
        ],
        "optional": ["fridge_hours_per_day"],
    },
    "WashingMachineInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": [
            "wm_capacity_kg",
            "wm_star_rating",
            "wm_type",
            "wm_cycles_per_week",
        ],
        "optional": [],
    },
    "WaterHeaterInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": [
            "water_heater_capacity_liters",
            "water_heater_type",
            "water_heater_usage_hours",
        ],
        "optional": [],
    },
    "CeilingFanInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": ["num_ceiling_fans", "fan_type", "fan_hours_per_day"],
        "optional": ["fan_star_rating"],
    },
    "TelevisionInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": ["tv_size_inches", "tv_type", "tv_hours_per_day"],
        "optional": ["num_televisions"],
    },
    "WaterPumpInput": {
        "base": ["n_occupants", "season", "location_type"],
        "required": ["water_pump_hp", "water_pump_usage_hours_per_day"],
        "optional": [],
    },
}

# Field name transformations (UI -> Backend)
FIELD_MAPPINGS = {
    # AC
    "ac_star": "ac_star_rating",
    "ac_hours": "ac_hours_per_day",
    # Fridge
    "fridge_star": "fridge_star_rating",
    "fridge_capacity": "fridge_capacity_liters",
    "fridge_age": "fridge_age_years",
    "fridge_hours": "fridge_hours_per_day",
    # Washing Machine
    "wm_star": "wm_star_rating",
    "wm_capacity": "wm_capacity_kg",
    # Geyser/Water Heater
    "geyser_type": "water_heater_type",
    "geyser_capacity": "water_heater_capacity_liters",
    "geyser_hours": "water_heater_usage_hours",
    # Fan
    "num_fans": "num_ceiling_fans",
    "fan_hours": "fan_hours_per_day",
    # TV
    "tv_size": "tv_size_inches",
    "tv_hours": "tv_hours_per_day",
    # Pump
    "pump_hp": "water_pump_hp",
    "pump_hours": "water_pump_usage_hours_per_day",
}


def check_field_mappings():
    print("=" * 80)
    print("UI TO BACKEND FIELD MAPPING VALIDATION")
    print("=" * 80)

    issues = []
    warnings = []

    # Check AC
    print("\n[AC / AIR CONDITIONER]")
    print("-" * 80)
    ui_fields = UI_FIELDS["ac"]
    backend = BACKEND_SCHEMAS["ACInput"]

    print("UI Fields:")
    all_ui = ui_fields["base"] + ui_fields["specific"] + ui_fields["derived"]
    for field in all_ui:
        backend_field = FIELD_MAPPINGS.get(field, field)
        in_backend = backend_field in (
            backend["base"] + backend["required"] + backend["optional"]
        )
        status = "[OK]" if in_backend else "[MISSING]"
        print(f"  {status} {field:25s} -> {backend_field:30s}")
        if not in_backend and field not in ["ac_age", "ac_pattern"]:
            issues.append(f"AC: {field} -> {backend_field} not in backend schema")

    print("\nBackend Required Fields:")
    for field in backend["required"]:
        # Reverse lookup
        ui_field = next((k for k, v in FIELD_MAPPINGS.items() if v == field), field)
        in_ui = ui_field in all_ui or field in all_ui
        status = "[OK]" if in_ui else "[MISSING]"
        print(f"  {status} {field:30s} <- {ui_field:25s}")
        if not in_ui:
            warnings.append(f"AC: Backend expects {field} but not in UI")

    # Check Fridge
    print("\n[FRIDGE / REFRIGERATOR]")
    print("-" * 80)
    ui_fields = UI_FIELDS["fridge"]
    backend = BACKEND_SCHEMAS["FridgeInput"]

    print("UI Fields:")
    all_ui = ui_fields["base"] + ui_fields["specific"] + ui_fields["derived"]
    for field in all_ui:
        backend_field = FIELD_MAPPINGS.get(field, field)
        in_backend = backend_field in (
            backend["base"] + backend["required"] + backend["optional"]
        )
        status = "[OK]" if in_backend else "[MISSING]"
        print(f"  {status} {field:25s} -> {backend_field:30s}")
        if not in_backend and field not in ["fridge_pattern"]:
            issues.append(f"Fridge: {field} -> {backend_field} not in backend schema")

    print("\nBackend Required Fields:")
    for field in backend["required"]:
        ui_field = next((k for k, v in FIELD_MAPPINGS.items() if v == field), field)
        in_ui = ui_field in all_ui or field in all_ui
        status = "[OK]" if in_ui else "[MISSING]"
        print(f"  {status} {field:30s} <- {ui_field:25s}")
        if not in_ui:
            warnings.append(f"Fridge: Backend expects {field} but not in UI")

    # Check Washing Machine
    print("\n[WASHING MACHINE]")
    print("-" * 80)
    ui_fields = UI_FIELDS["wm"]
    backend = BACKEND_SCHEMAS["WashingMachineInput"]

    print("UI Fields:")
    all_ui = ui_fields["base"] + ui_fields["specific"] + ui_fields["derived"]
    for field in all_ui:
        backend_field = FIELD_MAPPINGS.get(field, field)
        in_backend = backend_field in (
            backend["base"] + backend["required"] + backend["optional"]
        )
        status = "[OK]" if in_backend else "[MISSING]"
        print(f"  {status} {field:25s} -> {backend_field:30s}")
        if not in_backend and field not in ["wm_age", "wm_hours", "wm_pattern"]:
            issues.append(f"WM: {field} -> {backend_field} not in backend schema")

    print("\nBackend Required Fields:")
    for field in backend["required"]:
        ui_field = next((k for k, v in FIELD_MAPPINGS.items() if v == field), field)
        in_ui = ui_field in all_ui or field in all_ui
        status = "[OK]" if in_ui else "[MISSING]"
        print(f"  {status} {field:30s} <- {ui_field:25s}")
        if not in_ui:
            warnings.append(f"WM: Backend expects {field} but not in UI")

    # Check Water Heater
    print("\n[WATER HEATER / GEYSER]")
    print("-" * 80)
    ui_fields = UI_FIELDS["geyser"]
    backend = BACKEND_SCHEMAS["WaterHeaterInput"]

    print("UI Fields:")
    all_ui = ui_fields["base"] + ui_fields["specific"] + ui_fields["derived"]
    for field in all_ui:
        backend_field = FIELD_MAPPINGS.get(field, field)
        in_backend = backend_field in (
            backend["base"] + backend["required"] + backend["optional"]
        )
        status = "[OK]" if in_backend else "[MISSING]"
        print(f"  {status} {field:25s} -> {backend_field:30s}")
        if not in_backend and field not in ["geyser_age", "geyser_pattern"]:
            issues.append(f"Geyser: {field} -> {backend_field} not in backend schema")

    print("\nBackend Required Fields:")
    for field in backend["required"]:
        ui_field = next((k for k, v in FIELD_MAPPINGS.items() if v == field), field)
        in_ui = ui_field in all_ui or field in all_ui
        status = "[OK]" if in_ui else "[MISSING]"
        print(f"  {status} {field:30s} <- {ui_field:25s}")
        if not in_ui:
            warnings.append(f"Geyser: Backend expects {field} but not in UI")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if not issues and not warnings:
        print("[SUCCESS] All UI fields map correctly to backend schemas!")
    else:
        if issues:
            print(f"\n[ISSUES] {len(issues)} UI fields not in backend:")
            for issue in issues:
                print(f"  - {issue}")

        if warnings:
            print(f"\n[WARNINGS] {len(warnings)} backend fields not in UI:")
            for warning in warnings:
                print(f"  - {warning}")

    print("\n" + "=" * 80)
    print("KEY FIELD TRANSFORMATIONS")
    print("=" * 80)
    print("""
UI Field Name           Backend Expected Name
-------------           ---------------------
ac_star          ->     ac_star_rating
ac_hours         ->     ac_hours_per_day
fridge_star      ->     fridge_star_rating
fridge_capacity  ->     fridge_capacity_liters
fridge_age       ->     fridge_age_years
wm_star          ->     wm_star_rating
wm_capacity      ->     wm_capacity_kg
geyser_type      ->     water_heater_type
geyser_capacity  ->     water_heater_capacity_liters
pump_hp          ->     water_pump_hp
tv_size          ->     tv_size_inches
num_fans         ->     num_ceiling_fans

IMPORTANT: Frontend must transform field names before sending to API!
    """)


if __name__ == "__main__":
    check_field_mappings()
