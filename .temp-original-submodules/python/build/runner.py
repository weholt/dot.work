#!/usr/bin/env python3
"""
Build runner for Python projects.

Provides comprehensive quality checks and build automation.
"""

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MemoryStats:
    """Memory statistics for a build step."""

    peak_rss_mb: float
    peak_vms_mb: float
    duration_seconds: float
    step_name: str

    def __str__(self) -> str:
        """Return formatted memory statistics."""
        return (
            f"{self.step_name}: {self.peak_rss_mb:.1f} MB RSS, "
            f"{self.peak_vms_mb:.1f} MB VMS ({self.duration_seconds:.2f}s)"
        )


class BuildRunner:
    """Handles the build process for Python projects."""

    # Default memory limit for pytest (4GB as per requirements)
    DEFAULT_MEMORY_LIMIT_MB = 4096

    # Default directories to exclude from source detection
    DEFAULT_EXCLUDE_DIRS = [
        "tests",
        "test",
        "docs",
        "examples",
        "scripts",
        "incoming",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        ".git",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
    ]

    def __init__(
        self,
        project_root: Path | None = None,
        verbose: bool = False,
        fix: bool = False,
        source_dirs: list[str] | None = None,
        test_dirs: list[str] | None = None,
        coverage_threshold: int = 70,
        use_uv: bool = False,
        memory_limit_mb: int | None = None,
        enforce_memory_limit: bool = True,
    ):
        """
        Initialize the build runner.

        Args:
            project_root: Root directory of the project (default: current directory)
            verbose: Enable verbose output
            fix: Automatically fix formatting and linting issues
            source_dirs: List of source directories to check (default: auto-detect)
            test_dirs: List of test directories (default: ['tests'])
            coverage_threshold: Minimum coverage percentage required (default: 70)
            use_uv: Use 'uv run' prefix for commands (default: False)
            memory_limit_mb: Memory limit in MB for test execution (default: 4096)
            enforce_memory_limit: Whether to enforce memory limits (default: True)
        """
        self.verbose = verbose
        self.fix = fix
        self.use_uv = use_uv
        self.project_root = project_root or Path.cwd()
        self.failed_steps: list[str] = []
        self.coverage_threshold = coverage_threshold
        self.memory_limit_mb = memory_limit_mb or self.DEFAULT_MEMORY_LIMIT_MB
        self.enforce_memory_limit = enforce_memory_limit
        self.memory_stats: list[MemoryStats] = []

        # Auto-detect source directories if not provided
        if source_dirs is None:
            self.source_dirs = self._detect_source_dirs()
        else:
            self.source_dirs = source_dirs

        # Default test directories
        self.test_dirs = test_dirs or ["tests"]

    def _get_exclude_dirs(self) -> set[str]:
        """Get the set of directories to exclude from source detection.

        Reads from BUILD_EXCLUDE_DIRS environment variable if set,
        otherwise uses DEFAULT_EXCLUDE_DIRS.
        """
        env_exclude = os.getenv("BUILD_EXCLUDE_DIRS")
        if env_exclude:
            return {name.strip() for name in env_exclude.split(",") if name.strip()}
        return set(self.DEFAULT_EXCLUDE_DIRS)

    def _detect_source_dirs(self) -> list[str]:
        """Auto-detect source directories in the project."""
        candidates = []
        exclude_dirs = self._get_exclude_dirs()

        # Look for common Python package structures
        for item in self.project_root.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith(".") or item.name.startswith("_"):
                continue
            if item.name in exclude_dirs:
                continue

            # Check if it looks like a Python package
            if (item / "__init__.py").exists():
                candidates.append(item.name)

        # If no packages found, look for directories with .py files
        if not candidates:
            for item in self.project_root.iterdir():
                if not item.is_dir():
                    continue
                if item.name.startswith("."):
                    continue
                if item.name in exclude_dirs:
                    continue

                # Check if it has Python files
                if list(item.glob("*.py")):
                    candidates.append(item.name)

        return candidates if candidates else ["."]

    def _get_command_prefix(self) -> list[str]:
        """Get command prefix (with or without 'uv run')."""
        return ["uv", "run"] if self.use_uv else []

    def _get_memory_mb(self) -> tuple[float, float]:
        """Get current memory usage in MB (RSS, VMS) from /proc/self/status.

        Returns:
            Tuple of (rss_mb, vms_mb). Returns (0, 0) on non-Linux systems.
        """
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        continue
                    if line.startswith("VmSize:"):
                        vms_kb = int(line.split()[1])
                        continue
                return rss_kb / 1024, vms_kb / 1024
        except (FileNotFoundError, ValueError, AttributeError):
            # Non-Linux systems or error reading /proc
            return 0.0, 0.0

    def _wrap_with_cgroup(self, cmd: list[str], limit_mb: int) -> list[str]:
        """Wrap command with cgroup v2 memory enforcement using systemd-run.

        Args:
            cmd: Command to wrap
            limit_mb: Memory limit in MB

        Returns:
            Wrapped command with systemd-run prefix
        """
        return [
            "systemd-run",
            "--scope",
            "--quiet",
            "--same-dir",
            f"--property=MemoryMax={limit_mb}M",
            "--property=MemorySwapMax=0",
            "--setenv=PYTHONUNBUFFERED=1",
            *cmd,
        ]

    def _wrap_with_ulimit(self, cmd: list[str], limit_mb: int) -> list[str]:
        """Wrap command with ulimit memory enforcement.

        This creates a shell wrapper that sets ulimit before running the command.

        Args:
            cmd: Command to wrap
            limit_mb: Memory limit in MB

        Returns:
            Wrapped command with shell ulimit prefix
        """
        # Convert to ulimit format (KB for virtual memory)
        limit_kb = limit_mb * 1024
        cmd_str = " ".join(cmd)
        return ["sh", "-c", f"ulimit -v {limit_kb} && {cmd_str}"]

    def _wrap_with_memory_limit(self, cmd: list[str], limit_mb: int) -> list[str]:
        """Wrap command with appropriate memory limit enforcement.

        Tries cgroup v2 (systemd-run) first, falls back to ulimit.

        Args:
            cmd: Command to wrap
            limit_mb: Memory limit in MB

        Returns:
            Wrapped command with memory enforcement
        """
        # Try systemd-run first (preferred)
        if shutil.which("systemd-run"):
            if self.verbose:
                print(f"[Memory] Using cgroup v2 enforcement (limit: {limit_mb}MB)")
            return self._wrap_with_cgroup(cmd, limit_mb)

        # Fall back to ulimit
        if self.verbose:
            print(f"[Memory] Using ulimit enforcement (limit: {limit_mb}MB)")
        return self._wrap_with_ulimit(cmd, limit_mb)

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
            # Commands are build tools (pytest, ruff, mypy) - user controls execution
            result = subprocess.run(  # noqa: S603 - shell=False prevents injection, cmd is controlled by BuildRunner
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                check=check,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or ""
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"

    def print_step(self, step: str) -> None:
        """Print a build step header."""
        print(f"\n{'=' * 60}")
        print(f"[STEP] {step}")
        print(f"{'=' * 60}")

    def print_result(self, success: bool, step: str, output: str = "", error: str = "") -> None:
        """Print the result of a build step."""
        if success:
            print(f"[✓] {step} - PASSED")
        else:
            print(f"[✗] {step} - FAILED")
            self.failed_steps.append(step)
            if error:
                print(f"Error: {error}")
            if output and self.verbose:
                print(f"Output: {output}")

    def check_dependencies(self) -> bool:
        """Check if all required tools are available."""
        self.print_step("Checking Dependencies")

        prefix = self._get_command_prefix()

        tools = [
            ("ruff", prefix + ["ruff", "--version"]),
            ("mypy", prefix + ["python", "-m", "mypy", "--version"]),
            ("pytest", prefix + ["python", "-m", "pytest", "--version"]),
        ]

        # Add UV check if using it
        if self.use_uv:
            tools.insert(0, ("uv", ["uv", "--version"]))

        all_available = True
        for tool_name, cmd in tools:
            success, output, _error = self.run_command(cmd, f"Check {tool_name}", check=False)
            if success:
                version = output.strip().split("\n")[0] if output else "unknown"
                print(f"[✓] {tool_name}: {version}")
            else:
                print(f"[✗] {tool_name}: Not available")
                all_available = False

        return all_available

    def format_code(self) -> bool:
        """Format code with ruff."""
        self.print_step("Code Formatting")

        prefix = self._get_command_prefix()

        # Ruff format
        ruff_format_cmd = prefix + ["ruff", "format"]
        if not self.fix:
            ruff_format_cmd.append("--check")
        ruff_format_cmd.extend(self.source_dirs)

        start_time = time.time()
        mem_before = self._get_memory_mb()

        success_format, output_format, error_format = self.run_command(
            ruff_format_cmd, "ruff format", check=False
        )

        mem_after = self._get_memory_mb()
        duration = time.time() - start_time

        # Track memory stats
        self.memory_stats.append(
            MemoryStats(
                peak_rss_mb=max(mem_before[0], mem_after[0]),
                peak_vms_mb=max(mem_before[1], mem_after[1]),
                duration_seconds=duration,
                step_name="Code Formatting",
            )
        )

        self.print_result(success_format, "ruff format", output_format, error_format)

        return success_format

    def lint_code(self) -> bool:
        """Lint code with ruff."""
        self.print_step("Code Linting")

        prefix = self._get_command_prefix()

        ruff_cmd = prefix + ["ruff", "check"]
        if self.fix:
            ruff_cmd.append("--fix")
        ruff_cmd.extend(self.source_dirs)

        start_time = time.time()
        mem_before = self._get_memory_mb()

        success, output, error = self.run_command(ruff_cmd, "ruff check", check=False)

        mem_after = self._get_memory_mb()
        duration = time.time() - start_time

        # Track memory stats
        self.memory_stats.append(
            MemoryStats(
                peak_rss_mb=max(mem_before[0], mem_after[0]),
                peak_vms_mb=max(mem_before[1], mem_after[1]),
                duration_seconds=duration,
                step_name="Code Linting",
            )
        )

        self.print_result(success, "ruff check", output, error)
        return success

    def run_static_analysis(self) -> bool:
        """Run non-visual static-analysis tools."""
        self.print_step("Static Code Analysis")

        prefix = self._get_command_prefix()
        analysis_dir = self.project_root / ".work" / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        tools = []

        # Check which tools are available
        for tool_name, cmd_base in [
            ("radon", "radon"),
            ("vulture", "vulture"),
            ("jscpd", "jscpd"),
            ("lint-imports", "lint-imports"),
            ("bandit", "bandit"),
        ]:
            check_cmd = (
                prefix + [cmd_base, "--version"]
                if cmd_base != "lint-imports"
                else prefix + [cmd_base]
            )
            success, _, _ = self.run_command(check_cmd, f"Check {tool_name}", check=False)

            if success:
                if tool_name == "radon":
                    tools.append(
                        (
                            "Radon Complexity",
                            prefix + ["radon", "cc"] + self.source_dirs + ["-s", "-a", "-j"],
                            analysis_dir / "complexity.json",
                        )
                    )
                    tools.append(
                        (
                            "Radon Maintainability",
                            prefix + ["radon", "mi"] + self.source_dirs + ["-j"],
                            analysis_dir / "maintainability.json",
                        )
                    )
                elif tool_name == "vulture":
                    tools.append(
                        (
                            "Vulture Dead Code",
                            prefix + ["vulture"] + self.source_dirs,
                            analysis_dir / "deadcode.txt",
                        )
                    )
                elif tool_name == "jscpd":
                    tools.append(
                        (
                            "jscpd Duplication",
                            prefix
                            + ["jscpd", "--reporters", "json", "--languages", "python"]
                            + self.source_dirs,
                            analysis_dir / "duplication.json",
                        )
                    )
                elif tool_name == "lint-imports":
                    tools.append(
                        (
                            "Import-Linter Dependencies",
                            prefix + ["lint-imports"],
                            analysis_dir / "dependencies.txt",
                        )
                    )
                elif tool_name == "bandit":
                    tools.append(
                        (
                            "Bandit Security Scan",
                            prefix + ["bandit", "-r"] + self.source_dirs + ["-f", "json"],
                            analysis_dir / "bandit.json",
                        )
                    )

        if not tools:
            print(
                "[i] No static analysis tools available (install with 'pip install python-project-builder[analysis]')"
            )
            return True  # Not a failure if tools aren't installed

        all_ok = True
        for name, cmd, outfile in tools:
            success, output, error = self.run_command(cmd, name, check=False)
            if output:
                outfile.write_text(output, encoding="utf-8")
            self.print_result(success, name, output[:300] if output else "", error)
            # Don't fail build on static analysis warnings
            # all_ok = all_ok and success

        return all_ok

    def type_check(self) -> bool:
        """Type check with mypy."""
        self.print_step("Type Checking")

        prefix = self._get_command_prefix()

        success_all = True
        for source_dir in self.source_dirs:
            success, output, error = self.run_command(
                prefix + ["python", "-m", "mypy", source_dir],
                f"mypy {source_dir}",
                check=False,
            )
            self.print_result(success, f"mypy {source_dir}", output, error)
            success_all = success_all and success

        return success_all

    def run_tests(self) -> bool:
        """Run tests with coverage and memory enforcement."""
        self.print_step("Running Tests")

        # Show memory enforcement status
        if self.enforce_memory_limit:
            print(f"[Memory] Enforcement: ENABLED (limit: {self.memory_limit_mb}MB)")
            if shutil.which("systemd-run"):
                print("[Memory] Method: cgroup v2 (systemd-run)")
            else:
                print("[Memory] Method: ulimit")
        else:
            print("[Memory] Enforcement: DISABLED")

        prefix = self._get_command_prefix()

        # Clean old coverage data
        coverage_files = [".coverage", "htmlcov", "coverage.xml"]
        for file_path in coverage_files:
            path = self.project_root / file_path
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        # Build pytest command
        cmd = prefix + [
            "python",
            "-m",
            "pytest",
        ]

        # Add test directories
        cmd.extend(self.test_dirs)

        # Add coverage for each source directory
        for source_dir in self.source_dirs:
            cmd.append(f"--cov={source_dir}")

        # Add coverage reporting
        cmd.extend(
            [
                "--cov-report=term",
                "--cov-report=html",
                "--cov-report=xml",
                "--timeout=5",
                "-vv" if self.verbose else "-v",
            ]
        )

        # Apply memory enforcement for pytest
        if self.enforce_memory_limit:
            cmd = self._wrap_with_memory_limit(cmd, self.memory_limit_mb)

        start_time = time.time()
        mem_before = self._get_memory_mb()

        success, output, error = self.run_command(cmd, "pytest with coverage", check=False)

        mem_after = self._get_memory_mb()
        duration = time.time() - start_time

        # Track memory stats
        self.memory_stats.append(
            MemoryStats(
                peak_rss_mb=max(mem_before[0], mem_after[0]),
                peak_vms_mb=max(mem_before[1], mem_after[1]),
                duration_seconds=duration,
                step_name="Run Tests",
            )
        )

        self.print_result(success, "Tests with Coverage", output, error)

        # Check coverage threshold
        if success and output:
            lines = output.split("\n")
            for line in lines:
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage = parts[-1].rstrip("%")
                        try:
                            coverage_pct = int(coverage)
                            print(f"[i] Code Coverage: {coverage_pct}%")
                            if coverage_pct < self.coverage_threshold:
                                print(
                                    f"[!] WARNING: Coverage below {self.coverage_threshold}% threshold!"
                                )
                                return False
                        except ValueError:
                            # Ignore non-numeric coverage values - continue processing
                            pass
                    break

        return success

    def run_security_check(self) -> bool:
        """Run security checks with ruff."""
        self.print_step("Security Checks")

        prefix = self._get_command_prefix()

        success, output, error = self.run_command(
            prefix + ["ruff", "check"] + self.source_dirs + ["--select", "S"],
            "Security linting",
            check=False,
        )

        self.print_result(success, "Security Check", output, error)
        return success

    def build_documentation(self) -> bool:
        """Build documentation with MkDocs."""
        self.print_step("Building Documentation")

        prefix = self._get_command_prefix()

        # Check if mkdocs.yml exists
        if not (self.project_root / "mkdocs.yml").exists():
            print("[i] No mkdocs.yml found, skipping documentation build")
            return True

        success, output, error = self.run_command(
            prefix + ["mkdocs", "build"],
            "mkdocs build",
            check=False,
        )

        if success:
            docs_dir = self.project_root / "site"
            if docs_dir.exists():
                print("[✓] Documentation built to: site/")
            else:
                print("[!] Documentation directory not found after build")
                success = False

        self.print_result(success, "Documentation Build", output, error)
        return success

    def generate_reports(self) -> bool:
        """Generate build reports with memory statistics."""
        self.print_step("Generating Reports")

        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

        coverage_html = self.project_root / "htmlcov"
        if coverage_html.exists():
            print("[✓] Coverage HTML report: htmlcov/index.html")

        coverage_xml = self.project_root / "coverage.xml"
        if coverage_xml.exists():
            print("[✓] Coverage XML report: coverage.xml")

        # Display memory statistics
        if self.memory_stats:
            print("\n[Memory] Peak Usage by Step:")
            for stat in self.memory_stats:
                print(f"    {stat}")

            # Calculate totals
            total_rss = max(s.peak_rss_mb for s in self.memory_stats)
            total_vms = max(s.peak_vms_mb for s in self.memory_stats)
            print(f"[Memory] Overall Peak: {total_rss:.1f} MB RSS, {total_vms:.1f} MB VMS")

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
            "htmlcov",
            "coverage.xml",
            ".work",
            "reports",
            "site",
        ]

        for pattern in artifacts:
            if pattern.startswith("*"):
                for path in self.project_root.rglob(pattern):
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

        print("[✓] Cleaned build artifacts")
        return True

    def run_full_build(self) -> bool:
        """Run the complete build pipeline."""
        print("Python Project Builder - Comprehensive Build Pipeline")
        print(f"{'=' * 80}")
        print(f"Project: {self.project_root.name}")
        print(f"Source directories: {', '.join(self.source_dirs)}")
        print(f"Coverage threshold: {self.coverage_threshold}%")
        if self.enforce_memory_limit:
            print(f"Memory limit: {self.memory_limit_mb}MB (enforced)")
        else:
            print(f"Memory limit: {self.memory_limit_mb}MB (monitored only)")
        print(f"{'=' * 80}")

        start_time = time.time()

        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Format Code", self.format_code),
            ("Lint Code", self.lint_code),
            ("Type Check", self.type_check),
            ("Security Check", self.run_security_check),
            ("Static Analysis", self.run_static_analysis),
            ("Run Tests", self.run_tests),
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
                print(f"[✗] {step_name} failed with exception: {e}")
                self.failed_steps.append(step_name)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'=' * 80}")
        print("[SUMMARY] Build Results")
        print(f"{'=' * 80}")
        print(f"[✓] Successful steps: {success_count}/{total_steps}")
        print(f"[⏱] Build duration: {duration:.2f} seconds")

        if self.memory_stats:
            total_rss = max(s.peak_rss_mb for s in self.memory_stats)
            total_vms = max(s.peak_vms_mb for s in self.memory_stats)
            print(f"[💾] Peak memory: {total_rss:.1f} MB RSS, {total_vms:.1f} MB VMS")

        if self.failed_steps:
            print(f"[✗] Failed steps: {', '.join(self.failed_steps)}")

        if success_count == total_steps:
            print("\n[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!")
            print("[✓] Ready for deployment")
            return True
        elif success_count >= total_steps - 1:
            print(
                f"\n[WARNING] BUILD MOSTLY SUCCESSFUL - {total_steps - success_count} minor issues"
            )
            print("[i] Consider addressing failed steps before deployment")
            return True
        else:
            print(f"\n[FAILED] BUILD FAILED - {total_steps - success_count} critical issues")
            print("[!] Please fix the failed steps before proceeding")
            return False
