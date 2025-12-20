"""Configuration management for agent-review."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    storage_dir: str = ".agent-review"
    default_base_ref: str = "HEAD"
    server_host: str = "127.0.0.1"
    server_port: int = 0  # 0 = auto-pick

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            storage_dir=os.getenv("AGENT_REVIEW_STORAGE_DIR", ".agent-review"),
            default_base_ref=os.getenv("AGENT_REVIEW_BASE_REF", "HEAD"),
            server_host=os.getenv("AGENT_REVIEW_HOST", "127.0.0.1"),
            server_port=int(os.getenv("AGENT_REVIEW_PORT", "0")),
        )


def get_config() -> Config:
    """Get the application configuration."""
    return Config.from_env()
