"""Tests for ScanService path validation."""

from pathlib import Path

import pytest

from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.service import ScanService


class TestScanServiceValidation:
    """Test ScanService path validation."""

    def test_scan_rejects_nonexistent_path(self, tmp_path: Path) -> None:
        """Test that scan() raises FileNotFoundError for non-existent path."""
        service = ScanService(config=ScanConfig(base_path=tmp_path / "scan"))
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError, match="Scan path does not exist"):
            service.scan(nonexistent)

    def test_scan_rejects_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Test that scan() raises NotADirectoryError for a file path."""
        service = ScanService(config=ScanConfig(base_path=tmp_path / "scan"))
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        with pytest.raises(NotADirectoryError, match="Scan path is not a directory"):
            service.scan(test_file)

    def test_scan_accepts_valid_directory(self, tmp_path: Path) -> None:
        """Test that scan() accepts a valid directory path."""
        service = ScanService(config=ScanConfig(base_path=tmp_path / "scan"))
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")

        # Should not raise
        result = service.scan(test_dir, annotate_metrics=False)
        assert result is not None
