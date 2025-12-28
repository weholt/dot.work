#!/usr/bin/env python3
"""
Comprehensive build script for Solace.

Now extended with static-analysis and code-quality tools:
- Radon (complexity/maintainability)
- Vulture (dead code)
- jscpd (duplication)
- Import Linter (layer violations)
- Bandit (security)
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


class BuildRunner:
    """Handles the build process for Solace."""

    def __init__(self, verbose: bool = False, fix: bool = False, integration_suite: str | None = None):
        self.verbose = verbose
        self.fix = fix
        self.integration_suite = integration_suite
        self.project_root = Path(__file__).parent
        self.failed_steps: list[str] = []

    def run_command(
        self,
        cmd: list[str],
        description: str,
        check: bool = True,
        capture_output: bool = True,
    ) -> tuple[bool, str, str]:
        """Run a command and return success status and output."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                check=check,
                encoding="utf-8",
                errors="replace",
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or ""
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"

    def print_step(self, step: str) -> None:
        """Print a build step header."""
        print(f"\n{'=' * 60}")
        print(f"[TOOL] {step}")
        print(f"{'=' * 60}")

    def print_result(self, success: bool, step: str, output: str = "", error: str = "") -> None:
        """Print the result of a build step."""
        if success:
            print(f"[OK] {step} - PASSED")
        else:
            print(f"[FAIL] {step} - FAILED")
            self.failed_steps.append(step)
            if error:
                print(f"Error: {error}")
            if output:
                print(f"Output: {output}")

    def check_dependencies(self) -> bool:
        """Check if all required tools are available."""
        self.print_step("Checking Dependencies")

        tools = [
            ("uv", ["uv", "--version"]),
            ("ruff", ["uv", "run", "ruff", "--version"]),
            ("mypy", ["uv", "run", "python", "-m", "mypy", "--version"]),
            ("pytest", ["uv", "run", "python", "-m", "pytest", "--version"]),
        ]

        all_available = True
        for tool_name, cmd in tools:
            success, output, _error = self.run_command(cmd, f"Check {tool_name}")
            if success:
                version = output.strip().split("\n")[0] if output else "unknown"
                print(f"[OK] {tool_name}: {version}")
            else:
                print(f"[FAIL] {tool_name}: Not available")
                all_available = False

        return all_available

    def sync_dependencies(self) -> bool:
        """Sync project dependencies."""
        self.print_step("Syncing Dependencies")

        success, output, error = self.run_command(["uv", "sync"], "Sync dependencies")

        self.print_result(success, "Dependency Sync", output, error)
        return success

    def format_code(self) -> bool:
        """Format code with ruff."""
        self.print_step("Code Formatting")

        ruff_format_cmd = ["uv", "run", "ruff", "format"]
        if not self.fix:
            ruff_format_cmd.append("--check")
        ruff_format_cmd.extend(["--exclude", "tests", "--exclude", "scripts", "solace"])

        success_format, output_format, error_format = self.run_command(ruff_format_cmd, "ruff format")

        ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix", "--exclude", "tests", "--exclude", "scripts", "solace"]

        success_check, output_check, error_check = self.run_command(ruff_check_cmd, "ruff check")

        self.print_result(success_format, "ruff format", output_format, error_format)
        self.print_result(success_check, "ruff check", output_check, error_check)

        return success_format and success_check

    def lint_code(self) -> bool:
        """Lint code with ruff."""
        self.print_step("Code Linting")

        ruff_cmd = ["uv", "run", "ruff", "check", "--fix", "--exclude", "tests", "--exclude", "scripts", "solace"]

        success, output, error = self.run_command(ruff_cmd, "ruff linting")

        self.print_result(success, "ruff", output, error)
        return success

    def check_deprecated_config(self) -> bool:
        """Check for usage of deprecated config properties."""
        self.print_step("Deprecated Config Check")

        deprecated_tokens = ["docs_dir", "prompts_dir", "resources_dir", "templates_dir"]

        # Allowlist: files that can mention these for backward compatibility or documentation
        allowlist = [
            "solace/env_config.py",  # Backward compatibility warning
            "project-docs/agent/strict-layout-refactor-plan.md",  # Historical reference
        ]

        violations: list[tuple[str, str, int]] = []

        for token in deprecated_tokens:
            # Search in Python files
            success, output, _error = self.run_command(
                ["git", "grep", "-n", f"config\\.{token}", "--", "solace/"],
                f"Search for config.{token}",
                check=False,
            )

            if success and output:
                for line in output.strip().split("\n"):
                    if line:
                        # Parse git grep output: file:line:content
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            filepath, linenum, content = parts[0], parts[1], parts[2]
                            # Check if file is in allowlist
                            if not any(allowed in filepath for allowed in allowlist):
                                violations.append((filepath, token, int(linenum)))

        if violations:
            print("[FAIL] Found deprecated config property usage:")
            for filepath, token, linenum in violations:
                print(f"  {filepath}:{linenum} - config.{token}")
            print("\n[FIX] Replace with:")
            print("  - config.docs_dir → config.data_dir")
            print("  - Use helper functions from solace.utils.repo_helpers")
            print("  - See project-docs/agent/strict-layout-refactor-plan.md")
            self.print_result(False, "Deprecated Config Check")
            return False
        else:
            print("[OK] No deprecated config property usage found")
            self.print_result(True, "Deprecated Config Check")
            return True

    def run_static_analysis(self) -> bool:
        """Run non-visual static-analysis tools."""
        self.print_step("Static Code Analysis")

        analysis_dir = self.project_root / "project-docs" / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        tools = [
            (
                "Radon Complexity",
                ["uv", "run", "radon", "cc", "solace", "-s", "-a", "-j"],
                analysis_dir / "complexity.json",
            ),
            (
                "Radon Maintainability",
                ["uv", "run", "radon", "mi", "solace", "-j"],
                analysis_dir / "maintainability.json",
            ),
            (
                "Vulture Dead Code",
                ["uv", "run", "vulture", "solace"],
                analysis_dir / "deadcode.txt",
            ),
            (
                "jscpd Duplication",
                ["uv", "run", "jscpd", "--reporters", "json", "--languages", "python", "solace"],
                analysis_dir / "duplication.json",
            ),
            (
                "Import-Linter Dependencies",
                ["uv", "run", "lint-imports"],
                analysis_dir / "dependencies.txt",
            ),
            (
                "Bandit Security Scan",
                ["uv", "run", "bandit", "-r", "solace", "-f", "json"],
                analysis_dir / "bandit.json",
            ),
        ]

        all_ok = True
        for name, cmd, outfile in tools:
            success, output, error = self.run_command(cmd, name, check=False)
            if output:
                outfile.write_text(output)
            self.print_result(success, name, output[:300], error)
            all_ok = all_ok and success

        return all_ok

    def type_check(self) -> bool:
        """Type check with mypy."""
        self.print_step("Type Checking")

        success_module, output_module, error_module = self.run_command(["uv", "run", "python", "-m", "mypy", "solace/"], "mypy solace/")

        self.print_result(success_module, "mypy solace/", output_module, error_module)

        return success_module

    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        self.print_step("Unit Tests")

        coverage_files = [".coverage", "htmlcov", "coverage.xml"]
        for file_path in coverage_files:
            path = self.project_root / file_path
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "pytest",
            "tests/",
            "--ignore=tests/integration",  # Exclude integration tests directory
            "-m",
            "not playwright and not e2e",  # Exclude playwright and e2e tests (require server)
            "--cov=solace",
            "--cov-report=term",
            "--cov-report=html",
            "--cov-report=xml",
            "--timeout=5",
            "-vv" if self.verbose else "-v",
        ]

        success, output, error = self.run_command(
            cmd,
            "pytest with coverage (excluding playwright, e2e, and integration)",
        )

        self.print_result(success, "Unit Tests with Coverage", output, error)

        if success and output:
            lines = output.split("\n")
            for line in lines:
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage = parts[-1].rstrip("%")
                        try:
                            coverage_pct = int(coverage)
                            print(f"Code Coverage: {coverage_pct}%")
                            # 69% threshold accounts for CLI (thin UI layer) and manual test scripts excluded
                            if coverage_pct < 69:
                                print("WARNING: Coverage below 69% threshold!")
                                return False
                        except ValueError:
                            pass
                    break

        return success

    def run_integration_suite(self, suite: str = "all") -> bool:
        """Run integration tests by suite.

        Args:
            suite: Which test suite to run:
                - 'api': API endpoint tests
                - 'cli': CLI command tests
                - 'mcp': MCP tool tests
                - 'web': Web UI template tests
                - 'playwright': Browser automation tests
                - 'all': All integration tests (default)
        """
        valid_suites = ["api", "cli", "mcp", "web", "playwright", "all"]

        if suite not in valid_suites:
            print(f"[ERROR] Unknown integration suite: {suite}")
            print(f"[INFO]  Available suites: {', '.join(valid_suites)}")
            return False

        self.print_step(f"Integration Tests ({suite})")

        cmd = [
            "uv",
            "run",
            "python",
            "scripts/run_tests.py",
            "--integration",
            suite,
        ]

        if self.verbose:
            cmd.append("--verbose")

        success, output, error = self.run_command(
            cmd,
            f"Integration tests: {suite}",
            capture_output=not self.verbose,
        )

        self.print_result(success, f"Integration Tests ({suite})", output, error)
        return success

    def run_security_check(self) -> bool:
        """Run security checks."""
        self.print_step("Security Checks")

        success, output, error = self.run_command(["uv", "run", "ruff", "check", "--exclude", "tests", "--exclude", "scripts", "solace", "--select", "S"], "Security linting")

        self.print_result(success, "Security Check", output, error)
        return success

    def build_documentation(self) -> bool:
        """Build documentation with MkDocs."""
        self.print_step("Building Documentation")

        success, output, error = self.run_command(["uv", "run", "mkdocs", "build"], "mkdocs build")

        if success:
            docs_dir = self.project_root / "docs"
            if docs_dir.exists():
                print("[OK] Documentation built to: docs/")
            else:
                print("[WARN]  Documentation directory not found after build")
                success = False

        self.print_result(success, "Documentation Build", output, error)
        return success

    def generate_reports(self) -> bool:
        """Generate build reports."""
        self.print_step("Generating Reports")

        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

        coverage_html = self.project_root / "htmlcov"
        if coverage_html.exists():
            print("[OK] Coverage HTML report: htmlcov/index.html")

        coverage_xml = self.project_root / "coverage.xml"
        if coverage_xml.exists():
            print("[OK] Coverage XML report: coverage.xml")

        return True

    def clean_artifacts(self) -> bool:
        """Clean build artifacts."""
        self.print_step("Cleaning Artifacts")

        artifacts = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.egg-info",
            ".coverage",
        ]

        for pattern in artifacts:
            if pattern.startswith("*"):
                for path in self.project_root.glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            else:
                path = self.project_root / pattern
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        print("[OK] Cleaned build artifacts")
        return True

    def run_full_build(self) -> bool:
        """Run the complete build pipeline."""
        print("Solace - Comprehensive Build Pipeline")
        print(f"{'=' * 80}")

        start_time = time.time()

        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Sync Dependencies", self.sync_dependencies),
            ("Format Code", self.format_code),
            ("Lint Code", self.lint_code),
            ("Deprecated Config Check", self.check_deprecated_config),
            ("Static Analysis", self.run_static_analysis),
            ("Type Check", self.type_check),
            ("Security Check", self.run_security_check),
            ("Unit Tests", self.run_unit_tests),
            ("Build Documentation", self.build_documentation),
            ("Generate Reports", self.generate_reports),
        ]

        success_count = 0
        total_steps = len(steps)

        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
            except Exception as e:
                print(f"[FAIL] {step_name} failed with exception: {e}")
                self.failed_steps.append(step_name)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'=' * 80}")
        print("[STAT] Build Summary")
        print(f"{'=' * 80}")
        print(f"[OK] Successful steps: {success_count}/{total_steps}")
        print(f"[TIME]  Build duration: {duration:.2f} seconds")

        if self.failed_steps:
            print(f"[FAIL] Failed steps: {', '.join(self.failed_steps)}")

        if success_count == total_steps:
            print("\n[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!")
            print("[PKG] Ready for deployment")
            return True
        elif success_count >= total_steps - 1:
            print(f"\n[WARN]  BUILD MOSTLY SUCCESSFUL - {total_steps - success_count} minor issues")
            print("[TOOL] Consider addressing failed steps before deployment")
            return True
        else:
            print(f"\n[FAIL] BUILD FAILED - {total_steps - success_count} critical issues")
            print("[FIX]  Please fix the failed steps before proceeding")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive build script for Solace")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--fix", action="store_true", help="Automatically fix formatting and linting issues")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts and exit")
    parser.add_argument(
        "--integration",
        choices=["all", "api", "cli", "mcp", "web", "playwright"],
        help="Run integration test suite (all, api, cli, mcp, web, or playwright)",
    )

    args = parser.parse_args()

    builder = BuildRunner(verbose=args.verbose, fix=args.fix, integration_suite=args.integration)

    if args.clean:
        builder.clean_artifacts()
        return 0

    success = builder.run_full_build()

    # Optionally run integration tests after main build
    if args.integration and success:
        print(f"\n{'=' * 80}")
        print(f"Running Integration Tests: {args.integration}")
        print(f"{'=' * 80}\n")
        integration_success = builder.run_integration_suite(args.integration)
        if not integration_success:
            print(f"\n[WARN]  {args.integration} integration tests failed, but main build passed")
            print("[INFO] Use 'python scripts/run_tests.py --help' for more options")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
