"""Configuration management for review functionality."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration for review."""

    storage_dir: str = ".work/reviews"
    default_base_ref: str = "HEAD"
    server_host: str = "127.0.0.1"
    server_port: int = 0  # 0 = auto-pick

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        return cls(
            storage_dir=os.getenv("DOT_WORK_REVIEW_STORAGE_DIR", ".work/reviews"),
            default_base_ref=os.getenv("DOT_WORK_REVIEW_BASE_REF", "HEAD"),
            server_host=os.getenv("DOT_WORK_REVIEW_HOST", "127.0.0.1"),
            server_port=int(os.getenv("DOT_WORK_REVIEW_PORT", "0")),
        )


# Global config instance for convenience
settings = Config.from_env()


def get_config() -> Config:
    """Get the application configuration."""
    return settings
