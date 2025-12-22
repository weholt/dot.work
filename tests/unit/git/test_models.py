"""Tests for data models."""

import pytest
from datetime import datetime

from dot_work.git.models import (
    ChangeAnalysis,
    ComparisonResult,
    ComparisonDiff,
    CommitInfo,
    ContributorStats,
    AnalysisConfig,
    FileChange,
    FileCategory,
    ChangeType,
    ComparisonMetadata,
    CacheEntry,
    AnalysisError,
)


class TestFileChange:
    """Test the FileChange model."""

    def test_file_change_creation(self):
        """Test basic file change creation."""
        file_change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CODE,
            lines_added=10,
            lines_deleted=5
        )

        assert file_change.path == "src/main.py"
        assert file_change.change_type == ChangeType.MODIFIED
        assert file_change.category == FileCategory.CODE
        assert file_change.lines_added == 10
        assert file_change.lines_deleted == 5
        assert file_change.binary_file is False

    def test_file_change_rename(self):
        """Test file change with rename."""
        file_change = FileChange(
            path="src/new_main.py",
            old_path="src/old_main.py",
            change_type=ChangeType.RENAMED,
            category=FileCategory.CODE
        )

        assert file_change.path == "src/new_main.py"
        assert file_change.old_path == "src/old_main.py"
        assert file_change.change_type == ChangeType.RENAMED

    def test_file_change_binary(self):
        """Test binary file change."""
        file_change = FileChange(
            path="data/image.png",
            change_type=ChangeType.ADDED,
            binary_file=True
        )

        assert file_change.binary_file is True


class TestCommitInfo:
    """Test the CommitInfo model."""

    def test_commit_info_creation(self):
        """Test basic commit info creation."""
        timestamp = datetime.now()
        commit_info = CommitInfo(
            hash="abc123def456",
            short_hash="abc123de",
            author="John Doe",
            email="john@example.com",
            timestamp=timestamp,
            message="Add new feature",
            branch="main",
            tags=["v1.0.0", "release"]
        )

        assert commit_info.hash == "abc123def456"
        assert commit_info.short_hash == "abc123de"
        assert commit_info.author == "John Doe"
        assert commit_info.email == "john@example.com"
        assert commit_info.timestamp == timestamp
        assert commit_info.message == "Add new feature"
        assert commit_info.branch == "main"
        assert len(commit_info.tags) == 2


class TestChangeAnalysis:
    """Test the ChangeAnalysis model."""

    def test_change_analysis_creation(self):
        """Test basic change analysis creation."""
        timestamp = datetime.now()
        file_change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CODE,
            lines_added=10,
            lines_deleted=5
        )

        analysis = ChangeAnalysis(
            commit_hash="abc123def456",
            author="John Doe",
            email="john@example.com",
            timestamp=timestamp,
            branch="main",
            message="Add new feature",
            short_message="Add new feature",
            files_changed=[file_change],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=25.5,
            summary="Adds a new feature to the application",
            tags=["feature", "enhancement"],
            impact_areas=["core", "ui"]
        )

        assert analysis.commit_hash == "abc123def456"
        assert analysis.author == "John Doe"
        assert len(analysis.files_changed) == 1
        assert analysis.complexity_score == 25.5
        assert analysis.tags == ["feature", "enhancement"]
        assert analysis.impact_areas == ["core", "ui"]
        assert analysis.breaking_change is False
        assert analysis.security_relevant is False

    def test_change_analysis_with_breaking_change(self):
        """Test change analysis with breaking change."""
        analysis = ChangeAnalysis(
            commit_hash="def456abc123",
            author="Jane Doe",
            email="jane@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="BREAKING: Remove deprecated API",
            short_message="BREAKING: Remove deprecated API",
            files_changed=[],
            lines_added=0,
            lines_deleted=100,
            files_added=0,
            files_deleted=1,
            files_modified=0,
            complexity_score=45.0,
            summary="Removes deprecated API endpoints",
            tags=["breaking", "cleanup"],
            impact_areas=["api"],
            breaking_change=True
        )

        assert analysis.breaking_change is True
        assert analysis.complexity_score == 45.0


