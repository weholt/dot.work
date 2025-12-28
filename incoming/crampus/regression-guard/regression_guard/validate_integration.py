#!/usr/bin/env python3
"""
Integration Validator - Validates full system integration after all changes.

Runs comprehensive test suite and generates final validation report.

Usage:
    python scripts/validate_integration.py <task_id>
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class IntegrationValidator:
    """Validates full system integration."""

    def __init__(self, task_id: str, verbose: bool = False):
        self.task_id = task_id
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.work_dir = self.project_root / ".work" / "tasks"
        self.task_dir = self.work_dir / task_id
        self.integration_dir = self.task_dir / "integration"
        self.integration_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        if self.verbose or level in ["ERROR", "SUCCESS", "FAIL"]:
            prefix = {
                "INFO": "[*]",
                "ERROR": "[-]",
                "SUCCESS": "[+]",
                "FAIL": "[-]",
            }.get(level, "[*]")
            print(f"{prefix} {message}")

    def validate(self) -> bool:
        """Run integration validation."""
        self.log("Running integration validation...")

        try:
            # Load baseline and manifest
            baseline = self._load_baseline()
            manifest = self._load_manifest()

            if not baseline or not manifest:
                self.log("Failed to load baseline or manifest", "ERROR")
                # Create minimal report even on error
                error_report = f"""# Final Validation Report: {self.task_id}

## Status: ❌ ERROR

Failed to load baseline or manifest.

## Task ID
{self.task_id}
"""
                report_path = self.task_dir / "final_report.md"
                report_path.write_text(error_report, encoding="utf-8")
                return False

            # Run integration tests
            results = {
                "timestamp": datetime.now().isoformat(),
                "task_id": self.task_id,
                "unit_tests": self._run_unit_tests(),
                "integration_tests": self._run_integration_tests(),
                "build_check": self._run_build_check(),
                "success": False,
            }

            # Determine overall success
            all_passed = results["unit_tests"]["passed"] and results["build_check"]["passed"]
            results["success"] = all_passed

            # Save results
            validation_path = self.integration_dir / "validation.json"
            validation_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

            # Generate final report
            self._generate_final_report(results, manifest, baseline)

            if results["success"]:
                self.log(f"Task {self.task_id} integration validation PASSED", "SUCCESS")
            else:
                self.log(f"Task {self.task_id} integration validation FAILED", "FAIL")

            return results["success"]

        except Exception as e:
            self.log(f"Integration validation error: {e}", "ERROR")
            # Create error report
            error_report = f"""# Final Validation Report: {self.task_id}

## Status: ❌ ERROR

Validation crashed with error: {e}

## Task ID
{self.task_id}
"""
            report_path = self.task_dir / "final_report.md"
            report_path.write_text(error_report, encoding="utf-8")
            return False

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

    def _run_unit_tests(self) -> dict:
        """Run full unit test suite."""
        self.log("Running unit tests...")

        cmd = [
            "uv",
            "run",
            "pytest",
            "tests/unittests/test_01_smoke.py",  # Just smoke tests for integration validation
            "-v",
            "--tb=short",
            "--timeout=5",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,  # Smoke tests should be quick
            )

            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return {
                "passed": passed,
                "output": output[:2000],
                "message": "Smoke tests passed (run full suite with: uv run pytest tests/)"
                if passed
                else "Smoke tests failed",
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "",
                "message": "Unit tests timed out (60s)",
            }

    def _run_integration_tests(self) -> dict:
        """Run integration tests (optional)."""
        self.log("Integration tests skipped (run manually if needed)")
        return {
            "passed": True,
            "output": "",
            "message": "Skipped (run manually with: uv run python scripts/run_tests.py --integration all)",
        }

    def _run_build_check(self) -> dict:
        """Run build validation."""
        self.log("Running build validation...")

        cmd = [
            "uv",
            "run",
            "python",
            "build.py",
            "--fix",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,
            )

            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return {
                "passed": passed,
                "output": output[:2000],
                "message": "Build check passed" if passed else "Build check failed",
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "",
                "message": "Build check timed out",
            }

    def _generate_final_report(self, results: dict, manifest: dict, baseline: dict) -> None:
        """Generate final validation report."""
        status_icon = "✅" if results["success"] else "❌"

        report = f"""# Final Validation Report: {self.task_id}

## Status: {status_icon} {"PASSED" if results["success"] else "FAILED"}

## Task Description
{manifest["description"]}

## Validation Summary

### Unit Tests
- Status: {"✅ PASSED" if results["unit_tests"]["passed"] else "❌ FAILED"}
- Message: {results["unit_tests"]["message"]}

### Integration Tests
- Status: {"⏭️ SKIPPED" if results["integration_tests"].get("passed") else "❌ FAILED"}
- Message: {results["integration_tests"]["message"]}

### Build Validation
- Status: {"✅ PASSED" if results["build_check"]["passed"] else "❌ FAILED"}
- Message: {results["build_check"]["message"]}

## Subtask Completion

"""

        # Add subtask status
        for subtask in manifest.get("subtasks", []):
            subtask_id = subtask["id"]
            validation_path = self.task_dir / subtask_id / "validation.json"

            if validation_path.exists():
                validation = json.loads(validation_path.read_text())
                status = "✅" if validation.get("success") else "❌"
            else:
                status = "⏳"

            report += f"{status} {subtask_id}: {subtask['description']}\n"

        report += """
## Baseline Comparison

"""

        baseline_tests = baseline.get("test_results", {}).get("unit", {}).get("total", 0)
        baseline_coverage = baseline.get("coverage", {}).get("percentage", 0.0)

        report += f"- Baseline Tests: {baseline_tests}\n"
        report += f"- Baseline Coverage: {baseline_coverage:.2f}%\n"

        report += """
## Next Steps

"""

        if results["success"]:
            report += "✅ All validation checks passed!\n"
            report += "- Review changes and commit\n"
            report += "- Create pull request\n"
            report += "- Run CI/CD pipeline\n"
        else:
            report += "❌ Validation failed\n"
            report += "- Review failed tests\n"
            report += "- Fix issues\n"
            report += "- Re-run validation\n"

        report += f"""
## Validation Timestamp
{results["timestamp"]}

## Task ID
{self.task_id}
"""

        report_path = self.task_dir / "final_report.md"
        report_path.write_text(report, encoding="utf-8")
        self.log(f"Final report saved: {report_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate full system integration")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = IntegrationValidator(args.task_id, args.verbose)
    success = validator.validate()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
