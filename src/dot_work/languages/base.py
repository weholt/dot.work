"""Abstract base class for language adapters.

This module defines the interface that all language adapters must implement
to provide build, test, and lint functionality for their respective languages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BuildResult:
    """Result of a build operation.

    Attributes:
        success: Whether the build completed successfully.
        exit_code: The exit code from the build process.
        stdout: Standard output from the build process.
        stderr: Standard error from the build process.
        duration_seconds: Time taken to run the build.
    """

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class TestResult:
    """Result of a test operation.

    Attributes:
        success: Whether all tests passed.
        exit_code: The exit code from the test process.
        stdout: Standard output from the test process.
        stderr: Standard error from the test process.
        duration_seconds: Time taken to run the tests.
        tests_run: Number of tests executed (if available).
        tests_failed: Number of tests that failed (if available).
        tests_skipped: Number of tests skipped (if available).
    """

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    tests_run: int | None = None
    tests_failed: int | None = None
    tests_skipped: int | None = None


class LanguageAdapter(ABC):
    """Abstract base class for language-specific build adapters.

    Each language adapter provides methods for building, testing, and linting
    projects written in that language. Adapters are responsible for detecting
    whether a project uses their language and executing the appropriate commands.
    """

    @abstractmethod
    def can_handle(self, project_path: Path) -> bool:
        """Check if this adapter can handle the given project.

        Args:
            project_path: Path to the project directory.

        Returns:
            True if this adapter can handle the project, False otherwise.
        """
        ...

    @abstractmethod
    def get_build_command(self, project_path: Path) -> list[str]:
        """Get the command to build the project.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments.
        """
        ...

    @abstractmethod
    def get_test_command(self, project_path: Path) -> list[str]:
        """Get the command to run tests.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments.
        """
        ...

    @abstractmethod
    def get_lint_command(self, project_path: Path) -> list[str]:
        """Get the command to lint the code.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments.
        """
        ...

    @abstractmethod
    def get_type_check_command(self, project_path: Path) -> list[str]:
        """Get the command to run type checking.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments.
        """
        ...

    @abstractmethod
    def get_format_command(self, project_path: Path) -> list[str]:
        """Get the command to check code formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments.
        """
        ...

    def get_format_fix_command(self, project_path: Path) -> list[str]:
        """Get the command to automatically fix formatting issues.

        Args:
            project_path: Path to the project directory.

        Returns:
            List of command arguments. Returns empty list by default.
        """
        return []

    @abstractmethod
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
        ...

    @abstractmethod
    def parse_test_result(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResult:
        """Parse the result of a test operation.

        Args:
            exit_code: The exit code from the test process.
            stdout: Standard output from the test process.
            stderr: Standard error from the test process.
            duration_seconds: Time taken to run the tests.

        Returns:
            A TestResult object with parsed information including test counts.
        """
        ...
