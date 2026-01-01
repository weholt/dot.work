"""Tag generation for git commits based on analysis."""

from dot_work.git.models import ChangeAnalysis, ChangeType, FileCategory


class TagGenerator:
    """Generates tags for git commits based on analysis."""

    def __init__(self):
        # Common tag patterns and their associated keywords
        self.tag_patterns = {
            "feature": [
                "add",
                "implement",
                "create",
                "build",
                "new",
                "introduce",
                "feature",
                "enhancement",
                "improve",
                "upgrade",
                "extend",
            ],
            "fix": [
                "fix",
                "bug",
                "error",
                "issue",
                "problem",
                "resolve",
                "patch",
                "correct",
                "repair",
                "debug",
                "hotfix",
                "solve",
            ],
            "refactor": [
                "refactor",
                "restructure",
                "reorganize",
                "cleanup",
                "simplify",
                "optimize",
                "improve",
                "rework",
                "streamline",
                "consolidate",
            ],
            "test": [
                "test",
                "testing",
                "spec",
                "assert",
                "mock",
                "fixture",
                "coverage",
                "unittest",
                "integration",
                "e2e",
                "tdd",
            ],
            "docs": [
                "doc",
                "documentation",
                "readme",
                "guide",
                "manual",
                "comment",
                "wiki",
                "changelog",
                "release",
                "notes",
            ],
            "security": [
                "security",
                "auth",
                "authentication",
                "authorization",
                "permission",
                "vulnerability",
                "patch",
                "encrypt",
                "secure",
                "protect",
                "token",
            ],
            "performance": [
                "performance",
                "optimize",
                "speed",
                "fast",
                "slow",
                "memory",
                "cache",
                "latency",
                "benchmark",
                "profile",
                "improve",
                "enhance",
            ],
            "ui": [
                "ui",
                "frontend",
                "interface",
                "user",
                "visual",
                "design",
                "component",
                "view",
                "page",
                "layout",
                "style",
                "css",
            ],
            "api": [
                "api",
                "endpoint",
                "route",
                "controller",
                "handler",
                "service",
                "rest",
                "graphql",
                "websocket",
                "request",
                "response",
            ],
            "database": [
                "database",
                "db",
                "sql",
                "migration",
                "schema",
                "model",
                "query",
                "table",
                "index",
                "seed",
                "fixture",
                "entity",
            ],
            "config": [
                "config",
                "configuration",
                "setting",
                "environment",
                "env",
                "deploy",
                "deployment",
                "infrastructure",
                "provision",
            ],
            "ci/cd": [
                "ci",
                "cd",
                "pipeline",
                "workflow",
                "automation",
                "build",
                "test",
                "deploy",
                "release",
                "integration",
                "continuous",
            ],
            "dependency": [
                "dependency",
                "package",
                "library",
                "module",
                "import",
                "require",
                "install",
                "update",
                "upgrade",
                "version",
            ],
            "breaking": [
                "breaking",
                "deprecate",
                "remove",
                "delete",
                "replace",
                "migration",
                "incompatible",
                "major",
                "semver-major",
            ],
            "chore": [
                "chore",
                "maintenance",
                "update",
                "upgrade",
                "patch",
                "version",
                "bump",
                "format",
                "lint",
                "style",
                "fixup",
            ],
            "merge": ["merge", "merge request", "pull request", "pr", "feature branch"],
            "wip": ["wip", "work in progress", "draft", "todo", "fixme", "hack"],
        }

        # File category to tag mappings
        self.category_tags = {
            FileCategory.CODE: ["code"],
            FileCategory.TESTS: ["test"],
            FileCategory.CONFIG: ["config", "dependency"],
            FileCategory.DOCUMENTATION: ["docs"],
            FileCategory.DATA: ["data", "database"],
            FileCategory.BUILD: ["build", "ci/cd"],
            FileCategory.DEPLOYMENT: ["deployment", "config"],
            FileCategory.UNKNOWN: [],
        }

        # High-impact file patterns
        self.impact_patterns = {
            "security": [
                "auth",
                "password",
                "token",
                "key",
                "secret",
                "encryption",
                "permission",
                "role",
                "access",
                "login",
                "register",
                "session",
            ],
            "database": [
                "migration",
                "schema",
                "seed",
                "fixture",
                "model",
                "entity",
                "query",
                "table",
                "index",
                "sql",
                "database",
                "db",
            ],
            "api": [
                "route",
                "endpoint",
                "controller",
                "handler",
                "middleware",
                "api",
                "rest",
                "graphql",
                "websocket",
                "request",
                "response",
            ],
            "infrastructure": [
                "docker",
                "kubernetes",
                "deploy",
                "ci",
                "cd",
                "pipeline",
                "infrastructure",
                "provision",
                "terraform",
                "ansible",
            ],
            "ui": [
                "component",
                "view",
                "page",
                "layout",
                "style",
                "css",
                "frontend",
                "ui",
                "interface",
                "react",
                "vue",
                "angular",
            ],
        }

        # Complexity-based tags
        self.complexity_tags = {
            "low": [],
            "medium": [],
            "high": ["refactor", "complex", "architecture"],
            "very_high": ["breaking", "major", "infrastructure"],
            "critical": ["breaking", "security", "critical", "emergency"],
        }

    def generate_tags(self, analysis: ChangeAnalysis) -> list[str]:
        """
        Generate tags for a commit analysis.

        Args:
            analysis: ChangeAnalysis object

        Returns:
            List of tags
        """
        tags = set()

        # Generate tags from commit message
        message_tags = self._extract_message_tags(analysis.message)
        tags.update(message_tags)

        # Generate tags from file changes
        file_tags = self._extract_file_tags(analysis.files_changed)
        tags.update(file_tags)

        # Generate tags from impact areas
        impact_tags = self._extract_impact_tags(analysis.impact_areas)
        tags.update(impact_tags)

        # Generate complexity-based tags
        complexity_tags = self._extract_complexity_tags(analysis.complexity_score)
        tags.update(complexity_tags)

        # Generate special tags for breaking changes and security
        if analysis.breaking_change:
            tags.update(["breaking", "deprecation"])

        if analysis.security_relevant:
            tags.add("security")

        # Generate emoji-based tags
        emoji_tags = self._extract_emoji_tags(analysis.message)
        tags.update(emoji_tags)

        # Filter and finalize tags
        final_tags = self._filter_tags(tags)

        # Ensure we have some tags
        if not final_tags:
            final_tags = {"misc"}

        return list(final_tags)

    def _extract_message_tags(self, message: str) -> set[str]:
        """Extract tags from commit message."""
        tags = set()
        message_lower = message.lower()

        for tag, keywords in self.tag_patterns.items():
            for keyword in keywords:
                if keyword in message_lower:
                    tags.add(tag)
                    break  # Only add the tag once per category

        return tags

    def _extract_file_tags(self, files_changed) -> set[str]:
        """Extract tags from changed files."""
        tags = set()

        # Category-based tags
        categories = {f.category for f in files_changed}
        for category in categories:
            tags.update(self.category_tags.get(category, []))

        # Path-based impact tags
        for file_change in files_changed:
            path = file_change.path.lower()

            for impact_tag, patterns in self.impact_patterns.items():
                if any(pattern in path for pattern in patterns):
                    tags.add(impact_tag)

            # Change type tags
            if file_change.change_type == ChangeType.ADDED:
                tags.add("add")
            elif file_change.change_type == ChangeType.DELETED:
                tags.add("remove")
            elif file_change.change_type == ChangeType.RENAMED:
                tags.add("refactor")
            elif file_change.change_type == ChangeType.MODIFIED:
                # Change type is already reflected in other tags
                pass

        return tags

    def _extract_impact_tags(self, impact_areas: list[str]) -> set[str]:
        """Extract tags from impact areas."""
        tags = set()

        # Normalize impact areas
        normalized_areas = [area.lower() for area in impact_areas]

        for area in normalized_areas:
            if "auth" in area or "security" in area:
                tags.add("security")
            if "api" in area:
                tags.add("api")
            if "ui" in area or "frontend" in area:
                tags.add("ui")
            if "database" in area or "db" in area:
                tags.add("database")
            if "config" in area:
                tags.add("config")
            if "deploy" in area:
                tags.add("deployment")

        return tags

    def _extract_complexity_tags(self, complexity_score: float) -> set[str]:
        """Extract tags based on complexity score."""
        tags = set()

        if complexity_score >= 80:
            tags.update(self.complexity_tags["critical"])
        elif complexity_score >= 60:
            tags.update(self.complexity_tags["very_high"])
        elif complexity_score >= 40:
            tags.update(self.complexity_tags["high"])
        elif complexity_score >= 20:
            tags.update(self.complexity_tags["medium"])
        else:
            tags.update(self.complexity_tags["low"])

        return tags

    def _extract_emoji_tags(self, message: str) -> set[str]:
        """Extract semantic tags from emoji in commit message."""
        emoji_to_tag = {
            "🚀": "feature",  # Rocket - new feature
            "✨": "enhancement",  # Sparkles - improvement
            "🐛": "fix",  # Bug - bug fix
            "💥": "breaking",  # Collision explosion - breaking change
            "🔥": "urgent",  # Fire - urgent change
            "⚡": "performance",  # Lightning - performance improvement
            "🎉": "release",  # Party popper - release
            "🔒": "security",  # Lock - security change
            "🔑": "security",  # Key - authentication/security
            "🔧": "refactor",  # Wrench - refactoring
            "📝": "docs",  # Memo - documentation
            "🧪": "test",  # Test tube - testing
            "♻️": "refactor",  # Recycle - refactoring
            "♿": "accessibility",  # Wheelchair - accessibility
            "🌐": "i18n",  # Globe - internationalization
            "🏗️": "architecture",  # Building - architectural change
            "🎨": "ui",  # Palette - UI/styling
            "📊": "data",  # Bar chart - data/analytics
            "🔬": "analysis",  # Microscope - analysis/code review
            "🚨": "urgent",  # Warning - urgent fix
            "🆙": "security",  # Police car - security update
            "🔄": "refactor",  # Refresh - refactoring
            "⏪": "revert",  # Undo button - revert
            "⏭️": "skip",  # Next button - skip test/validation
            "⏯️": "play",  # Play button - enabling feature
            "⏹️": "pause",  # Pause button - disabling feature
            "⏸️": "stop",  # Square button - stopping process
            "⚠️": "warning",  # Warning sign - warning
            "❗": "breaking",  # Heavy exclamation - breaking change
            "❓": "question",  # Question mark - investigation/research
            "✅": "test",  # Check mark - test passing
            "❌": "fix",  # Cross mark - fix/bug fix
            "➕": "feature",  # Plus - addition/feature
            "➖": "remove",  # Minus - removal
            "🔀": "merge",  # Twisted right arrows - merge
            "🔁": "sync",  # Refresh - sync/update
            "🔂": "repeat",  # Repeat button - repeat operation
        }

        tags = set()
        for emoji, tag in emoji_to_tag.items():
            if emoji in message:
                tags.add(tag)

        return tags

    def _filter_tags(self, tags: set[str]) -> set[str]:
        """Filter and prioritize tags."""
        filtered = set()

        # Remove duplicate or redundant tags
        redundant_mappings = {
            "enhancement": "feature",
            "implement": "feature",
            "create": "feature",
            "bug": "fix",
            "patch": "fix",
            "hotfix": "fix",
            "error": "fix",
            "debug": "fix",
            "optimize": "performance",
            "speed": "performance",
            "refactor": "refactor",
            "cleanup": "refactor",
            "reorganize": "refactor",
            "documentation": "docs",
            "comment": "docs",
            "guide": "docs",
            "manual": "docs",
            "note": "docs",
        }

        for tag in tags:
            # Skip empty or invalid tags
            if not tag or len(tag.strip()) == 0:
                continue

            # Use preferred mapping for redundant tags
            canonical_tag = redundant_mappings.get(tag.lower(), tag.lower())
            filtered.add(canonical_tag)

        # Ensure we don't have too many tags
        if len(filtered) > 5:
            # Keep the most important ones
            priority_tags = [
                "breaking",
                "security",
                "critical",
                "feature",
                "fix",
                "refactor",
                "performance",
                "ui",
                "api",
                "database",
                "docs",
            ]

            # Keep priority tags first
            prioritized = [tag for tag in priority_tags if tag in filtered]

            # Add remaining tags up to limit
            remaining = [tag for tag in filtered if tag not in prioritized]
            final_tags = prioritized + remaining[: 5 - len(prioritized)]

            return set(final_tags)

        return filtered
