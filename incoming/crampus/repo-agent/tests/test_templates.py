import pytest
from pathlib import Path
from repo_agent.templates import DEFAULT_INSTRUCTIONS_TEMPLATE


class TestDefaultTemplate:
    """Test DEFAULT_INSTRUCTIONS_TEMPLATE."""

    def test_template_is_not_empty(self):
        assert len(DEFAULT_INSTRUCTIONS_TEMPLATE) > 0

    def test_template_has_frontmatter_delimiter(self):
        assert DEFAULT_INSTRUCTIONS_TEMPLATE.startswith("---")
        assert DEFAULT_INSTRUCTIONS_TEMPLATE.count("---") >= 2

    def test_template_contains_required_fields(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        
        # Required fields
        assert "repo_url:" in template
        assert "model:" in template
        assert "tool:" in template
        assert "name:" in template
        assert "entrypoint:" in template

    def test_template_contains_optional_fields(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        
        # Optional fields
        assert "base_branch:" in template
        assert "branch:" in template
        assert "strategy:" in template
        assert "auto_commit:" in template
        assert "create_pr:" in template
        assert "docker_image:" in template
        assert "dockerfile:" in template

    def test_template_contains_authentication_options(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        
        assert "github_token:" in template or "github_token_env:" in template
        assert "use_ssh:" in template

    def test_template_contains_pr_configuration(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        
        assert "pr_title:" in template
        assert "pr_body:" in template

    def test_template_contains_git_config(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        
        assert "git_user_name:" in template
        assert "git_user_email:" in template

    def test_template_contains_instructions_section(self):
        # Check that there's content after the frontmatter
        parts = DEFAULT_INSTRUCTIONS_TEMPLATE.split("---")
        assert len(parts) >= 3
        instructions = parts[2].strip()
        assert len(instructions) > 0

    def test_template_contains_tool_args_example(self):
        template = DEFAULT_INSTRUCTIONS_TEMPLATE
        assert "args:" in template

    def test_template_is_valid_yaml_frontmatter(self):
        """Test that the template can be parsed."""
        import frontmatter
        from io import StringIO
        
        # This will raise an exception if invalid
        post = frontmatter.load(StringIO(DEFAULT_INSTRUCTIONS_TEMPLATE))
        
        assert post.metadata is not None
        assert post.content is not None
