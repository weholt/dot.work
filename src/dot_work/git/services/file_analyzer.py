"""File analysis utilities for categorizing and analyzing file changes."""

import re
from dataclasses import dataclass
from pathlib import Path

from dot_work.git.models import FileCategory


@dataclass
class LanguageInfo:
    """Information about a programming language."""

    name: str
    extensions: list[str]
    category: FileCategory
    complexity_multiplier: float = 1.0
    test_patterns: list[str] | None = None


class FileAnalyzer:
    """Analyzes files and categorizes them based on type and content."""

    def __init__(self, config):
        self.config = config
        self.language_info = self._initialize_language_info()
        self.file_category_patterns = self._initialize_category_patterns()
        self.ignore_patterns = (
            config.file_ignore_patterns if hasattr(config, "file_ignore_patterns") else []
        )

    def categorize_file(self, file_path: str) -> FileCategory:
        """
        Categorize a file based on its path and extension.

        Args:
            file_path: Path to the file

        Returns:
            FileCategory enum value
        """
        # Check ignore patterns first
        if any(pattern in file_path for pattern in self.ignore_patterns):
            return FileCategory.UNKNOWN

        # Check category patterns
        for category, patterns in self.file_category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return category

        # Check by extension/language
        path = Path(file_path)
        ext = path.suffix.lower()

        for language in self.language_info.values():
            if ext in language.extensions:
                return language.category

        # Special cases
        if not ext:
            # No extension - could be config, script, or data
            if any(
                name in file_path.lower()
                for name in ["makefile", "dockerfile", "license", "readme"]
            ):
                return FileCategory.CONFIG
            elif any(name in file_path.lower() for name in ["test", "spec"]):
                return FileCategory.TESTS
            elif file_path.lower().startswith("doc"):
                return FileCategory.DOCUMENTATION

        return FileCategory.UNKNOWN

    def _initialize_language_info(self) -> dict[str, LanguageInfo]:
        """Initialize programming language information."""
        languages = {
            "python": LanguageInfo(
                name="Python",
                extensions=[".py", ".pyi", ".pyw"],
                category=FileCategory.CODE,
                test_patterns=[r"test_", r"_test\.py$", r"/tests/", r"/test_"],
            ),
            "javascript": LanguageInfo(
                name="JavaScript",
                extensions=[".js", ".jsx", ".mjs"],
                category=FileCategory.CODE,
                test_patterns=[r"\.test\.js$", r"\.spec\.js$", r"/tests/", r"/test_"],
            ),
            "typescript": LanguageInfo(
                name="TypeScript",
                extensions=[".ts", ".tsx", ".d.ts"],
                category=FileCategory.CODE,
                test_patterns=[r"\.test\.ts$", r"\.spec\.ts$", r"/tests/", r"/test_"],
            ),
            "java": LanguageInfo(
                name="Java",
                extensions=[".java"],
                category=FileCategory.CODE,
                test_patterns=[r"Test\.java$", r"/test/", r"/tests/"],
            ),
            "go": LanguageInfo(
                name="Go",
                extensions=[".go"],
                category=FileCategory.CODE,
                test_patterns=[r"_test\.go$", r"/test/"],
            ),
            "rust": LanguageInfo(
                name="Rust",
                extensions=[".rs"],
                category=FileCategory.CODE,
                test_patterns=[r"/tests/", r"#\[cfg\(test\)\]"],
            ),
            "sql": LanguageInfo(name="SQL", extensions=[".sql"], category=FileCategory.DATA),
            "shell": LanguageInfo(
                name="Shell",
                extensions=[".sh", ".bash", ".zsh", ".fish"],
                category=FileCategory.CONFIG,
            ),
            "yaml": LanguageInfo(
                name="YAML", extensions=[".yaml", ".yml"], category=FileCategory.CONFIG
            ),
            "json": LanguageInfo(name="JSON", extensions=[".json"], category=FileCategory.CONFIG),
        }

        return languages

    def _initialize_category_patterns(self) -> dict[FileCategory, list[str]]:
        """Initialize file category patterns."""
        return {
            FileCategory.CODE: [
                r"\.(py|js|ts|jsx|tsx|java|go|rs|c|cpp|cc|cxx|h|hpp|cs|php|rb|kt|scala|swift|dart|lua|perl|r|sql)$",
                r"^src/",
                r"^lib/",
                r"^app/",
                r"/src/",
                r"/lib/",
                r"/app/",
            ],
            FileCategory.TESTS: [
                r"^test/",
                r"^tests/",
                r"^spec/",
                r"/test/",
                r"/tests/",
                r"/spec/",
                r"_test\.",
                r"_spec\.",
                r"\.test\.",
                r"\.spec\.",
                r"pytest_",
                r"test_",
            ],
            FileCategory.CONFIG: [
                r"\.(yaml|yml|toml|ini|cfg|conf|json|xml|env|env\..+)$",
                r"^config/",
                r"^\.env",
                r"^settings/",
                r"/config/",
                r"^\.gitignore$",
                r"^\.editorconfig$",
                r"^dockerfile$",
                r"^makefile$",
                r"^requirements\.txt$",
                r"^package\.json$",
                r"^go\.mod$",
                r"^pom\.xml$",
                r"^build\.gradle$",
                r"^\.eslintrc$",
                r"^\.prettierrc$",
            ],
            FileCategory.DOCUMENTATION: [
                r"\.(md|rst|txt|doc|docx|pdf)$",
                r"^readme",
                r"^changelog",
                r"^license",
                r"^docs/",
                r"/docs/",
                r"^\.github/",
                r"/\.github/",
            ],
            FileCategory.DATA: [
                r"\.(csv|json|xml|yaml|yml|sql|db|sqlite|parquet|avro|orc)$",
                r"^data/",
                r"/data/",
                r"^db/",
                r"/db/",
                r"^storage/",
                r"/storage/",
                r"^fixtures/",
                r"/fixtures/",
            ],
            FileCategory.BUILD: [
                r"\.(dockerfile|docker-compose|docker-compose\.yml|docker-compose\.yaml|Dockerfile)$",
                r"^docker/",
                r"/docker/",
                r"^\.github/workflows/",
                r"\.yml$",
                r"pipeline\.yml$",
                r"^ci/",
                r"^\.gitlab-ci\.yml$",
                r"^jenkinsfile$",
                r"^azure-pipelines\.yml$",
                r"^bitbucket-pipelines\.yml$",
            ],
            FileCategory.DEPLOYMENT: [
                r"^deploy/",
                r"/deploy/",
                r"^ansible/",
                r"/ansible/",
                r"^terraform/",
                r"/terraform/",
                r"^k8s/",
                r"/k8s/",
                r"^kubernetes/",
                r"/kubernetes/",
                r"^helm/",
                r"/helm/",
                r"\.tf$",
                r"\.tfvars$",
                r"^cloudformation/",
                r"/cloudformation/",
            ],
        }
