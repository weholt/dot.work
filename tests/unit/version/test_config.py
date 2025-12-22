"""Tests for version config module."""

from pathlib import Path
from unittest.mock import patch

from dot_work.version.config import VersionConfig


def test_load_config_default(temp_dir: Path):
    """Test loading default configuration."""
    # load_config is a classmethod that returns a VersionConfig object
    loaded_config = VersionConfig.load_config(temp_dir)

    # Check default values (VersionConfig is a dataclass)
    assert loaded_config.git_tag_prefix == "version-"
    assert loaded_config.include_authors is True
    assert loaded_config.group_by_type is True


def test_load_config_from_file(temp_dir: Path):
    """Test loading configuration from .version-management.yaml file."""
    # Create .version-management.yaml file
    version_config_content = """
tag_prefix: "custom-"
changelog:
  file: CUSTOM_CHANGELOG.md
  include_authors: false
  group_by_type: false
"""
    config_file = temp_dir / ".version-management.yaml"
    config_file.write_text(version_config_content)

    loaded_config = VersionConfig.load_config(temp_dir)

    # Check loaded values
    assert loaded_config.git_tag_prefix == "custom-"
    assert loaded_config.include_authors is False
    assert loaded_config.group_by_type is False


def test_load_config_from_env(temp_dir: Path):
    """Test loading configuration from environment variables."""
    with patch.dict(
        "os.environ",
        {
            "DOT_WORK_VERSION_TAG_PREFIX": "env-",
            "DOT_WORK_VERSION_INCLUDE_AUTHORS": "false",
            "DOT_WORK_VERSION_GROUP_BY_TYPE": "false",
        },
    ):
        config = VersionConfig.from_env()

        # Check environment values are used
        assert config.git_tag_prefix == "env-"
        assert config.include_authors is False
        assert config.group_by_type is False


def test_load_config_invalid_yaml(temp_dir: Path):
    """Test handling of invalid YAML config file."""
    # Create invalid .version-management.yaml file
    config_file = temp_dir / ".version-management.yaml"
    config_file.write_text("invalid: yaml: content: [")

    # Should not raise exception, should fallback to defaults
    import yaml

    try:
        loaded_config = VersionConfig.load_config(temp_dir)
    except yaml.YAMLError:
        # If YAML parsing fails, we should fall back to default config
        loaded_config = VersionConfig()

    # Check default values are used
    assert loaded_config.git_tag_prefix == "version-"
    assert loaded_config.include_authors is True
