"""
Configuration for Python code scanner.

Storage paths and environment-based configuration.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScanConfig:
    """Configuration for scan storage locations."""

    base_path: Path = field(default_factory=lambda: Path(".work/scan"))
    index_file: str = "code_index.json"
    cache_file: str = "cache.json"

    @classmethod
    def from_env(cls) -> "ScanConfig":
        """Create configuration from environment variables.

        Returns:
            ScanConfig with DOT_WORK_SCAN_PATH override if set.
        """
        base = os.getenv("DOT_WORK_SCAN_PATH")
        return cls(base_path=Path(base) if base else Path(".work/scan"))

    @property
    def index_path(self) -> Path:
        """Get the full path to the code index file.

        Returns:
            Path to code_index.json.
        """
        return self.base_path / self.index_file

    @property
    def cache_path(self) -> Path:
        """Get the full path to the cache file.

        Returns:
            Path to cache.json.
        """
        return self.base_path / self.cache_file

    def ensure_directories(self) -> None:
        """Create the scan directory if it doesn't exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
