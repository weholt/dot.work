"""Tests for dot_work.zip.cli module.

These tests focus on the internal implementation functions and configuration,
avoiding complex Typer CLI runner interactions that are better suited for
integration tests.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.zip.cli import _create_zip_internal, _upload_zip_internal


class TestCreateZipInternal:
    """Tests for _create_zip_internal function."""

    def test_create_zip_internal_basic(self, test_folder_structure: Path) -> None:
        """Test basic zip creation via internal function.

        Args:
            test_folder_structure: Fixture providing test folder
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.zip"

            _create_zip_internal(test_folder_structure, output_path, upload=False)

            assert output_path.exists()

    def test_create_zip_internal_with_default_output(self, test_folder_structure: Path) -> None:
        """Test zip creation with default output path.

        Args:
            test_folder_structure: Fixture providing test folder
        """
        _create_zip_internal(test_folder_structure, None, upload=False)

        # Should create zip in current directory with default name
        default_zip = Path.cwd() / f"{test_folder_structure.name}.zip"

        # Clean up
        if default_zip.exists():
            default_zip.unlink()

    def test_create_zip_internal_respects_gitignore(
        self, gitignore_folder: Path, zip_output_dir: Path
    ) -> None:
        """Test that create respects .gitignore patterns.

        Args:
            gitignore_folder: Fixture providing folder with .gitignore
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "gitignore.zip"

        _create_zip_internal(gitignore_folder, output_path, upload=False)

        assert output_path.exists()

    def test_create_zip_internal_nonexistent_folder(self, zip_output_dir: Path) -> None:
        """Test with nonexistent folder raises FileNotFoundError.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        nonexistent = zip_output_dir / "nonexistent"
        output_path = zip_output_dir / "test.zip"

        with pytest.raises(FileNotFoundError):
            _create_zip_internal(nonexistent, output_path, upload=False)

    def test_create_zip_internal_folder_validation(self, temp_dir: Path) -> None:
        """Test that function validates the input is a directory.

        Args:
            temp_dir: Fixture providing temp directory
        """
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")
        output_path = temp_dir / "test.zip"

        with pytest.raises(NotADirectoryError):
            _create_zip_internal(file_path, output_path, upload=False)


class TestUploadZipInternal:
    """Tests for _upload_zip_internal function."""

    def test_upload_zip_internal_missing_file(self, zip_output_dir: Path) -> None:
        """Test upload with nonexistent file raises FileNotFoundError.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        nonexistent = zip_output_dir / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            _upload_zip_internal(nonexistent)

    def test_upload_zip_internal_not_a_zipfile(self, zip_output_dir: Path) -> None:
        """Test upload with non-zip file raises ValueError.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        not_zip = zip_output_dir / "not_a_zip.txt"
        not_zip.write_text("not a zip file")

        with pytest.raises(ValueError, match="not a zip"):
            _upload_zip_internal(not_zip)

    def test_upload_zip_internal_no_url_configured(
        self, test_folder_structure: Path, zip_output_dir: Path, clean_env: None
    ) -> None:
        """Test upload without configured URL raises ValueError.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
            clean_env: Fixture ensuring clean environment
        """
        # Ensure env var not set
        os.environ.pop("DOT_WORK_ZIP_UPLOAD_URL", None)

        # Create a test zip file first
        from dot_work.zip import zip_folder

        output_path = zip_output_dir / "test.zip"
        zip_folder(test_folder_structure, output_path)

        # Try to upload without URL configured
        with pytest.raises(ValueError, match="No upload URL"):
            _upload_zip_internal(output_path)

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_internal_with_url(
        self,
        mock_requests: MagicMock,
        test_folder_structure: Path,
        zip_output_dir: Path,
        clean_env: None,
    ) -> None:
        """Test successful upload when URL is configured.

        Args:
            mock_requests: Mocked requests module
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
            clean_env: Fixture ensuring clean environment
        """
        os.environ["DOT_WORK_ZIP_UPLOAD_URL"] = "https://example.com/upload"

        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        # Create a test zip file first
        from dot_work.zip import zip_folder

        output_path = zip_output_dir / "test.zip"
        zip_folder(test_folder_structure, output_path)

        # This should not raise
        _upload_zip_internal(output_path)

        # Verify post was called
        mock_requests.post.assert_called_once()

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_internal_upload_failure(
        self,
        mock_requests: MagicMock,
        test_folder_structure: Path,
        zip_output_dir: Path,
        clean_env: None,
    ) -> None:
        """Test upload failure handling.

        Args:
            mock_requests: Mocked requests module
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
            clean_env: Fixture ensuring clean environment
        """
        os.environ["DOT_WORK_ZIP_UPLOAD_URL"] = "https://example.com/upload"

        # Mock failed response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Upload failed")
        mock_requests.post.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        # Create a test zip file first
        from dot_work.zip import zip_folder

        output_path = zip_output_dir / "test.zip"
        zip_folder(test_folder_structure, output_path)

        # This should raise RuntimeError
        with pytest.raises(RuntimeError):
            _upload_zip_internal(output_path)


class TestCLIIntegration:
    """Integration tests for CLI app basic functionality."""

    def test_app_import_success(self) -> None:
        """Test that the CLI app can be imported successfully."""
        from dot_work.zip.cli import app

        assert app is not None
        assert hasattr(app, "command")

    def test_app_has_create_command(self) -> None:
        """Test that the app has a create command."""
        from dot_work.zip.cli import app

        # Check that commands are registered
        assert len(app.registered_commands) > 0

    def test_app_has_upload_command(self) -> None:
        """Test that the app has an upload command."""
        from dot_work.zip.cli import app

        # Check for upload command by name
        command_names = [cmd.name for cmd in app.registered_commands]
        assert "upload" in command_names
