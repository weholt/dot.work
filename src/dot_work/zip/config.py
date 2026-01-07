"""Configuration for zip module.

This module handles configuration for the zip functionality using environment
variables and dot-work patterns.
"""

import os
from dataclasses import dataclass


@dataclass
class ZipConfig:
    """Configuration for zip upload functionality.

    Attributes:
        upload_url: Optional API endpoint for uploading zip files
    """

    upload_url: str | None = None

    @classmethod
    def from_env(cls) -> "ZipConfig":
        """Load configuration from environment variables.

        Returns:
            ZipConfig instance with settings from environment

        Environment Variables:
            DOT_WORK_ZIP_UPLOAD_URL: API endpoint for zip uploads (optional)
        """
        return cls(
            upload_url=os.getenv("DOT_WORK_ZIP_UPLOAD_URL"),
        )

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If required configuration is missing
        """
        # Currently all settings are optional
        pass
