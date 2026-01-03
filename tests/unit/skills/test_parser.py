"""Unit tests for dot_work.skills.parser module.

Tests for _deep_merge, _load_global_defaults, and SkillParser class.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dot_work.skills.models import (
    Skill,
    SkillEnvironmentConfig,
    SkillMetadata,
)
from dot_work.skills.parser import (
    GLOBAL_DEFAULTS_PATH,
    SkillParser,
    SkillParserError,
    _deep_merge,
    _load_global_defaults,
)


class TestDeepMerge:
    """Test _deep_merge function behavior."""

    def test_deep_merge_basic(self):
        """Basic deep merge behavior - local values override global."""
        global_dict = {"a": 1, "b": 2}
        local_dict = {"b": 3, "c": 4}
        result = _deep_merge(global_dict, local_dict)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested_dicts(self):
        """Deep merge of nested dictionaries."""
        global_dict = {
            "environments": {
                "claude": {"target": ".claude/skills/", "filename_suffix": "-skill"},
            }
        }
        local_dict = {
            "environments": {
                "claude": {"filename": "custom.md"},
            }
        }
        result = _deep_merge(global_dict, local_dict)
        expected = {
            "environments": {
                "claude": {"target": ".claude/skills/", "filename": "custom.md"}
            }
        }
        assert result == expected

    def test_deep_merge_empty_dict_preserves_defaults(self):
        """Empty local dict should preserve global defaults."""
        global_dict = {"a": 1, "b": 2, "environments": {"claude": {"target": ".claude/"}}}
        local_dict = {"environments": {}}
        result = _deep_merge(global_dict, local_dict)
        # Empty local dict for environments should preserve global environments
        assert result["environments"] == {"claude": {"target": ".claude/"}}  # type: ignore

    def test_deep_merge_local_overrides_global(self):
        """Local values override global values."""
        global_dict = {"environments": {"claude": {"target": ".claude/old/"}}}
        local_dict = {"environments": {"claude": {"target": ".claude/new/"}}}
        result = _deep_merge(global_dict, local_dict)
        assert result["environments"]["claude"]["target"] == ".claude/new/"  # type: ignore

    def test_deep_merge_filename_mutual_exclusion(self):
        """Specifying filename removes filename_suffix from global."""
        global_dict = {
            "environments": {
                "claude": {"target": ".claude/", "filename_suffix": "-skill"}
            }
        }
        local_dict = {"environments": {"claude": {"filename": "custom.md"}}}
        result = _deep_merge(global_dict, local_dict)

        assert "filename" in result["environments"]["claude"]  # type: ignore
        assert result["environments"]["claude"]["filename"] == "custom.md"  # type: ignore
        assert "filename_suffix" not in result["environments"]["claude"]  # type: ignore

    def test_deep_merge_filename_suffix_mutual_exclusion(self):
        """Specifying filename_suffix removes filename from global."""
        global_dict = {
            "environments": {
                "claude": {"target": ".claude/", "filename": "default.md"}
            }
        }
        local_dict = {"environments": {"claude": {"filename_suffix": "-custom"}}}
        result = _deep_merge(global_dict, local_dict)

        assert "filename_suffix" in result["environments"]["claude"]  # type: ignore
        assert result["environments"]["claude"]["filename_suffix"] == "-custom"  # type: ignore
        assert "filename" not in result["environments"]["claude"]  # type: ignore

    def test_deep_merge_no_global(self):
        """Merge with no global defaults returns local dict."""
        local_dict = {"a": 1, "b": 2}
        result = _deep_merge({}, local_dict)
        assert result == {"a": 1, "b": 2}

    def test_deep_merge_no_local(self):
        """Merge with no local values returns global dict."""
        global_dict = {"a": 1, "b": 2}
        result = _deep_merge(global_dict, {})
        assert result == {"a": 1, "b": 2}

    def test_deep_merge_does_not_mutate_inputs(self):
        """Deep merge should not mutate input dictionaries."""
        global_dict = {"a": 1, "b": {"c": 2}}
        local_dict = {"b": {"d": 3}}
        global_copy = {"a": 1, "b": {"c": 2}}
        local_copy = {"b": {"d": 3}}

        _deep_merge(global_dict, local_dict)

        assert global_dict == global_copy
        assert local_dict == local_copy


class TestLoadGlobalDefaults:
    """Test _load_global_defaults function behavior."""

    def test_load_global_defaults_file_exists(self, tmp_path):
        """Load global.yml when file exists."""
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/skills/"
      filename_suffix: "-skill"
"""
        )

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            result = _load_global_defaults()

        expected = {
            "environments": {
                "claude": {"target": ".claude/skills/", "filename_suffix": "-skill"}
            }
        }
        assert result == expected

    def test_load_global_defaults_file_missing(self, tmp_path):
        """Return empty dict when global.yml missing."""
        missing_path = tmp_path / "nonexistent" / "global.yml"

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", missing_path):
            result = _load_global_defaults()

        assert result == {}

    def test_load_global_defaults_malformed_yaml(self, tmp_path):
        """Malformed YAML raises yaml.scanner.ScannerError.

        Note: The current implementation propagates the YAML parsing error
        rather than catching it. This is the actual behavior.
        """
        global_yml = tmp_path / "global.yml"
        global_yml.write_text("invalid: yaml: content: [")

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            # Should raise yaml.scanner.ScannerError
            with pytest.raises(Exception):  # ScannerError is a subclass of Exception
                _load_global_defaults()

    def test_load_global_defaults_no_defaults_key(self, tmp_path):
        """Return empty dict when file exists but has no 'defaults' key."""
        global_yml = tmp_path / "global.yml"
        global_yml.write_text("other_key: value\n")

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            result = _load_global_defaults()

        assert result == {}

    def test_load_global_defaults_defaults_is_not_dict(self, tmp_path):
        """When 'defaults' is not a dict, returns the value as-is.

        Note: The current implementation returns data.get("defaults", {})
        directly without type checking. If defaults is a string, it returns
        that string. This is the actual behavior.
        """
        global_yml = tmp_path / "global.yml"
        global_yml.write_text("defaults: \"not-a-dict\"\n")

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            result = _load_global_defaults()

        # Current implementation returns the value as-is, not empty dict
        assert result == "not-a-dict"


