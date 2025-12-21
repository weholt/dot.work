"""Unit tests for dot_work.review.config module."""

from __future__ import annotations

import os
from unittest.mock import patch

from dot_work.review.config import Config, get_config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = Config()
        # Note: dot_work.review uses .work/reviews as default
        assert config.storage_dir == ".work/reviews"
        assert config.default_base_ref == "HEAD"
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = Config(
            storage_dir=".custom-dir",
            default_base_ref="main",
            server_host="0.0.0.0",
            server_port=8080,
        )
        assert config.storage_dir == ".custom-dir"
        assert config.default_base_ref == "main"
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 8080

    def test_from_env_defaults(self) -> None:
        """Test loading from environment with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
            # Note: dot_work.review uses .work/reviews as default
            assert config.storage_dir == ".work/reviews"
            assert config.default_base_ref == "HEAD"
            assert config.server_host == "127.0.0.1"
            assert config.server_port == 0

    def test_from_env_custom(self) -> None:
        """Test loading from environment with custom values."""
        env = {
            "DOT_WORK_REVIEW_STORAGE_DIR": ".custom",
            "DOT_WORK_REVIEW_BASE_REF": "develop",
            "DOT_WORK_REVIEW_HOST": "0.0.0.0",
            "DOT_WORK_REVIEW_PORT": "9000",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config.from_env()
            assert config.storage_dir == ".custom"
            assert config.default_base_ref == "develop"
            assert config.server_host == "0.0.0.0"
            assert config.server_port == 9000


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_config(self) -> None:
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)
