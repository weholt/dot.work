"""Pytest configuration and fixtures for dot-work tests.

Includes memory leak detection and prevention with 4GB per-test limit.
Logs each test start/finish with memory usage to a persistent file for debugging.
"""

from __future__ import annotations

import gc
import os
import shutil
import subprocess
import threading
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest

# Memory limit in bytes (4GB)
_MEMORY_LIMIT_BYTES = 4 * 1024 * 1024 * 1024

# Track memory usage across tests
_memory_baseline: int | None = None
_test_count = 0

# Thread-safe file lock for test logging
_log_lock = threading.Lock()
_log_file: Path | None = None


def _get_test_log_file() -> Path:
    """Get the test log file path.

    Returns:
        Path to the test log file in the test_logs directory
    """
    global _log_file
    if _log_file is None:
        # Place log file in test_logs directory for proper Docker volume mounting
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "test_logs"
        logs_dir.mkdir(exist_ok=True)
        _log_file = logs_dir / "test_execution_log.txt"
    return _log_file


def _write_test_log(message: str) -> None:
    """Write a message to the test log file in a thread-safe manner.

    Args:
        message: The message to write
    """
    with _log_lock:
        log_file = _get_test_log_file()
        timestamp = datetime.now().isoformat(timespec="milliseconds")
        log_entry = f"[{timestamp}] {message}\n"

        # Write to file (append mode) with explicit flush for persistence
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            f.flush()
            os.fsync(f.fileno())


def _format_memory_mb(memory_mb: float) -> str:
    """Format memory usage in MB with GB approximation.

    Args:
        memory_mb: Memory usage in megabytes

    Returns:
        Formatted memory string
    """
    gb = memory_mb / 1024
    return f"{memory_mb:.1f} MB ({gb:.2f} GB)"


def get_process_memory_mb() -> float:
    """Get current process memory usage in MB.

    Returns:
        Memory usage in megabytes
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # Fallback: return 0 if psutil not available
        return 0.0


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with memory monitoring and initialize test log.

    Args:
        config: pytest config object
    """
    global _memory_baseline
    _memory_baseline = get_process_memory_mb()

    # Initialize the test log file
    log_file = _get_test_log_file()
    # Clear previous log file for fresh start
    # Handle both file and directory cases (directory can happen with Docker mounts)
    if log_file.exists():
        if log_file.is_dir():
            # Remove directory and recreate as file
            shutil.rmtree(log_file)
        else:
            log_file.unlink(missing_ok=True)

    # Write session header
    _write_test_log("=" * 70)
    _write_test_log("PYTEST SESSION STARTED")
    _write_test_log(f"Memory baseline: {_format_memory_mb(_memory_baseline)}")
    _write_test_log(f"Memory limit: {_format_memory_mb(_MEMORY_LIMIT_BYTES / (1024 * 1024))}")
    _write_test_log("=" * 70)

    # Register the memory marker
    config.addinivalue_line(
        "markers",
        "nomemcheck: skip memory leak check for this test",
    )


