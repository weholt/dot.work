"""Integration tests for URL fetching with mock HTTP server (FEAT-027)."""

import hashlib
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from urllib.error import HTTPError

from dot_work.container.provision.fetch import (
    FetchResult,
    fetch_and_extract,
    fetch_url,
)


@pytest.mark.integration
class TestFetchUrlIntegration:
    """Integration tests for URL fetching."""

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_simple_file(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch a simple file from HTTPS URL."""
        # Setup mock
        content = b"Hello, World!"
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        mock_response.read.side_effect = [content, b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Fetch
        result = fetch_url(
            url="https://example.com/test.txt",
            cache_dir=tmp_path,
        )

        # Verify
        assert result.was_cached is False
        assert result.local_path.exists()
        assert result.local_path.read_bytes() == content

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_with_bearer_token(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch with Bearer token authentication."""
        content = b"Authenticated content"
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        mock_response.read.side_effect = [content, b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Fetch with token
        result = fetch_url(
            url="https://api.example.com/data.json",
            token="secret-token-123",
            cache_dir=tmp_path,
        )

        # Verify Authorization header
        request = mock_urlopen.call_args[0][0]
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer secret-token-123"
        assert result.local_path.read_bytes() == content

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_caches_etag(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch should cache ETag for conditional GET."""
        # First request
        etag = '"33a64df551425fcc55e4d42a148795d9f25f89d4"'
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.side_effect = lambda h: {
            "ETag": etag,
            "Content-Length": "12",
        }.get(h)
        mock_response.read.side_effect = [b"First content", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result1 = fetch_url("https://example.com/file.txt", cache_dir=tmp_path)
        assert result1.etag == etag

        # Verify header file was created
        header_path = result1.local_path.with_suffix(".headers")
        assert header_path.exists()
        cached_headers = json.loads(header_path.read_text())
        assert cached_headers["etag"] == etag

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_uses_cached_response_on_304(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch should use cached file on 304 Not Modified."""
        # Calculate hash for URL to create proper cache file
        url_hash = hashlib.sha256(b"https://example.com/file.txt").hexdigest()

        # Create cached file with correct hash name
        cache_file = tmp_path / f"{url_hash}.cache"
        cache_file.write_bytes(b"Cached content")

        header_file = tmp_path / f"{url_hash}.headers"
        headers = {"etag": '"old-etag"', "last_modified": "Wed, 01 Jan 2024"}
        header_file.write_text(json.dumps(headers))

        # Mock 304 response
        mock_response = Mock()
        mock_response.code = 304
        mock_response.getheader.return_value = None
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_url("https://example.com/file.txt", cache_dir=tmp_path)

        assert result.was_cached is True
        assert result.local_path.read_text() == "Cached content"

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_enforces_size_limit(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """Fetch should reject files exceeding size limit."""
        # Mock response with large Content-Length
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = "150000000"  # 150MB
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with pytest.raises(RuntimeError, match="exceeds maximum"):
            fetch_url(
                "https://example.com/large.bin",
                cache_dir=tmp_path,
                max_size=100_000_000,  # 100MB limit
            )

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_fetch_http_error_propagates(self, mock_urlopen: Mock, tmp_path: Path) -> None:
        """HTTP errors should propagate to caller."""
        mock_urlopen.side_effect = HTTPError(
            url="https://example.com/missing.txt",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        with pytest.raises(HTTPError, match="404"):
            fetch_url("https://example.com/missing.txt", cache_dir=tmp_path)


@pytest.mark.integration
class TestFetchAndExtractIntegration:
    """Integration tests for fetch and extract."""

    @patch("dot_work.container.provision.fetch.extract_zip")
    @patch("dot_work.container.provision.fetch.urlopen")
    def test_zip_url_extraction(
        self,
        mock_urlopen: Mock,
        mock_extract: Mock,
        tmp_path: Path,
    ) -> None:
        """ZIP URL should be fetched and extracted."""
        # Mock fetch
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        mock_response.read.side_effect = [b"", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Mock extract - create actual directory for assertion
        output_dir = tmp_path / "output"
        extract_dir = output_dir / "context"  # stem of context.zip
        extract_dir.mkdir(parents=True)
        mock_extract.return_value = [extract_dir / "file.txt"]

        result = fetch_and_extract(
            url="https://example.com/context.zip",
            extract_to=output_dir,
            cache_dir=tmp_path,
        )

        # Should return directory path
        assert result.local_path.is_dir()
        assert mock_extract.called

    @patch("dot_work.container.provision.fetch.urlopen")
    def test_non_zip_url_not_extracted(
        self,
        mock_urlopen: Mock,
        tmp_path: Path,
    ) -> None:
        """Non-ZIP URL should not trigger extraction."""
        content = b"Plain text content"
        mock_response = Mock()
        mock_response.code = 200
        mock_response.getheader.return_value = None
        mock_response.read.side_effect = [content, b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = fetch_and_extract(
            url="https://example.com/config.json",
            extract_to=tmp_path / "output",
            cache_dir=tmp_path,
        )

        # Should return file path, not directory
        assert result.local_path.is_file()
        assert result.local_path.read_bytes() == content


@pytest.mark.integration
class TestRealZipExtraction:
    """Integration tests with real ZIP files."""

    def test_extract_real_zip_file(self, tmp_path: Path) -> None:
        """Extract a real ZIP file with multiple files."""
        from dot_work.container.provision.fetch import extract_zip

        # Create test ZIP
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("README.md", "# Test Project\n\nThis is a test.")
            zf.writestr("config.json", '{"key": "value"}')
            zf.writestr("src/main.py", "print('Hello')")

        # Extract
        extract_dir = tmp_path / "extracted"
        extracted = extract_zip(zip_path, extract_dir)

        # Verify all files extracted
        assert len(extracted) == 3
        assert (extract_dir / "README.md").exists()
        assert (extract_dir / "config.json").exists()
        assert (extract_dir / "src" / "main.py").exists()

        # Verify content
        assert (extract_dir / "config.json").read_text() == '{"key": "value"}'

    def test_extract_zip_with_subdirectories(self, tmp_path: Path) -> None:
        """Extract ZIP with nested directory structure."""
        from dot_work.container.provision.fetch import extract_zip

        zip_path = tmp_path / "nested.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("docs/guide.md", "# Guide")
            zf.writestr("src/utils/helper.py", "def help(): pass")

        extract_dir = tmp_path / "extracted"
        extracted = extract_zip(zip_path, extract_dir)

        # Verify nested structure
        assert (extract_dir / "docs" / "guide.md").exists()
        assert (extract_dir / "src" / "utils" / "helper.py").exists()
