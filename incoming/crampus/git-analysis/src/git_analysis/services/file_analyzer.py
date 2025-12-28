"""File analysis utilities for categorizing and analyzing file changes."""

import re
from dataclasses import dataclass
from pathlib import Path

from ..models import ChangeType, FileCategory, FileChange


@dataclass
class LanguageInfo:
    """Information about a programming language."""

    name: str
    extensions: list[str]
    category: FileCategory
    complexity_multiplier: float = 1.0
    test_patterns: list[str] = None


class FileAnalyzer:
    """Analyzes files and categorizes them based on type and content."""

    def __init__(self, config):
        self.config = config
        self.language_info = self._initialize_language_info()
        self.file_category_patterns = self._initialize_category_patterns()
        self.ignore_patterns = config.file_ignore_patterns if hasattr(config, "file_ignore_patterns") else []

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
            if any(name in file_path.lower() for name in ["makefile", "dockerfile", "license", "readme"]):
                return FileCategory.CONFIG
            elif any(name in file_path.lower() for name in ["test", "spec"]):
                return FileCategory.TESTS
            elif file_path.lower().startswith("doc"):
                return FileCategory.DOCUMENTATION

        return FileCategory.UNKNOWN

    def analyze_file_content(self, file_path: str, content: str | None = None) -> dict[str, any]:
        """
        Analyze file content to extract additional information.

        Args:
            file_path: Path to the file
            content: File content (optional, will be read if not provided)

        Returns:
            Dictionary with file analysis results
        """
        if content is None:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, FileNotFoundError, PermissionError):
                return {"binary_file": True, "readable": False}

        analysis = {
            "binary_file": False,
            "readable": True,
            "line_count": len(content.splitlines()),
            "character_count": len(content),
            "language": self._detect_language(file_path, content),
            "has_tests": self._contains_tests(content),
            "has_documentation": self._contains_documentation(content),
            "imports": self._extract_imports(content),
            "functions": self._extract_functions(content),
            "classes": self._extract_classes(content),
            "complexity_indicators": self._analyze_complexity_indicators(content),
        }

        return analysis

    def detect_file_type(self, file_path: str, content: str | None = None) -> str:
        """
        Detect file type based on path and content.

        Args:
            file_path: Path to the file
            content: File content (optional)

        Returns:
            File type string
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        # Check by extension first
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "react",
            ".tsx": "react-typescript",
            ".java": "java",
            ".cpp": "c++",
            ".cxx": "c++",
            ".cc": "c++",
            ".c": "c",
            ".h": "c-header",
            ".hpp": "cpp-header",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".sql": "sql",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "sass",
            ".less": "less",
            ".xml": "xml",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "config",
            ".conf": "config",
            ".md": "markdown",
            ".rst": "restructuredtext",
            ".txt": "text",
            ".dockerfile": "docker",
            ".gitignore": "git",
            ".gitattributes": "git",
            ".eslintrc": "eslint",
            ".prettierrc": "prettier",
            ".babelrc": "babel",
            ".editorconfig": "editor",
            ".env": "environment",
            ".lock": "lockfile",
        }

        if ext in extension_map:
            return extension_map[ext]

        # Check by filename
        filename = path.name.lower()
        if filename in ["makefile", "dockerfile", "license", "readme", "changelog"]:
            return filename
        elif filename.startswith("makefile."):
            return "makefile"
        elif filename.startswith("dockerfile."):
            return "dockerfile"
        elif filename.endswith(".mk"):
            return "makefile"

        # Check by content if provided
        if content:
            # Look for shebang lines
            first_line = content.split("\n")[0].strip()
            if first_line.startswith("#!"):
                if "python" in first_line:
                    return "python"
                elif "bash" in first_line or "sh" in first_line:
                    return "shell"
                elif "node" in first_line:
                    return "node"
                elif "perl" in first_line:
                    return "perl"
                elif "ruby" in first_line:
                    return "ruby"

            # Look for common patterns
            if "package.json" in filename and '"name"' in content:
                return "npm-package"
            elif "Gemfile" in filename and "gem" in content:
                return "ruby-gem"
            elif "go.mod" in filename and "module" in content:
                return "go-module"

        return "unknown"

    def get_file_dependencies(self, file_path: str, content: str | None = None) -> list[str]:
        """
        Extract dependencies from a file.

        Args:
            file_path: Path to the file
            content: File content (optional)

        Returns:
            List of dependencies
        """
        dependencies = []

        if content is None:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
            except:
                return dependencies

        file_type = self.detect_file_type(file_path, content)
        path = Path(file_path)

        # Extract based on file type
        if file_type == "python":
            dependencies = self._extract_python_dependencies(content, path)
        elif file_type in ["javascript", "typescript", "node"]:
            dependencies = self._extract_node_dependencies(content, path)
        elif file_type == "go":
            dependencies = self._extract_go_dependencies(content, path)
        elif file_type == "ruby":
            dependencies = self._extract_ruby_dependencies(content, path)
        elif file_type == "java":
            dependencies = self._extract_java_dependencies(content, path)
        elif file_type == "docker":
            dependencies = self._extract_docker_dependencies(content, path)

        return dependencies

    def calculate_file_importance(self, file_change: FileChange) -> float:
        """
        Calculate the importance score of a file change.

        Args:
            file_change: FileChange object

        Returns:
            Importance score (0.0 to 1.0)
        """
        base_score = 0.5

        # Category-based importance
        category_scores = {
            FileCategory.CODE: 0.8,
            FileCategory.CONFIG: 0.9,
            FileCategory.DOCUMENTATION: 0.3,
            FileCategory.TESTS: 0.6,
            FileCategory.DATA: 0.7,
            FileCategory.BUILD: 0.5,
            FileCategory.DEPLOYMENT: 0.9,
            FileCategory.UNKNOWN: 0.4,
        }

        category_score = category_scores.get(file_change.category, 0.5)

        # File path patterns that indicate importance
        importance_patterns = [
            (r"(main|index|app|server)\.(py|js|ts|java)$", 0.2),
            (r"(config|settings|environment)\.(json|yaml|yml|ini|toml)$", 0.3),
            (r"(dockerfile|docker-compose)\.(yml|yaml)$", 0.2),
            (r"(package|requirements|go\.mod|pom\.xml|build\.gradle)$", 0.2),
            (r"(\.env|\.env\..+)$", 0.3),
            (r"(security|auth|permission|role)\..+$", 0.2),
            (r"(schema|migration|seed)\..+$", 0.2),
            (r"(router|route|api|controller)\..+$", 0.15),
            (r"(model|entity|schema)\..+$", 0.15),
        ]

        pattern_bonus = 0.0
        for pattern, bonus in importance_patterns:
            if re.search(pattern, file_change.path, re.IGNORECASE):
                pattern_bonus += bonus

        # Change type impact
        change_type_scores = {
            ChangeType.ADDED: 0.1,
            ChangeType.DELETED: 0.15,
            ChangeType.MODIFIED: 0.0,
            ChangeType.RENAMED: 0.05,
            ChangeType.COPIED: 0.05,
        }

        change_type_score = change_type_scores.get(file_change.change_type, 0.0)

        # Volume of changes
        lines_changed = file_change.lines_added + file_change.lines_deleted
        volume_score = min(lines_changed / 1000.0, 0.1)  # Max 0.1 for very large changes

        # Calculate final importance
        importance = base_score + category_score + pattern_bonus + change_type_score + volume_score
        return min(importance, 1.0)

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
                name="Go", extensions=[".go"], category=FileCategory.CODE, test_patterns=[r"_test\.go$", r"/test/"]
            ),
            "rust": LanguageInfo(
                name="Rust",
                extensions=[".rs"],
                category=FileCategory.CODE,
                test_patterns=[r"/tests/", r"#\[cfg\(test\)\]"],
            ),
            "sql": LanguageInfo(name="SQL", extensions=[".sql"], category=FileCategory.DATA),
            "shell": LanguageInfo(
                name="Shell", extensions=[".sh", ".bash", ".zsh", ".fish"], category=FileCategory.CONFIG
            ),
            "yaml": LanguageInfo(name="YAML", extensions=[".yaml", ".yml"], category=FileCategory.CONFIG),
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

    def _detect_language(self, file_path: str, content: str) -> str | None:
        """Detect the programming language of a file."""
        path = Path(file_path)
        ext = path.suffix.lower()

        for lang_name, lang_info in self.language_info.items():
            if ext in lang_info.extensions:
                return lang_name.name

        return None

    def _contains_tests(self, content: str) -> bool:
        """Check if content contains test code."""
        test_indicators = [
            r"\btest\b",
            r"\bdescribe\b",
            r"\bit\b",
            r"\bexpect\b",
            r"\bassert\b",
            r"\bmock\b",
            r"\bstub\b",
            r"\bfixture\b",
            r"\bspec\b",
            r"\bsetup\b",
            r"\bteardown\b",
            r"\bbeforeEach\b",
            r"\bafterEach\b",
            r"\btest_\w+\(",
            r"def test_",
            r"import pytest",
            r"import unittest",
            r"import mocha",
            r"import jest",
            r"require.*test",
            r"#\[test\]",
            r"@Test",
            r"@TestMethod",
        ]

        for pattern in test_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _contains_documentation(self, content: str) -> bool:
        """Check if content contains documentation."""
        doc_indicators = [
            r"/\*\*.*?\*/",  # Multi-line comments
            r'""".*?"""',  # Python docstrings
            r"'''.*?'''",  # Python docstrings
            r"^\s*#.*$",  # Python comments
            r"^\s*//.*$",  # C-style comments
            r"@param\b",
            r"@return\b",
            r"@throws\b",
            r"@example\b",
            r"<summary>",
            r"<remarks>",
            r"<param>",
            r"<returns>",
        ]

        for pattern in doc_indicators:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                return True

        return False

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements from content."""
        imports = []

        # Python imports
        python_patterns = [
            r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
            r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
        ]

        # JavaScript/TypeScript imports
        js_patterns = [
            r'^import\s+.*?\s+from\s+["\']([^"\']+)["\']',
            r'^import\s+["\']([^"\']+)["\']',
            r'require\(["\']([^"\']+)["\']\)',
        ]

        # Java imports
        java_patterns = [r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"]

        all_patterns = python_patterns + js_patterns + java_patterns

        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)

        return list(set(imports))  # Remove duplicates

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function definitions from content."""
        functions = []

        # Function patterns for different languages
        function_patterns = [
            # Python
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            # JavaScript/TypeScript
            r"(?:function\s+|const\s+|let\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:function|\([^)]*\)\s*=>)",
            # Java/C#
            r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:void|[\w<>]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            # Go
            r"func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            # Rust
            r"fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            functions.extend(matches)

        return list(set(functions))

    def _extract_classes(self, content: str) -> list[str]:
        """Extract class definitions from content."""
        classes = []

        # Class patterns for different languages
        class_patterns = [
            # Python
            r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?:",
            # JavaScript/TypeScript
            r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:extends\s+[A-Za-z_][A-Za-z0-9_]*)?\s*\{",
            # Java/C#
            r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)",
            # Go
            r"type\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct\s*\{",
            # Rust
            r"(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{",
            r"(?:pub\s+)?enum\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{",
        ]

        for pattern in class_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            classes.extend(matches)

        return list(set(classes))

    def _analyze_complexity_indicators(self, content: str) -> dict[str, int]:
        """Analyze complexity indicators in file content."""
        indicators = {
            "nested_loops": 0,
            "nested_conditions": 0,
            "functions": 0,
            "classes": 0,
            "lines_of_code": len(content.splitlines()),
            "cyclomatic_complexity_hints": 0,
        }

        # Count nested loops
        nested_loop_patterns = [
            r"for.*for",  # Nested for loops
            r"while.*while",  # Nested while loops
            r"for.*while",  # Mixed nesting
            r"while.*for",  # Mixed nesting
        ]

        for pattern in nested_loop_patterns:
            indicators["nested_loops"] += len(re.findall(pattern, content, re.IGNORECASE))

        # Count nested conditions
        nested_condition_patterns = [
            r"if.*if",  # Nested if statements
            r"if.*elif.*elif",  # Multiple elif chains
        ]

        for pattern in nested_condition_patterns:
            indicators["nested_conditions"] += len(re.findall(pattern, content, re.IGNORECASE))

        # Count cyclomatic complexity hints
        complexity_patterns = [
            r"\bif\b",
            r"\belif\b",
            r"\bfor\b",
            r"\bwhile\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"\?[^:]*:",
            r"\band\b",
            r"\bor\b",
        ]

        for pattern in complexity_patterns:
            indicators["cyclomatic_complexity_hints"] += len(re.findall(pattern, content, re.IGNORECASE))

        return indicators

    def _extract_python_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Python dependencies."""
        dependencies = []

        # pip requirements
        pip_patterns = [r"^([a-zA-Z][a-zA-Z0-9_-]+)==[^\s]+)"]
        for pattern in pip_patterns:
            dependencies.extend(re.findall(pattern, content, re.MULTILINE))

        # Poetry dependencies
        if path.name in ["pyproject.toml", "poetry.lock"]:
            poetry_patterns = [r'^name\s*=\s*"([^"]+)"', r"^([a-zA-Z][a-zA-Z0-9_-]+)\s*="]
            for pattern in poetry_patterns:
                dependencies.extend(re.findall(pattern, content, re.MULTILINE))

        return dependencies

    def _extract_node_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Node.js dependencies."""
        dependencies = []

        if path.name == "package.json":
            # Parse JSON dependencies
            try:
                import json

                data = json.loads(content)
                dependencies.extend(data.get("dependencies", {}).keys())
                dependencies.extend(data.get("devDependencies", {}).keys())
            except:
                pass

        return dependencies

    def _extract_go_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Go dependencies."""
        dependencies = []

        if path.name == "go.mod":
            # Extract module dependencies
            require_pattern = r"require\s+([^\s]+)\s+"
            dependencies.extend(re.findall(require_pattern, content, re.MULTILINE))

        return dependencies

    def _extract_ruby_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Ruby dependencies."""
        dependencies = []

        if path.name in ["Gemfile", "Gemfile.lock"]:
            gem_pattern = r"gem\s+['\"]([^'\"]+)['\"]"
            dependencies.extend(re.findall(gem_pattern, content, re.MULTILINE))

        return dependencies

    def _extract_java_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Java dependencies."""
        dependencies = []

        if path.name in ["pom.xml", "build.gradle"]:
            # Maven dependencies
            if "pom.xml" in path.name:
                artifact_pattern = r"<artifactId>([^<]+)</artifactId>"
                dependencies.extend(re.findall(artifact_pattern, content))
            # Gradle dependencies
            elif "build.gradle" in path.name:
                gradle_pattern = r'implementation\s+["\']([^"\']+)["\']'
                dependencies.extend(re.findall(gradle_pattern, content))

        return dependencies

    def _extract_docker_dependencies(self, content: str, path: Path) -> list[str]:
        """Extract Docker dependencies."""
        dependencies = []

        # FROM statements
        from_pattern = r"FROM\s+([^:\s]+)"
        dependencies.extend(re.findall(from_pattern, content, re.MULTILINE))

        return dependencies
