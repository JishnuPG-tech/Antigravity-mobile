"""
Quick Test Script for Self-Learning System
Uses local CSV dataset instead of Supabase
"""

import os
import sys


def main():
    # Temporarily modify auto_train to use local CSV
    print("=" * 70)
    print(" TESTING SELF-LEARNING SYSTEM (LOCAL DATASET MODE)")
    print("=" * 70)
    print()

    # Check if local dataset exists
    dataset_files = [
        "kerala_smartwatt_ai.csv",
        "kerala_realworld_dataset.csv",
        "../kerala_smartwatt_ai.csv",
    ]

    dataset_found = None
    for f in dataset_files:
        if os.path.exists(f):
            dataset_found = f
            break

    if not dataset_found:
        print("❌ No local dataset found. Need one of:")
        for f in dataset_files:
            print(f"   - {f}")
        print()
        print("🔧 Solution: Run newdataset.py first to generate training data")
        print("   python newdataset.py")
        sys.exit(1)

    print(f"✅ Found dataset: {dataset_found}")
    print()

    # Create a modified version that uses local CSV
    print("📝 Creating test_auto_train_local.py...")

    # Add backend root to path
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    )

    # Load auto_train from dev_tools
    AUTO_TRAIN_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../dev_tools/auto_train.py")
    )

    with open(AUTO_TRAIN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace Supabase fetch with local CSV read
    modified = content.replace(
        "def fetch_training_data():", """def fetch_training_data_original():"""
    )

    # Add new fetch function that reads from CSV
    local_fetch = '''
def fetch_training_data():
    """Fetches data from local CSV file for testing."""
    import pandas as pd
    
    print("🔄 Loading local dataset...")
    
    # Try to find dataset
    for dataset_file in ['kerala_smartwatt_ai.csv', 'kerala_realworld_dataset.csv', '../kerala_smartwatt_ai.csv']:
        if os.path.exists(dataset_file):
            print(f"✅ Found: {dataset_file}")
            df = pd.read_csv(dataset_file)
            print(f"✅ Successfully loaded {len(df)} records from local CSV")
            
            # The CSV already has the correct format from newdataset.py
            # Just ensure we have total_kwh_monthly if bi_monthly_kwh exists
            if 'bi_monthly_kwh' in df.columns and 'total_kwh_monthly' not in df.columns:
                df['total_kwh_monthly'] = df['bi_monthly_kwh'] / 2
            
            # Ensure n_occupants exists
            if 'n_occupants' not in df.columns:
                df['n_occupants'] = 4  # Default
            
            return df
    
    print("❌ No dataset file found!")
    return None

'''

    # Insert the new function after imports
    import_section_end = modified.find("# Training History File")
    if import_section_end != -1:
        modified = (
            modified[:import_section_end]
            + local_fetch
            + "\n"
            + modified[import_section_end:]
        )

    # Write modified version
    with open("test_auto_train_local.py", "w", encoding="utf-8") as f:
        f.write(modified)

    print("✅ Created test_auto_train_local.py")
    print()
    print("=" * 70)
    print(" RUNNING SELF-LEARNING TRAINING TEST")
    print("=" * 70)
    print()

    # Run the test version
    import subprocess

    result = subprocess.run(
        [sys.executable, "test_auto_train_local.py"], capture_output=False, text=True
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
