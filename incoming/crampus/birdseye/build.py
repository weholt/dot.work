#!/usr/bin/env python3
"""Quality pipeline for the birdseye project."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

PROJECT_PACKAGE = "birdseye"
SRC_DIR = Path("src") / PROJECT_PACKAGE
TEST_DIR = Path("tests")
PROJECT_ROOT = Path(__file__).parent
ANALYSIS_DIR = PROJECT_ROOT / ".work/agent" / "analysis"


class BuildRunner:
    """Execute formatting, linting, typing, analysis, and tests for birdseye."""

    def __init__(self, verbose: bool = False, fix: bool = False) -> None:
        self.verbose = verbose
        self.fix = fix
        self.failed_steps: List[str] = []

    # ------------------------------- helpers ------------------------------- #
    def _run(
        self,
        cmd: Sequence[str],
        *,
        description: str,
        check: bool = True,
    ) -> Tuple[bool, str, str]:
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                list(cmd),
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=check,
                encoding="utf-8",
                errors="replace",
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as exc:
            return False, exc.stdout or "", exc.stderr or ""
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"

    def _print_step(self, label: str) -> None:
        print(f"\n{'=' * 60}")
        print(f"[STEP] {label}")
        print(f"{'=' * 60}")

    def _print_result(self, label: str, success: bool, stdout: str = "", stderr: str = "") -> None:
        status = "OK" if success else "FAIL"
        print(f"[{status}] {label}")
        if not success:
            self.failed_steps.append(label)
            if stderr:
                print(stderr.strip())
            if stdout:
                print(stdout.strip())

    # --------------------------- build operations -------------------------- #
    def check_dependencies(self) -> bool:
        self._print_step("Checking toolchain")
        checks: Iterable[Tuple[str, Sequence[str]]] = (
            ("uv", ["uv", "--version"]),
            ("ruff", ["uv", "run", "ruff", "--version"]),
            ("mypy", ["uv", "run", "mypy", "--version"]),
            ("pytest", ["uv", "run", "pytest", "--version"]),
            ("radon", ["uv", "run", "radon", "--version"]),
        )

        all_available = True
        for label, cmd in checks:
            success, stdout, stderr = self._run(cmd, description=f"Check {label}", check=False)
            if success:
                first_line = stdout.strip().splitlines()[0] if stdout.strip() else "(no version info)"
                print(f"[OK] {label}: {first_line}")
            else:
                all_available = False
                print(f"[WARN] {label}: unavailable ({stderr.strip() or 'no details'})")
        return all_available

    def sync_dependencies(self) -> bool:
        self._print_step("Syncing dependencies")
        success, stdout, stderr = self._run(["uv", "sync"], description="uv sync")
        self._print_result("uv sync", success, stdout, stderr)
        return success

    def format_code(self) -> bool:
        self._print_step("Formatting source")
        targets = [str(SRC_DIR), str(TEST_DIR), ".work/agent"]
        cmd = ["uv", "run", "ruff", "format", *targets]
        if not self.fix:
            cmd.append("--check")
        success, stdout, stderr = self._run(cmd, description="ruff format", check=False)
        self._print_result("ruff format", success, stdout, stderr)
        return success

    def lint_code(self) -> bool:
        self._print_step("Linting source")
        cmd = ["uv", "run", "ruff", "check", str(SRC_DIR), str(TEST_DIR)]
        if self.fix:
            cmd.append("--fix")
        success, stdout, stderr = self._run(cmd, description="ruff check", check=False)
        self._print_result("ruff check", success, stdout, stderr)
        return success

    def type_check(self) -> bool:
        self._print_step("Type checking")
        cmd = ["uv", "run", "mypy", str(SRC_DIR)]
        success, stdout, stderr = self._run(cmd, description="mypy", check=False)
        self._print_result("mypy", success, stdout, stderr)
        return success

    def run_static_analysis(self) -> bool:
        self._print_step("Static analysis (radon)")
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

        cmds = [
            ("radon cc", ["uv", "run", "radon", "cc", str(SRC_DIR), "-s", "-a", "-j"], ANALYSIS_DIR / "complexity.json"),
            ("radon mi", ["uv", "run", "radon", "mi", str(SRC_DIR), "-j"], ANALYSIS_DIR / "maintainability.json"),
        ]

        all_success = True
        for label, cmd, outfile in cmds:
            success, stdout, stderr = self._run(cmd, description=label, check=False)
            if stdout:
                outfile.write_text(stdout)
            self._print_result(label, success, stdout, stderr)
            all_success &= success
        return all_success

    def run_tests(self) -> bool:
        self._print_step("Running tests")
        cmd = ["uv", "run", "pytest", str(TEST_DIR)]
        success, stdout, stderr = self._run(cmd, description="pytest", check=False)
        self._print_result("pytest", success, stdout, stderr)
        return success

    def generate_reports(self) -> bool:
        self._print_step("Reporting")
        coverage_xml = PROJECT_ROOT / "coverage.xml"
        if coverage_xml.exists():
            print("[OK] coverage.xml available")
        else:
            print("[INFO] coverage.xml not found (pytest --cov produces it)")
        return True

    def clean(self) -> bool:
        self._print_step("Cleaning artifacts")
        patterns: Iterable[str] = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".coverage",
            "coverage.xml",
            "htmlcov",
        ]
        for path in _collect_artifacts(patterns):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        if ANALYSIS_DIR.exists():
            shutil.rmtree(ANALYSIS_DIR)
        print("[OK] cleaned")
        return True

    # ----------------------------- orchestration --------------------------- #
    def run(self) -> bool:
        print("birdseye quality pipeline")
        print("=" * 80)
        start = time.time()

        steps = [
            ("Dependency check", self.check_dependencies),
            ("uv sync", self.sync_dependencies),
            ("Formatting", self.format_code),
            ("Linting", self.lint_code),
            ("Type checking", self.type_check),
            ("Radon analysis", self.run_static_analysis),
            ("Tests", self.run_tests),
            ("Reports", self.generate_reports),
        ]

        passed = 0
        for label, step in steps:
            try:
                if step():
                    passed += 1
            except Exception as exc:  # pragma: no cover - defensive guard
                self.failed_steps.append(label)
                print(f"[FAIL] {label}: {exc}")

        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Passed {passed} / {len(steps)} steps")
        duration = time.time() - start
        print(f"Duration: {duration:.2f}s")

        if self.failed_steps:
            print("Failed steps: " + ", ".join(self.failed_steps))
            return False
        return True


def _collect_artifacts(patterns: Iterable[str]) -> Iterable[Path]:
    for pattern in patterns:
        yield from PROJECT_ROOT.rglob(pattern)


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the birdseye quality pipeline")
    parser.add_argument("--verbose", action="store_true", help="Show commands as they run")
    parser.add_argument("--fix", action="store_true", help="Apply autofixes where supported")
    parser.add_argument("--clean", action="store_true", help="Remove cached artifacts and exit")
    return parser.parse_args(args)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    runner = BuildRunner(verbose=args.verbose, fix=args.fix)

    if args.clean:
        runner.clean()
        return 0

    return 0 if runner.run() else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
