"""
Scheduled Self-Learning System
Automatically checks for new user data and triggers retraining when threshold is met.
Run this as a background service for continuous learning.
"""

import os
import subprocess
import time
from datetime import datetime

import schedule
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get(
    "SUPABASE_URL"
)
SUPABASE_KEY = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get(
    "SUPABASE_KEY"
)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials not found")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuration
MIN_NEW_SAMPLES = 20  # Minimum new predictions before retraining
LAST_TRAINED_FILE = "training_logs/last_training_timestamp.txt"


def get_last_training_timestamp():
    """Get the timestamp of the last training session"""
    if os.path.exists(LAST_TRAINED_FILE):
        with open(LAST_TRAINED_FILE, "r") as f:
            return f.read().strip()
    return "1970-01-01T00:00:00"  # Beginning of time


def update_last_training_timestamp():
    """Update the last training timestamp"""
    os.makedirs("training_logs", exist_ok=True)
    with open(LAST_TRAINED_FILE, "w") as f:
        f.write(datetime.now().isoformat())


def count_new_predictions():
    """Count predictions made since last training"""
    try:
        last_trained = get_last_training_timestamp()

        # Count records with final_breakdown updated after last training
        result = (
            supabase.table("smartwatt_training")
            .select("*", count="exact")
            .filter("updated_at", "gte", last_trained)
            .filter("final_breakdown", "neq", "null")
            .execute()
        )

        count = result.count if hasattr(result, "count") else len(result.data)
        return count
    except Exception as e:
        print(f"Error counting predictions: {e}")
        return 0


def check_and_retrain():
    """Check if retraining is needed and execute if threshold met"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 70)
    print(f"🔍 SELF-LEARNING CHECK at {timestamp}")
    print("=" * 70)

    try:
        new_count = count_new_predictions()

        print(f"   New predictions since last training: {new_count}")
        print(f"   Threshold for retraining: {MIN_NEW_SAMPLES}")

        if new_count >= MIN_NEW_SAMPLES:
            print(f"\n✅ Threshold met! Starting automatic retraining...")
            print(f"   🧠 AI will learn from {new_count} new real-world predictions\n")

            # Run auto_train.py
            result = subprocess.run(
                ["python", "auto_train.py"],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("\n✅ Retraining completed successfully!")
                update_last_training_timestamp()
                print(
                    f"   Next training will occur after {MIN_NEW_SAMPLES} more predictions"
                )
            else:
                print(f"\n❌ Retraining failed with error:")
                print(result.stderr)
        else:
            remaining = MIN_NEW_SAMPLES - new_count
            print(f"\n⏳ Waiting for more data...")
            print(f"   Need {remaining} more predictions before retraining")
            print(f"   Current: {new_count}/{MIN_NEW_SAMPLES}")

    except Exception as e:
        print(f"\n❌ Error during check: {e}")

    print("=" * 70 + "\n")


def run_scheduler():
    """Main scheduler loop"""
    print("\n" + "=" * 70)
    print("🚀 SMARTWATT SELF-LEARNING SCHEDULER STARTED")
    print("=" * 70)
    print(f"   Check interval: Every 6 hours")
    print(f"   Retraining threshold: {MIN_NEW_SAMPLES} new predictions")
    print(f"   Status: Monitoring for new user data...")
    print("=" * 70 + "\n")

    # Schedule checks every 6 hours
    schedule.every(6).hours.do(check_and_retrain)

    # For testing: check every 10 minutes (uncomment to use)
    # schedule.every(10).minutes.do(check_and_retrain)

    # Run initial check
    check_and_retrain()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user")
        print("   Self-learning will resume when scheduler is restarted")


if __name__ == "__main__":
    run_scheduler()
