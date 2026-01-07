"""Python language adapter implementation.

This module provides the Python-specific implementation of the LanguageAdapter
interface, handling Python project detection, building, testing, and linting.
"""

import re
from pathlib import Path

from dot_work.languages.base import BuildResult, LanguageAdapter, TestResult


class PythonAdapter(LanguageAdapter):
    """Adapter for Python projects.

    Detects Python projects by looking for pyproject.toml, setup.py, or
    requirements.txt files. Provides uv-based build, test, and lint commands.
    """

    def can_handle(self, project_path: Path) -> bool:
        """Check if this is a Python project.

        Args:
            project_path: Path to the project directory.

        Returns:
            True if Python project markers are found.
        """
        markers = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]
        return any((project_path / marker).exists() for marker in markers)

    def get_build_command(self, project_path: Path) -> list[str]:
        """Get the command to build the project.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run the build script with uv.
        """
        build_script = project_path / "scripts" / "build.py"
        if build_script.exists():
            return ["uv", "run", "python", str(build_script)]
        return ["uv", "run", "python", "-m", "build"]

    def get_test_command(self, project_path: Path) -> list[str]:
        """Get the command to run tests.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run pytest.
        """
        return ["uv", "run", "pytest", "tests/"]

    def get_lint_command(self, project_path: Path) -> list[str]:
        """Get the command to lint the code.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run ruff for linting.
        """
        return ["uv", "run", "ruff", "check", "."]

    def get_type_check_command(self, project_path: Path) -> list[str]:
        """Get the command to run type checking.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run mypy for type checking.
        """
        return ["uv", "run", "mypy", "src/"]

    def get_format_command(self, project_path: Path) -> list[str]:
        """Get the command to check code formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to check formatting with ruff.
        """
        return ["uv", "run", "ruff", "format", "--check", "."]

    def get_format_fix_command(self, project_path: Path) -> list[str]:
        """Get the command to automatically fix formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to format code with ruff.
        """
        return ["uv", "run", "ruff", "format", "."]

    def parse_build_result(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> BuildResult:
        """Parse the result of a build operation.

        Args:
            exit_code: The exit code from the build process.
            stdout: Standard output from the build process.
            stderr: Standard error from the build process.
            duration_seconds: Time taken to run the build.

        Returns:
            A BuildResult object with parsed information.
        """
        success = exit_code == 0
        return BuildResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
        )

    def parse_test_result(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResult:
        """Parse the result of a test operation.

        Extracts test counts from pytest output using regex patterns.

        Args:
            exit_code: The exit code from the test process.
            stdout: Standard output from the test process.
            stderr: Standard error from the test process.
            duration_seconds: Time taken to run the tests.

        Returns:
            A TestResult object with parsed information including test counts.
        """
        success = exit_code == 0

        # Parse pytest output for test counts
        tests_run = None
        tests_failed = None
        tests_skipped = None

        combined_output = stdout + stderr

        # Try to match the summary line
        summary_pattern = r"(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+skipped)?"
        match = re.search(summary_pattern, combined_output)
        if match:
            tests_run = int(match.group(1))
            if match.group(2):
                tests_failed = int(match.group(2))
            if match.group(3):
                tests_skipped = int(match.group(3))

        # Alternative pattern for "X tests collected" style output
        if tests_run is None:
            collected_pattern = r"(\d+)\s+tests? collected"
            match = re.search(collected_pattern, combined_output)
            if match:
                tests_run = int(match.group(1))

        return TestResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            tests_run=tests_run,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
        )
