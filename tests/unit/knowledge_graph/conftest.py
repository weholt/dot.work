"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test.sqlite"


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Ensure clean environment variables for tests."""
    original = os.environ.get("DOT_WORK_KG_DB_PATH")
    if "DOT_WORK_KG_DB_PATH" in os.environ:
        del os.environ["DOT_WORK_KG_DB_PATH"]
    yield
    if original is not None:
        os.environ["DOT_WORK_KG_DB_PATH"] = original
    elif "DOT_WORK_KG_DB_PATH" in os.environ:
        del os.environ["DOT_WORK_KG_DB_PATH"]
