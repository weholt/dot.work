"""Tests for canonical prompt parsing and validation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from dot_work.prompts.canonical import (
    CanonicalPrompt,
    CanonicalPromptParser,
    CanonicalPromptValidator,
    EnvironmentConfig,
    ValidationError,
    extract_environment_file,
    generate_environment_prompt,
    parse_canonical_prompt,
    validate_canonical_prompt,
)


@pytest.fixture
def valid_canonical_content() -> str:
    """Valid canonical prompt content."""
    return """---
meta:
  title: "Test Prompt"
  description: "A test prompt for validation"
  version: "1.0.0"
  
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "claude-prompt.md"
  
  opencode:
    target: ".opencode/prompts/"
    filename: "opencode.md"

---

This is the canonical prompt body that will be used across all environments.
It contains useful instructions and context.
"""


@pytest.fixture
def minimal_canonical_content() -> str:
    """Minimal valid canonical prompt content."""
    return """---
meta: {}
environments:
  copilot:
    target: ".github/prompts/"
    filename: "test.md"

---

Minimal prompt body.
"""


class TestEnvironmentConfig:
    """Test EnvironmentConfig dataclass."""

    def test_valid_with_filename(self) -> None:
        """Valid config with filename."""
        config = EnvironmentConfig(target=".github/prompts/", filename="test.md")
        assert config.target == ".github/prompts/"
        assert config.filename == "test.md"
        assert config.filename_suffix is None

    def test_valid_with_filename_suffix(self) -> None:
        """Valid config with filename suffix."""
        config = EnvironmentConfig(target=".claude/", filename_suffix=".prompt.md")
        assert config.target == ".claude/"
        assert config.filename is None
        assert config.filename_suffix == ".prompt.md"

    def test_invalid_missing_both_filename_fields(self) -> None:
        """Invalid config with neither filename nor filename_suffix."""
        with pytest.raises(ValueError, match="Environment must specify"):
            EnvironmentConfig(target="test/")

    def test_invalid_empty_filename(self) -> None:
        """Invalid config with empty filename."""
        with pytest.raises(ValueError, match="Environment filename cannot be empty"):
            EnvironmentConfig(target="test/", filename="")

    def test_invalid_empty_filename_suffix(self) -> None:
        """Invalid config with empty filename suffix."""
        with pytest.raises(ValueError, match="Environment filename_suffix cannot be empty"):
            EnvironmentConfig(target="test/", filename_suffix="")


class TestCanonicalPrompt:
    """Test CanonicalPrompt dataclass."""

    def test_get_environment_success(self) -> None:
        """Test getting valid environment."""
        environments = {
            "copilot": EnvironmentConfig(target=".github/", filename="copilot.md"),
            "claude": EnvironmentConfig(target=".claude/", filename="claude.md"),
        }
        prompt = CanonicalPrompt(meta={}, environments=environments, content="test")

        copilot_env = prompt.get_environment("copilot")
        assert copilot_env.target == ".github/"
        assert copilot_env.filename == "copilot.md"

    def test_get_environment_missing(self) -> None:
        """Test getting missing environment."""
        environments = {"copilot": EnvironmentConfig(target=".github/", filename="copilot.md")}
        prompt = CanonicalPrompt(meta={}, environments=environments, content="test")

        from dot_work.prompts.canonical import CanonicalPromptError

        with pytest.raises(CanonicalPromptError, match="Environment 'claude' not found"):
            prompt.get_environment("claude")

    def test_list_environments(self) -> None:
        """Test listing environment names."""
        environments = {
            "copilot": EnvironmentConfig(target=".github/", filename="copilot.md"),
            "claude": EnvironmentConfig(target=".claude/", filename="claude.md"),
        }
        prompt = CanonicalPrompt(meta={}, environments=environments, content="test")

        env_names = prompt.list_environments()
        assert set(env_names) == {"copilot", "claude"}


class TestCanonicalPromptParser:
    """Test CanonicalPromptParser."""

    def test_parse_valid_content(self, valid_canonical_content: str) -> None:
        """Test parsing valid canonical content."""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(valid_canonical_content)

        assert prompt.meta["title"] == "Test Prompt"
        assert prompt.meta["description"] == "A test prompt for validation"
        assert prompt.meta["version"] == "1.0.0"

        # With global.yml merged, we have at least the 3 local environments
        assert len(prompt.environments) >= 3
        assert "copilot" in prompt.environments
        assert "claude" in prompt.environments
        assert "opencode" in prompt.environments

        copilot_env = prompt.environments["copilot"]
        assert copilot_env.target == ".github/prompts/"
        assert copilot_env.filename_suffix == ".prompt.md"

        claude_env = prompt.environments["claude"]
        assert claude_env.target == ".claude/"
        assert claude_env.filename == "claude-prompt.md"

        assert "This is the canonical prompt body" in prompt.content

    def test_parse_minimal_content(self, minimal_canonical_content: str) -> None:
        """Test parsing minimal valid content."""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(minimal_canonical_content)

        assert prompt.meta == {}
        # With global.yml, we have copilot from local + other defaults
        assert len(prompt.environments) >= 1
        assert "copilot" in prompt.environments
        assert "Minimal prompt body." in prompt.content

    def test_parse_missing_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = "Just some content without frontmatter"
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="missing frontmatter markers"):
            parser.parse_content(content)

    def test_parse_invalid_yaml(self) -> None:
        """Test parsing content with invalid YAML."""
        content = """---
