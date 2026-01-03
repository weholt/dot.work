"""Unit tests for dot_work.subagents.parser module.

Tests for _deep_merge, _load_global_defaults, and SubagentParser class.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentEnvironmentConfig,
    SubagentMetadata,
)
from dot_work.subagents.parser import (
    GLOBAL_DEFAULTS_PATH,
    SubagentParser,
    SubagentParserError,
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
                "claude": {"target": ".claude/agents/", "filename_suffix": "-agent"},
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
                "claude": {"target": ".claude/agents/", "filename": "custom.md"}
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
                "claude": {"target": ".claude/", "filename_suffix": "-agent"}
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
      target: ".claude/agents/"
      filename_suffix: "-agent"
"""
        )

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            result = _load_global_defaults()

        expected = {
            "environments": {
                "claude": {"target": ".claude/agents/", "filename_suffix": "-agent"}
            }
        }
        assert result == expected

    def test_load_global_defaults_file_missing(self, tmp_path):
        """Return empty dict when global.yml missing."""
        missing_path = tmp_path / "nonexistent" / "global.yml"

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", missing_path):
            result = _load_global_defaults()

        assert result == {}

    def test_load_global_defaults_malformed_yaml(self, tmp_path):
        """Malformed YAML raises yaml.scanner.ScannerError.

        Note: The current implementation propagates the YAML parsing error
        rather than catching it. This is the actual behavior.
        """
        global_yml = tmp_path / "global.yml"
        global_yml.write_text("invalid: yaml: content: [")

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            # Should raise yaml.scanner.ScannerError
            with pytest.raises(Exception):  # ScannerError is a subclass of Exception
                _load_global_defaults()

    def test_load_global_defaults_no_defaults_key(self, tmp_path):
        """Return empty dict when file exists but has no 'defaults' key."""
        global_yml = tmp_path / "global.yml"
        global_yml.write_text("other_key: value\n")

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
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

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            result = _load_global_defaults()

        # Current implementation returns the value as-is, not empty dict
        assert result == "not-a-dict"


class TestSubagentParser:
    """Test SubagentParser class methods."""

    def test_parse_valid_canonical_subagent(self, tmp_path):
        """Parse a valid canonical subagent file."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
  description: A test subagent for unit testing

environments:
  claude:
    target: ".claude/agents/"
    model: sonnet

tools:
  - Read
  - Grep
---

You are a test subagent.
"""
        )

        parser = SubagentParser()
        subagent = parser.parse(subagent_file)

        assert isinstance(subagent, CanonicalSubagent)
        assert subagent.meta.name == "test-subagent"
        assert subagent.meta.description == "A test subagent for unit testing"
        assert subagent.config.name == "test-subagent"
        assert "You are a test subagent." in subagent.config.prompt
        assert "claude" in subagent.environments

    def test_parse_file_not_found(self, tmp_path):
        """Raise FileNotFoundError when subagent file not found."""
        missing_file = tmp_path / "nonexistent.md"

        parser = SubagentParser()
        with pytest.raises(FileNotFoundError, match="Subagent file not found"):
            parser.parse(missing_file)

    def test_parse_invalid_frontmatter_format(self, tmp_path):
        """Raise ValueError when frontmatter markers are missing."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text("No frontmatter markers here")

        parser = SubagentParser()
        with pytest.raises(ValueError, match="missing frontmatter markers"):
            parser.parse(subagent_file)

    def test_parse_invalid_yaml(self, tmp_path):
        """Raise SubagentParserError when YAML is invalid."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
