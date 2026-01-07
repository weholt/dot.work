"""Unit tests for dot_work.subagents.generator module.

Tests for SubagentGenerator class including generate_native,
generate_native_file, generate_all, _merge_config, and
generate_canonical_template methods.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.subagents.generator import SUBAGENT_GENERATOR, SubagentGenerator
from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentEnvironmentConfig,
    SubagentMetadata,
)


class TestSubagentGeneratorInit:
    """Test SubagentGenerator initialization."""

    def test_init_creates_instance(self):
        """Test that __init__ creates a SubagentGenerator instance."""
        generator = SubagentGenerator()
        assert isinstance(generator, SubagentGenerator)

    def test_singleton_instance(self):
        """Test that SUBAGENT_GENERATOR is a singleton instance."""
        assert isinstance(SUBAGENT_GENERATOR, SubagentGenerator)
        # Verify it's the same instance type
        generator = SubagentGenerator()
        assert type(generator) == type(SUBAGENT_GENERATOR)


class TestGenerateNative:
    """Test generate_native method."""

    def test_generate_native_basic(self):
        """Test generating native content for an environment."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        result = SUBAGENT_GENERATOR.generate_native(subagent, "claude")

        assert isinstance(result, str)
        assert "test-agent" in result or "Test agent" in result

    def test_generate_native_with_project_root(self):
        """Test generating native with project_root specified."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        result = SUBAGENT_GENERATOR.generate_native(
            subagent, "claude", project_root=Path("/tmp/project")
        )

        assert isinstance(result, str)

    def test_generate_native_invalid_environment(self):
        """Test that invalid environment raises ValueError."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        with pytest.raises(ValueError):
            SUBAGENT_GENERATOR.generate_native(subagent, "invalid-env")

    def test_generate_native_with_environment_overrides(self):
        """Test generating native with environment-specific config overrides."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="Base description",
                prompt="Base prompt",
                model="base-model",
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                    model="claude-model",
                ),
            },
        )

        result = SUBAGENT_GENERATOR.generate_native(subagent, "claude")

        assert isinstance(result, str)
        # The environment override should be applied


class TestGenerateNativeFile:
    """Test generate_native_file method."""

    def test_generate_native_file_creates_file(self, tmp_path: Path):
        """Test that generate_native_file creates the output file."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        output_path = SUBAGENT_GENERATOR.generate_native_file(
            subagent, "claude", tmp_path
        )

        assert output_path.exists()
        assert output_path.is_file()

    def test_generate_native_file_returns_path(self, tmp_path: Path):
        """Test that generate_native_file returns the file path."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        output_path = SUBAGENT_GENERATOR.generate_native_file(
            subagent, "claude", tmp_path
        )

        assert isinstance(output_path, Path)
        assert str(output_path).endswith("test-agent.md")

    def test_generate_native_file_with_custom_output_path(self, tmp_path: Path):
        """Test generating with custom output path."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        custom_path = tmp_path / "custom" / "output.md"
        output_path = SUBAGENT_GENERATOR.generate_native_file(
            subagent, "claude", tmp_path, output_path=custom_path
        )

        assert output_path == custom_path
        assert custom_path.exists()

    def test_generate_native_file_creates_parent_dirs(self, tmp_path: Path):
        """Test that parent directories are created."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        deep_path = tmp_path / "deep" / "nested" / "path" / "output.md"
        output_path = SUBAGENT_GENERATOR.generate_native_file(
            subagent, "claude", tmp_path, output_path=deep_path
        )

        assert output_path.exists()
        assert deep_path.parent.exists()

    def test_generate_native_file_invalid_environment(self, tmp_path: Path):
        """Test that invalid environment raises ValueError."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        with pytest.raises(ValueError):
            SUBAGENT_GENERATOR.generate_native_file(
                subagent, "invalid-env", tmp_path
            )


class TestGenerateAll:
    """Test generate_all method."""

    def test_generate_all_single_environment(self, tmp_path: Path):
        """Test generating for single configured environment."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                ),
            },
        )

        result = SUBAGENT_GENERATOR.generate_all(subagent, tmp_path)

        assert isinstance(result, dict)
        assert "claude" in result
        assert isinstance(result["claude"], Path)
        assert result["claude"].exists()

    def test_generate_all_multiple_environments(self, tmp_path: Path):
        """Test generating for multiple configured environments."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                ),
                "copilot": SubagentEnvironmentConfig(
                    target=".github/agents/",
                ),
            },
        )

        result = SUBAGENT_GENERATOR.generate_all(subagent, tmp_path)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "claude" in result
        assert "copilot" in result
        assert all(isinstance(p, Path) for p in result.values())

    def test_generate_all_empty_environments(self, tmp_path: Path):
        """Test generating with no configured environments."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={},
        )

        result = SUBAGENT_GENERATOR.generate_all(subagent, tmp_path)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_generate_all_handles_failure_gracefully(self, tmp_path: Path):
        """Test that failures in one environment don't stop others."""
        # Create a subagent with one valid and one invalid environment
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="A test agent",
                prompt="You are a test agent.",
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                ),
                # Invalid environment - will be skipped
                "invalid-env": SubagentEnvironmentConfig(
                    target="/invalid/",
                ),
            },
        )

        # Patch get_adapter to fail for invalid-env
        def mock_get_adapter(env: str):
            if env == "invalid-env":
                raise ValueError(f"Unknown environment: {env}")
            from dot_work.subagents.environments import get_adapter
            return get_adapter(env)

        with patch("dot_work.subagents.generator.get_adapter", side_effect=mock_get_adapter):
            result = SUBAGENT_GENERATOR.generate_all(subagent, tmp_path)

        # Should have only the valid environment
        assert "claude" in result
        assert "invalid-env" not in result


