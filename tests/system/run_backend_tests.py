import os
import subprocess
import sys
import time


def run_tests():
    print("=" * 60)
    print("🚀 STARTING SMARTWATT BACKEND QA SUITE")
    print("=" * 60)

    # 1. Install/Check Dependencies
    print("📦 Checking Dependencies...")
    try:
        import httpx
        import pytest

        print("✅ Dependencies found.")
    except ImportError:
        print("⚠️ Missing test dependencies. Attempting install...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"]
        )
        print("✅ Dependencies installed.")

    # 2. Run Pytest
    print("\n🔬 Executing Tests...")
    start_time = time.time()

    # Run pytest on the 'tests' directory
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-v"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    if result.returncode == 0:
        print(f"✅ ALL TESTS PASSED in {duration:.2f} seconds")
        print("🎉 Verify: System logic is consistent.")
    else:
        print(f"❌ TESTS FAILED in {duration:.2f} seconds")
        print("⚠️ Check the logs above for details.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
