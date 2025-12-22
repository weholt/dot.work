"""Tests for canonical prompt installer integration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from rich.console import Console

from dot_work.installer import (
    install_canonical_prompt,
    install_canonical_prompt_directory,
    validate_canonical_prompt_file,
)


class TestCanonicalPromptValidation:
    """Test canonical prompt validation in installer."""

    def test_validate_valid_canonical_file(self) -> None:
        """Test validating a valid canonical prompt file."""
        content = """---
meta:
  title: "Test Prompt"
  description: "A test prompt"
  version: "1.0.0"
  
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "claude-prompt.md"

---

Test prompt body content.
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "test.canon.md"
            prompt_file.write_text(content, encoding="utf-8")

            # Should not raise any exception
            validate_canonical_prompt_file(prompt_file)

    def test_validate_nonexistent_file(self) -> None:
        """Test validating a non-existent file."""
        prompt_file = Path("/non/existent/file.canon.md")

        with pytest.raises(FileNotFoundError, match="Canonical prompt file not found"):
            validate_canonical_prompt_file(prompt_file)

    def test_validate_invalid_canonical_file(self) -> None:
        """Test validating an invalid canonical prompt file."""
        content = """---
meta:
  title: "Test"
environments: {}

---

Content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "invalid.canon.md"
            prompt_file.write_text(content, encoding="utf-8")

            with pytest.raises(ValueError, match="Canonical prompt validation failed"):
                validate_canonical_prompt_file(prompt_file)

    def test_validate_strict_mode_with_warnings(self) -> None:
        """Test strict validation with warnings should fail."""
        content = """---
meta: {}
environments:
  copilot:
    target: ".github/prompts/"
    filename: "test.md"

---

Content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "minimal.canon.md"
            prompt_file.write_text(content, encoding="utf-8")

            with pytest.raises(ValueError, match="Canonical prompt strict validation failed"):
                validate_canonical_prompt_file(prompt_file, strict=True)


class TestCanonicalPromptInstallation:
    """Test canonical prompt installation."""

    @pytest.fixture
    def valid_canonical_content(self) -> str:
        """Valid canonical prompt content for testing."""
        return """---
meta:
  title: "Test Prompt"
  description: "A test prompt for installation"
  version: "1.0.0"
  
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "claude.md"

---

This is test prompt content that will be installed.
"""

    def test_install_canonical_prompt_with_filename(self, valid_canonical_content: str) -> None:
        """Test installing canonical prompt with explicit filename."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create canonical prompt file
            prompt_file = temp_path / "test.canon.md"
            prompt_file.write_text(valid_canonical_content, encoding="utf-8")

            # Install for claude (uses filename)
            target_dir = temp_path / "output"
            install_canonical_prompt(prompt_file, "claude", target_dir, console)

            # Verify installation
            expected_path = target_dir / ".claude" / "claude.md"
            assert expected_path.exists(), "Output file was not created"

            content = expected_path.read_text(encoding="utf-8")
            assert "claude.md" in content, "Filename should be in frontmatter"
            assert "This is test prompt content" in content, "Prompt body should be preserved"

    def test_install_canonical_prompt_with_suffix(self, valid_canonical_content: str) -> None:
        """Test installing canonical prompt with filename suffix."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create canonical prompt file
            prompt_file = temp_path / "test.canon.md"
            prompt_file.write_text(valid_canonical_content, encoding="utf-8")

            # Install for copilot (uses filename_suffix)
            target_dir = temp_path / "output"
            install_canonical_prompt(prompt_file, "copilot", target_dir, console)

            # Verify installation
            expected_path = target_dir / ".github" / "prompts" / "test.prompt.md"
            assert expected_path.exists(), "Output file was not created"

            content = expected_path.read_text(encoding="utf-8")
            assert "test.prompt.md" in content, "Filename should use suffix"
            assert "This is test prompt content" in content, "Prompt body should be preserved"

    def test_install_canonical_prompt_invalid_environment(
        self, valid_canonical_content: str
    ) -> None:
        """Test installing for environment not in canonical prompt."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create canonical prompt file
            prompt_file = temp_path / "test.canon.md"
            prompt_file.write_text(valid_canonical_content, encoding="utf-8")

            target_dir = temp_path / "output"

            with pytest.raises(
                ValueError, match="Environment 'invalid' not found in canonical prompt"
            ):
                install_canonical_prompt(prompt_file, "invalid", target_dir, console)

    def test_install_canonical_prompt_invalid_file(self) -> None:
        """Test installing invalid canonical prompt."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid canonical prompt file
            prompt_file = temp_path / "invalid.canon.md"
            prompt_file.write_text("invalid content", encoding="utf-8")

            target_dir = temp_path / "output"

            with pytest.raises(ValueError, match="Canonical prompt validation failed"):
                install_canonical_prompt(prompt_file, "copilot", target_dir, console)


