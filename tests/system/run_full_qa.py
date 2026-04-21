import datetime
import os
import subprocess
import sys
import webbrowser


def run_command(command, cwd=None):
    """Run command and capture output"""
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result
    except Exception as e:
        return str(e)


def generate_html_report(results):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SmartWatt QA Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            h1 {{ border-bottom: 2px solid #3b82f6; padding-bottom: 15px; color: #60a5fa; }}
            .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .status {{ font-weight: bold; padding: 5px 10px; border-radius: 4px; display: inline-block; }}
            .pass {{ background: #064e3b; color: #34d399; border: 1px solid #059669; }}
            .fail {{ background: #7f1d1d; color: #f87171; border: 1px solid #dc2626; }}
            pre {{ background: #0f172a; padding: 15px; border-radius: 6px; overflow-x: auto; font-family: 'Consolas', monospace; font-size: 13px; color: #cbd5e0; }}
            .summary {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .summary-item {{ background: #1e293b; padding: 15px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #334155; }}
            .summary-item h3 {{ margin: 0 0 10px 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; }}
            .summary-item p {{ margin: 0; font-size: 24px; font-weight: bold; color: #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ SmartWatt Automated QA Report</h1>
            <p style="color: #94a3b8;">Generated on: {timestamp}</p>

            <div class="summary">
                <div class="summary-item">
                    <h3>Backend Logic</h3>
                    <p style="color: {'#34d399' if results['backend_logic']['success'] else '#f87171'}">
                        {'PASS' if results['backend_logic']['success'] else 'FAIL'}
                    </p>
                </div>
                <div class="summary-item">
                    <h3>API Integration</h3>
                    <p style="color: {'#34d399' if results['api']['success'] else '#f87171'}">
                        {'PASS' if results['api']['success'] else 'FAIL'}
                    </p>
                </div>
                <div class="summary-item">
                    <h3>Edge Resilience</h3>
                    <p style="color: {'#34d399' if results['edge_cases']['success'] else '#f87171'}">
                        {'PASS' if results['edge_cases']['success'] else 'FAIL'}
                    </p>
                </div>
                <div class="summary-item">
                    <h3>Auto-Train</h3>
                    <p style="color: {'#34d399' if results['auto_train']['success'] else '#f87171'}">
                        {'PASS' if results['auto_train']['success'] else 'FAIL'}
                    </p>
                </div>
                <div class="summary-item">
                    <h3>Regression Drift</h3>
                    <p style="color: {'#34d399' if results['regression']['success'] else '#f87171'}">
                        {'STABLE' if results['regression']['success'] else 'DRIFT DETECTED'}
                    </p>
                </div>
            </div>

            <div class="card">
                <h2>1. Backend Logic & Unit Tests</h2>
                <span class="status {'pass' if results['backend_logic']['success'] else 'fail'}">
                    {'PASSED' if results['backend_logic']['success'] else 'FAILED'}
                </span>
                <details>
                    <summary style="cursor: pointer; padding: 10px 0; color: #60a5fa;">View Logs</summary>
                    <pre>{results['backend_logic']['output']}</pre>
                </details>
            </div>

            <div class="card">
                <h2>2. API Integration Tests</h2>
                <span class="status {'pass' if results['api']['success'] else 'fail'}">
                    {'PASSED' if results['api']['success'] else 'FAILED'}
                </span>
                <details>
                    <summary style="cursor: pointer; padding: 10px 0; color: #60a5fa;">View Logs</summary>
                    <pre>{results['api']['output']}</pre>
                </details>
            </div>

            <div class="card">
                <h2>3. Edge Case Resilience</h2>
                <span class="status {'pass' if results['edge_cases']['success'] else 'fail'}">
                    {'PASSED' if results['edge_cases']['success'] else 'FAILED'}
                </span>
                <details>
                    <summary style="cursor: pointer; padding: 10px 0; color: #60a5fa;">View Logs</summary>
                    <pre>{results['edge_cases']['output']}</pre>
                </details>
            </div>

            <div class="card">
                <h2>4. Auto-Train Pipeline Check</h2>
                <span class="status {'pass' if results['auto_train']['success'] else 'fail'}">
                    {'PASSED' if results['auto_train']['success'] else 'FAILED'}
                </span>
                <details>
                    <summary style="cursor: pointer; padding: 10px 0; color: #60a5fa;">View Logs</summary>
                    <pre>{results['auto_train']['output']}</pre>
                </details>
            </div>

            <div class="card">
                <h2>5. Regression Baseline Check</h2>
                <span class="status {'pass' if results['regression']['success'] else 'fail'}">
                    {'PASSED' if results['regression']['success'] else 'FAILED'}
                </span>
                <details>
                    <summary style="cursor: pointer; padding: 10px 0; color: #60a5fa;">View Logs</summary>
                    <pre>{results['regression']['output']}</pre>
                </details>
            </div>

            <p style="text-align: center; color: #64748b; font-size: 12px; margin-top: 50px;">
                Antigravity QA Engine v1.0
            </p>
        </div>
    </body>
    </html>
    """

    report_path = os.path.join(os.path.dirname(__file__), "qa_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    return report_path


def main():
    print("🚀 Initializing Master QA Sequence...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = base_dir

    results = {}

    # 1. Run Logic Unit Tests
    print("🔬 Running Unit Tests...")
    logic_res = run_command(
        [sys.executable, "-m", "pytest", "tests/test_logic.py"], cwd=backend_dir
    )
    results["backend_logic"] = {
        "success": logic_res.returncode == 0,
        "output": logic_res.stdout + "\n" + logic_res.stderr,
    }

    # 2. Run API Tests
    print("🔌 Running Integration Tests...")
    # Requires backend to be importable, usually pytest handles this efficiently
    api_res = run_command(
        [sys.executable, "-m", "pytest", "tests/test_api.py"], cwd=backend_dir
    )
    results["api"] = {
        "success": api_res.returncode == 0,
        "output": api_res.stdout + "\n" + api_res.stderr,
    }

    # 2.5 Run Edge Case Tests
    print("⚠️ Running Edge Case Tests...")
    edge_res = run_command(
        [sys.executable, "-m", "pytest", "tests/test_edge_cases.py"], cwd=backend_dir
    )
    results["edge_cases"] = {
        "success": edge_res.returncode == 0,
        "output": edge_res.stdout + "\n" + edge_res.stderr,
    }

    # 2.6 Run Auto-Train Logic Test
    print("🤖 Running Auto-Train Pipeline Verification...")
    train_res = run_command(
        [sys.executable, "-m", "pytest", "tests/test_auto_train.py"], cwd=backend_dir
    )
    results["auto_train"] = {
        "success": train_res.returncode == 0,
        "output": train_res.stdout + "\n" + train_res.stderr,
    }

    # 3. Run Regression
    print("📉 Running Regression Engine...")
    reg_res = run_command(
        [sys.executable, "tests/compare_predictions.py"], cwd=backend_dir
    )
    results["regression"] = {
        "success": reg_res.returncode == 0,
        "output": reg_res.stdout + "\n" + reg_res.stderr,
    }

    # Generate Report
    print("📝 Generating Report...")
    report_file = generate_html_report(results)

    print(f"\n✅ QA Sequence Complete!")
    print(f"📄 Report generated at: {report_file}")

    # Try to open
    try:
        webbrowser.open("file://" + report_file)
    except:
        pass


if __name__ == "__main__":
    main()