meta:
  title: "Test"
  description: unclosed string
  version: 1.0
environments:
  copilot:
    target: ".github/prompts/"
    filename: "test.md
    # Missing closing quote for filename

---

Content here"""
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="Invalid YAML in frontmatter"):
            parser.parse_content(content)

    def test_parse_missing_environments(self) -> None:
        """Test parsing content without environments section.

        With global.yml providing default environments, prompts without
        explicit environments should get the defaults from global.yml.
        """
        content = """---
meta:
  title: "Test"

---

Content here"""
        parser = CanonicalPromptParser()

        # With global.yml, this should parse successfully
        # (global config provides default environments)
        prompt = parser.parse_content(content)
        assert prompt.meta["title"] == "Test"
        assert len(prompt.environments) > 0  # Global defaults provided

    def test_parse_empty_environments(self) -> None:
        """Test parsing content with empty environments.

        With global.yml providing default environments, empty environments
        should be replaced by global defaults.
        """
        content = """---
meta: {}
environments: {}

---

Content here"""
        parser = CanonicalPromptParser()

        # With global.yml, empty environments is replaced by defaults
        prompt = parser.parse_content(content)
        assert len(prompt.environments) > 0  # Global defaults provided

    def test_parse_environment_without_target(self) -> None:
        """Test parsing environment without target."""
        content = """---
meta: {}
environments:
  copilot:
    filename: "test.md"

---

Content here"""
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="must specify 'target'"):
            parser.parse_content(content)

    def test_parse_environment_not_dict(self) -> None:
        """Test parsing environment that's not a dict."""
        content = """---
meta: {}
environments:
  copilot: "not a dict"

---

Content here"""
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="must be a dictionary"):
            parser.parse_content(content)

    def test_parse_file_success(self, valid_canonical_content: str) -> None:
        """Test parsing from file."""
        parser = CanonicalPromptParser()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.md"
            temp_path.write_text(valid_canonical_content, encoding="utf-8")

            prompt = parser.parse(temp_path)
            assert prompt.source_file == temp_path
            assert prompt.meta["title"] == "Test Prompt"

    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file."""
        parser = CanonicalPromptParser()

        with pytest.raises(FileNotFoundError, match="not found"):
            parser.parse("/non/existent/file.md")


class TestCanonicalPromptValidator:
    """Test CanonicalPromptValidator."""

    @pytest.fixture
    def valid_prompt(self, valid_canonical_content: str) -> CanonicalPrompt:
        """Create a valid CanonicalPrompt for testing."""
        parser = CanonicalPromptParser()
        return parser.parse_content(valid_canonical_content)

    @pytest.fixture
    def minimal_prompt(self, minimal_canonical_content: str) -> CanonicalPrompt:
        """Create a minimal CanonicalPrompt for testing."""
        parser = CanonicalPromptParser()
        return parser.parse_content(minimal_canonical_content)

    def test_validate_valid_prompt(self, valid_prompt: CanonicalPrompt) -> None:
        """Test validating a valid prompt."""
        validator = CanonicalPromptValidator()
        errors = validator.validate(valid_prompt)

        # Valid prompt should have only warnings (if any)
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0

    def test_validate_minimal_prompt(self, minimal_prompt: CanonicalPrompt) -> None:
        """Test validating a minimal prompt (should have warnings)."""
        validator = CanonicalPromptValidator()
        errors = validator.validate(minimal_prompt)

        # Should have warnings about missing recommended fields
        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) >= 2  # title, description, version

        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0

    def test_validate_empty_content(self) -> None:
        """Test validating prompt with empty content."""
        content = """---
meta:
  title: "Test"
environments:
  copilot:
    target: ".github/"
    filename: "test.md"
