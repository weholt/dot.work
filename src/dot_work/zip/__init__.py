"""Zip module for dot-work.

This module provides functionality to create zip archives of directories while
respecting .gitignore patterns, and optionally upload them to remote endpoints.

Main exports:
    - ZipConfig: Configuration dataclass
    - zip_folder: Create a zip archive
    - upload_zip: Upload a zip file (optional, requires requests)
"""

from dot_work.zip.config import ZipConfig

__all__ = [
    "ZipConfig",
    "zip_folder",
    "should_include",
    "upload_zip",
]


def __getattr__(name: str):
    """Lazy load module attributes to provide helpful error messages."""
    if name == "zip_folder":
        from dot_work.zip.zipper import zip_folder

        return zip_folder
    elif name == "should_include":
        from dot_work.zip.zipper import should_include

        return should_include
    elif name == "upload_zip":
        from dot_work.zip.uploader import upload_zip

        return upload_zip
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
