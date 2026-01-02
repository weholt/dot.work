#!/usr/bin/env python3
"""Add build.py script to all exported projects.

This script copies and adapts the main dot-work build.py to each exported project,
customizing the source path for each package.
"""

import shutil
import sys
from pathlib import Path

# Project configuration: (exported_project_name, source_package_name)
PROJECTS = [
    ("dot-container", "dot_container"),
    ("dot-git", "dot_git"),
    ("dot-harness", "dot_harness"),
    ("dot-issues", "dot_issues"),
    ("dot-kg", "dot_kg"),
    ("dot-overview", "dot_overview"),
    ("dot-python", "dot_python"),
    ("dot-review", "dot_review"),
    ("dot-version", "dot_version"),
]

BUILD_PY_TEMPLATE = '''#!/usr/bin/env python3
"""Build script for {package_name}."""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


class BuildRunner:
    """Handles the build process for the project."""

    def __init__(self, verbose: bool = False, fix: bool = False, run_integration: bool = False):
        self.verbose = verbose
        self.fix = fix
        self.run_integration = run_integration
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / "src" / "{package_name}"
        self.tests_path = self.project_root / "tests"
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
            print(f"Running: {{' '.join(cmd)}}")

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
            return False, "", f"Command not found: {{cmd[0]}}"

    def print_step(self, step: str) -> None:
        """Print a build step header."""
        print(f"\\n{{'=' * 60}}")
        print(f"[TOOL] {{step}}")
        print(f"{{'=' * 60}}")

    def print_result(self, success: bool, step: str, output: str = "", error: str = "") -> None:
        """Print the result of a build step."""
        if success:
            print(f"[OK] {{step}} - PASSED")
        else:
            print(f"[FAIL] {{step}} - FAILED")
            self.failed_steps.append(step)
            if error:
                print(f"Error: {{error}}")
            if output:
                print(f"Output: {{output}}")

    def check_dependencies(self) -> bool:
        """Check if all required tools are available."""
        self.print_step("Checking Dependencies")

        tools = [
            ("uv", ["uv", "--version"]),
            ("ruff", ["uv", "run", "ruff", "--version"]),
            ("mypy", ["uv", "run", "mypy", "--version"]),
            ("pytest", ["uv", "run", "pytest", "--version"]),
        ]

        all_available = True
        for tool_name, cmd in tools:
            success, output, _error = self.run_command(cmd, f"Check {{tool_name}}")
            if success:
                version = output.strip().split("\\n")[0] if output else "unknown"
                print(f"[OK] {{tool_name}}: {{version}}")
            else:
                print(f"[FAIL] {{tool_name}}: Not available")
                all_available = False

        return all_available

    def sync_dependencies(self) -> bool:
        """Sync project dependencies."""
        self.print_step("Syncing Dependencies")
        success, output, error = self.run_command(
            ["uv", "sync", "--all-extras"], "Sync dependencies"
        )
        self.print_result(success, "Dependency Sync", output, error)
        return success

    def format_code(self) -> bool:
        """Format code with ruff."""
        self.print_step("Code Formatting")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {{self.src_path}}")
            return False

        cmd = ["uv", "run", "ruff", "format"]
        if self.fix:
            cmd.append(str(self.src_path))
        else:
            cmd.extend(["--check", str(self.src_path)])

        success_format, output_format, error_format = self.run_command(cmd, "ruff format")

        check_cmd = ["uv", "run", "ruff", "check"]
        if self.fix:
            check_cmd.append("--fix")
        check_cmd.append(str(self.src_path))

        success_check, output_check, error_check = self.run_command(check_cmd, "ruff check")

        self.print_result(success_format, "ruff format", output_format, error_format)
        self.print_result(success_check, "ruff check", output_check, error_check)

        return success_format and success_check

    def lint_code(self) -> bool:
        """Lint code with ruff."""
        self.print_step("Code Linting")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {{self.src_path}}")
            return False

        cmd = ["uv", "run", "ruff", "check"]
        if self.fix:
            cmd.append("--fix")
        cmd.append(str(self.src_path))

        success, output, error = self.run_command(cmd, "ruff linting")
        self.print_result(success, "ruff", output, error)
        return success

    def type_check(self) -> bool:
        """Type check with mypy."""
        self.print_step("Type Checking")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {{self.src_path}}")
            return False

        success, output, error = self.run_command(
            ["uv", "run", "mypy", str(self.src_path)],
            f"mypy {{self.src_path}}",
        )

        self.print_result(success, f"mypy {{self.src_path}}", output, error)
        return success

    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        self.print_step("Unit Tests")

        coverage_files = [".coverage", "htmlcov", "coverage.xml"]
        for file_name in coverage_files:
            path = self.project_root / file_name
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        if not self.tests_path.exists():
            print(f"[WARN] Test directory not found at {{self.tests_path}}")
            return False

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {{self.src_path}}")
            return False

        cmd = [
            "uv",
            "run",
            "pytest",
            str(self.tests_path),
            f"--cov={{self.src_path}}",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=15",  # Minimum while growing test suite
            "--durations=20",
            "-vv" if self.verbose else "-v",
        ]

        # Exclude integration tests unless explicitly requested
        if not self.run_integration:
            cmd.extend(["-m", "not integration"])
        else:
            print("[INFO] Including integration tests")

        if self.verbose:
            cmd[cmd.index("--durations=20")] = "--durations=50"

        success, output, error = self.run_command(
            cmd,
            "pytest with coverage",
            capture_output=False,
        )

        self.print_result(success, "Unit Tests with Coverage", "", "")

        if success:
            coverage_xml = self.project_root / "coverage.xml"
            if coverage_xml.exists():
                import xml.etree.ElementTree as ET

                try:
                    tree = ET.parse(coverage_xml)
                    root = tree.getroot()
                    coverage_elem = root.find(".//coverage")
                    if coverage_elem is not None:
                        line_rate = float(coverage_elem.get("line-rate", "0"))
                        coverage_pct = int(line_rate * 100)
                        print(f"Code Coverage: {{coverage_pct}}%")
                        if coverage_pct < 75:
                            print("WARNING: Coverage below 75% threshold!")
                            return False
                except Exception as e:
                    print(f"Warning: Could not parse coverage.xml: {{e}}")
            else:
                print("Warning: coverage.xml not found")

        return success

    def step_security(self) -> bool:
        """Run security checks."""
        self.print_step("Security Checks")

        if not self.src_path.exists():
            print(f"[WARN] Source directory not found at {{self.src_path}}")
            return False

        success, output, error = self.run_command(
            ["uv", "run", "ruff", "check", str(self.src_path), "--select", "S"],
            "Security linting",
        )

        self.print_result(success, "Security Check", output, error)
        return success

    def generate_reports(self) -> bool:
        """Generate build reports."""
        self.print_step("Generating Reports")

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
        print("{package_name} - Build Pipeline")
        print(f"{{'=' * 60}}")

        start_time = time.time()

        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Sync Dependencies", self.sync_dependencies),
            ("Format Code", self.format_code),
            ("Lint Code", self.lint_code),
            ("Type Check", self.type_check),
            ("Security Check", self.step_security),
            ("Unit Tests", self.run_unit_tests),
            ("Generate Reports", self.generate_reports),
        ]

        success_count = 0
        total_steps = len(steps)

        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
            except Exception as e:
                print(f"[FAIL] {{step_name}} failed with exception: {{e}}")
                self.failed_steps.append(step_name)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\\n{{'=' * 60}}")
        print("[STAT] Build Summary")
        print(f"{{'=' * 60}}")
        print(f"[OK] Successful steps: {{success_count}}/{{total_steps}}")
        print(f"[TIME]  Build duration: {{duration:.2f}} seconds")

        if self.failed_steps:
            print(f"[FAIL] Failed steps: {{', '.join(self.failed_steps)}}")

        if success_count == total_steps:
            print("\\n[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!")
            print("[PKG] Ready for deployment")
            return True
        elif success_count >= total_steps - 1:
            print(f"\\n[WARN]  BUILD MOSTLY SUCCESSFUL - {{total_steps - success_count}} minor issues")
            print("[TOOL] Consider addressing failed steps before deployment")
            return True
        else:
            print(f"\\n[FAIL] BUILD FAILED - {{total_steps - success_count}} critical issues")
            print("[FIX]  Please fix the failed steps before proceeding")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build script for {package_name}")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix formatting and linting issues")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts and exit")
    parser.add_argument(
        "--integration",
        choices=["all", "none"],
        default="none",
        help="Run integration tests: 'all' to include them, 'none' to skip (default: none)",
    )

    args = parser.parse_args()

    builder = BuildRunner(
        verbose=args.verbose,
        fix=args.fix,
        run_integration=args.integration == "all",
    )

    if args.clean:
        builder.clean_artifacts()
        return 0

    success = builder.run_full_build()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
'''