class TestContributorStats:
    """Test the ContributorStats model."""

    def test_contributor_stats_creation(self):
        """Test basic contributor stats creation."""
        first_commit = datetime(2023, 1, 1)
        last_commit = datetime(2023, 12, 31)

        stats = ContributorStats(
            name="John Doe",
            email="john@example.com",
            commits=50,
            lines_added=5000,
            lines_deleted=1000,
            files_touched=100,
            complexity_contribution=250.5,
            first_commit=first_commit,
            last_commit=last_commit
        )

        assert stats.name == "John Doe"
        assert stats.email == "john@example.com"
        assert stats.commits == 50
        assert stats.lines_added == 5000
        assert stats.lines_deleted == 1000
        assert stats.files_touched == 100
        assert stats.complexity_contribution == 250.5
        assert stats.first_commit == first_commit
        assert stats.last_commit == last_commit


class TestAnalysisConfig:
    """Test the AnalysisConfig model."""

    def test_analysis_config_defaults(self):
        """Test analysis config with default values."""
        config = AnalysisConfig()

        assert config.use_llm is False
        assert config.llm_provider == "openai"
        assert config.complexity_threshold == 50.0
        assert config.max_commits == 1000
        assert config.include_binary_files is False
        assert config.output_format == "json"
        assert config.cache_ttl_hours == 24

    def test_analysis_config_custom(self):
        """Test analysis config with custom values."""
        from pathlib import Path

        config = AnalysisConfig(
            repo_path=Path("/custom/repo"),
            use_llm=True,
            llm_provider="anthropic",
            complexity_threshold=30.0,
            max_commits=500,
            output_format="yaml"
        )

        assert str(config.repo_path) == "/custom/repo"
        assert config.use_llm is True
        assert config.llm_provider == "anthropic"
        assert config.complexity_threshold == 30.0
        assert config.max_commits == 500
        assert config.output_format == "yaml"


