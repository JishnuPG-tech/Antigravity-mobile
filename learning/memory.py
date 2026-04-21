import hashlib
import json
import os
from typing import Any, Dict


class HouseholdMemory:
    def __init__(self, storage_file="learned_params.json"):
        self.storage_file = storage_file
        self.memory_cache = {}
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self.memory_cache = json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                self.memory_cache = {}

    def _save_memory(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.memory_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def get_profile_hash(self, context: Dict[str, Any]) -> str:
        """Create a stable hash from household context (Pseudo-ID)"""
        # We use strict keys to ensure same household gets same hash
        key_parts = [
            str(context.get("n_occupants", 4)),
            str(context.get("location_type", "urban")),
            str(context.get("house_type", "Apartment")),
            str(
                context.get("total_kwh_monthly", 0)
            ),  # Using Bill as part of ID might be strict?
            # Actually user changes bill monthly.
            # Better to use just structural info + training_id if available?
            # User wants "Per household".
            # For now, let's use the 'id' if passed, or hash of immutable traits.
        ]
        # Ideally, Training ID is the session key.
        if "training_id" in context:
            return str(context["training_id"])

        # Fallback to structural hash
        combined = "-".join(key_parts)
        return hashlib.md5(combined.encode()).hexdigest()

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        return self.memory_cache.get(
            profile_id,
            {"background_load_kwh": 0.0, "efficiency_bias": 1.0, "sample_count": 0},
        )

    def update_profile(self, profile_id: str, updates: Dict[str, Any]):
        profile = self.get_profile(profile_id)
        profile.update(updates)
        self.memory_cache[profile_id] = profile
        self._save_memory()
