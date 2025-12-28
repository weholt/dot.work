from pathlib import Path

import pytest
import yaml


class TestCodeRabbitConfig:
    """Test CodeRabbit configuration file."""

    @pytest.fixture
    def config_path(self):
        """Path to the CodeRabbit configuration file."""
        return Path(__file__).parent.parent / ".coderabbit.yaml"

    @pytest.fixture
    def config(self, config_path):
        """Load the CodeRabbit configuration."""
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self, config_path):
        """Test that the configuration file exists."""
        assert config_path.exists(), "CodeRabbit configuration file should exist"

    def test_valid_yaml_syntax(self, config_path):
        """Test that the configuration file has valid YAML syntax."""
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert config is not None, "Configuration should be valid YAML"

    def test_required_sections(self, config):
        """Test that all required sections are present."""
        required_sections = [
            "language",
            "reviews",
            "finishing_touches",
            "pre_merge_checks",
            "tools",
        ]
        for section in required_sections:
            assert section in config, f"Configuration should have '{section}' section"

    def test_language_setting(self, config):
        """Test that language is set correctly."""
        assert config["language"] == "en-US", "Language should be set to en-US"

    def test_review_profile(self, config):
        """Test that review profile is set to assertive."""
        assert config["reviews"]["profile"] == "assertive", "Review profile should be 'assertive'"

    def test_auto_review_enabled(self, config):
        """Test that auto review is enabled."""
        auto_review = config["reviews"]["auto_review"]
        assert auto_review["enabled"] is True, "Auto review should be enabled"
        assert auto_review["auto_incremental_review"] is True, (
            "Auto incremental review should be enabled"
        )

    def test_high_level_summary(self, config):
        """Test that high-level summary is configured."""
        reviews = config["reviews"]
        assert reviews["high_level_summary"] is True, "High-level summary should be enabled"
        assert "high_level_summary_instructions" in reviews, (
            "Summary instructions should be present"
        )
        assert reviews["high_level_summary_placeholder"] == "@coderabbitai summary"

    def test_path_instructions(self, config):
        """Test that path instructions are configured."""
        path_instructions = config["reviews"]["path_instructions"]
        assert len(path_instructions) >= 2, "Should have at least 2 path instructions"

        # Check Python path instruction
        python_path = next((p for p in path_instructions if p["path"] == "**/*.py"), None)
        assert python_path is not None, "Python path instruction should exist"
        assert "typing" in python_path["instructions"], "Python instructions should mention typing"
        assert "dataclasses" in python_path["instructions"], (
            "Python instructions should mention dataclasses"
        )

    def test_custom_checks(self, config):
        """Test that custom checks are configured."""
        custom_checks = config["pre_merge_checks"]["custom_checks"]
        assert len(custom_checks) == 3, "Should have 3 custom checks"

        check_names = [c["name"] for c in custom_checks]
        assert "SRP‐enforcement" in check_names, "SRP enforcement check should exist"
        assert "Layer‐boundary‐violation" in check_names, "Layer boundary check should exist"
        assert "Magic‐values" in check_names, "Magic values check should exist"

        # Check severity modes
        srp_check = next(c for c in custom_checks if c["name"] == "SRP‐enforcement")
        assert srp_check["mode"] == "error", "SRP check should be in error mode"

        layer_check = next(c for c in custom_checks if c["name"] == "Layer‐boundary‐violation")
        assert layer_check["mode"] == "error", "Layer boundary check should be in error mode"

        magic_check = next(c for c in custom_checks if c["name"] == "Magic‐values")
        assert magic_check["mode"] == "warning", "Magic values check should be in warning mode"

    def test_tools_configuration(self, config):
        """Test that tools are configured."""
        tools = config["tools"]
        expected_tools = ["ruff", "shellcheck", "markdownlint", "github-checks", "ast-grep"]
        for tool in expected_tools:
            assert tool in tools, f"Tool '{tool}' should be configured"

        # Check specific tool settings
        assert tools["ruff"]["enabled"] is True, "Ruff should be enabled"
        assert tools["shellcheck"]["enabled"] is True, "Shellcheck should be enabled"
        assert tools["markdownlint"]["enabled"] is True, "Markdownlint should be enabled"
        assert tools["github-checks"]["enabled"] is True, "GitHub checks should be enabled"

    def test_docstring_configuration(self, config):
        """Test that docstring configuration is present."""
        pre_merge = config["pre_merge_checks"]
        assert "docstrings" in pre_merge, "Docstrings check should be configured"
        assert pre_merge["docstrings"]["mode"] == "warning", "Docstrings should be in warning mode"
        assert pre_merge["docstrings"]["threshold"] == 80, "Docstrings threshold should be 80%"

    def test_finishing_touches(self, config):
        """Test that finishing touches are configured."""
        finishing = config["finishing_touches"]
        assert finishing["docstrings"]["enabled"] is True, (
            "Docstrings finishing touch should be enabled"
        )
        assert finishing["unit_tests"]["enabled"] is True, (
            "Unit tests finishing touch should be enabled"
        )

    def test_code_generation(self, config):
        """Test that code generation is configured."""
        code_gen = config["code_generation"]
        assert "docstrings" in code_gen, "Docstrings generation should be configured"
        assert "unit_tests" in code_gen, "Unit tests generation should be configured"

        # Check docstrings configuration
        assert code_gen["docstrings"]["language"] == "en-US", "Docstrings language should be en-US"
        assert len(code_gen["docstrings"]["path_instructions"]) > 0, (
            "Docstrings path instructions should exist"
        )

        # Check unit tests configuration
        assert len(code_gen["unit_tests"]["path_instructions"]) > 0, (
            "Unit tests path instructions should exist"
        )

    def test_knowledge_base(self, config):
        """Test that knowledge base is configured."""
        kb = config["knowledge_base"]
        assert kb["web_search"]["enabled"] is True, "Web search should be enabled"
        assert kb["code_guidelines"]["enabled"] is True, "Code guidelines should be enabled"
        assert "filePatterns" in kb["code_guidelines"], "File patterns should be configured"

    def test_pr_title_requirements(self, config):
        """Test that PR title requirements are configured."""
        reviews = config["reviews"]
        assert "auto_title_instructions" in reviews, "Auto title instructions should be present"
        assert "<area>: <action>" in reviews["auto_title_instructions"], (
            "Title format should be specified"
        )

        pre_merge = config["pre_merge_checks"]
        assert "title" in pre_merge, "Title check should be configured"
        assert "<area>: <action>" in pre_merge["title"]["requirements"], (
            "Title requirements should match format"
        )
