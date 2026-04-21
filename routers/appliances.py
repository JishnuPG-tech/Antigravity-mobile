import concurrent.futures
import json
from datetime import datetime
from typing import Any, Dict, List, Union

from fastapi import APIRouter, HTTPException
# Import Core Logic and Schemas
from predictor import get_predictor
from pydantic import BaseModel, Field
from schemas import (MODEL_MAPPING, ACInput, BaseApplianceInput,
                     CeilingFanInput, FridgeInput, KitchenApplianceInput,
                     LightingInput, TelevisionInput, WashingMachineInput,
                     WaterHeaterInput, WaterPumpInput)

router = APIRouter()
predictor = get_predictor()

from simulation_service import SimulationService


# --- DEBUG LOGGER ---
def log_user_input(appliance_name: str, details: Dict, total_bill: float):
    """Log all user inputs for debugging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "appliance": appliance_name,
        "total_bill": total_bill,
        "inputs": details,
    }

    # Print to console with clear formatting
    print("\n" + "=" * 80)
    print(f"🔍 DEBUG: USER INPUT CAPTURED at {timestamp}")
    print("=" * 80)
    print(f"📱 Appliance: {appliance_name}")
    print(f"💰 Total Bill: {total_bill} kWh")
    print(f"📝 Input Details:")
    for key, value in details.items():
        print(f"   • {key}: {value}")
    print("=" * 80 + "\n")

    # Also write to file for persistent logging
    try:
        with open("user_inputs_debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, indent=2) + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")


# --- PYDANTIC MODELS FOR API REQUEST ---


class ApplianceRequest(BaseModel):
    appliance_name: str
    # We accept a Dict first, then validate it dynamically based on name
    details: Dict[str, Any]
    total_bill: float = Field(
        ..., ge=0, description="Total bill amount cannot be negative"
    )

    def validate_details(self):
        """Dynamic validation based on appliance name"""
        key = self.appliance_name.lower().replace(" ", "_")
        if key == "air_conditioner":
            key = "ac"
        if key == "refrigerator":
            key = "fridge"

        ModelClass = MODEL_MAPPING.get(key, BaseApplianceInput)

        # We try to strict validate. If it fails, Pydantic raises error.
        # This ensures we don't pass garbage to the AI.
        return ModelClass(**self.details)


class BatchApplianceRequest(BaseModel):
    requests: List[ApplianceRequest]


class SimulationRequest(BaseModel):
    details: Dict[str, Any]
    total_bill: float


# Field mapper: Schema field names → Training column names
def map_schema_to_training_columns(details: Dict) -> Dict:
    """Convert API schema field names to training dataset column names"""
    field_mapping = {
        # Fridge
        "fridge_capacity_liters": "fridge_capacity",
        "fridge_age_years": "fridge_age",
        "fridge_hours_per_day": "fridge_hours",
        # Washing Machine
        "wm_capacity_kg": "wm_capacity",
        # Water Heater
        "water_heater_capacity_liters": "water_heater_capacity",
        "water_heater_usage_hours": "water_heater_hours",
        # AC
        "ac_hours_per_day": "ac_hours",
        # Fan
        "num_ceiling_fans": "num_fans",
        "fan_hours_per_day": "fan_hours",
        # TV
        "tv_size_inches": "tv_size",
        "num_televisions": "num_tv",
        "tv_hours_per_day": "tv_hours",
        "television_hours": "tv_hours",
        # Water Pump
        "water_pump_usage_hours_per_day": "water_pump_hours",
        # Usage Patterns (Frontend sends *_pattern, Model needs *_usage_pattern)
        "fan_pattern": "fan_usage_pattern",
        "ac_pattern": "ac_usage_pattern",
        "fridge_pattern": "refrigerator_usage_pattern",
        "tv_pattern": "television_usage_pattern",
        "wm_pattern": "wm_usage_pattern",
        "geyser_pattern": "geyser_usage_pattern",
        "led_pattern": "led_lights_usage_pattern",
        "cfl_pattern": "cfl_lights_usage_pattern",
        "tube_pattern": "tube_lights_usage_pattern",
        "pump_pattern": "pump_usage_pattern",
        "mixer_pattern": "mixer_usage_pattern",
        "microwave_pattern": "microwave_usage_pattern",
        "kettle_pattern": "kettle_usage_pattern",
        "induction_pattern": "induction_usage_pattern",
        "rice_cooker_pattern": "rice_cooker_usage_pattern",
        "toaster_pattern": "toaster_usage_pattern",
        "food_processor_pattern": "food_processor_usage_pattern",
        "iron_pattern": "iron_usage_pattern",
        "desktop_pattern": "desktop_usage_pattern",
        "laptop_pattern": "laptop_usage_pattern",
    }

    mapped_data = {}
    for key, value in details.items():
        # Use mapped name if exists, otherwise keep original
        mapped_key = field_mapping.get(key, key)
        mapped_data[mapped_key] = value

    return mapped_data


# Helper to bridge API requests to the AI Engine
def call_model(name: str, details: Dict, bill_total: float):
    # Map schema field names to training column names
    mapped_details = map_schema_to_training_columns(details)
    mapped_details["total_kwh_monthly"] = bill_total

    # 🧠 Apply AI-based range resolution AFTER field mapping
    # This ensures resolved values use correct column names
    from range_resolver import resolve_range_values

    mapped_details = resolve_range_values(mapped_details)

    return predictor.predict(name, [mapped_details])


@router.post("/predict-appliance")
def predict_usage(req: ApplianceRequest):
    """Runs the specific Neural Network for an appliance"""
    try:
        # 🔍 DEBUG: Log all user inputs
        log_user_input(req.appliance_name, req.details, req.total_bill)

        # 1. Enforce Strict Type Safety via Pydantic
        # This will raise an Exception if fields are missing (e.g. ac_tonnage)
        validated_model = req.validate_details()

        # 2. Convert back to dict for the legacy AI predictor (or update predictor to accept models later)
        # We trust the data now.
        # CRITICAL FIX: exclude_none=True prevents optional fields (like ac_hours=None)
        # from conflicting with mapped fields (like ac_hours_per_day -> ac_hours) during conversion.
        validated_data = validated_model.model_dump(exclude_none=True)

        # Standardize key (handle 'air_conditioner' vs 'ac')
        key = req.appliance_name.lower().replace(" ", "_")
        if key == "air_conditioner":
            key = "ac"
        if key == "refrigerator":
            key = "fridge"

        # Call Logic
        result = call_model(key, validated_data, req.total_bill)

        # Check source for debugging
        source = result.get("insights", {}).get("source", "Unknown")
        predicted_hours = result.get("insights", {}).get("predicted_hours", 0)
        predicted_kwh = result.get("prediction", 0)

        # Enhanced debug output
        print(f"✅ Predicted {key}:")
        print(f"   Source: {source}")
        print(f"   Hours: {predicted_hours}h")
        print(f"   kWh: {predicted_kwh:.2f}")

        return {
            "status": "success",
            "prediction": result["prediction"],
            "insights": result["insights"],
        }

    except Exception as e:
        print(f"Error predicting {req.appliance_name}: {e}")
        # Return error details if validation failed, so frontend devs know what's wrong
        if "validation error" in str(e).lower():
            return {"status": "error", "message": str(e), "prediction": 0.0}

        # Fallback to safe value only for non-validation errors
        return {"status": "fallback", "prediction": 15.0}


@router.post("/simulate-savings")
def simulate_savings(req: SimulationRequest):
    """
    This is the "Time Machine".
    It asks the AI: "What if I changed X?"
    For example: "What if I threw away my 10-year old fridge and bought a new one?"
    The AI re-runs the simulation and tells you how much money you'd save.
    """

    # Define a simple callback wrapper for call_model
    def model_predictor(name, details, bill):
        return call_model(name, details, bill)

    try:
        insights = SimulationService.run_simulation(
            req.details, req.total_bill, model_predictor
        )
        return {"status": "success", "insights": insights}

    except Exception as e:
        print(f"Simulation Error: {e}")
        return {"status": "error", "message": str(e), "insights": []}


@router.post("/predict-all")
def predict_all(batch: BatchApplianceRequest):
    """
    Clean single-batch prediction endpoint.

    Golden Rule: One request → One batch → One prediction → One learning step
    """
    from services import (BatchPredictor, BiasAdjuster, InputNormalizer,
                          LearningPipeline)
    from utils.prediction_logger import PredictionLogger

    try:
        # ========================================
        # STEP 1: NORMALIZE INPUTS (ONCE)
        # ========================================
        # Extract user context and appliance inputs
        batch_data = {
            "total_kwh_monthly": batch.requests[0].total_bill if batch.requests else 0,
            "n_occupants": (
                batch.requests[0].details.get("num_people", 3) if batch.requests else 3
            ),
            "season": (
                batch.requests[0].details.get("season", "monsoon")
                if batch.requests
                else "monsoon"
            ),
            "location_type": (
                batch.requests[0].details.get("location_type", "urban")
                if batch.requests
                else "urban"
            ),
            "requests": [
                {"appliance_name": r.appliance_name, "details": r.details}
                for r in batch.requests
            ],
        }

        normalized = InputNormalizer.normalize_batch_request(batch_data)
        user_context = normalized["user_context"]
        appliance_inputs = normalized["appliance_inputs"]

        # Log header
        PredictionLogger.log_header(user_context, len(appliance_inputs))

        # ========================================
        # STEP 2: BATCH PREDICTION (SINGLE LOOP)
        # ========================================
        batch_predictor = BatchPredictor(predictor)

        # Validate inputs first
        validated_inputs = {}
        for appliance_name, inputs in appliance_inputs.items():
            try:
                # Find matching request for validation
                matching_req = next(
                    (r for r in batch.requests if r.appliance_name == appliance_name),
                    None,
                )
                if matching_req:
                    validated_model = matching_req.validate_details()
                    validated_data = validated_model.model_dump(exclude_none=True)

                    # Apply field mapping
                    mapped_data = map_schema_to_training_columns(validated_data)

                    # Apply range resolution
                    from range_resolver import resolve_range_values

                    mapped_data = resolve_range_values(mapped_data)

                    validated_inputs[appliance_name] = mapped_data
            except Exception as e:
                print(f"Validation error for {appliance_name}: {e}")
                validated_inputs[appliance_name] = inputs.copy()

        # Run batch prediction
        results_list = batch_predictor.predict_batch(user_context, validated_inputs)

        # ========================================
        # STEP 3: APPLY EFFICIENCY BIAS (ONCE)
        # ========================================
        user_id = "default"  # Extract from auth if available
        results_list, bias_applied = BiasAdjuster.apply_bias_to_results(
            results_list, user_id
        )

        # ========================================
        # STEP 3.5: LOG USER INPUTS (ONCE)
        # ========================================
        print("\n" + "=" * 60)
        print("USER INPUTS CAPTURED")
        print("=" * 60)
        for req in batch.requests:
            print(f"\n{req.appliance_name.upper()}:")
            for key, value in req.details.items():
                print(f"  • {key}: {value}")
        print("=" * 60 + "\n")

        # ========================================
        # STEP 4: CALCULATE TOTALS WITH SMART BALANCING
        # ========================================
        from services import SystemLoadBalancer

        predicted_total_before_bias = batch_predictor.calculate_total_kwh(results_list)
        actual_kwh = user_context["total_kwh_monthly"]

        # Use smart system load balancer
        # This caps system load at 15% and redistributes excess proportionally
        system_load, results_list, balancing_info = (
            SystemLoadBalancer.calculate_balanced_load(
                actual_kwh=actual_kwh,
                predicted_total=predicted_total_before_bias,
                results_list=results_list,
            )
        )

        # Recalculate total after redistribution
        predicted_total = batch_predictor.calculate_total_kwh(results_list)

        # Log balancing details if redistribution occurred
        if balancing_info["redistribution_applied"]:
            print(f"\n🔧 SYSTEM LOAD BALANCING APPLIED:")
            print(
                f"   Raw System Load: {balancing_info['raw_system_load']:.2f} kWh ({balancing_info['raw_percentage']:.1f}%)"
            )
            print(
                f"   Capped At: {system_load:.2f} kWh ({balancing_info['capped_percentage']:.1f}%)"
            )
            print(
                f"   Excess Redistributed: {balancing_info['excess_redistributed']:.2f} kWh"
            )
            print(f"   Redistribution:")
            for app, amount in balancing_info.get("redistribution_details", {}).items():
                print(f"     • {app}: +{amount:.2f} kWh")
            print()

        # ========================================
        # STEP 5: LEARNING PIPELINE (ONCE)
        # ========================================
        learning_result = None
        if LearningPipeline.should_trigger_learning(actual_kwh):
            learning_result = LearningPipeline.learn_from_gap(
                user_id=user_id,
                actual_kwh=actual_kwh,
                predicted_total=predicted_total,
                current_bias=bias_applied,
            )

        # ========================================
        # STEP 6: CLEAN LOGGING
        # ========================================
        system_load_explanation = SystemLoadBalancer.get_system_load_explanation(
            balancing_info["capped_percentage"],
            user_context.get("location_type", "urban"),
        )
        PredictionLogger.log_results(results_list, system_load)
        print(f"\n💡 System Load: {system_load_explanation}")
        PredictionLogger.log_footer(
            predicted_total + system_load, bias_applied, learning_result
        )

        # ========================================
        # STEP 7: FORMAT RESPONSE (FREEZE SYSTEM LOAD)
        # ========================================
        # ⚠️ CRITICAL: System load is now FROZEN - never recalculate
        final_system_load = system_load
        final_total = predicted_total + final_system_load

        # Convert results list to dict format for API response
        results_dict = {}
        for r in results_list:
            results_dict[r["appliance"]] = {
                "status": "success",
                "prediction": r["kwh"],
                "insights": r["insights"],
            }

        # Add system load as virtual appliance with FROZEN value
        results_dict["system_load"] = {
            "status": "success",
            "prediction": final_system_load,  # ⚠️ FROZEN VALUE - DO NOT RECALCULATE
            "insights": {
                "source": "System & Unaccounted Load",
                "description": system_load_explanation,
                "percentage": balancing_info["capped_percentage"],
                "is_balanced": balancing_info["redistribution_applied"],
                "frozen": True,  # Flag to prevent downstream recalculation
            },
        }

        # Add metadata for comprehensive response
        results_dict["_metadata"] = {
            "total_kwh": final_total,
            "predicted_total": predicted_total,
            "system_load_kwh": final_system_load,  # ⚠️ OFFICIAL FROZEN VALUE
            "system_load_percentage": balancing_info["capped_percentage"],
            "bias_applied": bias_applied,
            "location_type": user_context.get("location_type", "urban"),
            "balancing_applied": balancing_info["redistribution_applied"],
        }

        return results_dict

    except Exception as e:
        print(f"❌ Batch Prediction Error: {e}")
        import traceback

        traceback.print_exc()
        return {}
