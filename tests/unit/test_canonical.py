"""Tests for canonical prompt parsing and validation."""

from __future__ import annotations

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

        assert len(prompt.environments) == 3
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
        assert len(prompt.environments) == 1
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
        """Test parsing content without environments section."""
        content = """---
meta:
  title: "Test"

---

Content here"""
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="must contain 'environments' section"):
            parser.parse_content(content)

    def test_parse_empty_environments(self) -> None:
        """Test parsing content with empty environments."""
        content = """---
meta: {}
environments: {}

---

Content here"""
        parser = CanonicalPromptParser()

        with pytest.raises(ValueError, match="'environments' cannot be empty"):
            parser.parse_content(content)

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
