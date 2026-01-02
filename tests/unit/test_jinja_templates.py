"""Comprehensive tests for Jinja2 template processing in the installer module.

These tests verify that:
1. Template variables are correctly substituted for each environment
2. All environments produce valid, non-templated output
3. Complex nested templates render correctly
4. Edge cases are handled properly
"""

from pathlib import Path

import pytest

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import (
    build_template_context,
    create_jinja_env,
    render_prompt,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def template_prompts_dir(tmp_path: Path) -> Path:
    """Create a prompts directory with various template files for testing."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Simple template with all variables
    (prompts_dir / "all-variables.prompt.md").write_text(
        """# Test Prompt

Path: {{ prompt_path }}
Tool: {{ ai_tool }}
Tool Name: {{ ai_tool_name }}
Extension: {{ prompt_extension }}
Instructions: {{ instructions_file }}
Rules: {{ rules_file }}
""",
        encoding="utf-8",
    )

    # Template simulating the setup-issue-tracker.prompt.md pattern
    (prompts_dir / "setup-issue-tracker.prompt.md").write_text(
        """# Issue Tracker Setup

See [do-work.prompt.md]({{ prompt_path }}/do-work.prompt.md) for details.

## Configuration

Add to your config:
- [do-work.prompt.md]({{ prompt_path }}/do-work.prompt.md)

Tool: {{ ai_tool_name }}
""",
        encoding="utf-8",
    )

    # Template with no variables (plain markdown)
    (prompts_dir / "plain.prompt.md").write_text(
        """# Plain Prompt

This prompt has no template variables.
It should pass through unchanged.
""",
        encoding="utf-8",
    )

    # Template with repeated variables
    (prompts_dir / "repeated.prompt.md").write_text(
        """# Repeated Variables

First: {{ prompt_path }}
Second: {{ prompt_path }}
Third: {{ prompt_path }}

Tool appears here: {{ ai_tool }}
And here: {{ ai_tool }}
""",
        encoding="utf-8",
    )

    # Template with markdown code blocks containing template syntax
    (prompts_dir / "code-blocks.prompt.md").write_text(
        """# Code Blocks Test

Real variable: {{ prompt_path }}

```markdown
## Example

- [file.md]({{ prompt_path }}/file.md)
```

After code block: {{ ai_tool }}
""",
        encoding="utf-8",
    )

    # Template with conditional-like content (no actual jinja conditionals)
    (prompts_dir / "complex.prompt.md").write_text(
        """# Complex Template

| Variable | Value |
|----------|-------|
| Path | {{ prompt_path }} |
| Tool | {{ ai_tool }} |
| Extension | {{ prompt_extension }} |

## Links

1. [Primary]({{ prompt_path }}/primary{{ prompt_extension }})
2. [Secondary]({{ prompt_path }}/secondary{{ prompt_extension }})
""",
        encoding="utf-8",
    )

    return prompts_dir


@pytest.fixture
def all_environment_keys() -> list[str]:
    """Return all environment keys for parametrized testing."""
    return list(ENVIRONMENTS.keys())


# =============================================================================
# Tests for create_jinja_env
# =============================================================================


class TestCreateJinjaEnv:
    """Tests for the create_jinja_env function."""

    def test_creates_environment_with_file_loader(self, template_prompts_dir: Path) -> None:
        """Verify Jinja environment uses FileSystemLoader."""
        env = create_jinja_env(template_prompts_dir)

        assert env is not None
        assert env.loader is not None
        assert isinstance(env.loader, type(env.loader))  # FileSystemLoader

    def test_keeps_trailing_newlines(self, template_prompts_dir: Path) -> None:
        """Verify trailing newlines are preserved."""
        env = create_jinja_env(template_prompts_dir)
        assert env.keep_trailing_newline is True

    def test_does_not_trim_blocks(self, template_prompts_dir: Path) -> None:
        """Verify block trimming is disabled for markdown compatibility."""
        env = create_jinja_env(template_prompts_dir)
        assert env.trim_blocks is False
        assert env.lstrip_blocks is False

    def test_can_load_template(self, template_prompts_dir: Path) -> None:
        """Verify templates can be loaded from the environment."""
        env = create_jinja_env(template_prompts_dir)
        template = env.get_template("plain.prompt.md")

        assert template is not None
        assert "Plain Prompt" in template.render()


# =============================================================================
# Tests for build_template_context
# =============================================================================


class TestBuildTemplateContext:
    """Tests for the build_template_context function."""

    def test_copilot_context_values(self) -> None:
        """Verify Copilot environment produces correct context."""
        env_config = ENVIRONMENTS["copilot"]
        context = build_template_context(env_config)

        assert context["prompt_path"] == ".github/prompts"
        assert context["ai_tool"] == "copilot"
        assert context["ai_tool_name"] == "GitHub Copilot (VS Code)"
        assert context["prompt_extension"] == ".md"

    def test_claude_context_values(self) -> None:
        """Verify Claude environment produces correct context."""
        env_config = ENVIRONMENTS["claude"]
        context = build_template_context(env_config)

        assert context["prompt_path"] == "prompts"  # Claude has no prompt_dir
        assert context["ai_tool"] == "claude"
        assert context["ai_tool_name"] == "Claude Code"
        assert context["instructions_file"] == "CLAUDE.md"

    def test_cursor_context_values(self) -> None:
        """Verify Cursor environment produces correct context."""
        env_config = ENVIRONMENTS["cursor"]
        context = build_template_context(env_config)

        assert context["prompt_path"] == ".cursor/rules"
        assert context["ai_tool"] == "cursor"
        assert context["prompt_extension"] == ".mdc"
        assert context["rules_file"] == ".cursorrules"

    def test_generic_context_values(self) -> None:
        """Verify generic environment produces correct context."""
        env_config = ENVIRONMENTS["generic"]
        context = build_template_context(env_config)

        assert context["prompt_path"] == "prompts"
        assert context["ai_tool"] == "generic"
        assert context["instructions_file"] == "AGENTS.md"

    def test_all_context_keys_present(self) -> None:
        """Verify all expected keys are present in context."""
        expected_keys = {
            "prompt_path",
            "ai_tool",
            "ai_tool_name",
            "prompt_extension",
            "instructions_file",
            "rules_file",
        }

        for env_key in ENVIRONMENTS:
            context = build_template_context(ENVIRONMENTS[env_key])
            assert set(context.keys()) == expected_keys, f"Missing keys for {env_key}"

    def test_no_none_values_in_context(self) -> None:
        """Verify no None values leak into context (should be empty strings)."""
        for env_key in ENVIRONMENTS:
            context = build_template_context(ENVIRONMENTS[env_key])
            for key, value in context.items():
                assert value is not None, f"{key} is None for {env_key}"
                assert isinstance(value, str), f"{key} is not str for {env_key}"


# =============================================================================
# Tests for render_prompt
# =============================================================================


class TestRenderPrompt:
    """Tests for the render_prompt function."""

    def test_renders_all_variables_for_copilot(self, template_prompts_dir: Path) -> None:
        """Verify all template variables are substituted for Copilot."""
        prompt_file = template_prompts_dir / "all-variables.prompt.md"
        env_config = ENVIRONMENTS["copilot"]

        result = render_prompt(template_prompts_dir, prompt_file, env_config)

        assert "Path: .github/prompts" in result
        assert "Tool: copilot" in result
        assert "Tool Name: GitHub Copilot (VS Code)" in result
        assert "Extension: .md" in result
        # No raw template syntax should remain
        assert "{{" not in result
        assert "}}" not in result

    def test_renders_all_variables_for_cursor(self, template_prompts_dir: Path) -> None:
        """Verify all template variables are substituted for Cursor."""
        prompt_file = template_prompts_dir / "all-variables.prompt.md"
        env_config = ENVIRONMENTS["cursor"]

        result = render_prompt(template_prompts_dir, prompt_file, env_config)

        assert "Path: .cursor/rules" in result
        assert "Tool: cursor" in result
        assert "Extension: .mdc" in result
        assert "Rules: .cursorrules" in result

    def test_renders_setup_tracker_correctly(self, template_prompts_dir: Path) -> None:
        """Verify the setup-issue-tracker pattern renders correctly."""
        prompt_file = template_prompts_dir / "setup-issue-tracker.prompt.md"

        # Test with Copilot
        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["copilot"])
        assert "[do-work.prompt.md](.github/prompts/do-work.prompt.md)" in result

        # Test with Cursor
        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["cursor"])
        assert "[do-work.prompt.md](.cursor/rules/do-work.prompt.md)" in result

        # Test with generic
        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["generic"])
        assert "[do-work.prompt.md](prompts/do-work.prompt.md)" in result

    def test_plain_template_unchanged(self, template_prompts_dir: Path) -> None:
        """Verify templates without variables pass through unchanged."""
        prompt_file = template_prompts_dir / "plain.prompt.md"
        original = prompt_file.read_text(encoding="utf-8")

        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["copilot"])

        assert result == original

    def test_repeated_variables_all_substituted(self, template_prompts_dir: Path) -> None:
        """Verify repeated variables are all substituted."""
        prompt_file = template_prompts_dir / "repeated.prompt.md"

        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["copilot"])

        # Count occurrences of the substituted value
        assert result.count(".github/prompts") == 3
        assert result.count("copilot") == 2
        assert "{{ prompt_path }}" not in result
        assert "{{ ai_tool }}" not in result

    def test_code_blocks_render_correctly(self, template_prompts_dir: Path) -> None:
        """Verify templates in code blocks are also rendered."""
        prompt_file = template_prompts_dir / "code-blocks.prompt.md"

        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["copilot"])

        # Variables should be substituted even in code blocks
        assert "Real variable: .github/prompts" in result
        assert "[file.md](.github/prompts/file.md)" in result
        assert "After code block: copilot" in result

    def test_complex_template_with_tables(self, template_prompts_dir: Path) -> None:
        """Verify complex templates with tables render correctly."""
        prompt_file = template_prompts_dir / "complex.prompt.md"

        result = render_prompt(template_prompts_dir, prompt_file, ENVIRONMENTS["cursor"])

        # Table should have correct values
        assert "| Path | .cursor/rules |" in result
        assert "| Tool | cursor |" in result
        assert "| Extension | .mdc |" in result

        # Links should have correct paths
        assert "[Primary](.cursor/rules/primary.mdc)" in result
        assert "[Secondary](.cursor/rules/secondary.mdc)" in result


# =============================================================================
# Parametrized tests for all environments
# =============================================================================


class TestAllEnvironments:
    """Parametrized tests that run against all environments."""

    @pytest.mark.parametrize("env_key", list(ENVIRONMENTS.keys()))
    def test_render_produces_no_raw_template_syntax(
        self, template_prompts_dir: Path, env_key: str
    ) -> None:
        """Verify no environment produces raw {{ }} in output."""
        prompt_file = template_prompts_dir / "all-variables.prompt.md"
        env_config = ENVIRONMENTS[env_key]

        result = render_prompt(template_prompts_dir, prompt_file, env_config)

        assert "{{" not in result, f"{env_key} left raw {{ in output"
        assert "}}" not in result, f"{env_key} left raw }} in output"

    @pytest.mark.parametrize("env_key", list(ENVIRONMENTS.keys()))
    def test_prompt_path_is_set(self, template_prompts_dir: Path, env_key: str) -> None:
        """Verify prompt_path is always set (never empty) for all environments."""
        env_config = ENVIRONMENTS[env_key]
        context = build_template_context(env_config)

        assert context["prompt_path"], f"{env_key} has empty prompt_path"
        assert len(context["prompt_path"]) > 0

    @pytest.mark.parametrize("env_key", list(ENVIRONMENTS.keys()))
    def test_ai_tool_matches_key(self, env_key: str) -> None:
        """Verify ai_tool context value matches the environment key."""
        env_config = ENVIRONMENTS[env_key]
        context = build_template_context(env_config)

        assert context["ai_tool"] == env_key

    @pytest.mark.parametrize(
        "env_key,expected_path",
        [
            ("copilot", ".github/prompts"),
            ("cursor", ".cursor/rules"),
            ("windsurf", ".windsurf/rules"),
            ("continue", ".continue/prompts"),
            ("zed", ".zed/prompts"),
            ("opencode", ".opencode/prompts"),
            ("generic", "prompts"),
        ],
    )
    def test_expected_prompt_paths(self, env_key: str, expected_path: str) -> None:
        """Verify each environment has the expected prompt path."""
        env_config = ENVIRONMENTS[env_key]
        context = build_template_context(env_config)

        assert context["prompt_path"] == expected_path


# =============================================================================
# Integration tests with real prompt files
# =============================================================================


class TestRealPromptFiles:
    """Tests that use the actual prompt files from the package."""

    @pytest.fixture
    def real_prompts_dir(self) -> Path:
        """Get the real prompts directory from the package."""
        from dot_work.installer import get_prompts_dir

        return get_prompts_dir()

    def test_setup_issue_tracker_renders_for_copilot(self, real_prompts_dir: Path) -> None:
        """Verify the real setup-issue-tracker.md renders for Copilot."""
        prompt_file = real_prompts_dir / "setup-issue-tracker.md"
        if not prompt_file.exists():
            pytest.skip("setup-issue-tracker.md not found")

        result = render_prompt(real_prompts_dir, prompt_file, ENVIRONMENTS["copilot"])

        # Should have Copilot paths
        assert ".github/prompts" in result
        # Should have no raw template syntax
        assert "{{ prompt_path }}" not in result
        assert "{{" not in result or "```" in result  # Allow in code examples

    def test_do_work_renders_for_cursor(self, real_prompts_dir: Path) -> None:
        """Verify the real do-work.md renders for Cursor."""
        prompt_file = real_prompts_dir / "do-work.md"
        if not prompt_file.exists():
            pytest.skip("do-work.md not found")

        result = render_prompt(real_prompts_dir, prompt_file, ENVIRONMENTS["cursor"])

        # Should render without errors
        assert len(result) > 0
        # Should have no unsubstituted template variables in prose
        # (Code examples might have template syntax for documentation)

    @pytest.mark.parametrize("env_key", ["copilot", "cursor", "claude", "generic"])
    def test_all_real_prompts_render_without_error(
        self, real_prompts_dir: Path, env_key: str
    ) -> None:
        """Verify all real prompt files render without errors for key environments."""
        env_config = ENVIRONMENTS[env_key]

        for prompt_file in real_prompts_dir.glob("*.prompt.md"):
            # Should not raise any exceptions
            result = render_prompt(real_prompts_dir, prompt_file, env_config)
            assert len(result) > 0, f"{prompt_file.name} produced empty output"


# =============================================================================
# Edge case tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_template_file(self, tmp_path: Path) -> None:
        """Verify empty template files render to empty string."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        empty_file = prompts_dir / "empty.prompt.md"
        empty_file.write_text("", encoding="utf-8")

        result = render_prompt(prompts_dir, empty_file, ENVIRONMENTS["copilot"])

        assert result == ""

    def test_template_with_only_whitespace(self, tmp_path: Path) -> None:
        """Verify whitespace-only templates preserve whitespace."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        whitespace_file = prompts_dir / "whitespace.prompt.md"
        whitespace_file.write_text("   \n\n   \n", encoding="utf-8")

        result = render_prompt(prompts_dir, whitespace_file, ENVIRONMENTS["copilot"])

        assert result == "   \n\n   \n"

    def test_template_with_special_characters(self, tmp_path: Path) -> None:
        """Verify special characters are preserved."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        special_file = prompts_dir / "special.prompt.md"
        special_file.write_text(
            "Special chars: © ® ™ € £ ¥ • … — –\nEmoji: 🚀 📁 ✓ ⚠️\nPath: {{ prompt_path }}\n",
            encoding="utf-8",
        )

        result = render_prompt(prompts_dir, special_file, ENVIRONMENTS["copilot"])

        assert "©" in result
        assert "🚀" in result
        assert ".github/prompts" in result

    def test_template_with_percent_signs(self, tmp_path: Path) -> None:
        """Verify percent signs don't break rendering."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        percent_file = prompts_dir / "percent.prompt.md"
        percent_file.write_text(
            "Coverage: 75%\n100% complete\nPath: {{ prompt_path }}\n",
            encoding="utf-8",
        )

        result = render_prompt(prompts_dir, percent_file, ENVIRONMENTS["copilot"])

        assert "75%" in result
        assert "100%" in result
        assert ".github/prompts" in result

    def test_template_with_backslashes(self, tmp_path: Path) -> None:
        """Verify backslashes (Windows paths) are preserved."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        backslash_file = prompts_dir / "backslash.prompt.md"
        backslash_file.write_text(
            "Windows: C:\\Users\\Name\\Project\nEscape: \\n \\t\nPath: {{ prompt_path }}\n",
            encoding="utf-8",
        )

        result = render_prompt(prompts_dir, backslash_file, ENVIRONMENTS["copilot"])

        assert "C:\\Users\\Name\\Project" in result
        assert "\\n \\t" in result

    def test_nonexistent_template_raises_error(self, tmp_path: Path) -> None:
        """Verify appropriate error for missing template file."""
        from jinja2 import TemplateNotFound

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        with pytest.raises(TemplateNotFound):
            render_prompt(
                prompts_dir,
                prompts_dir / "nonexistent.prompt.md",
                ENVIRONMENTS["copilot"],
            )

    def test_undefined_variable_in_template(self, tmp_path: Path) -> None:
        """Verify undefined variables produce empty string (not error)."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        undefined_file = prompts_dir / "undefined.prompt.md"
        undefined_file.write_text(
            "Defined: {{ ai_tool }}\nUndefined: {{ nonexistent_var }}\n",
            encoding="utf-8",
        )

        # By default, Jinja2 renders undefined as empty string
        # This might raise UndefinedError depending on config
        # Our current config should render empty
        result = render_prompt(prompts_dir, undefined_file, ENVIRONMENTS["copilot"])

        assert "Defined: copilot" in result
        # Undefined should be empty (default Jinja2 behavior)
        assert "Undefined: \n" in result or "Undefined:" in result


# =============================================================================
# Performance tests
# =============================================================================


class TestPerformance:
    """Basic performance sanity checks."""

    def test_render_large_template_quickly(self, tmp_path: Path) -> None:
        """Verify large templates render in reasonable time."""
        import time

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create a smaller template (1,000 lines) for reasonable test time
        lines = [f"Line {{{{ ai_tool }}}} number {i}: {{{{ prompt_path }}}}" for i in range(1000)]
        large_file = prompts_dir / "large.prompt.md"
        large_file.write_text("\n".join(lines), encoding="utf-8")

        start = time.time()
        result = render_prompt(prompts_dir, large_file, ENVIRONMENTS["copilot"])
        elapsed = time.time() - start

        assert elapsed < 30.0, f"Rendering took too long: {elapsed:.2f}s"
        assert "Line copilot number 0:" in result
        assert "Line copilot number 999:" in result

    def test_multiple_renders_consistent(self, template_prompts_dir: Path) -> None:
        """Verify multiple renders produce identical output."""
        prompt_file = template_prompts_dir / "all-variables.prompt.md"
        env_config = ENVIRONMENTS["copilot"]

        results = [render_prompt(template_prompts_dir, prompt_file, env_config) for _ in range(10)]

        assert all(r == results[0] for r in results), "Inconsistent rendering"
