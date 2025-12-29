"""Integration test fixtures for database operations."""

import os
from collections.abc import Generator
from pathlib import Path

import psutil
import pytest
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel
from typer.testing import CliRunner

from dot_work.db_issues.adapters import create_db_engine
from dot_work.db_issues.config import get_db_url


def pytest_sessionstart(session):
    """Clean up all daemon processes before test session starts."""
    killed = 0
    try:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass

    if killed > 0:
        print(f"\n[CLEANUP] Killed {killed} orphaned daemon processes before test session")


def pytest_sessionfinish(session, exitstatus):
    """Clean up all daemon processes after test session ends."""
    killed = 0
    try:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
                if cmdline and any("issue_tracker.daemon.service" in str(arg) for arg in cmdline):
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass

    if killed > 0:
        print(f"\n[CLEANUP] Killed {killed} orphaned daemon processes after test session")

    # CRITICAL: Dispose all cached engines to prevent memory leak
    # Without this, engines accumulate in registry causing Linux OOM
    try:
        # Engine disposal is handled by individual test fixtures
        print("\n[CLEANUP] Test session completed, engines disposed by fixtures")
    except Exception as e:
        print(f"\n[CLEANUP] Failed during cleanup: {e}")


@pytest.fixture(scope="function")
def test_engine() -> Generator[Engine, None, None]:
    """Create an in-memory database engine for testing.

    Uses SQLite in-memory database for fast, isolated tests.
    Properly disposes engine to prevent memory leaks on Linux.
    """
    engine = create_db_engine("sqlite:///:memory:")
    yield engine
    # CRITICAL: Dispose engine to release connection pool and file descriptors
    # Without this, Linux accumulates memory and file handles causing OOM
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Create a test database session.

    Creates all tables and provides a clean session for each test.
    Session is automatically closed after the test.
    """
    # Create all tables
    SQLModel.metadata.create_all(test_engine)

    # Create session
    session = Session(test_engine)

    yield session

    # Cleanup - close session first, then drop tables
    session.close()
    SQLModel.metadata.drop_all(test_engine)
    # Note: Engine disposal is handled by test_engine fixture


@pytest.fixture(scope="function")
def integration_cli_runner(tmp_path: Path) -> CliRunner:
    """Create a CLI runner configured with a test database.

    Provides a CliRunner instance with environment variables set to use
    an isolated test database for integration testing.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        CliRunner instance configured for testing.
    """

    # Create test database in current directory (required by config validation)
    test_db_dir = Path.cwd() / ".work" / "test_integration_db"
    test_db_dir.mkdir(parents=True, exist_ok=True)

    # Initialize the database schema for integration tests
    # Set env var first, then get URL and create tables
    os.environ["DOT_WORK_DB_ISSUES_PATH"] = str(test_db_dir)
    db_url = get_db_url()
    engine = create_db_engine(db_url)
    try:
        SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()

    # Create CLI runner with test environment
    return CliRunner(env={**os.environ, "DOT_WORK_DB_ISSUES_PATH": str(test_db_dir)})
