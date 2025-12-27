"""Upload functionality for zip archives.

This module handles uploading zip files to remote endpoints. The requests library
is optional - if not installed, operations will fail gracefully with a helpful error.
"""

from pathlib import Path

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None


def upload_zip(zip_path: Path, api_url: str) -> None:
    """Upload a zip file to a configured API endpoint.

    Args:
        zip_path: Path to the zip file to upload
        api_url: API endpoint URL for uploading (must be HTTPS)

    Raises:
        ImportError: If requests library is not installed
        FileNotFoundError: If zip file does not exist
        ValueError: If api_url is not HTTPS
        RuntimeError: If upload fails (HTTP error or SSL verification failure)
    """
    if requests is None:
        raise ImportError(
            "The 'requests' library is required for upload functionality. "
            "Install it with: pip install 'dot-work[zip-upload]'"
        )

    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    if not zip_path.is_file():
        raise ValueError(f"Not a file: {zip_path}")

    # Validate URL scheme - require HTTPS for secure uploads
    if not api_url.startswith("https://"):
        raise ValueError(
            f"Only HTTPS URLs are supported for secure uploads. Got: {api_url}"
        )

    # Upload the file with explicit SSL verification
    # timeout=(10, 30) = 10s for connection, 30s for read
    with open(zip_path, "rb") as f:
        files = {"file": (zip_path.name, f, "application/zip")}
        try:
            response = requests.post(
                api_url,
                files=files,
                timeout=(10, 30),  # (connect timeout, read timeout)
                verify=True,  # Explicit SSL certificate verification
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Upload failed: {e}") from e
