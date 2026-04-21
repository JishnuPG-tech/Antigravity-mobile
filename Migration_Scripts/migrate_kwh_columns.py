"""
Migration Script: Populate predicted_kwh and input_kwh columns
================================================================
This script extracts data from existing JSON columns and populates
the new dedicated columns for faster self-learning.
"""

import json
import os

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client():
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_KEY in environment variables"
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def extract_predicted_kwh(final_breakdown):
    """Extract AI's predicted kWh from final_breakdown.rawTotal"""
    try:
        if not final_breakdown:
            return None

        # Parse JSON string if needed
        if isinstance(final_breakdown, str):
            final_breakdown = json.loads(final_breakdown)

        if not isinstance(final_breakdown, dict):
            return None

        # Get rawTotal (AI's prediction)
        raw_total = final_breakdown.get("rawTotal")
        if raw_total and 0 < raw_total < 100000:  # Sanity check
            return float(raw_total)

        # Fallback: sum predictions dictionary
        predictions = final_breakdown.get("predictions", {})
        if predictions:
            total = sum(
                float(v) for v in predictions.values() if isinstance(v, (int, float))
            )
            if 0 < total < 100000:
                return total

        return None

    except Exception as e:
        print(f"      Error extracting predicted_kwh: {e}")
        return None


def migrate_data():
    """Migrate existing data to populate new columns"""
    print("=" * 70)
    print("🔄 MIGRATION: Populating predicted_kwh and input_kwh columns")
    print("=" * 70)

    supabase = get_supabase_client()

    # Fetch all records
    print("\n📥 Fetching all records from smartwatt_training...")
    response = supabase.table("smartwatt_training").select("*").execute()

    if not response.data:
        print("❌ No records found!")
        return

    total_records = len(response.data)
    print(f"✅ Found {total_records} records\n")

    # Process each record
    updated_count = 0
    skipped_count = 0

    for idx, record in enumerate(response.data, 1):
        record_id = record.get("id", "unknown")[:8]
        print(f"\n[{idx}/{total_records}] Processing record {record_id}...")

        updates = {}

        # Extract input_kwh (actual from user's KSEB bill)
        bi_monthly_kwh = record.get("bi_monthly_kwh")
        if bi_monthly_kwh and bi_monthly_kwh > 0:
            updates["input_kwh"] = float(bi_monthly_kwh)
            print(f"   ✓ input_kwh: {bi_monthly_kwh} kWh")
        else:
            print(f"   ⚠ No valid bi_monthly_kwh")

        # Extract predicted_kwh (from final_breakdown.rawTotal)
        final_breakdown = record.get("final_breakdown")
        if final_breakdown:
            predicted = extract_predicted_kwh(final_breakdown)
            if predicted:
                updates["predicted_kwh"] = predicted
                print(f"   ✓ predicted_kwh: {predicted:.2f} kWh")
            else:
                print(f"   ⚠ Could not extract predicted_kwh")
        else:
            print(f"   ⚠ No final_breakdown data")

        # Update record if we have data
        if updates:
            try:
                supabase.table("smartwatt_training").update(updates).eq(
                    "id", record["id"]
                ).execute()

                if len(updates) == 2:
                    error = updates["input_kwh"] - updates["predicted_kwh"]
                    error_pct = (error / updates["input_kwh"]) * 100
                    print(f"   ✅ Updated! Error: {error:+.1f} kWh ({error_pct:+.1f}%)")
                else:
                    print(f"   ⚠ Partial update (missing data)")

                updated_count += 1
            except Exception as e:
                print(f"   ❌ Update failed: {e}")
                skipped_count += 1
        else:
            print(f"   ⏭️  Skipped (no data to update)")
            skipped_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Total Records: {total_records}")
    print(f"✅ Updated: {updated_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print("=" * 70)

    if updated_count > 0:
        print("\n🎉 Migration completed successfully!")
        print("   You can now run auto_train.py to use the new columns.")
    else:
        print("\n⚠️  No records were updated. Check if data exists in the table.")


if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
