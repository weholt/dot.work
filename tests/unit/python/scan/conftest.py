"""
Fixtures for scan module tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a sample Python file for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the created file.
    """
    file_path = tmp_path / "sample.py"
    file_path.write_text(
        '''"""Sample module for testing."""

from typing import Any


def simple_function(x: int, y: int) -> int:
    """A simple function."""
    return x + y


class SampleClass:
    """A sample class."""

    def __init__(self, value: int) -> None:
        """Initialize the class.

        Args:
            value: Initial value.
        """
        self.value = value

    def compute(self, other: int) -> int:
        """Compute something.

        Args:
            other: Other value.

        Returns:
            Result of computation.
        """
        result = self.value + other
        if result > 10:
            return result * 2
        return result


async def async_function() -> None:
    """An async function."""
    pass
''',
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def complex_python_file(tmp_path: Path) -> Path:
    """Create a Python file with complex code.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the created file.
    """
    file_path = tmp_path / "complex.py"
    file_path.write_text(
        '''"""Complex module for testing."""


def complex_function(x: int, y: int, z: int) -> int:
    """A complex function with multiple branches."""
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            if z > 0:
                return x + z
            else:
                return x
    else:
        if y > 0:
            if z > 0:
                return y + z
            else:
                return y
        else:
            if z > 0:
                return z
            else:
                return 0
''',
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def syntax_error_file(tmp_path: Path) -> Path:
    """Create a Python file with syntax errors.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the created file.
    """
    file_path = tmp_path / "syntax_error.py"
    file_path.write_text(
        '''"""Module with syntax error."""

def broken_function(
    # Missing closing parenthesis
''',
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def sample_imports_file(tmp_path: Path) -> Path:
    """Create a Python file with various imports.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the created file.
    """
    file_path = tmp_path / "imports.py"
    file_path.write_text(
        '''"""Module with various imports."""

import os
import sys
from pathlib import Path
from typing import Any, List

import typer
from dot_work.python.scan import ASTScanner


def use_imports() -> None:
    """Function using the imports."""
    path = Path(".")
    items: List[Any] = []
''',
        encoding="utf-8",
    )
    return file_path
