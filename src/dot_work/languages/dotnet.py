""".NET language adapter implementation.

This module provides the .NET-specific implementation of the LanguageAdapter
interface, handling .NET project detection, building, testing, and linting.
"""

import re
from pathlib import Path

from dot_work.languages.base import BuildResult, LanguageAdapter, TestResult


class DotNetAdapter(LanguageAdapter):
    """Adapter for .NET projects (C#, F#, VB.NET).

    Detects .NET projects by looking for .csproj, .fsproj, .vbproj, or .sln files.
    Provides dotnet CLI-based commands for build, test, and lint operations.
    """

    def can_handle(self, project_path: Path) -> bool:
        """Check if this is a .NET project.

        Args:
            project_path: Path to the project directory.

        Returns:
            True if .NET project markers are found.
        """
        # Check for solution file
        if list(project_path.glob("*.sln")):
            return True

        # Check for project files
        project_patterns = ["*.csproj", "*.fsproj", "*.vbproj"]
        for pattern in project_patterns:
            if list(project_path.rglob(pattern)):
                return True

        return False

    def get_build_command(self, project_path: Path) -> list[str]:
        """Get the command to build the project.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run dotnet build.
        """
        # Prefer solution file if available
        sln_files = list(project_path.glob("*.sln"))
        if sln_files:
            return ["dotnet", "build", str(sln_files[0])]

        # Fallback to dotnet build without specific target
        return ["dotnet", "build"]

    def get_test_command(self, project_path: Path) -> list[str]:
        """Get the command to run tests.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run dotnet test with coverage.
        """
        return [
            "dotnet",
            "test",
            "--collect:" + "XPlat Code Coverage",
            "--no-build",
        ]

    def get_lint_command(self, project_path: Path) -> list[str]:
        """Get the command to lint the code.

        For .NET, "linting" is done via the compiler with Roslyn analyzers.
        This is essentially the same as building.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run dotnet build (which runs Roslyn analyzers).
        """
        return self.get_build_command(project_path)

    def get_type_check_command(self, project_path: Path) -> list[str]:
        """Get the command to run type checking.

        For .NET, type checking is done by the compiler during build.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run dotnet build.
        """
        return self.get_build_command(project_path)

    def get_format_command(self, project_path: Path) -> list[str]:
        """Get the command to check code formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to check formatting with dotnet format.
        """
        return ["dotnet", "format", "--verify-no-changes"]

    def get_format_fix_command(self, project_path: Path) -> list[str]:
        """Get the command to automatically fix formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to format code with dotnet format.
        """
        return ["dotnet", "format"]

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

        # .NET builds often output errors to stdout, not stderr
        errors = []
        combined = stdout + stderr

        # Parse for error/warning counts
        error_pattern = r"(\d+)\s+Error\(s\)"
        warning_pattern = r"(\d+)\s+Warning\(s\)"

        error_match = re.search(error_pattern, combined)
        warning_match = re.search(warning_pattern, combined)

        if error_match:
            errors.append(f"{error_match.group(1)} errors found")
        if warning_match:
            errors.append(f"{warning_match.group(1)} warnings found")

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

        Extracts test counts from dotnet test output.

        Args:
            exit_code: The exit code from the test process.
            stdout: Standard output from the test process.
            stderr: Standard error from the test process.
            duration_seconds: Time taken to run the tests.

        Returns:
            A TestResult object with parsed information including test counts.
        """
        success = exit_code == 0

        # Parse dotnet test output for test counts
        # Example patterns:
        # "Passed: 10, Failed: 2, Skipped: 1"
        # "Total: 15, Passed: 13, Failed: 2"
        tests_run = None
        tests_failed = None
        tests_skipped = None

        combined_output = stdout + stderr

        # Try to match "Passed:" pattern
        passed_pattern = r"Passed:\s*(\d+)"
        failed_pattern = r"Failed:\s*(\d+)"
        skipped_pattern = r"Skipped:\s*(\d+)"

        passed_match = re.search(passed_pattern, combined_output, re.IGNORECASE)
        failed_match = re.search(failed_pattern, combined_output, re.IGNORECASE)
        skipped_match = re.search(skipped_pattern, combined_output, re.IGNORECASE)

        if passed_match:
            tests_run = int(passed_match.group(1))
            if failed_match:
                tests_failed = int(failed_match.group(1))
                tests_run += tests_failed
            if skipped_match:
                tests_skipped = int(skipped_match.group(1))
                tests_run += tests_skipped

        # Alternative pattern for "Total:" style
        if tests_run is None:
            total_pattern = r"Total:\s*(\d+)"
            total_match = re.search(total_pattern, combined_output, re.IGNORECASE)
            if total_match:
                tests_run = int(total_match.group(1))

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
