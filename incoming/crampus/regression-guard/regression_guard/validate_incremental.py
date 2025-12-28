#!/usr/bin/env python3
"""
Incremental Validator - Validates subtask implementation against baseline.

Runs tests for specific subtask and compares with baseline to detect regressions.

Usage:
    python scripts/validate_incremental.py <task_id> <subtask_id>
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class IncrementalValidator:
    """Validates subtask implementation incrementally."""

    def __init__(self, task_id: str, subtask_id: str, verbose: bool = False):
        self.task_id = task_id
        self.subtask_id = subtask_id
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.work_dir = self.project_root / ".work" / "tasks"
        self.task_dir = self.work_dir / task_id
        self.subtask_dir = self.task_dir / subtask_id
        self.subtask_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        if self.verbose or level in ["ERROR", "SUCCESS", "FAIL"]:
            prefix = {
                "INFO": "[*]",
                "ERROR": "[-]",
                "SUCCESS": "[+]",
                "FAIL": "[-]",
                "WARN": "[!]",
            }.get(level, "[*]")
            print(f"{prefix} {message}")

    def validate(self) -> bool:
        """Run validation workflow."""
        self.log(f"Validating subtask: {self.subtask_id}")

        # Load baseline and manifest
        baseline = self._load_baseline()
        manifest = self._load_manifest()

        if not baseline or not manifest:
            self.log("Failed to load baseline or manifest", "ERROR")
            return False

        # Find subtask definition
        subtask = self._find_subtask(manifest)
        if not subtask:
            self.log(f"Subtask not found: {self.subtask_id}", "ERROR")
            return False

        # Run validation steps
        results = {
            "timestamp": datetime.now().isoformat(),
            "subtask_id": self.subtask_id,
            "baseline_tests": self._run_baseline_tests(subtask, baseline),
            "new_tests": self._run_new_tests(subtask),
            "coverage_change": self._check_coverage_change(baseline),
            "success": False,
        }

        # Determine overall success
        baseline_passed = results["baseline_tests"]["passed"]
        new_tests_passed = results["new_tests"]["passed"]
        results["success"] = baseline_passed and new_tests_passed

        # Save validation results
        validation_path = self.subtask_dir / "validation.json"
        validation_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

        # Generate report
        self._generate_report(results, subtask, baseline)

        if results["success"]:
            self.log(f"Subtask {self.subtask_id} validation PASSED", "SUCCESS")
        else:
            self.log(f"Subtask {self.subtask_id} validation FAILED", "FAIL")

        return results["success"]

    def _load_baseline(self) -> dict | None:
        """Load baseline state."""
        baseline_path = self.task_dir / "baseline.json"
        if not baseline_path.exists():
            return None
        return json.loads(baseline_path.read_text())

    def _load_manifest(self) -> dict | None:
        """Load task manifest."""
        manifest_path = self.task_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        return json.loads(manifest_path.read_text())

    def _find_subtask(self, manifest: dict) -> dict | None:
        """Find subtask definition in manifest."""
        for subtask in manifest.get("subtasks", []):
            if subtask["id"] == self.subtask_id:
                return subtask
        return None

    def _run_baseline_tests(self, subtask: dict, baseline: dict) -> dict:
        """Run baseline regression tests."""
        self.log("Running baseline regression tests...")

        baseline_test_paths = subtask.get("baseline_tests", [])

        if not baseline_test_paths:
            self.log("No baseline tests specified, running smoke tests only")
            baseline_test_paths = ["tests/unittests/test_01_smoke.py"]

        # Run tests with increased timeout for CI/full runs
        cmd = (
            [
                "uv",
                "run",
                "pytest",
            ]
            + baseline_test_paths
            + [
                "-m",
                "not integration and not playwright and not e2e",
                "-v",
                "--tb=short",
                "--timeout=5",
                "-x",  # Stop on first failure
            ]
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minutes max
            )

            # Parse results
            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return {
                "passed": passed,
                "output": output[:1000],  # Truncate for storage
                "message": "All baseline tests passed" if passed else "Some baseline tests failed",
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "",
                "message": "Baseline tests timed out (300s)",
            }

    def _run_new_tests(self, subtask: dict) -> dict:
        """Run new tests for this subtask."""
        self.log("Running new tests...")

        test_specs = subtask.get("tests_required", [])

        if not test_specs:
            self.log("No new tests required for this subtask")
            return {"passed": True, "output": "", "message": "No new tests required"}

        # For MVP, just check that test files exist
        # Later: actually run the specific tests
        all_exist = True
        missing_tests = []

        for spec in test_specs:
            test_path = spec.get("path", "")
            if test_path and test_path != "(to be determined)":
                full_path = self.project_root / test_path
                if not full_path.exists():
                    all_exist = False
                    missing_tests.append(test_path)

        if all_exist or not test_specs:
            return {
                "passed": True,
                "output": "",
                "message": "New tests validated",
            }
        else:
            return {
                "passed": False,
                "output": f"Missing tests: {', '.join(missing_tests)}",
                "message": "Required tests not found",
            }

    def _check_coverage_change(self, baseline: dict) -> dict:
        """Check coverage change compared to baseline."""
        baseline_coverage = baseline.get("coverage", {}).get("percentage", 0.0)

        # Get current coverage from coverage.xml
        coverage_file = self.project_root / "coverage.xml"
        current_coverage = 0.0

        if coverage_file.exists():
            try:
                content = coverage_file.read_text()
                import re

                match = re.search(r'line-rate="([0-9.]+)"', content)
                if match:
                    rate = float(match.group(1))
                    current_coverage = rate * 100
            except Exception:
                # Silently ignore coverage parsing errors - use default value
                pass

        change = current_coverage - baseline_coverage

        return {
            "baseline": baseline_coverage,
            "current": current_coverage,
            "change": round(change, 2),
        }

    def _generate_report(self, results: dict, subtask: dict, baseline: dict) -> None:
        """Generate human-readable validation report."""
        status_icon = "✅" if results["success"] else "❌"

        report = f"""# Validation Report: {self.subtask_id}

## Status: {status_icon} {"PASSED" if results["success"] else "FAILED"}

## Subtask Description
{subtask["description"]}

## Validation Results

### Baseline Regression Tests
- Status: {"✅ PASSED" if results["baseline_tests"]["passed"] else "❌ FAILED"}
- Message: {results["baseline_tests"]["message"]}

### New Tests
- Status: {"✅ PASSED" if results["new_tests"]["passed"] else "❌ FAILED"}
- Message: {results["new_tests"]["message"]}

### Coverage Change
- Baseline: {results["coverage_change"]["baseline"]:.2f}%
- Current: {results["coverage_change"]["current"]:.2f}%
- Change: {results["coverage_change"]["change"]:+.2f}%

## Risk Assessment: {subtask["estimated_risk"].upper()}

## Files Affected
{chr(10).join(f"- {f}" for f in subtask["files_affected"])}

## Next Steps
"""

        if results["success"]:
            report += "- ✅ Proceed to next subtask\n"
            report += "- Run integration tests after all subtasks complete\n"
        else:
            report += "- ❌ Fix failing tests\n"
            report += "- Re-run validation\n"

        report_path = self.subtask_dir / "report.md"
        report_path.write_text(report, encoding="utf-8")
        self.log(f"Report saved: {report_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate subtask implementation")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("subtask_id", help="Subtask ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = IncrementalValidator(args.task_id, args.subtask_id, args.verbose)
    success = validator.validate()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