class TestCanonicalPromptDirectoryInstallation:
    """Test canonical prompt directory installation."""

    @pytest.fixture
    def multiple_canonical_prompts(self) -> list[tuple[str, str]]:
        """Multiple canonical prompt files for testing."""
        return [
            (
                "prompt1.canon.md",
                """---
meta:
   title: "Prompt 1"
environments:
   copilot:
     target: ".github/"
     filename: "prompt1.md"

---

Prompt 1 content""",
            ),
            (
                "prompt2.canonical.md",
                """---
meta:
   title: "Prompt 2"  
environments:
   claude:
     target: ".claude/"
     filename: "prompt2.md"

---

Prompt 2 content""",
            ),
        ]

    def test_install_canonical_prompt_directory_success(
        self, multiple_canonical_prompts: list[tuple[str, str]]
    ) -> None:
        """Test installing directory with multiple canonical prompts."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source directory with canonical prompts
            source_dir = temp_path / "prompts"
            source_dir.mkdir()

            for filename, content in multiple_canonical_prompts:
                (source_dir / filename).write_text(content, encoding="utf-8")

            # Install for copilot (only prompt1 has copilot environment)
            target_dir = temp_path / "output"
            install_canonical_prompt_directory(source_dir, "copilot", target_dir, console)

            # Verify installation
            expected_path = target_dir / ".github" / "prompt1.md"
            assert expected_path.exists(), "Expected output file should be created"

            content = expected_path.read_text(encoding="utf-8")
            assert "Prompt 1 content" in content

    def test_install_canonical_prompt_directory_no_files(self) -> None:
        """Test installing directory with no canonical prompts."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Empty source directory
            source_dir = temp_path / "empty"
            source_dir.mkdir()

            target_dir = temp_path / "output"

            with pytest.raises(ValueError, match="No canonical prompt files found"):
                install_canonical_prompt_directory(source_dir, "copilot", target_dir, console)

    def test_install_canonical_prompt_directory_with_invalid_environment(
        self, multiple_canonical_prompts: list[tuple[str, str]]
    ) -> None:
        """Test installing directory with invalid environment."""
        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            source_dir = temp_path / "prompts"
            source_dir.mkdir()

            for filename, content in multiple_canonical_prompts:
                (source_dir / filename).write_text(content, encoding="utf-8")

            target_dir = temp_path / "output"

            with pytest.raises(
                ValueError, match="Environment 'invalid' not found in any canonical prompt"
            ):
                install_canonical_prompt_directory(source_dir, "invalid", target_dir, console)


