"""Unit tests for dot_work.subagents.models module.

Tests for SubagentMetadata, SubagentConfig, SubagentEnvironmentConfig,
and CanonicalSubagent dataclasses.
"""

import pytest

from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentEnvironmentConfig,
    SubagentMetadata,
)


class TestSubagentMetadata:
    """Test SubagentMetadata validation and behavior."""

    def test_valid_minimal_metadata(self):
        """Valid metadata with only required fields."""
        metadata = SubagentMetadata(name="test-subagent", description="A test subagent")
        assert metadata.name == "test-subagent"
        assert metadata.description == "A test subagent"

    def test_valid_full_metadata(self):
        """Valid metadata with all fields."""
        metadata = SubagentMetadata(
            name="test-subagent",
            description="A test subagent for unit testing",
        )
        assert metadata.name == "test-subagent"
        assert metadata.description == "A test subagent for unit testing"

    def test_name_validation_lowercase_only(self):
        """Name must contain only lowercase letters, numbers, and hyphens."""
        with pytest.raises(ValueError, match="lowercase letters, numbers, and hyphens"):
            SubagentMetadata(name="TestSubagent", description="Invalid name")

    def test_name_validation_no_leading_hyphen(self):
        """Name cannot start with hyphen."""
        with pytest.raises(ValueError, match="cannot start/end with hyphen"):
            SubagentMetadata(name="-test-subagent", description="Invalid name")

    def test_name_validation_no_trailing_hyphen(self):
        """Name cannot end with hyphen."""
        with pytest.raises(ValueError, match="cannot start/end with hyphen"):
            SubagentMetadata(name="test-subagent-", description="Invalid name")

    def test_name_validation_allows_consecutive_hyphens(self):
        """The regex pattern allows consecutive hyphens (implementation detail).

        Note: The NAME_PATTERN regex '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
        uses '[a-z0-9-]*' which allows consecutive hyphens. This is a
        known behavior of the current implementation.
        """
        # This should NOT raise - consecutive hyphens are currently allowed
        metadata = SubagentMetadata(name="test--subagent", description="Consecutive hyphens")
        assert metadata.name == "test--subagent"

    def test_name_validation_valid_patterns(self):
        """Test valid name patterns."""
        valid_names = [
            "test",
            "test-subagent",
            "my-subagent-123",
            "a",
            "test123",
            "123test",
        ]
        for name in valid_names:
            metadata = SubagentMetadata(name=name, description="Valid name")
            assert metadata.name == name

    def test_name_length_validation_too_short(self):
        """Name must be at least 1 character."""
        with pytest.raises(ValueError, match="must be 1-64 characters"):
            SubagentMetadata(name="", description="Invalid name")

    def test_name_length_validation_too_long(self):
        """Name must be at most 64 characters."""
        with pytest.raises(ValueError, match="must be 1-64 characters"):
            SubagentMetadata(name="a" * 65, description="Invalid name")

    def test_description_must_be_non_empty(self):
        """Description cannot be empty or whitespace only."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SubagentMetadata(name="test-subagent", description="")

        with pytest.raises(ValueError, match="cannot be empty"):
            SubagentMetadata(name="test-subagent", description="   ")

    def test_description_length_validation_too_long(self):
        """Description must be at most 1024 characters."""
        with pytest.raises(ValueError, match="must be 1-1024 characters"):
            SubagentMetadata(name="test-subagent", description="a" * 1025)

    def test_name_must_be_string(self):
        """Name must be a string."""
        with pytest.raises(ValueError, match="must be a string"):
            SubagentMetadata(name=123, description="Invalid name")  # type: ignore

    def test_description_must_be_string(self):
        """Description must be a string."""
        with pytest.raises(ValueError, match="must be a string"):
            SubagentMetadata(name="test-subagent", description=123)  # type: ignore


class TestSubagentEnvironmentConfig:
    """Test SubagentEnvironmentConfig behavior."""

    def test_valid_with_target_only(self):
        """Valid config with only target (required field)."""
        config = SubagentEnvironmentConfig(target=".claude/agents/")
        assert config.target == ".claude/agents/"
        assert config.model is None
        assert config.permission_mode is None
        assert config.tools is None
        assert config.mode is None
        assert config.temperature is None
        assert config.max_steps is None
        assert config.skills is None
        assert config.infer is None

    def test_valid_with_all_fields(self):
        """Valid config with all optional fields."""
        config = SubagentEnvironmentConfig(
            target=".claude/agents/",
            model="sonnet",
            permission_mode="default",
            tools=["Read", "Write"],
            mode="subagent",
            temperature=0.1,
            max_steps=100,
            skills=["code-review"],
            infer=True,
        )
        assert config.target == ".claude/agents/"
        assert config.model == "sonnet"
        assert config.permission_mode == "default"
        assert config.tools == ["Read", "Write"]
        assert config.mode == "subagent"
        assert config.temperature == 0.1
        assert config.max_steps == 100
        assert config.skills == ["code-review"]
        assert config.infer is True


class TestSubagentConfig:
    """Test SubagentConfig behavior."""

    def test_valid_minimal_config(self):
        """Valid config with only required fields."""
        config = SubagentConfig(
            name="test-subagent",
            description="A test subagent",
            prompt="You are a test subagent.",
        )
        assert config.name == "test-subagent"
        assert config.description == "A test subagent"
        assert config.prompt == "You are a test subagent."
        assert config.tools is None
        assert config.model is None
        assert config.permission_mode is None
        assert config.permissions is None

    def test_valid_full_config(self):
        """Valid config with all optional fields."""
        config = SubagentConfig(
            name="test-subagent",
            description="A test subagent",
            prompt="You are a test subagent.",
            tools=["Read", "Write", "Bash"],
            model="sonnet",
            permission_mode="default",
            permissions={"bash": True},
            mode="subagent",
            temperature=0.1,
            max_steps=100,
            skills=["code-review"],
            target="vscode",
            infer=True,
            mcp_servers={"github": {"enabled": True}},
        )
        assert config.name == "test-subagent"
        assert config.tools == ["Read", "Write", "Bash"]
        assert config.model == "sonnet"
        assert config.permission_mode == "default"
        assert config.permissions == {"bash": True}
        assert config.mode == "subagent"
        assert config.temperature == 0.1
        assert config.max_steps == 100
        assert config.skills == ["code-review"]
        assert config.target == "vscode"
        assert config.infer is True
        assert config.mcp_servers == {"github": {"enabled": True}}


class TestCanonicalSubagent:
    """Test CanonicalSubagent validation and behavior."""

    def test_valid_canonical_subagent(self):
        """Valid canonical subagent with required fields."""
        meta = SubagentMetadata(name="test-subagent", description="A test subagent")
        config = SubagentConfig(
            name="test-subagent",
            description="A test subagent",
            prompt="You are a test subagent.",
        )

        subagent = CanonicalSubagent(meta=meta, config=config)

        assert subagent.meta.name == "test-subagent"
        assert subagent.config.name == "test-subagent"
        assert subagent.environments == {}
        assert subagent.source_file is None

    def test_valid_canonical_subagent_with_environments(self):
        """Valid canonical subagent with environment configs."""
        meta = SubagentMetadata(name="test-subagent", description="A test subagent")
        config = SubagentConfig(
            name="test-subagent",
            description="A test subagent",
            prompt="You are a test subagent.",
        )
        environments = {
            "claude": SubagentEnvironmentConfig(
                target=".claude/agents/", model="sonnet"
            ),
            "opencode": SubagentEnvironmentConfig(
                target=".opencode/agent/", mode="subagent"
            ),
        }

        subagent = CanonicalSubagent(
            meta=meta, config=config, environments=environments
        )

        assert subagent.meta.name == "test-subagent"
        assert len(subagent.environments) == 2
        assert "claude" in subagent.environments
        assert "opencode" in subagent.environments

    def test_metadata_name_must_match_config_name(self):
        """Raise ValueError if metadata name doesn't match config name."""
        meta = SubagentMetadata(name="meta-name", description="Test")
        config = SubagentConfig(
            name="config-name",
            description="Test",
            prompt="Test",
        )

        with pytest.raises(ValueError, match="must match config name"):
            CanonicalSubagent(meta=meta, config=config)

    def test_source_file_converted_to_path_object(self):
        """Source file is converted to Path object if string is provided."""
        from pathlib import Path

        meta = SubagentMetadata(name="test-subagent", description="A test subagent")
        config = SubagentConfig(
            name="test-subagent",
            description="A test subagent",
            prompt="You are a test subagent.",
        )

        subagent = CanonicalSubagent(
            meta=meta,
            config=config,
            source_file="/path/to/subagent.md",
        )

        assert isinstance(subagent.source_file, Path)
        assert str(subagent.source_file) == "/path/to/subagent.md"
