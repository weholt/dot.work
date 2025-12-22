"""
Tests for the ScanConfig class.
"""

import os
from pathlib import Path

from dot_work.python.scan.config import ScanConfig


def test_default_config() -> None:
    """Test default configuration values."""
    config = ScanConfig()

    assert config.base_path == Path(".work/scan")
    assert config.index_file == "code_index.json"
    assert config.cache_file == "cache.json"


def test_index_path_property() -> None:
    """Test index_path property."""
    config = ScanConfig()

    assert config.index_path == Path(".work/scan/code_index.json")


def test_cache_path_property() -> None:
    """Test cache_path property."""
    config = ScanConfig()

    assert config.cache_path == Path(".work/scan/cache.json")


def test_from_env_default() -> None:
    """Test from_env with default values."""
    # Ensure env var is not set
    os.environ.pop("DOT_WORK_SCAN_PATH", None)

    config = ScanConfig.from_env()

    assert config.base_path == Path(".work/scan")


def test_from_env_custom() -> None:
    """Test from_env with custom path."""
    os.environ["DOT_WORK_SCAN_PATH"] = "/custom/path"

    config = ScanConfig.from_env()

    assert config.base_path == Path("/custom/path")

    # Clean up
    os.environ.pop("DOT_WORK_SCAN_PATH", None)


def test_ensure_directories(tmp_path: Path) -> None:
    """Test that ensure_directories creates the directory.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    config = ScanConfig(base_path=tmp_path / "scan")
    scan_dir = tmp_path / "scan"

    assert not scan_dir.exists()

    config.ensure_directories()

    assert scan_dir.exists()
    assert scan_dir.is_dir()
