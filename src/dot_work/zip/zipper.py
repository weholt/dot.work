"""Core zip module for creating archives respecting .gitignore patterns.

This module provides functionality to create zip archives from directories while
respecting .gitignore patterns. It uses gitignore_parser to accurately match
gitignore rules.
"""

import os
import zipfile
from collections.abc import Callable
from pathlib import Path

try:
    from gitignore_parser import parse_gitignore  # type: ignore[import-untyped]
except ImportError as e:
    raise ImportError(
        "gitignore_parser is required for zip functionality. "
        "Install it with: pip install gitignore-parser"
    ) from e


def should_include(filepath: Path, ignore_matcher: Callable[[str], bool] | None) -> bool:
    """Check if a file should be included in the zip archive.

    Args:
        filepath: Path to the file to check
        ignore_matcher: Gitignore matcher callable from parse_gitignore, or None

    Returns:
        True if the file should be included, False if it matches gitignore patterns
    """
    if ignore_matcher:
        try:
            return not ignore_matcher(str(filepath))
        except Exception:
            # If matching fails, include the file by default
            return True
    return True


def zip_folder(
    folder_path: Path,
    output_path: Path,
    compression: int = zipfile.ZIP_DEFLATED,
) -> None:
    """Create a zip archive of a folder respecting .gitignore patterns.

    Args:
        folder_path: Path to the folder to zip
        output_path: Path where the zip file should be created
        compression: Compression method (default: ZIP_DEFLATED for deflate)

    Raises:
        FileNotFoundError: If folder_path does not exist
        ValueError: If output_path is not writable
    """
    folder_path = Path(folder_path)
    output_path = Path(output_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    # Load .gitignore if it exists
    gitignore_path = folder_path / ".gitignore"
    ignore_matcher = None
    if gitignore_path.exists():
        try:
            ignore_matcher = parse_gitignore(gitignore_path)
        except Exception as e:
            # If .gitignore parsing fails, warn but continue
            print(f"Warning: Failed to parse .gitignore: {e}")

    # Create zip archive
    with zipfile.ZipFile(output_path, "w", compression) as zipf:
        for root, _dirs, files in os.walk(folder_path):
            root_path = Path(root)

            for filename in files:
                file_path = root_path / filename
                rel_path = file_path.relative_to(folder_path)

                # Check if file should be included
                if should_include(file_path, ignore_matcher):
                    zipf.write(file_path, rel_path)
