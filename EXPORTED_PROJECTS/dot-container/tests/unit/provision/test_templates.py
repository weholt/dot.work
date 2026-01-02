"""Tests for container provision templates module."""

from __future__ import annotations

import frontmatter

from dot_container.provision.templates import DEFAULT_INSTRUCTIONS_TEMPLATE


class TestDefaultTemplate:
    """Test the default instruction template."""

    def test_default_template_is_valid(self) -> None:
        """Test that the default template has valid frontmatter."""
        # Parse the template with frontmatter
        post = frontmatter.loads(DEFAULT_INSTRUCTIONS_TEMPLATE)

        # Check that we have metadata
        assert post.metadata is not None
        assert len(post.metadata) > 0

        # Check required fields are present
        required_fields = ["repo_url", "model"]
        for field in required_fields:
            assert field in post.metadata, f"Missing required field: {field}"

        # Check that tool block exists
        assert "tool" in post.metadata
        tool = post.metadata["tool"]
        assert isinstance(tool, dict)

        # Check required tool fields
        tool_required = ["name", "entrypoint"]
        for field in tool_required:
            assert field in tool, f"Missing required tool field: {field}"

        # Check that strategy is valid
        strategy = post.metadata.get("strategy", "agentic")
        assert strategy in ["agentic", "direct"], f"Invalid strategy: {strategy}"

        # Check that we have content after frontmatter
        assert post.content.strip() != "", "Template has no instruction content"

    def test_default_template_has_placeholders(self) -> None:
        """Test that the default template contains placeholder values."""
        post = frontmatter.loads(DEFAULT_INSTRUCTIONS_TEMPLATE)

        # Check that repo_url has placeholder
        assert "your/repo" in post.metadata["repo_url"]

        # Check that model is specified
        assert "gpt-4" in post.metadata["model"]

        # Check that tool configuration has expected structure
        tool = post.metadata["tool"]
        assert tool["name"] == "opencode"
        assert "run" in tool["entrypoint"]

    def test_default_template_has_authentication_config(self) -> None:
        """Test that the default template includes authentication configuration."""
        post = frontmatter.loads(DEFAULT_INSTRUCTIONS_TEMPLATE)

        # Should have authentication options
        assert "github_token_env" in post.metadata or "use_ssh" in post.metadata
        assert post.metadata.get("use_ssh", False) is False
