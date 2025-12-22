"""Tests for version config module."""

from pathlib import Path
from unittest.mock import patch

from dot_work.version.config import VersionConfig


def test_load_config_default(temp_dir: Path):
    """Test loading default configuration."""
    config = VersionConfig()

    loaded_config = config.load_config(temp_dir)

    # Check default values
    assert loaded_config["version_file"] == ".version"
    assert loaded_config["changelog_file"] == "CHANGELOG.md"
    assert loaded_config["commit_types"] == [
        "feat", "fix", "docs", "style", "refactor", "test", "chore"
    ]
    assert loaded_config["major_bump_types"] == ["feat"]
    assert loaded_config["minor_bump_types"] == ["fix"]


def test_load_config_from_file(temp_dir: Path):
    """Test loading configuration from .versionrc file."""
    # Create .versionrc file
    versionrc_content = """
version_file: ".custom-version"
changelog_file: "CUSTOM_CHANGELOG.md"
commit_types:
  - "feature"
  - "bugfix"
major_bump_types:
  - "feature"
minor_bump_types:
  - "bugfix"
"""
    versionrc_file = temp_dir / ".versionrc"
    versionrc_file.write_text(versionrc_content)

    config = VersionConfig()
    loaded_config = config.load_config(temp_dir)

    # Check loaded values
    assert loaded_config["version_file"] == ".custom-version"
    assert loaded_config["changelog_file"] == "CUSTOM_CHANGELOG.md"
    assert loaded_config["commit_types"] == ["feature", "bugfix"]
    assert loaded_config["major_bump_types"] == ["feature"]
    assert loaded_config["minor_bump_types"] == ["bugfix"]


def test_load_config_from_env(temp_dir: Path):
    """Test loading configuration from environment variables."""
    with patch.dict(
        "os.environ",
        {
            "DOT_WORK_VERSION_FILE": ".env-version",
            "DOT_WORK_CHANGELOG_FILE": "ENV_CHANGELOG.md",
        },
    ):
        config = VersionConfig()
        loaded_config = config.load_config(temp_dir)

        # Check environment values override defaults
        assert loaded_config["version_file"] == ".env-version"
        assert loaded_config["changelog_file"] == "ENV_CHANGELOG.md"


def test_load_config_invalid_yaml(temp_dir: Path):
    """Test handling of invalid YAML config file."""
    # Create invalid .versionrc file
    versionrc_file = temp_dir / ".versionrc"
    versionrc_file.write_text("invalid: yaml: content: [")

    config = VersionConfig()

    # Should not raise exception, should fallback to defaults
    loaded_config = config.load_config(temp_dir)

    # Check default values are used
    assert loaded_config["version_file"] == ".version"
    assert loaded_config["changelog_file"] == "CHANGELOG.md"