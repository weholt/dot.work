"""Tests for URL fetching functionality (FEAT-027)."""

import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dot_work.container.provision.fetch import (
    DEFAULT_CACHE_DIR,
    FetchResult,
    extract_zip,
    fetch_and_extract,
    fetch_url,
    get_cache_path,
    read_cache_headers,
    validate_url,
    write_cache_headers,
)


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_https_url(self) -> None:
        """Valid HTTPS URL should pass."""
        validate_url("https://example.com/file.txt")

    def test_valid_https_url_with_path(self) -> None:
        """Valid HTTPS URL with path should pass."""
        validate_url("https://example.com/path/to/file.json")

    def test_empty_url_raises(self) -> None:
        """Empty URL should raise ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            validate_url("")

    def test_missing_scheme_raises(self) -> None:
        """URL without scheme should raise ValueError."""
        with pytest.raises(ValueError, match="scheme"):
            validate_url("example.com/file.txt")

    def test_http_scheme_rejected(self) -> None:
        """HTTP (not HTTPS) scheme should be rejected."""
        with pytest.raises(ValueError, match="not allowed.*HTTPS"):
            validate_url("http://example.com/file.txt")

    def test_file_scheme_rejected(self) -> None:
        """file:// scheme should be rejected."""
        with pytest.raises(ValueError, match="not allowed"):
            validate_url("file:///etc/passwd")

    def test_missing_path_after_scheme(self) -> None:
        """URL with scheme but no path should raise ValueError."""
        with pytest.raises(ValueError, match="path after scheme"):
            validate_url("https://")


class TestGetCachePath:
    """Tests for cache path generation."""

    def test_cache_path_is_in_cache_dir(self, tmp_path: Path) -> None:
        """Cache path should be in cache directory."""
        cache_dir = tmp_path / "cache"
        result = get_cache_path("https://example.com/file.txt", cache_dir)
        assert result.parent == cache_dir

    def test_cache_path_uses_hash(self) -> None:
        """Cache filename should be hash of URL."""
        result1 = get_cache_path("https://example.com/file.txt")
        result2 = get_cache_path("https://example.com/file.txt")
        assert result1.name == result2.name
        assert result1.name.endswith(".cache")

    def test_different_urls_different_hashes(self) -> None:
        """Different URLs should produce different hashes."""
        result1 = get_cache_path("https://example.com/file1.txt")
        result2 = get_cache_path("https://example.com/file2.txt")
        assert result1.name != result2.name


class TestFetchUrl:
    """Tests for URL fetching."""

    def test_invalid_url_raises(self, tmp_path: Path) -> None:
        """Invalid URL should raise ValueError."""
        with pytest.raises(ValueError):
            fetch_url("not-a-url", cache_dir=tmp_path)

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_successful_fetch(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Successful fetch should create cache file."""
        # Mock response
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        # Return content once, then empty bytes to end the read loop
        mock_response.read.side_effect = [b"test content", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_url("https://example.com/test.txt", cache_dir=tmp_path)

        assert result.was_cached is False
        assert result.local_path.exists()
        assert result.local_path.read_text() == "test content"

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_with_token(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch with token should include Authorization header."""
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        mock_response.read.side_effect = [b"", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        fetch_url("https://example.com/test.txt", token="my-token", cache_dir=tmp_path)

        # Verify Authorization header was set
        request = mock_urlopen.call_args[0][0]
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer my-token"

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_respects_size_limit(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch should enforce size limit."""
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = "200000000"  # 200MB
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with pytest.raises(RuntimeError, match="exceeds maximum"):
            fetch_url("https://example.com/large.txt", cache_dir=tmp_path, max_size=50_000_000)


class TestExtractZip:
    """Tests for ZIP extraction."""

    def test_extract_non_zip_raises(self, tmp_path: Path) -> None:
        """Non-zip file should raise ValueError."""
        not_zip = tmp_path / "test.txt"
        not_zip.write_text("not a zip")

        with pytest.raises(ValueError, match="Not a .zip file"):
            extract_zip(not_zip, tmp_path / "output")

    def test_extract_zip_creates_files(self, tmp_path: Path) -> None:
        """Extracting zip should create files."""
        # Create a test zip
        zip_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extract"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        extracted = extract_zip(zip_path, extract_dir)

        assert len(extracted) == 2
        assert (extract_dir / "file1.txt").read_text() == "content1"
        assert (extract_dir / "file2.txt").read_text() == "content2"

    def test_extract_zip_rejects_path_traversal(self, tmp_path: Path) -> None:
        """Zip with path traversal should be rejected."""
        zip_path = tmp_path / "malicious.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../escape.txt", "malicious")

        with pytest.raises(RuntimeError, match="unsafe path"):
            extract_zip(zip_path, tmp_path / "extract")


class TestFetchAndExtract:
    """Tests for combined fetch and extract."""

    @patch("dot_work.container.provision.fetch.extract_zip")
    @patch("dot_work.container.provision.fetch.fetch_url")
    def test_zip_file_is_extracted(
        self,
        mock_fetch: Mock,
        mock_extract: Mock,
        tmp_path: Path,
    ) -> None:
        """ZIP file should be extracted after fetch."""
        mock_fetch.return_value = FetchResult(
            local_path=tmp_path / "archive.zip",
            was_cached=False,
        )
        # Create the extract directory for the test
        extract_dir = tmp_path / "output" / "archive"
        extract_dir.mkdir(parents=True)
        mock_extract.return_value = [extract_dir / "file.txt"]

        result = fetch_and_extract(
            url="https://example.com/archive.zip",
            extract_to=tmp_path / "output",
        )

        assert mock_extract.called
        assert result.local_path.is_dir()
        assert result.local_path == extract_dir


class TestCacheHeaders:
    """Tests for cache header management."""

    def test_read_nonexistent_cache_headers(self, tmp_path: Path) -> None:
        """Reading nonexistent headers should return None."""
        result = read_cache_headers(tmp_path / "nonexistent.cache")
        assert result is None

    def test_write_and_read_cache_headers(self, tmp_path: Path) -> None:
        """Writing and reading cache headers should persist data."""
        cache_path = tmp_path / "test.cache"
        headers = {"etag": '"abc123"', "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT"}

        write_cache_headers(cache_path, headers)
        result = read_cache_headers(cache_path)

        assert result == headers