class TestDeterministicOutput:
    """Test that generated prompts are deterministic."""

    @pytest.fixture
    def canonical_content(self) -> str:
        """Canonical prompt for determinism testing."""
        return """---
meta:
  title: "Determinism Test Prompt"
  description: "For testing deterministic output"
  version: "1.0.0"
  
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "claude.md"

---

Deterministic prompt content for testing reproducibility."""

    def test_generate_environment_prompt_is_deterministic(self, canonical_content: str) -> None:
        """Test that generating same environment from same prompt yields identical output."""
        from dot_work.prompts.canonical import CanonicalPromptParser, generate_environment_prompt

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(canonical_content)

        # Generate same environment multiple times
        filename1, content1 = generate_environment_prompt(prompt, "copilot")
        filename2, content2 = generate_environment_prompt(prompt, "copilot")
        filename3, content3 = generate_environment_prompt(prompt, "copilot")

        # All should be identical
        assert filename1 == filename2 == filename3
        assert content1 == content2 == content3

    def test_install_creates_deterministic_files(self, canonical_content: str) -> None:
        """Test that installing same canonical prompt twice creates identical files."""
        import hashlib

        console = Console()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create canonical prompt file
            prompt_file = temp_path / "test.canon.md"
            prompt_file.write_text(canonical_content, encoding="utf-8")

            # Install twice to different directories
            target_dir1 = temp_path / "output1"
            target_dir2 = temp_path / "output2"

            install_canonical_prompt(prompt_file, "copilot", target_dir1, console)
            install_canonical_prompt(prompt_file, "copilot", target_dir2, console)

            # Get paths to generated files
            output_file1 = target_dir1 / ".github" / "prompts" / "test.prompt.md"
            output_file2 = target_dir2 / ".github" / "prompts" / "test.prompt.md"

            assert output_file1.exists()
            assert output_file2.exists()

            # Files should be byte-for-byte identical
            content1 = output_file1.read_bytes()
            content2 = output_file2.read_bytes()

            assert content1 == content2
            assert hashlib.sha256(content1).hexdigest() == hashlib.sha256(content2).hexdigest()

    def test_generated_frontmatter_is_stable(self, canonical_content: str) -> None:
        """Test that frontmatter is consistent across multiple generations."""
        from dot_work.prompts.canonical import CanonicalPromptParser, generate_environment_prompt
        import yaml

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(canonical_content)

        # Generate multiple times
        generations = [generate_environment_prompt(prompt, "claude") for _ in range(3)]

        # Extract frontmatter from each
        frontmatters = []
        for filename, content in generations:
            # Extract frontmatter (between --- markers)
            parts = content.split("---")
            frontmatter_text = parts[1]
            frontmatter = yaml.safe_load(frontmatter_text)
            frontmatters.append(frontmatter)

        # All frontmatters should be identical
        for fm in frontmatters[1:]:
            assert fm == frontmatters[0]

    def test_filename_determinism(self, canonical_content: str) -> None:
        """Test that filename generation is deterministic."""
        from dot_work.prompts.canonical import CanonicalPromptParser, generate_environment_prompt

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(canonical_content)

        # Multiple generations should produce same filename
        filenames = [generate_environment_prompt(prompt, "copilot")[0] for _ in range(5)]

        assert all(fn == filenames[0] for fn in filenames)
        assert filenames[0] == "determinism-test-prompt.prompt.md"

    def test_output_contains_only_selected_environment(self, canonical_content: str) -> None:
        """Test that output only contains selected environment, not others."""
        from dot_work.prompts.canonical import CanonicalPromptParser, generate_environment_prompt
        import yaml

        parser = CanonicalPromptParser()
        prompt = parser.parse_content(canonical_content)

        filename, content = generate_environment_prompt(prompt, "copilot")

        # Parse frontmatter
        parts = content.split("---")
        frontmatter_text = parts[1]
        frontmatter = yaml.safe_load(frontmatter_text)

        # Should have meta and environment sections
        assert "meta" in frontmatter
        assert "environment" in frontmatter

        # Should NOT have other environment keys
        assert "copilot" not in frontmatter  # Not duplicated as key
        assert "claude" not in frontmatter  # Other environment not included

        # Environment section should have filename_suffix for copilot
        assert frontmatter["environment"]["filename_suffix"] == ".prompt.md"
