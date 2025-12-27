"""Tests for dot_work.zip.uploader module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.zip.uploader import upload_zip


class TestUploadZip:
    """Tests for upload_zip function."""

    def test_upload_zip_requires_requests(self, zip_output_dir: Path) -> None:
        """Test that upload_zip raises ImportError if requests is not available.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04")  # Minimal zip header

        # Patch requests to None to simulate missing module
        with patch("dot_work.zip.uploader.requests", None):
            with pytest.raises(ImportError, match="requests"):
                upload_zip(test_zip, "https://example.com/upload")

    def test_upload_zip_file_not_found(self, zip_output_dir: Path) -> None:
        """Test that upload_zip raises FileNotFoundError for missing file.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        nonexistent = zip_output_dir / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            upload_zip(nonexistent, "https://example.com/upload")

    def test_upload_zip_not_a_file(self, zip_output_dir: Path) -> None:
        """Test that upload_zip raises ValueError for directories.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        with pytest.raises(ValueError, match="Not a file"):
            upload_zip(zip_output_dir, "https://example.com/upload")

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_success(self, mock_requests: MagicMock, zip_output_dir: Path) -> None:
        """Test successful upload with mocked requests.

        Args:
            mock_requests: Mocked requests module
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04\x00\x00\x00\x00")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        # This should not raise
        upload_zip(test_zip, "https://example.com/upload")

        # Verify post was called
        mock_requests.post.assert_called_once()
        args, kwargs = mock_requests.post.call_args
        assert args[0] == "https://example.com/upload"
        assert "files" in kwargs
        assert kwargs["timeout"] == (10, 30)  # (connect timeout, read timeout)
        assert kwargs["verify"] is True  # Explicit SSL verification

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_http_error(self, mock_requests: MagicMock, zip_output_dir: Path) -> None:
        """Test upload failure with HTTP error.

        Args:
            mock_requests: Mocked requests module
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04\x00\x00\x00\x00")

        # Mock failed response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_requests.post.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        # This should raise RuntimeError
        with pytest.raises(RuntimeError, match="Upload failed"):
            upload_zip(test_zip, "https://example.com/upload")

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_network_error(self, mock_requests: MagicMock, zip_output_dir: Path) -> None:
        """Test upload failure with network error.

        Args:
            mock_requests: Mocked requests module
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04\x00\x00\x00\x00")

        # Mock network error
        mock_requests.post.side_effect = Exception("Connection failed")
        mock_requests.exceptions.RequestException = Exception

        # This should raise RuntimeError
        with pytest.raises(RuntimeError, match="Upload failed"):
            upload_zip(test_zip, "https://example.com/upload")

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_path_object(self, mock_requests: MagicMock, zip_output_dir: Path) -> None:
        """Test that upload_zip accepts Path objects.

        Args:
            mock_requests: Mocked requests module
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file using Path object
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04\x00\x00\x00\x00")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        # Should work with Path object
        upload_zip(test_zip, "https://example.com/upload")

        mock_requests.post.assert_called_once()

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_file_sent_correctly(self, mock_requests: MagicMock, temp_dir: Path) -> None:
        """Test that the zip file content is sent correctly.

        Args:
            mock_requests: Mocked requests module
            temp_dir: Fixture providing temp directory
        """
        # Create a test zip file with specific content
        test_zip = temp_dir / "test.zip"
        content = b"PK\x03\x04test content"
        test_zip.write_bytes(content)

        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        upload_zip(test_zip, "https://example.com/upload")

        # Verify the file was passed to post
        mock_requests.post.assert_called_once()
        kwargs = mock_requests.post.call_args.kwargs
        assert "files" in kwargs

        # Extract the file content from the mock call
        files_dict = kwargs["files"]
        assert "file" in files_dict
        file_name, file_obj, content_type = files_dict["file"]
        assert file_name == "test.zip"
        assert content_type == "application/zip"

    @patch("dot_work.zip.uploader.requests")
    def test_upload_zip_timeout_set(self, mock_requests: MagicMock, zip_output_dir: Path) -> None:
        """Test that upload uses timeout parameter.

        Args:
            mock_requests: Mocked requests module
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        upload_zip(test_zip, "https://example.com/upload")

        # Verify timeout and SSL verification parameters
        kwargs = mock_requests.post.call_args.kwargs
        assert kwargs["timeout"] == (10, 30)  # (connect timeout, read timeout)
        assert kwargs["verify"] is True  # Explicit SSL verification

    def test_upload_zip_rejects_http_url(self, zip_output_dir: Path) -> None:
        """Test that upload_zip rejects HTTP (non-HTTPS) URLs.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04")

        # HTTP URL should raise ValueError
        with pytest.raises(ValueError, match="Only HTTPS URLs are supported"):
            upload_zip(test_zip, "http://example.com/upload")

    def test_upload_zip_rejects_non_http_url(self, zip_output_dir: Path) -> None:
        """Test that upload_zip rejects non-HTTP URLs.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        # Create a test zip file
        test_zip = zip_output_dir / "test.zip"
        test_zip.write_bytes(b"PK\x03\x04")

        # FTP URL should raise ValueError
        with pytest.raises(ValueError, match="Only HTTPS URLs are supported"):
            upload_zip(test_zip, "ftp://example.com/upload")
