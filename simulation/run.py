"""Run the Pocket NAS integration scenarios and produce a shareable JSON report."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "access": [sys.executable, "scripts/sim-access.py"],
    "drive": [sys.executable, "scripts/sim-drive-faults.py"],
    "sync": [sys.executable, "scripts/sim-sync.py"],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    results = []
    for name, command in SCENARIOS.items():
        if args.scenario not in ("all", name):
            continue
        print(f"Running {name}", flush=True)
        start = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, check=False)
        results.append({
            "scenario": name,
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "elapsed_seconds": round(time.monotonic() - start, 2),
        })
    report = json.dumps({"environment": "linux-loopback", "results": results}, indent=2)
    print(report)
    if args.report:
        args.report.write_text(report + "\n", encoding="utf-8")
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
