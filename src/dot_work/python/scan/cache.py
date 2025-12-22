"""
File caching for incremental scanning.
"""

import json
from pathlib import Path

from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.models import CacheEntry
from dot_work.python.scan.utils import compute_file_hash, get_file_mtime, get_file_size


class ScanCache:
    """Cache for incremental scanning of Python files."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        """Initialize the cache.

        Args:
            config: Scan configuration. Uses default if None.
        """
        self.config = config or ScanConfig()
        self.cache: dict[str, CacheEntry] = {}
        self._loaded = False

    def load(self) -> None:
        """Load cache from disk."""
        if self._loaded:
            return

        cache_path = self.config.cache_path
        if not cache_path.exists():
            self._loaded = True
            return

        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            self.cache = {
                path: CacheEntry(
                    path=entry["path"],
                    mtime=entry["mtime"],
                    size=entry["size"],
                    hash=entry.get("hash"),
                )
                for path, entry in data.items()
            }
        except (OSError, json.JSONDecodeError, KeyError):
            self.cache = {}

        self._loaded = True

    def save(self) -> None:
        """Save cache to disk."""
        self.config.ensure_directories()

        cache_path = self.config.cache_path
        data = {
            path: {
                "path": entry.path,
                "mtime": entry.mtime,
                "size": entry.size,
                "hash": entry.hash,
            }
            for path, entry in self.cache.items()
        }

        cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def is_cached(self, path: Path) -> bool:
        """Check if a file is in the cache and unchanged.

        Args:
            path: File path to check.

        Returns:
            True if file is cached and unchanged.
        """
        self.load()
        path_str = str(path)

        if path_str not in self.cache:
            return False

        entry = self.cache[path_str]

        try:
            current_mtime = get_file_mtime(path)
            current_size = get_file_size(path)

            if entry.mtime == current_mtime and entry.size == current_size:
                return True
        except OSError:
            return False

        return False

    def update(self, path: Path) -> None:
        """Update cache entry for a file.

        Args:
            path: File path to update.
        """
        self.load()

        try:
            path_str = str(path)
            self.cache[path_str] = CacheEntry(
                path=path_str,
                mtime=get_file_mtime(path),
                size=get_file_size(path),
                hash=compute_file_hash(path),
            )
        except OSError:
            pass

    def remove(self, path: Path) -> None:
        """Remove a file from the cache.

        Args:
            path: File path to remove.
        """
        self.load()
        path_str = str(path)
        self.cache.pop(path_str, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    @property
    def size(self) -> int:
        """Get the number of cached entries.

        Returns:
            Number of cache entries.
        """
        self.load()
        return len(self.cache)
