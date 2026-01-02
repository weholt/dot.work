#!/usr/bin/env python3
"""Validate that main dot-work project works after submodule removal.

This script performs comprehensive validation to ensure the main project
functions correctly after removing all submodule source code and tests.

Part of the module split migration (SPLIT-107).

Usage:
    # Run all validation checks
    uv run python scripts/validate-migration.py

    # Run specific checks only
    uv run python scripts/validate-migration.py --check source imports

    # Verbose output
    uv run python scripts/validate-migration.py --verbose

    # Generate report only
    uv run python scripts/validate-migration.py --report validation-report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src" / "dot_work"

# Core modules that should remain
CORE_MODULES = [
    "__init__.py",
    "cli.py",
    "plugins.py",
    "environments.py",
    "installer.py",
    "prompts/",
    "skills/",
    "subagents/",
    "tools/",
    "utils/",
    "zip/",
]

# Submodule modules that should NOT remain
FORBIDDEN_MODULES = [
    "container/",
    "git/",
    "harness/",
    "db_issues/",
    "knowledge_graph/",
    "overview/",
    "python/",
    "review/",
    "version/",
]

# Forbidden import patterns
FORBIDDEN_IMPORTS = [
    "from dot_work.container",
    "from dot_work.git",
    "from dot_work.harness",
    "from dot_work.db_issues",
    "from dot_work.knowledge_graph",
    "from dot_work.overview",
    "from dot_work.python",
    "from dot_work.review",
    "from dot_work.version",
]

# Core commands that should work
CORE_COMMANDS = [
    "install",
    "list",
    "detect",
    "init",
    "init-tracking",
    "status",
    "plugins",
    "validate",
    "canonical",
    "prompt",
    "prompts",
    "zip",
    "skills",
    "subagents",
]


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    check_name: str
    passed: bool
    message: str
    details: dict[str, str | int | bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class MigrationValidator:
    """Validate the migration by checking the main project still works."""

    def __init__(self, project_root: Path, verbose: bool = False):
        """Initialize the validator.

        Args:
            project_root: Root directory of dot-work project
            verbose: Enable verbose logging
        """
        self.project_root = project_root
        self.src_path = project_root / "src" / "dot_work"
        self.verbose = verbose

        # Setup logging
        self._setup_logging()

        # Results tracking
        self.results: list[ValidationResult] = []

    def _setup_logging(self) -> None:
        """Setup logging."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger("migration_validator")

    def _log_result(self, result: ValidationResult) -> None:
        """Log a validation result.

        Args:
            result: The validation result to log
        """
        self.results.append(result)

        status = "✓ PASS" if result.passed else "✗ FAIL"
        self.logger.info(f"{status}: {result.check_name}")
        if result.message:
            self.logger.info(f"  {result.message}")
        if self.verbose and result.details:
            for key, value in result.details.items():
                self.logger.debug(f"  {key}: {value}")

    def validate_source_structure(self) -> ValidationResult:
        """Verify only core modules remain in src/dot_work/."""
        self.logger.info("Validating source structure...")

        errors: list[str] = []
        found_forbidden: list[str] = []
        missing_core: list[str] = []

        # Check no forbidden modules exist
        for forbidden in FORBIDDEN_MODULES:
            path = self.src_path / forbidden.rstrip("/")
            if path.exists():
                found_forbidden.append(forbidden)

        # Check core modules exist
        for core in CORE_MODULES:
            path = self.src_path / core.rstrip("/")
            if not path.exists():
                missing_core.append(core)

        if found_forbidden:
            errors.append(f"Found forbidden modules: {', '.join(found_forbidden)}")

        if missing_core:
            errors.append(f"Missing core modules: {', '.join(missing_core)}")

        passed = not errors
        message = "; ".join(errors) if errors else "Source structure is correct"

        result = ValidationResult(
            check_name="source_structure",
            passed=passed,
            message=message,
            details={
                "forbidden_found": len(found_forbidden),
                "core_missing": len(missing_core),
                "forbidden_list": found_forbidden,
                "missing_list": missing_core,
            },
        )
        self._log_result(result)
        return result

    def validate_imports(self) -> ValidationResult:
        """Verify no broken imports in core code."""
        self.logger.info("Validating imports...")

        # Try to import dot_work
        try:
            result = subprocess.run(
                ["uv", "run", "python", "-c", "import dot_work"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            import_ok = result.returncode == 0
            import_error = result.stderr if result.returncode != 0 else ""

        except subprocess.TimeoutExpired:
            import_ok = False
            import_error = "Import timed out"
        except Exception as e:
            import_ok = False
            import_error = str(e)

        # Check for forbidden imports in source files
        # Allow try/except wrapped imports (they're safe)
        found_forbidden: list[tuple[str, str]] = []

        for py_file in self.src_path.rglob("*.py"):
            # Skip __pycache__ and temp files
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    for forbidden in FORBIDDEN_IMPORTS:
                        if forbidden in line:
                            # Check if it's in a try/except block (safe)
                            # Look back up to 5 lines for "try:"
                            in_try = False
                            for j in range(max(0, i - 5), i):
                                if "try:" in lines[j] or "try :" in lines[j]:
                                    in_try = True
                                    break

                            if not in_try:
                                rel_path = py_file.relative_to(self.project_root)
                                found_forbidden.append((str(rel_path), forbidden, i + 1))
            except Exception:
                # Skip files that can't be read
                continue

        # Build result
        errors: list[str] = []
        if not import_ok:
            errors.append(f"Import failed: {import_error}")

        if found_forbidden:
            errors.append(f"Found {len(found_forbidden)} forbidden imports")
            for file_path, imp, line_num in found_forbidden[:5]:  # Show first 5
                errors.append(f"  {file_path}:{line_num}: {imp}")

        passed = import_ok and not found_forbidden
        message = "; ".join(errors) if errors else "No broken imports found"

        result = ValidationResult(
            check_name="imports",
            passed=passed,
            message=message,
            details={
                "import_ok": import_ok,
                "import_error": import_error,
                "forbidden_count": len(found_forbidden),
                "forbidden_imports": [f"{f}:{ln}: {i}" for f, i, ln in found_forbidden],
            },
        )
        self._log_result(result)
        return result

    def validate_core_commands(self) -> ValidationResult:
        """Verify core CLI commands work."""
        self.logger.info("Validating core commands...")

        # Test that CLI app loads
        try:
            result = subprocess.run(
                ["uv", "run", "python", "-m", "dot_work.cli", "--help"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            cli_ok = result.returncode == 0
            help_output = result.stdout

        except subprocess.TimeoutExpired:
            cli_ok = False
            help_output = "CLI timed out"
        except Exception as e:
            cli_ok = False
            help_output = str(e)

        # Check for core commands in help output
        missing_commands: list[str] = []
        found_commands: list[str] = []

        for command in CORE_COMMANDS:
            if command in help_output:
                found_commands.append(command)
            else:
                missing_commands.append(command)

        passed = cli_ok and not missing_commands
        message = "All core commands available" if passed else f"Missing commands: {missing_commands}"

        result = ValidationResult(
            check_name="core_commands",
            passed=passed,
            message=message,
            details={
                "cli_ok": cli_ok,
                "commands_found": len(found_commands),
                "commands_missing": len(missing_commands),
                "found_list": found_commands,
                "missing_list": missing_commands,
            },
        )
        self._log_result(result)
        return result

    def validate_no_submodule_tests(self) -> ValidationResult:
        """Verify that submodule tests were removed from tests/."""
        self.logger.info("Validating test directory structure...")

        tests_path = self.project_root / "tests"
        problems: list[str] = []

        if tests_path.exists():
            # Check for submodule test directories
            test_dirs = [
                "tests/unit/container",
                "tests/unit/git",
                "tests/unit/harness",
                "tests/unit/db_issues",
                "tests/unit/knowledge_graph",
                "tests/unit/overview",
                "tests/unit/python",
                "tests/unit/review",
                "tests/unit/version",
                "tests/integration/container",
                "tests/integration/test_git_history",
                "tests/integration/knowledge_graph",
                "tests/integration/test_plugin_ecosystem",
                "tests/integration/test_server",
                "tests/integration/db_issues",
            ]

            for test_dir in test_dirs:
                full_path = self.project_root / test_dir
                if full_path.exists():
                    problems.append(f"Test directory still exists: {test_dir}")

        # Check for temp-original-submodules (should exist as backup)
        temp_path = self.project_root / ".temp-original-submodules"
        temp_exists = temp_path.exists()

        passed = not problems
        message = "; ".join(problems) if problems else "Test directories properly cleaned up"

        result = ValidationResult(
            check_name="test_structure",
            passed=passed,
            message=message,
            details={
                "problems_found": len(problems),
                "problem_list": problems,
                "temp_backup_exists": temp_exists,
            },
        )
        self._log_result(result)
        return result

    def run_all(self, checks: list[str] | None = None) -> list[ValidationResult]:
        """Run all validation checks.

        Args:
            checks: List of specific checks to run (None = all)

        Returns:
            List of validation results
        """
        self.logger.info("Starting migration validation...\n")

        # Map check names to methods
        check_methods = {
            "source": self.validate_source_structure,
            "imports": self.validate_imports,
            "commands": self.validate_core_commands,
            "tests": self.validate_no_submodule_tests,
        }

        # Determine which checks to run
        if checks:
            for check_name in checks:
                if check_name not in check_methods:
                    self.logger.warning(f"Unknown check: {check_name}")
            check_list = [(name, check_methods[name]) for name in checks if name in check_methods]
        else:
            check_list = list(check_methods.items())

        # Run checks
        for name, method in check_list:
            try:
                method()
            except Exception as e:
                self.logger.error(f"Check '{name}' failed with exception: {e}")
                if self.verbose:
                    import traceback

                    traceback.print_exc()

        return self.results

    def generate_report(self, output_path: Path) -> None:
        """Generate JSON report of validation results.

        Args:
            output_path: Path to write the report file
        """
        report = {
            "timestamp": Path.cwd().stat().st_mtime,
            "total_checks": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "results": [r.to_dict() for r in self.results],
        }

        output_path.write_text(json.dumps(report, indent=2))
        self.logger.info(f"Report written to: {output_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate main project after submodule removal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--check",
        nargs="+",
        choices=["source", "imports", "commands", "tests"],
        help="Specific checks to run (default: all)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=Path("validation-report.json"),
        help="Output report file (default: validation-report.json)",
    )

    args = parser.parse_args()

    # Create validator
    validator = MigrationValidator(
        project_root=PROJECT_ROOT,
        verbose=args.verbose,
    )

    # Run validation
    results = validator.run_all(args.check)

    # Generate report
    if args.report:
        validator.generate_report(args.report)

    # Print summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"Validation Summary: {passed}/{total} checks passed")
    print(f"{'=' * 60}")

    if passed == total:
        print("✓ All checks passed!")
        return 0
    else:
        print(f"✗ {total - passed} check(s) failed")
        for result in results:
            if not result.passed:
                print(f"  - {result.check_name}: {result.message}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
