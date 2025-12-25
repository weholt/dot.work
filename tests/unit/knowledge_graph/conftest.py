"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from dot_work.knowledge_graph.db import Database


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


@pytest.fixture
def kg_database(temp_db_path: Path) -> Generator[Database, None, None]:
    """Create a Database instance with automatic cleanup.

    CRITICAL: This fixture ensures Database connections are properly closed
    after each test to prevent memory leaks.

    Args:
        temp_db_path: Path to temporary database file

    Returns:
        Database instance
    """
    db = Database(temp_db_path)
    try:
        yield db
    finally:
        # CRITICAL: Always close the database connection
        try:
            db.close()
        except Exception:
            pass
        # Clear reference to help garbage collection
        del db
