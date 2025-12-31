"""Caching system for git analysis results."""

import hashlib
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

from dot_work.git.models import AnalysisConfig, CacheEntry, ChangeAnalysis

T = TypeVar("T")


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
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash[:16]}.json"  # Use first 16 chars for filename

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
            return self._deserialize_data(entry.data)

        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
            self.logger.warning(f"Failed to retrieve cache for key {key}: {e}")
            # Remove corrupted cache file
            try:
                self._remove_cache_file(self._get_cache_path(key))
            except Exception as remove_error:
                self.logger.debug(f"Failed to remove cache file for key {key}: {remove_error}")
            return None

    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON storage, handling dataclasses and datetime."""
        if is_dataclass(data):
            # Convert dataclass to dict and store type info
            return {
                "__dataclass__": data.__class__.__name__,
                "__module__": data.__class__.__module__,
                "data": asdict(data) if not isinstance(data, type) else asdict(data()),
            }
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, type):
            return {"__dataclass__": data.__name__, "__module__": data.__module__, "data": {}}
        else:
            return data

    def _deserialize_data(self, data: Any) -> Any:
        """Deserialize data from JSON, reconstructing dataclasses and datetime."""
        if isinstance(data, dict):
            # Check if this is a serialized dataclass
            if "__dataclass__" in data and "__module__" in data:
                # Import the class and reconstruct
                module_name = data["__module__"]
                class_name = data["__dataclass__"]
                # Handle ChangeAnalysis from models
                if module_name == "dot_work.git.models" and class_name == "ChangeAnalysis":
                    # Convert datetime strings back to datetime objects
                    inner_data = data["data"]
                    if "timestamp" in inner_data:
                        inner_data["timestamp"] = datetime.fromisoformat(inner_data["timestamp"])
                    return ChangeAnalysis(**inner_data)
                # For other types, return as dict
                return data["data"]
            # Regular dict - deserialize values
            return {k: self._deserialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deserialize_data(item) for item in data]
        elif isinstance(data, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(data)
            except ValueError:
                return data
        else:
            return data

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

            # Serialize data properly
            serialized_data = self._serialize_data(data)

            cache_data = {
                "key": key,
                "data": serialized_data,
                "timestamp": datetime.now().isoformat(),
                "ttl_hours": ttl_hours,
            }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

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
                return {
                    "total_entries": 0,
                    "total_size_bytes": 0,
                    "cache_directory": str(self.cache_dir),
                }

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

                except Exception:
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
