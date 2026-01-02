"""Fixtures for overview module tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_project_dir(tmp_path: Path) -> Path:
    """Create a sample project directory for testing."""
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    # Create a sample Python module
    (project_dir / "example.py").write_text(
        '''"""Example module for testing."""

from dataclasses import dataclass


def hello(name: str) -> str:
    """Say hello to someone.

    Args:
        name: The person's name.

    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"


@dataclass
class Person:
    """Represents a person."""

    name: str
    age: int


class Greeter:
    """A class that greets people."""

    def greet(self, person: Person) -> str:
        """Greet a person.

        Args:
            person: The person to greet.

        Returns:
            A greeting message.
        """
        return f"Hi, {person.name}!"
'''
    )

    # Create a sample markdown file
    (project_dir / "README.md").write_text(
        """# Sample Project

This is a sample project for testing the overview module.

## Features

- Feature 1: Does something cool
- Feature 2: Does something else

## Usage

```python
from example import hello
hello("World")
```
"""
    )

    return project_dir


@pytest.fixture
def empty_project_dir(tmp_path: Path) -> Path:
    """Create an empty project directory for testing."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()
    return project_dir
