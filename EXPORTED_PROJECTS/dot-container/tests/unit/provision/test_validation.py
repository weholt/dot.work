"""Tests for container provision validation module."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from dot_container.provision.core import RepoAgentError
from dot_container.provision.validation import validate_instructions


class TestValidateInstructions:
    """Test the validate_instructions function."""

    def test_validate_valid_instructions(self, tmp_path: Path) -> None:
        """Test validation passes with valid instruction file."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            base_branch: "main"
            branch: "test/feature"
            docker_image: "test:latest"
            use_ssh: false
            github_token_env: "GITHUB_TOKEN"
            strategy: "agentic"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
              args:
                strategy: "agentic"
            git_user_name: "Test User"
            git_user_email: "test@example.com"
            auto_commit: true
            create_pr: true
            ---

            Make some changes to the codebase.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        # Should not raise any exception
        validate_instructions(test_file)

    def test_validate_missing_repo_url(self, tmp_path: Path) -> None:
        """Test validation fails when repo_url is missing."""
        content = dedent("""\
            ---
            model: "openai/gpt-4"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(
            RepoAgentError, match="Missing required fields in frontmatter: \\['repo_url'\\]"
        ):
            validate_instructions(test_file)

    def test_validate_missing_model(self, tmp_path: Path) -> None:
        """Test validation fails when model is missing."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(
            RepoAgentError, match="Missing required fields in frontmatter: \\['model'\\]"
        ):
            validate_instructions(test_file)

    def test_validate_missing_tool_block(self, tmp_path: Path) -> None:
        """Test validation fails when tool block is missing."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="tool block is missing from frontmatter"):
            validate_instructions(test_file)

    def test_validate_invalid_tool_block(self, tmp_path: Path) -> None:
        """Test validation fails when tool block is not a dict."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            tool: "not-a-dict"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="tool must be a mapping in frontmatter"):
            validate_instructions(test_file)

    def test_validate_missing_tool_name(self, tmp_path: Path) -> None:
        """Test validation fails when tool name is missing."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            tool:
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="Missing required tool fields: \\['name'\\]"):
            validate_instructions(test_file)

    def test_validate_missing_tool_entrypoint(self, tmp_path: Path) -> None:
        """Test validation fails when tool entrypoint is missing."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            tool:
              name: "opencode"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(
            RepoAgentError, match="Missing required tool fields: \\['entrypoint'\\]"
        ):
            validate_instructions(test_file)

    def test_validate_invalid_strategy(self, tmp_path: Path) -> None:
        """Test validation fails with invalid strategy."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            strategy: "invalid"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="strategy must be 'agentic' or 'direct'"):
            validate_instructions(test_file)

    def test_validate_missing_dockerfile(self, tmp_path: Path) -> None:
        """Test validation fails when specified dockerfile doesn't exist."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            dockerfile: "missing.Dockerfile"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="Dockerfile not found at: missing.Dockerfile"):
            validate_instructions(test_file)

    def test_validate_missing_authentication(self, tmp_path: Path) -> None:
        """Test validation fails when no authentication is configured."""
        content = dedent("""\
            ---
            repo_url: "https://github.com/test/repo.git"
            model: "openai/gpt-4"
            tool:
              name: "opencode"
              entrypoint: "opencode run"
            ---

            Instructions here.
            """)

        test_file = tmp_path / "instructions.md"
        test_file.write_text(content)

        with pytest.raises(RepoAgentError, match="Authentication not configured"):
            validate_instructions(test_file)