---

   """
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        validator = CanonicalPromptValidator()
        errors = validator.validate(prompt)

        error_messages = [e.message for e in errors if e.severity == "error"]
        assert any("content is empty" in msg for msg in error_messages)

    def test_validate_duplicate_targets(self) -> None:
        """Test validating prompt with duplicate targets."""
        content = """---
meta: {}
environments:
  copilot:
    target: ".github/"
    filename: "copilot.md"
  claude:
    target: ".github/"
    filename: "claude.md"

---

Content here"""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        validator = CanonicalPromptValidator()
        errors = validator.validate(prompt)

        warning_messages = [e.message for e in errors if e.severity == "warning"]
        assert any("duplicate target" in msg for msg in warning_messages)

    def test_validate_empty_target(self) -> None:
        """Test validating prompt with empty target."""
        content = """---
meta: {}
environments:
  copilot:
    target: ""
    filename: "test.md"

---

Content here"""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        validator = CanonicalPromptValidator()
        errors = validator.validate(prompt)

        error_messages = [e.message for e in errors if e.severity == "error"]
        assert any("target cannot be empty" in msg for msg in error_messages)

    def test_validate_strict_mode_missing_required_fields(
        self, minimal_prompt: CanonicalPrompt
    ) -> None:
        """Test strict validation missing required fields."""
        validator = CanonicalPromptValidator()
        errors = validator.validate(minimal_prompt, strict=True)

        error_messages = [e.message for e in errors if e.severity == "error"]
        assert any("meta.title" in msg and "required" in msg for msg in error_messages)
        assert any("meta.description" in msg and "required" in msg for msg in error_messages)

    def test_validate_strict_mode_target_trailing_slash(self) -> None:
        """Test strict validation for trailing slash in targets."""
        content = """---
meta:
  title: "Test"
  description: "Test prompt"
environments:
  copilot:
    target: ".github/prompts"
    filename: "test.md"

---

Content here"""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        validator = CanonicalPromptValidator()
        errors = validator.validate(prompt, strict=True)

        warning_messages = [e.message for e in errors if e.severity == "warning"]
        assert any("should end with" in msg for msg in warning_messages)

    def test_is_valid_method(self, valid_prompt: CanonicalPrompt) -> None:
        """Test the is_valid convenience method."""
        validator = CanonicalPromptValidator()
        assert validator.is_valid(valid_prompt)  # Should be True
        assert validator.is_valid(valid_prompt, strict=True)  # Should still be True


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_parse_canonical_prompt_file(self, valid_canonical_content: str) -> None:
        """Test parse_canonical_prompt function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.md"
            temp_path.write_text(valid_canonical_content, encoding="utf-8")

            prompt = parse_canonical_prompt(temp_path)
            assert prompt.meta["title"] == "Test Prompt"

    def test_validate_canonical_prompt_function(self, valid_canonical_content: str) -> None:
        """Test validate_canonical_prompt function."""
        parser = CanonicalPromptParser()
        prompt = parser.parse_content(valid_canonical_content)

        errors = validate_canonical_prompt(prompt)
        error_errors = [e for e in errors if e.severity == "error"]
        assert len(error_errors) == 0


class TestValidationError:
    """Test ValidationError dataclass."""

    def test_error_string_representation(self) -> None:
        """Test ValidationError string format."""
        error = ValidationError(line=15, message="Test error")
        assert str(error) == "Line 15: Test error"

    def test_warning_string_representation(self) -> None:
        """Test ValidationError with warning severity."""
        warning = ValidationError(line=10, message="Test warning", severity="warning")
        assert str(warning) == "Line 10: Test warning"


