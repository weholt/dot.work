"""Caching system for git analysis results."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..models import AnalysisConfig, CacheEntry


class AnalysisCache:
    """Cache system for storing and retrieving git analysis results."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path.cwd() / ".git-analysis" / "cache"
        self.logger = logging.getLogger(__name__)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Use hash of key to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Any | None:
        """
        Retrieve cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return None

            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            # Create cache entry
            entry = CacheEntry(
                key=cache_data["key"],
                data=cache_data["data"],
                timestamp=datetime.fromisoformat(cache_data["timestamp"]),
                ttl_hours=cache_data.get("ttl_hours", 24),
            )

            # Check if expired
            if entry.is_expired():
                self._remove_cache_file(cache_path)
                return None

            self.logger.debug(f"Cache hit for key: {key}")
            return entry.data

        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
            self.logger.warning(f"Failed to retrieve cache for key {key}: {e}")
            # Remove corrupted cache file
            try:
                self._remove_cache_file(self._get_cache_path(key))
            except:
                pass
            return None

    def set(self, key: str, data: Any, ttl_hours: int = 24) -> bool:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl_hours: Time to live in hours

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)

            cache_data = {"key": key, "data": data, "timestamp": datetime.now().isoformat(), "ttl_hours": ttl_hours}

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, default=str)

            self.logger.debug(f"Cached data for key: {key}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cache data for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete cached data by key.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            self._remove_cache_file(cache_path)
            self.logger.debug(f"Deleted cache for key: {key}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to delete cache for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cached data.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                self.logger.info("Cleared all cache files")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        expired_count = 0

        try:
            if not self.cache_dir.exists():
                return 0

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache_data = json.load(f)

                    timestamp = datetime.fromisoformat(cache_data["timestamp"])
                    ttl_hours = cache_data.get("ttl_hours", 24)

                    if datetime.now() - timestamp > timedelta(hours=ttl_hours):
                        cache_file.unlink()
                        expired_count += 1

                except (json.JSONDecodeError, KeyError, ValueError):
                    # Remove corrupted cache files
                    cache_file.unlink()
                    expired_count += 1

            if expired_count > 0:
                self.logger.info(f"Cleaned up {expired_count} expired cache entries")

            return expired_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired cache: {e}")
            return 0

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            if not self.cache_dir.exists():
                return {"total_entries": 0, "total_size_bytes": 0, "cache_directory": str(self.cache_dir)}

            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            # Count expired entries
            expired_count = 0
            valid_count = 0

            for cache_file in cache_files:
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache_data = json.load(f)

                    timestamp = datetime.fromisoformat(cache_data["timestamp"])
                    ttl_hours = cache_data.get("ttl_hours", 24)

                    if datetime.now() - timestamp > timedelta(hours=ttl_hours):
                        expired_count += 1
                    else:
                        valid_count += 1

                except:
                    # Corrupted file counts as expired
                    expired_count += 1

            return {
                "total_entries": len(cache_files),
                "valid_entries": valid_count,
                "expired_entries": expired_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_directory": str(self.cache_dir),
            }

        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e), "cache_directory": str(self.cache_dir)}

    def _remove_cache_file(self, cache_path: Path):
        """Safely remove a cache file."""
        try:
            if cache_path.exists():
                cache_path.unlink()
        except Exception as e:
            self.logger.warning(f"Failed to remove cache file {cache_path}: {e}")


class CacheManager:
    """Manager for multiple cache instances with different configurations."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.main_cache = AnalysisCache(config.cache_dir)
        self.caches = {
            "commits": AnalysisCache(config.cache_dir / "commits"),
            "comparisons": AnalysisCache(config.cache_dir / "comparisons"),
            "files": AnalysisCache(config.cache_dir / "files"),
        }

    def get_cache(self, cache_type: str = "default") -> AnalysisCache:
        """
        Get cache instance by type.

        Args:
            cache_type: Type of cache ('default', 'commits', 'comparisons', 'files')

        Returns:
            Cache instance
        """
        return self.caches.get(cache_type, self.main_cache)

    def get_commit_cache(self) -> AnalysisCache:
        """Get cache for commit analyses."""
        return self.get_cache("commits")

    def get_comparison_cache(self) -> AnalysisCache:
        """Get cache for comparison results."""
        return self.get_cache("comparisons")

    def get_file_cache(self) -> AnalysisCache:
        """Get cache for file analyses."""
        return self.get_cache("files")

    def cleanup_all(self) -> dict[str, int]:
        """
        Clean up expired entries in all caches.

        Returns:
            Dictionary with cleanup results per cache type
        """
        results = {}

        for cache_name, cache in self.caches.items():
            removed = cache.cleanup_expired()
            results[cache_name] = removed

        # Also cleanup main cache
        removed = self.main_cache.cleanup_expired()
        results["default"] = removed

        total_removed = sum(results.values())
        if total_removed > 0:
            self.logger.info(f"Cleaned up {total_removed} expired cache entries total")

        return results

    def clear_all(self) -> bool:
        """
        Clear all caches.

        Returns:
            True if successful, False otherwise
        """
        success = True

        for cache in self.caches.values():
            if not cache.clear():
                success = False

        if not self.main_cache.clear():
            success = False

        return success

    def get_all_stats(self) -> dict[str, Any]:
        """
        Get statistics for all caches.

        Returns:
            Dictionary with cache statistics
        """
        stats = {}

        for cache_name, cache in self.caches.items():
            stats[cache_name] = cache.get_cache_stats()

        stats["default"] = self.main_cache.get_cache_stats()

        # Add totals
        total_entries = sum(s.get("total_entries", 0) for s in stats.values())
        total_size = sum(s.get("total_size_bytes", 0) for s in stats.values())

        stats["totals"] = {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

        return stats


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    import json

    key_data = {"args": args, "kwargs": sorted(kwargs.items())}

    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def is_cache_enabled(config: AnalysisConfig) -> bool:
    """
    Check if caching is enabled in configuration.

    Args:
        config: Analysis configuration

    Returns:
        True if caching should be used
    """
    # Check if caching is explicitly disabled
    if hasattr(config, "cache_enabled") and not config.cache_enabled:
        return False

    # Check if force refresh is enabled (bypasses cache)
    if config.force_refresh:
        return False

    return True
