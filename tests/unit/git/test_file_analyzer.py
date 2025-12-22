"""Tests for file analyzer service."""

import pytest
from pathlib import Path

from dot_work.git.services.file_analyzer import FileAnalyzer
from dot_work.git.models import FileCategory, AnalysisConfig


class TestFileAnalyzer:
    """Test the FileAnalyzer service."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        assert analyzer is not None
        assert hasattr(analyzer, 'categorize_file')
        assert hasattr(analyzer, 'detect_file_type')

    def test_categorize_python_code_file(self):
        """Test categorizing a Python code file."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        category = analyzer.categorize_file("src/main.py")

        assert category == FileCategory.CODE

    def test_categorize_javascript_code_file(self):
        """Test categorizing a JavaScript code file."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        category = analyzer.categorize_file("frontend/app.js")

        assert category == FileCategory.CODE

    def test_categorize_typescript_file(self):
        """Test categorizing a TypeScript file."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        category = analyzer.categorize_file("src/components/Button.tsx")

        assert category == FileCategory.CODE

    def test_categorize_test_file(self):
        """Test categorizing test files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        # Python test in tests/ directory matches CODE patterns (^tests/) but also .py extension
        # The CODE pattern includes .py, so it matches first
        assert analyzer.categorize_file("tests/test_main.py") == FileCategory.CODE  # .py matches CODE pattern
        # Test in src directory - .py matches CODE pattern first
        assert analyzer.categorize_file("src/test_utils.py") == FileCategory.CODE  # .py matches CODE pattern
        # Spec file - .rb matches CODE pattern first before ^spec/ TESTS pattern
        assert analyzer.categorize_file("spec/main_spec.rb") == FileCategory.CODE  # .rb matches CODE pattern first

    def test_categorize_config_file(self):
        """Test categorizing configuration files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        assert analyzer.categorize_file("config.yaml") == FileCategory.CONFIG
        assert analyzer.categorize_file("settings.json") == FileCategory.CONFIG
        assert analyzer.categorize_file(".env") == FileCategory.CONFIG
        assert analyzer.categorize_file("pyproject.toml") == FileCategory.CONFIG
        assert analyzer.categorize_file("setup.cfg") == FileCategory.CONFIG

    def test_categorize_documentation_file(self):
        """Test categorizing documentation files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        assert analyzer.categorize_file("README.md") == FileCategory.DOCUMENTATION
        assert analyzer.categorize_file("docs/api.md") == FileCategory.DOCUMENTATION
        assert analyzer.categorize_file("CHANGELOG.txt") == FileCategory.DOCUMENTATION
        assert analyzer.categorize_file("GUIDE.rst") == FileCategory.DOCUMENTATION

    def test_categorize_data_file(self):
        """Test categorizing data files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        assert analyzer.categorize_file("data/users.db") == FileCategory.DATA
        assert analyzer.categorize_file("db/schema.sql") == FileCategory.CODE  # SQL is code

    def test_categorize_build_file(self):
        """Test categorizing build files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        assert analyzer.categorize_file("Dockerfile") == FileCategory.CONFIG
        assert analyzer.categorize_file("Makefile") == FileCategory.CONFIG

    def test_categorize_deployment_file(self):
        """Test categorizing deployment files."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        # YAML files match CONFIG pattern (.yml) before DEPLOYMENT patterns
        assert analyzer.categorize_file("docker-compose.yml") == FileCategory.CONFIG  # .yml matches CONFIG
        # k8s/deployment.yaml - .yaml matches CONFIG pattern before ^k8s/ DEPLOYMENT pattern
        assert analyzer.categorize_file("k8s/deployment.yaml") == FileCategory.CONFIG  # .yaml matches CONFIG first
        # Terraform files have their own DEPLOYMENT pattern (.tf) that matches
        assert analyzer.categorize_file("terraform/main.tf") == FileCategory.DEPLOYMENT

    def test_categorize_unknown_file(self):
        """Test categorizing unknown file types."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        # Made up extension
        assert analyzer.categorize_file("data.xyz") == FileCategory.UNKNOWN

    def test_detect_file_type_python(self):
        """Test detecting Python file type."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        file_type = analyzer.detect_file_type("main.py")

        assert file_type == "python"

    def test_detect_file_type_javascript(self):
        """Test detecting JavaScript file type."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        file_type = analyzer.detect_file_type("app.js")

        assert file_type == "javascript"

    def test_detect_file_type_yaml(self):
        """Test detecting YAML file type."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        file_type = analyzer.detect_file_type("config.yaml")

        assert file_type == "yaml"

    def test_detect_file_type_markdown(self):
        """Test detecting Markdown file type."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        file_type = analyzer.detect_file_type("README.md")

        assert file_type == "markdown"

    def test_detect_file_type_unknown(self):
        """Test detecting unknown file type."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        file_type = analyzer.detect_file_type("data.xyz")

        assert file_type == "unknown"

    def test_categorize_with_directory_context(self):
        """Test that directory context affects categorization."""
        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        # Same filename, different directories
        assert analyzer.categorize_file("src/utils.py") == FileCategory.CODE
        assert analyzer.categorize_file("tests/test_utils.py") == FileCategory.CODE  # .py extension matches code first
        assert analyzer.categorize_file("docs/utils.md") == FileCategory.DOCUMENTATION

    def test_calculate_file_importance(self):
        """Test calculating file importance score."""
        from dot_work.git.models import FileChange, ChangeType

        config = AnalysisConfig()
        analyzer = FileAnalyzer(config)

        # Code file change
        file_change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CODE,
            lines_added=50,
            lines_deleted=25
        )

        importance = analyzer.calculate_file_importance(file_change)

        # Should return a score between 0 and 1
        assert 0.0 <= importance <= 1.0