invalid_yaml: [
---

Content
"""
        )

        parser = SubagentParser()
        with pytest.raises(SubagentParserError, match="Invalid YAML"):
            parser.parse(subagent_file)

    def test_parse_missing_meta_section(self, tmp_path):
        """Raise SubagentParserError when 'meta' section is missing."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
name: test-subagent
description: A test subagent
---

Content
"""
        )

        parser = SubagentParser()
        with pytest.raises(SubagentParserError, match="Missing or invalid 'meta' section"):
            parser.parse(subagent_file)

    def test_parse_missing_meta_name(self, tmp_path):
        """Raise SubagentParserError when 'meta.name' field is missing."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  description: A test subagent
---

Content
"""
        )

        parser = SubagentParser()
        with pytest.raises(SubagentParserError, match="Missing required field 'meta.name'"):
            parser.parse(subagent_file)

    def test_parse_missing_meta_description(self, tmp_path):
        """Raise SubagentParserError when 'meta.description' field is missing."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
---

Content
"""
        )

        parser = SubagentParser()
        with pytest.raises(
            SubagentParserError, match="Missing required field 'meta.description'"
        ):
            parser.parse(subagent_file)

    def test_parse_with_global_defaults(self, tmp_path):
        """Subagent parsing should merge global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/agents/"
      model: sonnet
"""
        )

        # Create subagent file
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
  description: A test subagent

environments:
  claude:
    permission_mode: bypassPermissions
---

Content
"""
        )

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SubagentParser()
            subagent = parser.parse(subagent_file)

        # Should have merged global defaults with local frontmatter
        assert "claude" in subagent.environments
        env_config = subagent.environments["claude"]
        assert env_config.target == ".claude/agents/"  # From global
        assert env_config.model == "sonnet"  # From global
        assert env_config.permission_mode == "bypassPermissions"  # From local

    def test_parse_local_override_global_env(self, tmp_path):
        """Local frontmatter overrides global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/agents/"
      model: haiku
"""
        )

        # Create subagent file that overrides model
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
  description: A test subagent

environments:
  claude:
    model: sonnet
---

Content
"""
        )

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SubagentParser()
            subagent = parser.parse(subagent_file)

        assert subagent.environments["claude"].target == ".claude/agents/"
        assert subagent.environments["claude"].model == "sonnet"

    def test_parse_empty_environments_preserves_global(self, tmp_path):
        """Empty environments dict in subagent should preserve global defaults."""
        # Create global.yml
        global_yml = tmp_path / "global.yml"
        global_yml.write_text(
            """
defaults:
  environments:
    claude:
      target: ".claude/agents/"
"""
        )

        # Create subagent file with empty environments
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
  description: A test subagent
environments: {}
---

Content
"""
        )

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", global_yml):
            parser = SubagentParser()
            subagent = parser.parse(subagent_file)

        # Empty local environments should preserve global defaults
        assert "claude" in subagent.environments
        assert subagent.environments["claude"].target == ".claude/agents/"

    def test_parse_native_subagent(self, tmp_path):
        """Parse a native environment-specific subagent file."""
        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
name: test-subagent
description: A test subagent
model: sonnet
permissionMode: default
tools:
  - Read
  - Write
---

You are a test subagent.
"""
        )

        parser = SubagentParser()
        config = parser.parse_native(subagent_file, environment="claude")

        assert isinstance(config, SubagentConfig)
        assert config.name == "test-subagent"
        assert config.description == "A test subagent"
        assert config.model == "sonnet"
        assert config.permission_mode == "default"
        assert config.tools == ["Read", "Write"]
        assert "You are a test subagent." in config.prompt

    def test_extract_environments_skips_missing_target(self, tmp_path):
        """Environment configs without target field are skipped.

        The _extract_environments method filters out environments that
        don't have a target field. This is by design in the subagent parser.
        """
        # Create empty global.yml (no defaults)
        empty_global = tmp_path / "global.yml"
        empty_global.write_text("")

        subagent_file = tmp_path / "test-subagent.md"
        subagent_file.write_text(
            """---
meta:
  name: test-subagent
  description: A test subagent

environments:
  claude:
    model: sonnet
    target: ".claude/agents/"
  opencode:
    mode: subagent
    # Missing target field - should be skipped
  copilot:
    target: ".github/copilot-instructions.md"
---

Content
"""
        )

        with patch("dot_work.subagents.parser.GLOBAL_DEFAULTS_PATH", empty_global):
            parser = SubagentParser()
            subagent = parser.parse(subagent_file)

        # Only environments with target are included
        assert "claude" in subagent.environments
        assert "copilot" in subagent.environments
        # opencode is skipped because it has no target
        assert "opencode" not in subagent.environments


# Singleton instance
SUBAGENT_PARSER = SubagentParser()
