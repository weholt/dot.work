"""Integration test fixtures for database operations."""

import os
from collections.abc import Generator
from pathlib import Path

import psutil
import pytest
import sqlmodel
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


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """Create a single in-memory database engine for all integration tests.

    This fixture is session-scoped (runs once per test session) to prevent
    memory leaks from creating multiple engines. Each engine creation with
    SQLModel.metadata.create_all() accumulates metadata in the global singleton.

    The engine uses StaticPool which keeps a single connection alive for
    :memory: databases so the database persists across tests.

    Yields:
        SQLAlchemy Engine backed by in-memory SQLite
    """
    engine = create_db_engine("sqlite:///:memory:")

    # Create all tables once for the entire test session
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        # CRITICAL: Clear global metadata to prevent memory leaks
        SQLModel.metadata.clear()

        # Dispose engine to close all connections
        try:
            engine.dispose()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _reset_database_state(test_engine: Engine) -> None:
    """Automatically reset database state between integration tests.

    This fixture is autouse=True so it runs before and after every test.
    It deletes all data from the database to ensure test isolation.

    For in-memory SQLite with StaticPool, we can't rely on transaction
    rollback alone because the database persists across tests. We need
    to explicitly delete all data.

    Args:
        test_engine: The session-scoped database engine
    """

    def _delete_all_data(session: Session) -> None:
        """Delete all data from all tables, ignoring errors for missing tables."""
        tables = [
            "epic_issues",
            "dependencies",  # Correct table name for IssueModel dependencies
            "comments",
            "issues",
            "epics",
            "projects",
            "issue_labels",  # Added for label associations
            "labels",  # Added for labels
        ]
        for table in tables:
            try:
                session.exec(sqlmodel.text(f"DELETE FROM {table}"))
            except Exception:
                # Table doesn't exist or other error - ignore
                pass
        try:
            session.commit()
        except Exception:
            pass

    # Before test: ensure we're starting fresh
    with Session(test_engine) as session:
        _delete_all_data(session)

    yield

    # After test: clean up again for next test
    with Session(test_engine) as session:
        _delete_all_data(session)


@pytest.fixture(scope="function")
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Create a test database session.

    Provides a clean session for each test. The database schema is already
    created by the session-scoped test_engine fixture. Session is
    automatically closed after the test.

    Args:
        test_engine: The session-scoped database engine

    Yields:
        SQLModel Session backed by in-memory SQLite
    """
    # Create session
    session = Session(test_engine)

    yield session

    # Cleanup - close session
    session.close()


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
