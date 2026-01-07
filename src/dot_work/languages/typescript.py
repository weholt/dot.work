"""TypeScript/JavaScript language adapter implementation.

This module provides the TypeScript/JavaScript-specific implementation of the
LanguageAdapter interface, handling TS/JS project detection, building, testing, and linting.
"""

import re
from pathlib import Path

from dot_work.languages.base import BuildResult, LanguageAdapter, TestResult


class TypeScriptAdapter(LanguageAdapter):
    """Adapter for TypeScript/JavaScript projects.

    Detects TypeScript/JavaScript projects by looking for package.json,
    tsconfig.json, or other Node.js marker files. Supports npm, yarn, pnpm, and bun.
    """

    def can_handle(self, project_path: Path) -> bool:
        """Check if this is a TypeScript/JavaScript project.

        Args:
            project_path: Path to the project directory.

        Returns:
            True if TS/JS project markers are found.
        """
        markers = [
            "package.json",
            "tsconfig.json",
            "jsconfig.json",
        ]
        return any((project_path / marker).exists() for marker in markers)

    def get_build_command(self, project_path: Path) -> list[str]:
        """Get the command to build the project.

        For TypeScript/JavaScript, build commands are typically defined in package.json scripts.
        We use 'npm run build' or equivalent based on the detected package manager.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run the build script.
        """
        package_manager = self._detect_package_manager(project_path)
        build_command = "build"  # Common build script name

        if package_manager == "yarn":
            return ["yarn", build_command]
        elif package_manager == "pnpm":
            return ["pnpm", "run", build_command]
        elif package_manager == "bun":
            return ["bun", "run", build_command]
        else:  # npm (default)
            return ["npm", "run", build_command]

    def get_test_command(self, project_path: Path) -> list[str]:
        """Get the command to run tests.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run tests using vitest/jest.
        """
        package_manager = self._detect_package_manager(project_path)
        test_command = "test"  # Common test script name

        if package_manager == "yarn":
            return ["yarn", test_command]
        elif package_manager == "pnpm":
            return ["pnpm", "run", test_command]
        elif package_manager == "bun":
            return ["bun", "run", test_command]
        else:  # npm (default)
            return ["npm", "run", test_command]

    def get_lint_command(self, project_path: Path) -> list[str]:
        """Get the command to lint the code.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run eslint.
        """
        # Common lint script names
        lint_scripts = ["lint", "eslint"]
        package_json = project_path / "package.json"

        if package_json.exists():
            import json

            try:
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    for script_name in lint_scripts:
                        if script_name in scripts:
                            package_manager = self._detect_package_manager(project_path)
                            if package_manager == "yarn":
                                return ["yarn", script_name]
                            elif package_manager == "pnpm":
                                return ["pnpm", "run", script_name]
                            elif package_manager == "bun":
                                return ["bun", "run", script_name]
                            else:
                                return ["npm", "run", script_name]
            except (OSError, json.JSONDecodeError):
                pass

        # Fallback to direct eslint
        return ["npx", "eslint", "."]

    def get_type_check_command(self, project_path: Path) -> list[str]:
        """Get the command to run type checking.

        For TypeScript, this is tsc --noEmit. For JavaScript, returns empty list.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to run tsc, or empty list for pure JS projects.
        """
        # Check if this is a TypeScript project
        if (project_path / "tsconfig.json").exists():
            return ["npx", "tsc", "--noEmit"]
        return []

    def get_format_command(self, project_path: Path) -> list[str]:
        """Get the command to check code formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to check formatting with prettier.
        """
        # Check for format script in package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            import json

            try:
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    if "format:check" in scripts:
                        package_manager = self._detect_package_manager(project_path)
                        if package_manager == "yarn":
                            return ["yarn", "format:check"]
                        elif package_manager == "pnpm":
                            return ["pnpm", "run", "format:check"]
                        elif package_manager == "bun":
                            return ["bun", "run", "format:check"]
                        else:
                            return ["npm", "run", "format:check"]
            except (OSError, json.JSONDecodeError):
                pass

        # Fallback to direct prettier
        return ["npx", "prettier", "--check", "."]

    def get_format_fix_command(self, project_path: Path) -> list[str]:
        """Get the command to automatically fix formatting.

        Args:
            project_path: Path to the project directory.

        Returns:
            Command to format code with prettier.
        """
        # Check for format script in package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            import json

            try:
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    if "format" in scripts:
                        package_manager = self._detect_package_manager(project_path)
                        if package_manager == "yarn":
                            return ["yarn", "format"]
                        elif package_manager == "pnpm":
                            return ["pnpm", "run", "format"]
                        elif package_manager == "bun":
                            return ["bun", "run", "format"]
                        else:
                            return ["npm", "run", "format"]
            except (OSError, json.JSONDecodeError):
                pass

        # Fallback to direct prettier
        return ["npx", "prettier", "--write", "."]

    def _detect_package_manager(self, project_path: Path) -> str:
        """Detect which package manager is in use.

        Args:
            project_path: Path to the project directory.

        Returns:
            Package manager name: "npm", "yarn", "pnpm", or "bun".
        """
        # Check for lockfiles in order of specificity
        lockfiles = [
            ("bun.lockb", "bun"),
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "yarn"),
            ("package-lock.json", "npm"),
        ]

        for lockfile, manager in lockfiles:
            if (project_path / lockfile).exists():
                return manager

        # Default to npm
        return "npm"

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

        Extracts test counts from vitest/jest output.

        Args:
            exit_code: The exit code from the test process.
            stdout: Standard output from the test process.
            stderr: Standard error from the test process.
            duration_seconds: Time taken to run the tests.

        Returns:
            A TestResult object with parsed information including test counts.
        """
        success = exit_code == 0

        # Parse vitest/jest output for test counts
        tests_run = None
        tests_failed = None
        tests_skipped = None

        combined_output = stdout + stderr

        # Vitest pattern: "✓ src/test.ts (2)"
        # Jest pattern: "PASS src/test.js"
        # Summary patterns: "Tests: 10 passed, 2 failed, 1 skipped"

        # Try to match summary pattern
        summary_pattern = r"Tests?:\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?"
        match = re.search(summary_pattern, combined_output, re.IGNORECASE)
        if match:
            tests_run = int(match.group(1))
            if match.group(2):
                tests_failed = int(match.group(2))
                tests_run += tests_failed
            if match.group(3):
                tests_skipped = int(match.group(3))
                tests_run += tests_skipped

        # Alternative pattern for "Test Files: X passed, Y failed"
        if tests_run is None:
            alt_pattern = r"Test Files:\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?"
            match = re.search(alt_pattern, combined_output, re.IGNORECASE)
            if match:
                passed = int(match.group(1))
                tests_run = passed
                if match.group(2):
                    failed = int(match.group(2))
                    tests_run += failed
                    tests_failed = failed

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