def add_build_script(exported_projects_dir: Path, dry_run: bool = False) -> dict[str, dict]:
    """Add build.py script to all exported projects.

    Args:
        exported_projects_dir: Path to EXPORTED_PROJECTS directory
        dry_run: If True, show what would be done without making changes

    Returns:
        Dictionary with results for each project
    """
    results = {}

    for project_name, package_name in PROJECTS:
        project_dir = exported_projects_dir / project_name
        scripts_dir = project_dir / "scripts"
        build_py_path = scripts_dir / "build.py"

        print(f"\n=== Processing {project_name} ===")

        # Check if project exists
        if not project_dir.exists():
            print(f"[SKIP] {project_name} does not exist")
            results[project_name] = {"status": "skip", "reason": "project not found"}
            continue

        # Check if build.py already exists
        if build_py_path.exists():
            print(f"[SKIP] {project_name}/scripts/build.py already exists")
            results[project_name] = {"status": "skip", "reason": "already exists"}
            continue

        if dry_run:
            print(f"[DRY RUN] Would create {build_py_path}")
            results[project_name] = {"status": "dry_run", "path": str(build_py_path)}
            continue

        # Create scripts directory
        scripts_dir.mkdir(parents=True, exist_ok=True)
        print(f"[CREATE] {scripts_dir}")

        # Generate build.py with package-specific customization
        build_content = BUILD_PY_TEMPLATE.format(package_name=package_name)
        build_py_path.write_text(build_content)
        print(f"[CREATE] {build_py_path}")

        # Make executable
        build_py_path.chmod(0o755)
        print(f"[CHMOD] +x {build_py_path}")

        results[project_name] = {
            "status": "created",
            "path": str(build_py_path),
            "package": package_name,
        }

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Add build.py script to all exported projects"
    )
    parser.add_argument(
        "--exported-dir",
        type=Path,
        default=Path("EXPORTED_PROJECTS"),
        help="Path to EXPORTED_PROJECTS directory (default: EXPORTED_PROJECTS)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    if not args.exported_dir.exists():
        print(f"[ERROR] Exported projects directory not found: {args.exported_dir}")
        return 1

    print(f"Exported projects directory: {args.exported_dir}")
    print(f"Projects to process: {len(PROJECTS)}")

    if args.dry_run:
        print("[DRY RUN] No changes will be made")

    results = add_build_script(args.exported_dir, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    created = sum(1 for r in results.values() if r["status"] == "created")
    skipped = sum(1 for r in results.values() if r["status"] == "skip")
    dry_runs = sum(1 for r in results.values() if r["status"] == "dry_run")

    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print(f"Dry run: {dry_runs}")
    print(f"Total: {len(results)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