class TestMergeConfig:
    """Test _merge_config private method."""

    def test_merge_config_no_environment_override(self):
        """Test merging when environment has no overrides."""
        base_config = SubagentConfig(
            name="test-agent",
            description="Base description",
            prompt="Base prompt",
            model="base-model",
        )

        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=base_config,
            environments={},
        )

        result = SUBAGENT_GENERATOR._merge_config(subagent, "claude")

        assert result.name == "test-agent"
        assert result.description == "Base description"
        assert result.model == "base-model"

    def test_merge_config_with_environment_overrides(self):
        """Test merging with environment-specific overrides."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="Base description",
                prompt="Base prompt",
                model="base-model",
                tools=["base-tool"],
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                    model="claude-model",
                    tools=["claude-tool"],
                ),
            },
        )

        result = SUBAGENT_GENERATOR._merge_config(subagent, "claude")

        # Base fields preserved
        assert result.name == "test-agent"
        assert result.description == "Base description"

        # Environment overrides applied
        assert result.model == "claude-model"
        assert result.tools == ["claude-tool"]

    def test_merge_config_partial_override(self):
        """Test merging when environment only overrides some fields."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="Base description",
                prompt="Base prompt",
                model="base-model",
                temperature=0.7,
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                    model="claude-model",
                    # temperature not overridden
                ),
            },
        )

        result = SUBAGENT_GENERATOR._merge_config(subagent, "claude")

        assert result.model == "claude-model"
        assert result.temperature == 0.7  # Base value preserved

    def test_merge_config_all_override_fields(self):
        """Test merging with all possible override fields."""
        subagent = CanonicalSubagent(
            meta=SubagentMetadata(
                name="test-agent",
                description="A test agent",
            ),
            config=SubagentConfig(
                name="test-agent",
                description="Base description",
                prompt="Base prompt",
                model="base-model",
                tools=["base-tool"],
                permission_mode="base-mode",
                mode="base-mode-value",
                temperature=0.7,
                max_steps=10,
                skills=["base-skill"],
                infer=False,
            ),
            environments={
                "claude": SubagentEnvironmentConfig(
                    target=".claude/agents/",
                    model="claude-model",
                    tools=["claude-tool"],
                    permission_mode="claude-mode",
                    mode="claude-mode-value",
                    temperature=0.5,
                    max_steps=20,
                    skills=["claude-skill"],
                    infer=True,
                ),
            },
        )

        result = SUBAGENT_GENERATOR._merge_config(subagent, "claude")

        # All overrides should be applied
        assert result.model == "claude-model"
        assert result.tools == ["claude-tool"]
        assert result.permission_mode == "claude-mode"
        assert result.mode == "claude-mode-value"
        assert result.temperature == 0.5
        assert result.max_steps == 20
        assert result.skills == ["claude-skill"]
        assert result.infer is True


class TestGenerateCanonicalTemplate:
    """Test generate_canonical_template method."""

    def test_generate_template_basic(self):
        """Test generating a basic canonical template."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent"
        )

        assert isinstance(result, str)
        assert "name: test-agent" in result
        assert "description: A test agent" in result
        assert "---" in result

    def test_generate_template_with_custom_environments(self):
        """Test generating template with specific environments."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent", environments=["claude"]
        )

        assert isinstance(result, str)
        assert "claude:" in result
        assert "copilot:" not in result
        assert "opencode:" not in result

    def test_generate_template_default_environments(self):
        """Test generating template with default environments."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent"
        )

        # Should include all default environments
        assert "claude:" in result
        assert "opencode:" in result
        assert "copilot:" in result

    def test_generate_template_structure(self):
        """Test that template has proper structure."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent"
        )

        lines = result.split("\n")

        # Should start with meta section
        assert lines[0] == "---"
        assert "meta:" in lines

        # Should have environments section
        assert "environments:" in result

        # Should have common config
        assert "tools:" in result

        # Should end with instructions section
        assert "## Instructions" in result

    def test_generate_template_claude_environment(self):
        """Test Claude environment in template."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent", environments=["claude"]
        )

        assert 'target: ".claude/agents/"' in result
        assert "model: sonnet" in result
        assert "permissionMode: default" in result

    def test_generate_template_opencode_environment(self):
        """Test OpenCode environment in template."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent", environments=["opencode"]
        )

        assert 'target: ".opencode/agent/"' in result
        assert "mode: subagent" in result
        assert "temperature: 0.1" in result

    def test_generate_template_copilot_environment(self):
        """Test Copilot environment in template."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent", environments=["copilot"]
        )

        assert 'target: ".github/agents/"' in result
        assert "infer: true" in result
        assert "tools:" in result

    def test_generate_template_empty_environments(self):
        """Test generating template with empty environments list."""
        result = SUBAGENT_GENERATOR.generate_canonical_template(
            "test-agent", "A test agent", environments=[]
        )

        assert isinstance(result, str)
        # Should not have specific environment configs
        assert "claude:" not in result
        assert "copilot:" not in result
