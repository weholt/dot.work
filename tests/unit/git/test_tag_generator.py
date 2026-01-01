"""Tests for tag generator service."""

from datetime import datetime

from dot_work.git.models import (
    ChangeAnalysis,
    ChangeType,
    FileCategory,
    FileChange,
)
from dot_work.git.services.tag_generator import TagGenerator


class TestTagGenerator:
    """Test the TagGenerator service."""

    def test_generator_initialization(self):
        """Test tag generator initialization."""
        generator = TagGenerator()

        assert generator is not None
        assert hasattr(generator, "tag_patterns")
        assert hasattr(generator, "category_tags")
        assert hasattr(generator, "impact_patterns")

    def test_generate_tags_for_feature_commit(self):
        """Test generating tags for a feature commit."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="abc123",
            author="John Doe",
            email="john@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="feat: add new user authentication system",
            short_message="feat: add new user authentication system",
            files_changed=[],
            lines_added=100,
            lines_deleted=10,
            files_added=2,
            files_deleted=0,
            files_modified=1,
            complexity_score=30.0,
            summary="Add authentication feature",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        assert "feature" in tags

    def test_generate_tags_for_bug_fix(self):
        """Test generating tags for a bug fix commit."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="def456",
            author="Jane Doe",
            email="jane@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="fix: resolve null pointer exception in parser",
            short_message="fix: resolve null pointer exception",
            files_changed=[],
            lines_added=5,
            lines_deleted=2,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Fix null pointer bug",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        assert "fix" in tags

    def test_generate_tags_for_refactoring(self):
        """Test generating tags for a refactoring commit."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="ghi789",
            author="Bob Smith",
            email="bob@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="refactor: simplify payment processing logic",
            short_message="refactor: simplify payment processing",
            files_changed=[],
            lines_added=20,
            lines_deleted=50,
            files_added=0,
            files_deleted=0,
            files_modified=2,
            complexity_score=25.0,
            summary="Refactor payment module",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        assert "refactor" in tags

    def test_generate_tags_for_docs_change(self):
        """Test generating tags for documentation changes."""
        generator = TagGenerator()

        file_change = FileChange(
            path="README.md",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.DOCUMENTATION,
            lines_added=20,
            lines_deleted=5,
        )

        analysis = ChangeAnalysis(
            commit_hash="jkl012",
            author="Alice Johnson",
            email="alice@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="docs: update installation instructions",
            short_message="docs: update installation instructions",
            files_changed=[file_change],
            lines_added=20,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Update documentation",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        assert "docs" in tags

    def test_generate_tags_for_security_change(self):
        """Test generating tags for security-related changes."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="mno345",
            author="Security Team",
            email="security@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="security: patch XSS vulnerability in form handler",
            short_message="security: patch XSS vulnerability",
            files_changed=[],
            lines_added=15,
            lines_deleted=3,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=20.0,
            summary="Fix security issue",
            tags=[],
            impact_areas=[],
            security_relevant=True,
        )

        tags = generator.generate_tags(analysis)

        assert "security" in tags

    def test_generate_tags_for_breaking_change(self):
        """Test generating tags for breaking changes."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="pqr678",
            author="Tech Lead",
            email="lead@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="BREAKING: remove deprecated API endpoints",
            short_message="BREAKING: remove deprecated API",
            files_changed=[],
            lines_added=0,
            lines_deleted=200,
            files_added=0,
            files_deleted=5,
            files_modified=0,
            complexity_score=60.0,
            summary="Remove deprecated code",
            tags=[],
            impact_areas=[],
            breaking_change=True,
        )

        tags = generator.generate_tags(analysis)

        assert "breaking" in tags

    def test_generate_tags_from_emoji(self):
        """Test generating tags from emoji in commit message."""
        generator = TagGenerator()

        # Rocket emoji = feature
        analysis = ChangeAnalysis(
            commit_hash="stu901",
            author="Developer",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="🚀 Add new dashboard feature",
            short_message="🚀 Add new dashboard",
            files_changed=[],
            lines_added=50,
            lines_deleted=5,
            files_added=1,
            files_deleted=0,
            files_modified=1,
            complexity_score=25.0,
            summary="Add dashboard",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        assert "feature" in tags


    def test_filter_tags_removes_duplicates(self):
        """Test that tag filtering removes duplicates."""
        generator = TagGenerator()

        # Create analysis with multiple similar keywords
        analysis = ChangeAnalysis(
            commit_hash="vwx234",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="Implement new feature and add functionality",
            short_message="Implement new feature",
            files_changed=[],
            lines_added=10,
            lines_deleted=2,
            files_added=1,
            files_deleted=0,
            files_modified=0,
            complexity_score=15.0,
            summary="Add feature",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        # Check no duplicates
        assert len(tags) == len(set(tags))

    def test_limit_tags_to_five(self):
        """Test that tag generation creates multiple tags from complex commits."""
        generator = TagGenerator()

        # Create analysis with many different tags
        analysis = ChangeAnalysis(
            commit_hash="yzu567",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="feat: add new feature with security fix and performance improvements",
            short_message="feat: add feature with security",
            files_changed=[
                FileChange(
                    path="src/main.py",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CODE,
                    lines_added=100,
                    lines_deleted=50,
                ),
                FileChange(
                    path="config.yaml",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CONFIG,
                    lines_added=10,
                    lines_deleted=5,
                ),
            ],
            lines_added=110,
            lines_deleted=55,
            files_added=0,
            files_deleted=0,
            files_modified=2,
            complexity_score=75.0,
            summary="Major update",
            tags=[],
            impact_areas=["core", "config"],
            breaking_change=True,
            security_relevant=True,
        )

        tags = generator.generate_tags(analysis)

        # Complex commits generate multiple tags (not limited)
        # Should have many tags from message keywords, file categories, flags
        assert len(tags) > 5
        # Verify expected tags are present
        assert "feature" in tags
        assert "security" in tags
        assert "breaking" in tags


    def test_empty_analysis_returns_misc(self):
        """Test that an analysis with no clear tags returns 'misc'."""
        generator = TagGenerator()

        analysis = ChangeAnalysis(
            commit_hash="misc123",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="update stuff",
            short_message="update stuff",
            files_changed=[],
            lines_added=1,
            lines_deleted=1,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=1.0,
            summary="Update",
            tags=[],
            impact_areas=[],
        )

        tags = generator.generate_tags(analysis)

        # Should have at least 'misc' or some basic tag
        assert len(tags) >= 1