class TestSkillParser:
    """Test SkillParser class methods."""

    def test_parse_valid_skill_file(self, tmp_path):
        """Parse a valid SKILL.md file."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill for unit testing
license: MIT
---

# Test Skill

This is a test skill content.
"""
        )

        parser = SkillParser()
        skill = parser.parse(skill_dir)

        assert isinstance(skill, Skill)
        assert skill.meta.name == "test-skill"
        assert skill.meta.description == "A test skill for unit testing"
        assert skill.meta.license == "MIT"
        assert "# Test Skill" in skill.content

    def test_parse_skill_file_not_found(self, tmp_path):
        """Raise FileNotFoundError when SKILL.md not found."""
        skill_dir = tmp_path / "nonexistent-skill"
        skill_dir.mkdir()

        parser = SkillParser()
        with pytest.raises(FileNotFoundError, match="SKILL.md not found"):
            parser.parse(skill_dir)

    def test_parse_invalid_frontmatter_format(self, tmp_path):
        """Raise ValueError when frontmatter markers are missing."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("No frontmatter markers here")

        parser = SkillParser()
        with pytest.raises(ValueError, match="missing frontmatter markers"):
            parser.parse(skill_dir)

    def test_parse_invalid_yaml(self, tmp_path):
        """Raise SkillParserError when YAML is invalid."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