def pytest_report_header(config: pytest.Config) -> str:
    """Add memory info to pytest header.

    Args:
        config: pytest config object

    Returns:
        Header string with memory info
    """
    baseline = get_process_memory_mb()
    return f"Memory monitoring - Limit: 4GB | Baseline: {baseline:.1f} MB"


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Check memory before each test and log test start.

    Args:
        item: pytest test item
    """
    if "nomemcheck" in item.keywords:
        _write_test_log(f"START [SKIP_MEMCHECK]: {item.nodeid}")
        return

    memory_mb = get_process_memory_mb()
    limit_mb = _MEMORY_LIMIT_BYTES / (1024 * 1024)

    # Log test start
    _write_test_log(f"START: {item.nodeid} | Memory: {_format_memory_mb(memory_mb)}")

    # Check if we're already over the limit before starting
    if memory_mb > limit_mb:
        _write_test_log(f"ERROR: Memory limit exceeded BEFORE test: {_format_memory_mb(memory_mb)}")
        pytest.fail(
            f"MEMORY LIMIT EXCEEDED before test: {memory_mb:.1f} MB > {limit_mb:.1f} MB. "
            f"Previous tests leaked memory. Test: {item.name}"
        )


def pytest_runtest_call(item: pytest.Item) -> None:
    """Monitor memory during test execution - kill if over 4GB.

    Args:
        item: pytest test item
    """
    if "nomemcheck" in item.keywords:
        return

    memory_mb = get_process_memory_mb()
    limit_mb = _MEMORY_LIMIT_BYTES / (1024 * 1024)

    # Log mid-execution memory for long-running tests
    _write_test_log(f"EXECUTING: {item.nodeid} | Memory: {_format_memory_mb(memory_mb)}")

    # Kill test if it exceeded memory limit
    if memory_mb > limit_mb:
        _write_test_log(f"ERROR: Memory limit exceeded DURING test: {_format_memory_mb(memory_mb)}")
        pytest.fail(
            f"MEMORY LIMIT EXCEEDED: {memory_mb:.1f} MB > {limit_mb:.1f} MB. "
            f"Test '{item.name}' is leaking memory and was killed."
        )


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Clean up after each test, check for leaks, and log test completion.

    Args:
        item: pytest test item that just ran
        nextitem: next test item to run
    """
    if "nomemcheck" in item.keywords:
        _write_test_log(f"FINISH [SKIP_MEMCHECK]: {item.nodeid}")
        return

    global _test_count
    _test_count += 1

    # Force garbage collection
    gc.collect()
    gc.collect()  # Call twice to handle objects with __del__ that create new objects

    # Get memory after test
    memory_mb = get_process_memory_mb()
    _write_test_log(f"FINISH: {item.nodeid} | Memory: {_format_memory_mb(memory_mb)}")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up after pytest session and log session summary.

    Args:
        session: pytest session object
        exitstatus: exit status code
    """
    # Force final garbage collection
    gc.collect()
    gc.collect()

    # Report final memory stats
    final_memory = get_process_memory_mb()
    if _memory_baseline is not None:
        total_growth = final_memory - _memory_baseline
        print(
            f"\n[MEMORY] Baseline: {_memory_baseline:.1f} MB, "
            f"Final: {final_memory:.1f} MB, "
            f"Growth: {total_growth:+.1f} MB"
        )

    # Write session summary to log
    _write_test_log("=" * 70)
    _write_test_log("PYTEST SESSION FINISHED")
    _write_test_log(f"Exit status: {exitstatus}")
    _write_test_log(f"Tests run: {_test_count}")
    _write_test_log(f"Final memory: {_format_memory_mb(final_memory)}")
    if _memory_baseline is not None:
        total_growth = final_memory - _memory_baseline
        _write_test_log(f"Total memory growth: {_format_memory_mb(total_growth)}")
    _write_test_log(f"Log file: {_get_test_log_file()}")
    _write_test_log("=" * 70)

    # Close any remaining SQLAlchemy connections
    try:
        from sqlalchemy import pool

        pool.dispose_all()
    except Exception:
        pass
    gc.collect()


@pytest.fixture(scope="function", autouse=True)
def force_garbage_collection() -> Generator[None, None, None]:
    """Auto-use fixture that forces garbage collection after each test.

    This helps clean up circular references and other garbage that
    might not be collected immediately.
    """
    yield
    # After test, force garbage collection twice
    gc.collect()
    gc.collect()


@pytest.fixture(scope="module", autouse=True)
def cleanup_connection_pools() -> Generator[None, None, None]:
    """Auto-use fixture that cleans up SQLAlchemy connection pools between modules.

    This prevents connection pool accumulation throughout the test session.
    Without this, connection pools can grow unbounded, consuming 2-5GB of memory.
    """
    yield
    # After module finishes, dispose all connection pools
    try:
        from sqlalchemy import pool

        pool.dispose_all()
    except Exception:
        pass


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests.

    This is an alias for pytest's tmp_path for compatibility.
    """
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository for tests."""
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create an initial commit
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial content\n")
    subprocess.run(
        ["git", "add", "."],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    yield tmp_path


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory for testing installations."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_prompts_dir(tmp_path: Path) -> Path:
    """Create a sample prompts directory with test prompt files."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Create sample prompt files
    (prompts_dir / "test.prompt.md").write_text(
        "# Test Prompt\n\nPath: {{ prompt_path }}\nTool: {{ ai_tool }}\n",
        encoding="utf-8",
    )
    (prompts_dir / "another.prompt.md").write_text(
        "# Another Prompt\n\nExtension: {{ prompt_extension }}\n",
        encoding="utf-8",
    )

    return prompts_dir
