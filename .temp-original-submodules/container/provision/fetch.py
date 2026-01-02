"""URL fetching and extraction for context injection.

This module provides functionality for fetching remote context files
and archives from URLs, with support for caching, authentication, and
security validation.
"""

from __future__ import annotations

import hashlib
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "dot-work" / "context"
MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
CHUNK_SIZE = 8192


@dataclass
class FetchResult:
    """Result of a URL fetch operation.

    Attributes:
        local_path: Path to the downloaded/cached file.
        was_cached: Whether the file was retrieved from cache.
        etag: ETag header from response (if available).
        last_modified: Last-Modified header from response (if available).
    """

    local_path: Path
    was_cached: bool
    etag: str | None = None
    last_modified: str | None = None


def validate_url(url: str) -> None:
    """Validate URL scheme and format.

    Args:
        url: URL to validate.

    Raises:
        ValueError: If URL is invalid or uses disallowed scheme.
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Parse URL to check scheme
    if "://" not in url:
        raise ValueError("URL must include scheme (e.g., https://)")

    scheme = url.split("://")[0].lower()

    # Only allow HTTPS
    allowed_schemes = {"https"}
    if scheme not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{scheme}' not allowed. Only HTTPS is supported for security."
        )

    # Basic format validation
    if not url.split("://")[1]:
        raise ValueError("URL must have a path after scheme")


def get_cache_path(url: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Get cache file path for a URL.

    Args:
        url: URL to cache.
        cache_dir: Cache directory.

    Returns:
        Path to cache file.
    """
    # Create cache directory if needed
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Hash URL for filename
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    return cache_dir / f"{url_hash}.cache"


