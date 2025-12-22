"""Tests for dot_work.zip.config module."""

import os

import pytest

from dot_work.zip.config import ZipConfig


class TestZipConfig:
    """Tests for ZipConfig class."""

    def test_config_init_default(self) -> None:
        """Test ZipConfig initialization with defaults."""
        config = ZipConfig()

        assert config.upload_url is None

    def test_config_init_with_url(self) -> None:
        """Test ZipConfig initialization with upload_url."""
        url = "https://example.com/upload"
        config = ZipConfig(upload_url=url)

        assert config.upload_url == url

    def test_config_from_env_with_url(self, clean_env: None) -> None:
        """Test ZipConfig.from_env() loads upload_url from environment.

        Args:
            clean_env: Fixture ensuring clean environment
        """
        url = "https://api.example.com/zip"
        os.environ["DOT_WORK_ZIP_UPLOAD_URL"] = url

        config = ZipConfig.from_env()

        assert config.upload_url == url

    def test_config_from_env_without_url(self, clean_env: None) -> None:
        """Test ZipConfig.from_env() handles missing environment variable.

        Args:
            clean_env: Fixture ensuring clean environment
        """
        # Ensure env var is not set
        os.environ.pop("DOT_WORK_ZIP_UPLOAD_URL", None)

        config = ZipConfig.from_env()

        assert config.upload_url is None

    def test_config_from_env_empty_string(self, clean_env: None) -> None:
        """Test ZipConfig.from_env() handles empty string in environment.

        Args:
            clean_env: Fixture ensuring clean environment
        """
        os.environ["DOT_WORK_ZIP_UPLOAD_URL"] = ""

        config = ZipConfig.from_env()

        # Empty string should be treated as set (not None)
        assert config.upload_url == ""

    def test_config_validate_no_error(self) -> None:
        """Test ZipConfig.validate() doesn't raise with valid config."""
        config = ZipConfig(upload_url="https://example.com")

        # Should not raise
        config.validate()

    def test_config_validate_with_none_url(self) -> None:
        """Test ZipConfig.validate() doesn't raise with None upload_url."""
        config = ZipConfig(upload_url=None)

        # Should not raise (all settings are optional)
        config.validate()

    def test_config_dataclass_attributes(self) -> None:
        """Test ZipConfig dataclass attributes."""
        config = ZipConfig(upload_url="https://example.com")

        # Should have expected attributes
        assert hasattr(config, "upload_url")
        assert config.upload_url == "https://example.com"

    def test_config_equality(self) -> None:
        """Test ZipConfig equality comparison."""
        config1 = ZipConfig(upload_url="https://example.com")
        config2 = ZipConfig(upload_url="https://example.com")
        config3 = ZipConfig(upload_url="https://different.com")

        assert config1 == config2
        assert config1 != config3

    def test_config_repr(self) -> None:
        """Test ZipConfig string representation."""
        config = ZipConfig(upload_url="https://example.com")

        repr_str = repr(config)

        # Should contain class name and attribute
        assert "ZipConfig" in repr_str
        assert "upload_url" in repr_str