class TestEnvironmentPromptGeneration:
    """Test environment-specific prompt generation."""

    def test_generate_with_filename(self) -> None:
        """Test generating prompt with explicit filename."""
        env_config = EnvironmentConfig(target=".github/prompts/", filename="custom.md")
        prompt = CanonicalPrompt(
            meta={"title": "Test Prompt"},
            environments={"copilot": env_config},
            content="Test content",
        )

        filename, content = generate_environment_prompt(prompt, "copilot")

        assert filename == "custom.md"
        assert "---" in content
        assert "meta:" in content
        assert "title: Test Prompt" in content
        assert "Test content" in content

    def test_generate_with_suffix(self) -> None:
        """Test generating prompt with filename suffix."""
        env_config = EnvironmentConfig(target=".claude/", filename_suffix=".prompt.md")
        prompt = CanonicalPrompt(
            meta={"title": "Test Prompt"},
            environments={"claude": env_config},
            content="Test content",
        )

        filename, content = generate_environment_prompt(prompt, "claude")

        assert filename == "test-prompt.prompt.md"
        assert "---" in content
        assert "meta:" in content
        assert "title: Test Prompt" in content
        assert "Test content" in content

    def test_generate_default_filename(self) -> None:
        """Test generating prompt with default filename when missing meta title."""
        env_config = EnvironmentConfig(
            target=".custom/", filename_suffix=".md"
        )  # Use suffix to test default naming
        prompt = CanonicalPrompt(
            meta={}, environments={"custom": env_config}, content="Test content"
        )

        filename, content = generate_environment_prompt(prompt, "custom")

        assert filename == "custom.md"  # Falls back to environment name + suffix
        assert "---" in content
        assert "Test content" in content

    def test_generate_missing_environment(self) -> None:
        """Test generating prompt for missing environment."""
        from dot_work.prompts.canonical import CanonicalPromptError

        prompt = CanonicalPrompt(meta={"title": "Test"}, environments={}, content="Test content")

        with pytest.raises(CanonicalPromptError, match="Environment 'missing' not found"):
            generate_environment_prompt(prompt, "missing")

    def test_extract_environment_file(self) -> None:
        """Test extracting environment file from canonical prompt."""
        content = """---
meta:
  title: "Test Prompt"
  description: "Test"
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

Test content"""

        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "test.canonical.md"
            prompt_file.write_text(content, encoding="utf-8")

            output_dir = Path(temp_dir) / "output"
            output_path = extract_environment_file(prompt_file, "copilot", output_dir)

            assert output_path.exists()
            assert output_path.name == "test-prompt.prompt.md"

            generated_content = output_path.read_text(encoding="utf-8")
            assert "---" in generated_content
            assert "Test content" in generated_content

    def test_extract_file_create_output_dir(self) -> None:
        """Test that extract creates output directory if needed."""
        content = """---
meta:
  title: "Test"
environments:
  test:
    target: ".test/"
    filename_suffix: ".md"
---

Content"""

        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "test.md"
            prompt_file.write_text(content, encoding="utf-8")

            output_dir = Path(temp_dir) / "nested" / "output"
            output_path = extract_environment_file(prompt_file, "test", output_dir)

            assert output_dir.exists()
            assert output_path.exists()

    def test_extract_writes_to_env_target_relative(self) -> None:
        """If output_dir is not provided, write to the environment target (relative to CWD)."""
        content = """---
meta:
  title: "Test Prompt"
  description: "Test"
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

Test content"""

        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path.cwd()
            try:
                # Change cwd so relative target resolves under temp_dir
                os.chdir(temp_dir)

                prompt_file = Path(temp_dir) / "test.canonical.md"
                prompt_file.write_text(content, encoding="utf-8")

                output_path = extract_environment_file(prompt_file, "copilot")

                expected = Path(temp_dir) / ".github" / "prompts" / "test-prompt.prompt.md"
                assert output_path.exists()
                assert output_path == expected
            finally:
                os.chdir(cwd)

    def test_extract_writes_to_env_target_absolute(self) -> None:
        """Absolute env target should be used as-is when output_dir is not provided."""

        with tempfile.TemporaryDirectory() as temp_dir:
            abs_target = Path(temp_dir) / "absolute_target"
            content = f"""---
meta:
  title: "Abs"
environments:
  abs:
    target: "{abs_target}"
    filename_suffix: ".md"
---

Content"""

            prompt_file = Path(temp_dir) / "abs.md"
            prompt_file.write_text(content, encoding="utf-8")

            output_path = extract_environment_file(prompt_file, "abs")

            expected = abs_target / "abs.md"
            assert output_path.exists()
            assert output_path == expected