def read_cache_headers(cache_path: Path) -> dict[str, str] | None:
    """Read cached ETag and Last-Modified headers.

    Args:
        cache_path: Path to cache file.

    Returns:
        Dict with 'etag' and 'last_modified' keys, or None if not cached.
    """
    header_path = cache_path.with_suffix(".headers")
    if not header_path.exists():
        return None

    try:
        import json

        return json.loads(header_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def write_cache_headers(cache_path: Path, headers: dict[str, str]) -> None:
    """Write cache headers to disk.

    Args:
        cache_path: Path to cache file.
        headers: Dict with 'etag' and/or 'last_modified'.
    """
    header_path = cache_path.with_suffix(".headers")
    try:
        import json

        header_path.write_text(json.dumps(headers))
    except OSError as e:
        logger.warning(f"Failed to write cache headers: {e}")


def fetch_url(
    url: str,
    token: str | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    max_size: int = MAX_SIZE_BYTES,
) -> FetchResult:
    """Fetch a file from URL, with caching support.

    Args:
        url: HTTPS URL to fetch.
        token: Optional Bearer token for authentication.
        cache_dir: Directory for cached files.
        max_size: Maximum allowed file size in bytes.

    Returns:
        FetchResult with local path and caching info.

    Raises:
        ValueError: If URL is invalid.
        HTTPError: If HTTP request fails.
        URLError: If URL cannot be accessed.
        RuntimeError: If file size exceeds max_size.
    """
    validate_url(url)

    cache_path = get_cache_path(url, cache_dir)
    cache_headers = read_cache_headers(cache_path)

    # Check cache
    if cache_path.exists() and cache_headers:
        logger.debug(f"Using cached file for {url}")
        return FetchResult(
            local_path=cache_path,
            was_cached=True,
            etag=cache_headers.get("etag"),
            last_modified=cache_headers.get("last_modified"),
        )

    # Prepare request
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Add conditional headers if we have cached data
    if cache_headers:
        if cache_headers.get("etag"):
            headers["If-None-Match"] = cache_headers["etag"]
        if cache_headers.get("last_modified"):
            headers["If-Modified-Since"] = cache_headers["last_modified"]

    request = Request(url, headers=headers)

    # Fetch with size limit
    logger.debug(f"Fetching {url}")
    try:
        with urlopen(request, timeout=30) as response:
            # Handle 304 Not Modified
            if response.code == 304 and cache_path.exists():
                logger.debug(f"Content unchanged, using cache for {url}")
                return FetchResult(
                    local_path=cache_path,
                    was_cached=True,
                    etag=cache_headers.get("etag") if cache_headers else None,
                    last_modified=cache_headers.get("last_modified") if cache_headers else None,
                )

            # Check content length
            content_length = response.getheader("Content-Length")
            if content_length:
                size = int(content_length)
                if size > max_size:
                    raise RuntimeError(
                        f"File size ({size} bytes) exceeds maximum ({max_size} bytes)"
                    )

            # Download file
            temp_path = cache_path.with_suffix(".tmp")
            downloaded_size = 0

            with open(temp_path, "wb") as f:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size:
                        temp_path.unlink(missing_ok=True)
                        raise RuntimeError(f"File size exceeds maximum ({max_size} bytes)")
                    f.write(chunk)

            # Move to final location
            temp_path.replace(cache_path)

            # Cache headers for conditional GET
            response_headers = {}
            etag = response.getheader("ETag")
            last_modified = response.getheader("Last-Modified")
            if etag or last_modified:
                if etag:
                    response_headers["etag"] = etag
                if last_modified:
                    response_headers["last_modified"] = last_modified
                write_cache_headers(cache_path, response_headers)

            return FetchResult(
                local_path=cache_path,
                was_cached=False,
                etag=etag,
                last_modified=last_modified,
            )

    except HTTPError as e:
        raise HTTPError(url, e.code, e.reason, e.headers, e.fp) from e
    except URLError as e:
        raise URLError(f"Failed to fetch {url}: {e.reason}") from e


def extract_zip(zip_path: Path, extract_dir: Path) -> list[Path]:
    """Extract a .zip archive to a directory.

    Args:
        zip_path: Path to .zip file.
        extract_dir: Directory to extract to.

    Returns:
        List of extracted file paths.

    Raises:
        ValueError: If file is not a .zip archive.
        RuntimeError: If extraction fails.
    """
    if not zip_path.name.endswith(".zip"):
        raise ValueError(f"Not a .zip file: {zip_path}")

    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        extracted_files = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Validate zip contents
            for name in zf.namelist():
                # Security: Check for path traversal
                if ".." in name or name.startswith("/"):
                    raise RuntimeError(f"Zip file contains unsafe path: {name}")

            # Extract all
            for name in zf.namelist():
                # Skip directories in the list (they're created implicitly)
                if name.endswith("/"):
                    continue

                zf.extract(name, extract_dir)
                extracted_path = extract_dir / name
                extracted_files.append(extracted_path)
                logger.debug(f"Extracted: {extracted_path}")

        return extracted_files

    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Invalid zip file: {e}") from e


def fetch_and_extract(
    url: str,
    extract_to: Path,
    token: str | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    max_size: int = MAX_SIZE_BYTES,
) -> FetchResult:
    """Fetch a URL and extract if it's a .zip archive.

    Args:
        url: HTTPS URL to fetch.
        extract_to: Directory to extract archives to.
        token: Optional Bearer token for authentication.
        cache_dir: Directory for cached files.
        max_size: Maximum allowed file size in bytes.

    Returns:
        FetchResult with path to downloaded or extracted content.
    """
    result = fetch_url(url, token=token, cache_dir=cache_dir, max_size=max_size)

    # If URL ends with .zip, extract the cached file
    if url.lower().endswith(".zip"):
        logger.debug(f"Extracting .zip file: {result.local_path}")
        # Use stem of URL filename for extract directory
        url_filename = url.split("/")[-1]
        extract_dir = extract_to / Path(url_filename).stem
        extract_zip(result.local_path, extract_dir)

        # Return path to extracted directory
        return FetchResult(
            local_path=extract_dir,
            was_cached=result.was_cached,
            etag=result.etag,
            last_modified=result.last_modified,
        )

    return result
