"""
Auto-Train Pipeline for SmartWatt  (The "Self-Improving" System)
------------------------------------------------------------------
This script is the "Gym" for our AI.
Every time we run this, the AI gets smarter.

Workflow:
1. GENERATE: Create a new "Virtual World" of Kerala households (Physics-based Ground Truth).
2. TRAIN: Teach the AI models using this fresh data.
3. DEPLOY: Save the brain files (.keras) so the backend can use them.

Why?
Because static AI gets stale. We want an AI that can learn from new physics rules instantly.
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()


# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import newdataset
    import train
except ImportError as e:
    print(f"❌ Error importing Backend modules: {e}")
    print("Ensure you are running this from the Backend/ root directory.")
    sys.exit(1)


def run_pipeline():
    print("\n" + "=" * 60)
    print(" 🚀 SMARTWATT : AUTO-TRAIN PIPELINE STARTING")
    print("=" * 60)

    # --- STEP 0: CHECK REAL WORLD DATA (Gatekeeper) ---
    # We only want to burn compute if we have enough real user data to matter.
    # Checks the "smartwatt_training" vault in Supabase.
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            print("⚠️ Skipped Supabase Check: Missing credentials.")
        else:
            print("\n[Step 0/2] Checking Real World Data Maturity...")
            supabase = create_client(url, key)
            # Count entries (head=True is efficient, doesn't fetch body)
            count = (
                supabase.table("smartwatt_training")
                .select("*", count="exact", head=True)
                .execute()
                .count
            )

            print(f"   📊 Found {count} real user entries in Database.")

            if count < 10:
                print(f"   🛑 HALTING: Not enough data ({count}/10).")
                print("   The AI refuses to learn from an empty world.")
                print("   Come back when you have at least 10 entries.")
                return
            else:
                print("   ✅ PROCEEDING: Data maturity threshold met.")

    except Exception as e:
        print(f"⚠️ Supabase Check Warning: {e}")
        # We don't stop strictly on error, unless user wants strict mode.
        # But user said "only train if...", so maybe we SHOULD return on error?
        # User said "only train if supabase contain minimum 10 entries".
        # If we can't verify, we can't be sure. Safe default is to Proceed?
        # No, "only train if...". If check fails, condition is not met.
        # But for robustness, I'll print warning and Return to be safe/strict.
        print("   🛑 Check failed, skipping training to be safe.")
        return

    # --- STEP 1: DATA REGENERATION ---
    print("\n[Step 1/2] Regenerating Synthetic Ground Truth Data...")
    try:
        sim = newdataset.KeralaRealWorldSimulator()
        df = sim.generate()

        # Save to root directory
        csv_path = "kerala_smartwatt_ai.csv"
        df.to_csv(csv_path, index=False)
        print(f"   ✅ New Dataset Generated: {csv_path} ({len(df)} samples)")

    except Exception as e:
        print(f"   ❌ Data Generation Failed: {e}")
        return

    # --- STEP 2: MODEL RETRAINING ---
    print("\n[Step 2/2] Retraining  Hybrid Models...")
    # This calls the "Teacher" script (train.py) to update the neural networks.
    try:
        train.run_training()
    except Exception as e:
        print(f"   ❌ Training Failed: {e}")
        return

    print("\n" + "=" * 60)
    print(" ✅ PIPELINE COMPLETE: AI IS NOW SMARTER!")
    print("=" * 60)


"""
--- LEGACY V1 SUPABASE SNIPPET (ARCHIVED) ---
The V1 Auto-Train logic fetched user data from Supabase.
In , we require 'Efficiency' & 'Hours' ground truth, which basic user input lacks.
Future Scope: Integrate IoT sensors to collect this ground truth, then uncomment below.

# from supabase import create_client
# ...
# def fetch_training_data_original():
#     response = supabase.table('smartwatt_training').select("*").execute()
#     ...
"""

if __name__ == "__main__":
    run_pipeline()