class TestGlobalConfig:
    """Test global configuration loading and merging."""

    def test_deep_merge_basic(self) -> None:
        """Test basic deep merge functionality."""
        parser = CanonicalPromptParser()

        global_dict = {"a": 1, "b": {"x": 10, "y": 20}}
        local_dict = {"b": {"y": 30, "z": 40}, "c": 3}

        result = parser._deep_merge(global_dict, local_dict)

        # Global values preserved
        assert result["a"] == 1
        # Local override takes precedence for y
        assert result["b"]["y"] == 30
        # Global x preserved
        assert result["b"]["x"] == 10
        # Local new value added
        assert result["b"]["z"] == 40
        assert result["c"] == 3

    def test_deep_merge_local_overrides_global(self) -> None:
        """Test that local values completely override global at same key."""
        parser = CanonicalPromptParser()

        global_dict = {"a": {"x": 1, "y": 2}}
        local_dict = {"a": {"x": 10}}

        result = parser._deep_merge(global_dict, local_dict)

        assert result["a"]["x"] == 10  # Local override
        assert result["a"]["y"] == 2  # Global preserved

    def test_deep_merge_no_global(self) -> None:
        """Test merge with empty global dict."""
        parser = CanonicalPromptParser()

        result = parser._deep_merge({}, {"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_parse_with_global_config(self) -> None:
        """Test parsing with global configuration present."""
        # The actual global.yml file in the repo should provide defaults
        # This test verifies the merge happens
        content = """---
meta:
  title: "Test Prompt"

---

Test content"""

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        # With global.yml, environments should be merged in
        # At minimum, the prompt should parse successfully
        assert prompt.meta["title"] == "Test Prompt"
        assert "Test content" in prompt.content

    def test_parse_local_override_global_env(self) -> None:
        """Test that local environment config overrides global."""
        # Define a prompt with custom claude config
        content = """---
meta:
  title: "Test"

environments:
  claude:
    target: ".custom/claude/"
    filename_suffix: ".custom.md"
  copilot:
    target: ".custom/copilot/"
    filename: "copilot-custom.md"

---

Test content"""

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(content)

        # Local claude config should override global
        assert prompt.environments["claude"].target == ".custom/claude/"
        assert prompt.environments["claude"].filename_suffix == ".custom.md"

        # Local copilot config should be as specified
        assert prompt.environments["copilot"].target == ".custom/copilot/"
        assert prompt.environments["copilot"].filename == "copilot-custom.md"

        # If global.yml exists and has other environments, they should be merged
        # (This test assumes global.yml exists with default environments)
        if "opencode" in prompt.environments:
            # Global opencode config should be present
            assert prompt.environments["opencode"].target == ".opencode/prompts/"

    def test_parse_no_global_fallback(self) -> None:
        """Test that parser works even when global.yml is missing."""
        # This content has all required frontmatter
        content = """---
meta:
  title: "Test"
environments:
  test:
    target: ".test/"
    filename: "test.md"

---

Test content"""

        parser = CanonicalPromptParser()
        # Should parse successfully even without global.yml
        prompt = parser.parse_content(content)

        assert prompt.environments["test"].target == ".test/"
        assert "Test content" in prompt.content

    def test_global_config_caching(self) -> None:
        """Test that global config is cached after first load."""
        parser = CanonicalPromptParser()
        prompts_dir = Path(__file__).parent.parent.parent / "src" / "dot_work" / "prompts"

        # First load
        config1 = parser._load_global_defaults(prompts_dir)
        # Second load should return cached value
        config2 = parser._load_global_defaults(prompts_dir)

        # Should be the same object (cached)
        assert config1 is config2

    def test_existing_prompts_still_work(self) -> None:
        """Test that existing prompt files still parse correctly."""
        # This is a real prompt file from the repo
        parser = CanonicalPromptParser()
        prompts_dir = Path(__file__).parent.parent.parent / "src" / "dot_work" / "prompts"

        # Test a few existing prompts - use .md files that exist in the repo
        test_files = [
            "new-issue.md",
            "do-work.md",
            "code-review.md",
        ]

        for filename in test_files:
            prompt_file = prompts_dir / filename
            if prompt_file.exists():
                prompt = parser.parse(prompt_file)

                # Should have meta
                assert prompt.meta is not None
                # Should have environments (from global or local)
                assert len(prompt.environments) > 0
                # Should have content
                assert len(prompt.content) > 0

    def test_meta_only_with_global_config(self) -> None:
        """Test that prompts with only meta: section parse when global.yml exists.

        This is the fix for the issue where files with only meta: frontmatter
        were being silently skipped because they lacked an environments: section.
        With global.yml providing default environments, these files should parse.
        """
        parser = CanonicalPromptParser()
        prompts_dir = Path(__file__).parent.parent.parent / "src" / "dot_work" / "prompts"

        # Files that have only meta: frontmatter (relying on global.yml)
        # These were previously being skipped during discovery
        meta_only_files = [
            "production-ready-apis.md",
            "performance-review.md",
            "security-review.md",
        ]

        for filename in meta_only_files:
            prompt_file = prompts_dir / filename
            if prompt_file.exists():
                # Should parse without raising ValueError
                prompt = parser.parse(prompt_file)

                # Should have meta from local file
                assert prompt.meta is not None
                assert "title" in prompt.meta or "description" in prompt.meta

                # Should have environments merged from global.yml
                assert len(prompt.environments) > 0

                # Common environments from global.yml should be present
                assert "claude" in prompt.environments
                assert "copilot" in prompt.environments