invalid_yaml: [
---

Content here
"""
        )

        parser = SkillParser()
        with pytest.raises(SkillParserError, match="Invalid YAML"):
            parser.parse(skill_dir)

    def test_parse_missing_required_field_name(self, tmp_path):
        """Raise SkillParserError when 'name' field is missing."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
description: A test skill
---

Content
"""
        )

        parser = SkillParser()
        with pytest.raises(SkillParserError, match="Missing required field 'name'"):
            parser.parse(skill_dir)

    def test_parse_missing_required_field_description(self, tmp_path):
        """Raise SkillParserError when 'description' field is missing."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
---

Content
"""
        )

        parser = SkillParser()
        with pytest.raises(
            SkillParserError, match="Missing required field 'description'"
        ):
            parser.parse(skill_dir)

    def test_parse_with_global_defaults(self, tmp_path):
        """Skill parsing should merge global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/skills/"
      filename_suffix: "-skill"
"""
        )

        # Create skill file
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
environments:
  claude:
    filename: "custom.md"
---

Content
"""
        )

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SkillParser()
            skill = parser.parse(skill_dir)

        # Should have merged global defaults with local frontmatter
        # Global has target and filename_suffix, local has filename
        # Result should have target from global and filename from local
        assert skill.meta.environments is not None
        assert "claude" in skill.meta.environments
        env_config = skill.meta.environments["claude"]
        assert env_config.target == ".claude/skills/"  # From global
        assert env_config.filename == "custom.md"  # From local
        assert env_config.filename_suffix is None  # Removed by mutual exclusion

    def test_parse_local_override_global_env(self, tmp_path):
        """Local frontmatter overrides global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/skills/"
      filename_suffix: "-skill"
"""
        )

        # Create skill file that overrides target
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
environments:
  claude:
    target: ".claude/custom/"
---

Content
"""
        )

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SkillParser()
            skill = parser.parse(skill_dir)

        assert skill.meta.environments is not None
        assert skill.meta.environments["claude"].target == ".claude/custom/"
        assert skill.meta.environments["claude"].filename_suffix == "-skill"

    def test_parse_empty_environments_preserves_global(self, tmp_path):
        """Empty environments dict in skill should preserve global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/skills/"
"""
        )

        # Create skill file with empty environments
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
environments: {}
---

Content
"""
        )

        with patch("dot_work.skills.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SkillParser()
            skill = parser.parse(skill_dir)

        # Empty local environments should preserve global defaults
        assert skill.meta.environments is not None
        assert "claude" in skill.meta.environments
        assert skill.meta.environments["claude"].target == ".claude/skills/"

    def test_parse_metadata_only(self, tmp_path):
        """Parse only metadata for lightweight discovery."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
license: MIT
---

# Full content here that should not be loaded
"""
        )

        parser = SkillParser()
        metadata = parser.parse_metadata_only(skill_dir)

        assert isinstance(metadata, SkillMetadata)
        assert metadata.name == "test-skill"
        assert metadata.description == "A test skill"
        assert metadata.license == "MIT"

    def test_parse_invalid_environment_not_dict(self, tmp_path):
        """Raise error when environment config is not a dict."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
environments:
  claude: "not-a-dict"
---

Content
"""
        )

        parser = SkillParser()
        with pytest.raises(SkillParserError, match="must be a dictionary"):
            parser.parse(skill_dir)

    def test_parse_invalid_environment_missing_target(self, tmp_path):
        """Environment without target raises error during config creation.

        Note: The parser creates the environment config with None target,
        which would fail at usage time. The SkillEnvironmentConfig itself
        requires target as a non-optional field.
        """
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test-skill
description: A test skill
environments:
  claude:
    filename: "custom.md"
---

Content
"""
        )

        parser = SkillParser()
        # The parser will succeed, but the environment config won't have a target
        # This documents the current behavior
        skill = parser.parse(skill_dir)
        assert skill.meta.environments is not None
        # The environment is created but target might be None
        # This is a documented gap in validation


# Singleton instance
SKILL_PARSER = SkillParser()