class TestComparisonMetadata:
    """Test the ComparisonMetadata model."""

    def test_comparison_metadata_creation(self):
        """Test basic comparison metadata creation."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        metadata = ComparisonMetadata(
            from_ref="main",
            to_ref="feature-branch",
            from_commit_hash="abc123",
            to_commit_hash="def456",
            date_range=(start_date, end_date),
            total_commits=25,
            total_files_changed=50,
            total_lines_added=1000,
            total_lines_deleted=200,
            total_complexity=125.5,
            time_span_days=30,
            branches_involved=["main", "feature-branch"]
        )

        assert metadata.from_ref == "main"
        assert metadata.to_ref == "feature-branch"
        assert metadata.from_commit_hash == "abc123"
        assert metadata.to_commit_hash == "def456"
        assert metadata.date_range == (start_date, end_date)
        assert metadata.total_commits == 25
        assert metadata.total_files_changed == 50
        assert metadata.total_lines_added == 1000
        assert metadata.total_lines_deleted == 200
        assert metadata.total_complexity == 125.5
        assert metadata.time_span_days == 30
        assert metadata.branches_involved == ["main", "feature-branch"]


class TestComparisonResult:
    """Test the ComparisonResult model."""

    def test_comparison_result_creation(self):
        """Test basic comparison result creation."""
        metadata = ComparisonMetadata(
            from_ref="main",
            to_ref="feature-branch",
            from_commit_hash="abc123",
            to_commit_hash="def456",
            date_range=(datetime.now(), datetime.now()),
            total_commits=5,
            total_files_changed=10,
            total_lines_added=100,
            total_lines_deleted=20,
            total_complexity=50.0,
            time_span_days=5,
            branches_involved=["main", "feature-branch"]
        )

        analysis = ChangeAnalysis(
            commit_hash="abc123",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime.now(),
            branch="feature-branch",
            message="Test commit",
            short_message="Test commit",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=15.0,
            summary="Test commit summary",
            tags=["test"],
            impact_areas=["core"]
        )

        result = ComparisonResult(
            metadata=metadata,
            commits=[analysis],
            contributors={},
            aggregate_summary="Test summary",
            highlights=["Test highlight"],
            risk_assessment="Low risk",
            recommendations=["Test recommendation"],
            file_categories={FileCategory.CODE: 5},
            complexity_distribution={"0-20": 2, "20-40": 3},
            top_complex_files=[]
        )

        assert result.metadata == metadata
        assert len(result.commits) == 1
        assert result.commits[0] == analysis
        assert result.aggregate_summary == "Test summary"
        assert result.highlights == ["Test highlight"]
        assert result.risk_assessment == "Low risk"
        assert result.recommendations == ["Test recommendation"]
        assert result.file_categories[FileCategory.CODE] == 5
        assert result.complexity_distribution["0-20"] == 2
        assert result.complexity_distribution["20-40"] == 3


class TestComparisonDiff:
    """Test the ComparisonDiff model."""

    def test_comparison_diff_creation(self):
        """Test basic comparison diff creation."""
        diff = ComparisonDiff(
            commit_a_hash="abc123",
            commit_b_hash="def456",
            similarity_score=0.75,
            differences=["Different file modified"],
            common_themes=["Both modify core functionality"],
            impact_description="Medium impact changes",
            regression_risk="Low regression risk",
            migration_notes=["Update dependent code"]
        )

        assert diff.commit_a_hash == "abc123"
        assert diff.commit_b_hash == "def456"
        assert diff.similarity_score == 0.75
        assert diff.differences == ["Different file modified"]
        assert diff.common_themes == ["Both modify core functionality"]
        assert diff.impact_description == "Medium impact changes"
        assert diff.regression_risk == "Low regression risk"
        assert diff.migration_notes == ["Update dependent code"]


class TestCacheEntry:
    """Test the CacheEntry model."""

    def test_cache_entry_creation(self):
        """Test basic cache entry creation."""
        timestamp = datetime.now()
        entry = CacheEntry(
            key="test_key",
            data={"test": "data"},
            timestamp=timestamp,
            ttl_hours=24
        )

        assert entry.key == "test_key"
        assert entry.data == {"test": "data"}
        assert entry.timestamp == timestamp
        assert entry.ttl_hours == 24

    def test_cache_entry_expired(self):
        """Test cache entry expiration."""
        from datetime import timedelta

        # Non-expired entry
        recent_timestamp = datetime.now() - timedelta(hours=12)
        recent_entry = CacheEntry(
            key="recent_key",
            data={"test": "data"},
            timestamp=recent_timestamp
        )
        assert recent_entry.is_expired() is False

        # Expired entry
        old_timestamp = datetime.now() - timedelta(hours=25)
        old_entry = CacheEntry(
            key="old_key",
            data={"test": "data"},
            timestamp=old_timestamp
        )
        assert old_entry.is_expired() is True


class TestAnalysisError:
    """Test the AnalysisError model."""

    def test_analysis_error_creation(self):
        """Test basic analysis error creation."""
        timestamp = datetime.now()
        error = AnalysisError(
            error_type="ParseError",
            message="Failed to parse commit",
            commit_hash="abc123",
            file_path="src/main.py",
            timestamp=timestamp,
            stack_trace="Traceback..."
        )

        assert error.error_type == "ParseError"
        assert error.message == "Failed to parse commit"
        assert error.commit_hash == "abc123"
        assert error.file_path == "src/main.py"
        assert error.timestamp == timestamp
        assert error.stack_trace == "Traceback..."

    def test_analysis_error_minimal(self):
        """Test analysis error with minimal data."""
        error = AnalysisError(
            error_type="ValidationError",
            message="Invalid data"
        )

        assert error.error_type == "ValidationError"
        assert error.message == "Invalid data"
        assert error.commit_hash is None
        assert error.file_path is None
        assert isinstance(error.timestamp, datetime)


class TestEnums:
    """Test enum values."""

    def test_change_type_values(self):
        """Test ChangeType enum values."""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.DELETED.value == "deleted"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.RENAMED.value == "renamed"
        assert ChangeType.COPIED.value == "copied"

    def test_file_category_values(self):
        """Test FileCategory enum values."""
        assert FileCategory.CODE.value == "code"
        assert FileCategory.TESTS.value == "tests"
        assert FileCategory.CONFIG.value == "config"
        assert FileCategory.DOCUMENTATION.value == "documentation"
        assert FileCategory.DATA.value == "data"
        assert FileCategory.BUILD.value == "build"
        assert FileCategory.DEPLOYMENT.value == "deployment"
        assert FileCategory.UNKNOWN.value == "unknown"
