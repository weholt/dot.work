"""Tests for GitAnalysisService core business logic."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dot_work.git.models import (
    AnalysisConfig,
    ChangeAnalysis,
    ChangeType,
    FileCategory,
    FileChange,
)
from dot_work.git.services.git_service import GitAnalysisService


class TestGitAnalysisServiceInit:
    """Test GitAnalysisService initialization."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_init_with_config(self, mock_repo_class):
        """Test service initialization with config."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        assert service.config == config
        mock_repo_class.assert_called_once_with(Path("/test/repo"))

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_init_invalid_repo_raises_error(self, mock_repo_class):
        """Test that invalid repo path raises ValueError."""
        mock_repo_class.side_effect = Exception("Not a git repo")

        config = AnalysisConfig(repo_path=Path("/invalid/repo"))
        with pytest.raises(ValueError, match="Invalid git repository"):
            GitAnalysisService(config)


class TestAnalyzeCommit:
    """Test commit analysis logic."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_commit_returns_change_analysis(self, mock_repo_class):
        """Test that analyze_commit returns a ChangeAnalysis object."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        # Mock the commit
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"
        mock_commit.message = "Test commit\n\nBody here"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.committed_date = 1704067200  # 2024-01-01
        mock_commit.parents = []

        # Mock diff to return empty list
        mock_commit.diff.return_value = []

        mock_repo.commit.return_value = mock_commit
        mock_repo.branches = []

        result = service.analyze_commit("abc123")

        assert isinstance(result, ChangeAnalysis)
        assert result.commit_hash == "abc123"
        assert result.author == "Test Author"
        assert result.message == "Test commit\n\nBody here"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_commit_invalid_hash_raises_error(self, mock_repo_class):
        """Test that invalid commit hash raises ValueError."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.commit.side_effect = Exception("Invalid commit")

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        with pytest.raises(ValueError, match="Invalid commit hash"):
            service.analyze_commit("invalid")


class TestGetCommitBranch:
    """Test commit to branch mapping."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_get_commit_branch_from_cache(self, mock_repo_class):
        """Test that branch lookup uses cache."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        # Set up cache
        service._commit_to_branch_cache = {"abc123": "main", "def456": "feature"}

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"

        result = service._get_commit_branch(mock_commit)

        assert result == "main"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_get_commit_branch_unknown_when_not_cached(self, mock_repo_class):
        """Test that unknown branch is returned when not in cache."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        service._commit_to_branch_cache = {}

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"

        result = service._get_commit_branch(mock_commit)

        assert result == "unknown"


class TestBuildCommitBranchMapping:
    """Test commit-to-branch mapping cache building."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_build_mapping_single_branch(self, mock_repo_class):
        """Test mapping with a single branch."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        # Mock repo with one branch
        mock_branch = MagicMock()
        mock_branch.name = "main"

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"

        service.repo = mock_repo
        mock_repo.branches = [mock_branch]
        mock_repo.iter_commits.return_value = [mock_commit]

        result = service._build_commit_branch_mapping()

        assert result == {"abc123": "main"}

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_build_mapping_multiple_branches(self, mock_repo_class):
        """Test mapping with multiple branches and commits."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        # Mock two branches with different commits
        mock_main = MagicMock()
        mock_main.name = "main"

        mock_feature = MagicMock()
        mock_feature.name = "feature/test"

        commit1 = MagicMock()
        commit1.hexsha = "abc123"

        commit2 = MagicMock()
        commit2.hexsha = "def456"

        service.repo = mock_repo
        mock_repo.branches = [mock_main, mock_feature]

        def iter_commits_branch(branch):
            if branch == "main":
                return [commit1]
            return [commit2]

        mock_repo.iter_commits.side_effect = iter_commits_branch

        result = service._build_commit_branch_mapping()

        assert result == {"abc123": "main", "def456": "feature/test"}


class TestGetCommitsBetweenRefs:
    """Test getting commits between git references."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_get_commits_linear_history(self, mock_repo_class):
        """Test getting commits in a linear history."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        # Mock commits
        mock_commit1 = MagicMock()
        mock_commit2 = MagicMock()
        mock_commit3 = MagicMock()

        service.repo = mock_repo
        mock_repo.iter_commits.return_value = [
            mock_commit3,
            mock_commit2,
            mock_commit1,
        ]

        result = service._get_commits_between_refs("main~2", "main")

        assert len(result) == 3
        # Verify order (newest first)
        assert result[0] == mock_commit3
        assert result[1] == mock_commit2
        assert result[2] == mock_commit1


class TestExtractShortMessage:
    """Test short message extraction from commit messages."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_extract_title_only(self, mock_repo_class):
        """Test extraction with title only."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        result = service._extract_short_message("Fix bug in parser")

        assert result == "Fix bug in parser"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_extract_with_body(self, mock_repo_class):
        """Test extraction with title and body."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        result = service._extract_short_message("feat: add new feature\n\nThis is a long description.")

        assert result == "feat: add new feature"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_extract_returns_first_line_only(self, mock_repo_class):
        """Test that only the first line is returned."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        message = "First line\nSecond line\nThird line"
        result = service._extract_short_message(message)

        assert result == "First line"


class TestIdentifyImpactAreas:
    """Test identification of impact areas from file changes."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_identify_impact_from_path(self, mock_repo_class):
        """Test impact identification from file paths."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = [
            FileChange(
                path="src/main.py",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.CODE,
                lines_added=50,
                lines_deleted=10,
            )
        ]

        result = service._identify_impact_areas(files)

        assert len(result) > 0
        assert "src" in result

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_identify_security_impact(self, mock_repo_class):
        """Test security impact identification."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = [
            FileChange(
                path="src/auth.py",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.CODE,
                lines_added=10,
                lines_deleted=0,
            )
        ]

        result = service._identify_impact_areas(files)

        assert "security" in result

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_identify_api_impact(self, mock_repo_class):
        """Test API impact identification."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = [
            FileChange(
                path="api/routes.py",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.API,
                lines_added=20,
                lines_deleted=5,
            )
        ]

        result = service._identify_impact_areas(files)

        assert "api" in result


class TestIsBreakingChange:
    """Test breaking change detection."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_breaking_change_keywords(self, mock_repo_class):
        """Test detection of breaking change keywords."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = []

        # Test various breaking change indicators
        breaking_messages = [
            "BREAKING CHANGE: API migration",
            "feat!: remove deprecated method",
        ]

        for msg in breaking_messages:
            result = service._is_breaking_change(msg, files)
            assert result is True, f"Should detect breaking change in: {msg}"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_non_breaking_change(self, mock_repo_class):
        """Test that normal commits are not flagged as breaking."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = []
        normal_message = "feat: add new feature"

        result = service._is_breaking_change(normal_message, files)

        assert result is False

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_breaking_migration_file(self, mock_repo_class):
        """Test breaking change detection for migration files."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = [
            FileChange(
                path="db/migration/001_add_users.py",
                change_type=ChangeType.ADDED,
                category=FileCategory.DATABASE,
                lines_added=50,
                lines_deleted=0,
            )
        ]

        result = service._is_breaking_change("Add user table", files)

        assert result is True


class TestIsSecurityRelevant:
    """Test security relevance detection."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_security_keywords_detected(self, mock_repo_class):
        """Test detection of security-related commits."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        files = []

        security_messages = [
            "Fix security vulnerability in authentication",
            "Update dependencies for CVE-2024-1234",
            "security: add rate limiting",
        ]

        for msg in security_messages:
            result = service._is_security_relevant(msg, files)
            assert result is True, f"Should detect security in: {msg}"

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_security_file_changes(self, mock_repo_class):
        """Test detection of security-relevant file changes."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        security_files = [
            FileChange(
                path="src/auth.py",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.CODE,
                lines_added=10,
                lines_deleted=0,
            ),
            FileChange(
                path="config/secrets.yaml",
                change_type=ChangeType.ADDED,
                category=FileCategory.CONFIG,
                lines_added=5,
                lines_deleted=0,
            ),
        ]

        for file_change in security_files:
            result = service._is_security_relevant("Update config", [file_change])
            assert result is True


class TestCalculateCommitSimilarity:
    """Test commit similarity calculation."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_identical_commits_high_similarity(self, mock_repo_class):
        """Test that identical commits have high similarity."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc123",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Fix bug",
            short_message="Fix bug",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Fix",
            tags=["bugfix"],
            impact_areas=["code"],
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def456",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Fix bug",
            short_message="Fix bug",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Fix",
            tags=["bugfix"],
            impact_areas=["code"],
        )

        result = service._calculate_commit_similarity(analysis_a, analysis_b)

        # High similarity for identical tags (average of tag and file similarity)
        # With identical tags but no files: (1.0 + 0.0) / 2 = 0.5
        assert result == 0.5

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_different_commits_low_similarity(self, mock_repo_class):
        """Test that different commits have low similarity."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc123",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Add new feature",
            short_message="Add new feature",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Add",
            tags=["feature"],
            impact_areas=["code"],
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def456",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Update documentation",
            short_message="Update documentation",
            files_changed=[],
            lines_added=20,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=3.0,
            summary="Docs",
            tags=["docs"],
            impact_areas=["documentation"],
        )

        result = service._calculate_commit_similarity(analysis_a, analysis_b)

        # Low similarity for different tags
        assert result == 0.0


class TestGenerateBasicSummary:
    """Test basic summary generation."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_summary_includes_key_info(self, mock_repo_class):
        """Test that summary includes commit key information."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis = ChangeAnalysis(
            commit_hash="abc123",
            author="Test Author",
            email="test@example.com",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            branch="main",
            message="Fix bug in parser\n\nThis fixes the parsing issue",
            short_message="Fix bug in parser",
            files_changed=[
                FileChange(
                    path="src/parser.py",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CODE,
                    lines_added=10,
                    lines_deleted=5,
                )
            ],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="",
            tags=["bugfix"],
            impact_areas=["parser", "code"],
        )

        result = service._generate_basic_summary(analysis)

        assert "Changed 1 files" in result
        assert "added 10 lines" in result
        assert "deleted 5 lines" in result


class TestCalculateFileCategories:
    """Test file category calculation."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_categories_aggregation(self, mock_repo_class):
        """Test that file categories are properly aggregated."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        commits = [
            ChangeAnalysis(
                commit_hash="abc",
                author="Author",
                email="author@example.com",
                timestamp=datetime(2024, 1, 1, 0, 0, 0),
                branch="main",
                message="Add code",
                short_message="Add code",
                files_changed=[
                    FileChange(
                        path="src/main.py",
                        change_type=ChangeType.ADDED,
                        category=FileCategory.CODE,
                        lines_added=100,
                        lines_deleted=0,
                    )
                ],
                lines_added=100,
                lines_deleted=0,
                files_added=1,
                files_deleted=0,
                files_modified=0,
                complexity_score=10.0,
                summary="Add",
                tags=[],
                impact_areas=[],
            ),
            ChangeAnalysis(
                commit_hash="def",
                author="Author",
                email="author@example.com",
                timestamp=datetime(2024, 1, 1, 0, 0, 0),
                branch="main",
                message="Add docs",
                short_message="Add docs",
                files_changed=[
                    FileChange(
                        path="README.md",
                        change_type=ChangeType.MODIFIED,
                        category=FileCategory.DOCUMENTATION,
                        lines_added=20,
                        lines_deleted=0,
                    )
                ],
                lines_added=20,
                lines_deleted=0,
                files_added=0,
                files_deleted=0,
                files_modified=1,
                complexity_score=2.0,
                summary="Docs",
                tags=[],
                impact_areas=[],
            ),
        ]

        result = service._calculate_file_categories(commits)

        assert FileCategory.CODE in result
        assert FileCategory.DOCUMENTATION in result
        assert result[FileCategory.CODE] == 1
        assert result[FileCategory.DOCUMENTATION] == 1


class TestGetCommitTags:
    """Test commit tag retrieval."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_get_commit_tags_with_tags(self, mock_repo_class):
        """Test getting tags for a commit."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_tag = MagicMock()
        mock_tag.name = "v1.0.0"
        mock_tag.commit.hexsha = "abc123"

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"

        service.repo = mock_repo
        mock_repo.tags = [mock_tag]

        result = service._get_commit_tags(mock_commit)

        assert result == ["v1.0.0"]

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_get_commit_tags_no_tags(self, mock_repo_class):
        """Test getting tags when commit has no tags."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123"

        service.repo = mock_repo
        mock_repo.tags = []

        result = service._get_commit_tags(mock_commit)

        assert result == []


class TestAnalyzeFileDiff:
    """Test file diff analysis."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_file_diff_added(self, mock_repo_class):
        """Test analyzing an added file."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_diff = MagicMock()
        mock_diff.new_file = True
        mock_diff.deleted_file = False
        mock_diff.renamed_file = False
        mock_diff.copied_file = False
        mock_diff.b_path = "new_file.py"
        mock_diff.a_path = None
        mock_diff.diff = b"+ line 1\n+ line 2\n"

        result = service._analyze_file_diff(mock_diff)

        assert result.change_type == ChangeType.ADDED
        assert result.path == "new_file.py"
        assert result.lines_added == 2

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_file_diff_deleted(self, mock_repo_class):
        """Test analyzing a deleted file."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_diff = MagicMock()
        mock_diff.new_file = False
        mock_diff.deleted_file = True
        mock_diff.renamed_file = False
        mock_diff.copied_file = False
        mock_diff.b_path = None
        mock_diff.a_path = "old_file.py"
        mock_diff.diff = b"- line 1\n- line 2\n"

        result = service._analyze_file_diff(mock_diff)

        assert result.change_type == ChangeType.DELETED
        assert result.path == "old_file.py"
        assert result.lines_deleted == 2

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_file_diff_modified(self, mock_repo_class):
        """Test analyzing a modified file."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_diff = MagicMock()
        mock_diff.new_file = False
        mock_diff.deleted_file = False
        mock_diff.renamed_file = False
        mock_diff.copied_file = False
        mock_diff.b_path = "file.py"
        mock_diff.a_path = "file.py"
        mock_diff.diff = b"- old\n+ new\n"

        result = service._analyze_file_diff(mock_diff)

        assert result.change_type == ChangeType.MODIFIED
        assert result.lines_added == 1
        assert result.lines_deleted == 1

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_analyze_file_diff_binary(self, mock_repo_class):
        """Test analyzing a binary file."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        mock_diff = MagicMock()
        mock_diff.new_file = True
        mock_diff.deleted_file = False
        mock_diff.renamed_file = False
        mock_diff.copied_file = False
        mock_diff.b_path = "image.png"
        mock_diff.a_path = None
        mock_diff.diff = None  # Binary files have no diff

        result = service._analyze_file_diff(mock_diff)

        assert result.binary_file is True


class TestCommitComparisonHelpers:
    """Test helper methods for comparing commits."""

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_find_commit_differences(self, mock_repo_class):
        """Test finding differences between commits."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Complex change",
            short_message="Complex change",
            files_changed=[],
            lines_added=100,
            lines_deleted=50,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=80.0,
            summary="Complex",
            tags=["refactor"],
            impact_areas=[],
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Simple change",
            short_message="Simple change",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Simple",
            tags=["fix"],
            impact_areas=[],
        )

        result = service._find_commit_differences(analysis_a, analysis_b)

        assert len(result) > 0
        assert any("significantly more complex" in r.lower() for r in result)

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_find_common_themes(self, mock_repo_class):
        """Test finding common themes between commits."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Fix bug",
            short_message="Fix bug",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Fix",
            tags=["bugfix", "security"],
            impact_areas=["auth"],
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Another fix",
            short_message="Another fix",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=5.0,
            summary="Fix",
            tags=["bugfix"],
            impact_areas=["auth", "api"],
        )

        result = service._find_common_themes(analysis_a, analysis_b)

        assert len(result) > 0
        assert any("Tags:" in r and "bugfix" in r for r in result)

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_describe_impact(self, mock_repo_class):
        """Test describing combined impact of commits."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Change A",
            short_message="Change A",
            files_changed=[],
            lines_added=50,
            lines_deleted=10,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=30.0,
            summary="A",
            tags=[],
            impact_areas=[],
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Change B",
            short_message="Change B",
            files_changed=[],
            lines_added=20,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=15.0,
            summary="B",
            tags=[],
            impact_areas=[],
        )

        result = service._describe_impact(analysis_a, analysis_b)

        assert "impact" in result.lower()
        assert "45.0" in result  # Combined complexity

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_assess_regression_risk(self, mock_repo_class):
        """Test regression risk assessment."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Safe change",
            short_message="Safe change",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Safe",
            tags=[],
            impact_areas=[],
            breaking_change=False,
            security_relevant=False,
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Also safe",
            short_message="Also safe",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Safe",
            tags=[],
            impact_areas=[],
            breaking_change=False,
            security_relevant=False,
        )

        result = service._assess_regression_risk(analysis_a, analysis_b)

        assert "Low" in result

    @patch("dot_work.git.services.git_service.gitpython.Repo")
    def test_generate_migration_notes(self, mock_repo_class):
        """Test migration notes generation."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        config = AnalysisConfig(repo_path=Path("/test/repo"))
        service = GitAnalysisService(config)

        analysis_a = ChangeAnalysis(
            commit_hash="abc",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            branch="main",
            message="Breaking API change",
            short_message="Breaking API change",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Breaking",
            tags=["api", "migration"],
            impact_areas=[],
            breaking_change=True,
            security_relevant=False,
        )

        analysis_b = ChangeAnalysis(
            commit_hash="def",
            author="Author",
            email="author@example.com",
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            branch="main",
            message="Security update",
            short_message="Security update",
            files_changed=[],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Security",
            tags=["security"],
            impact_areas=[],
            breaking_change=False,
            security_relevant=True,
        )

        result = service._generate_migration_notes(analysis_a, analysis_b)

        assert len(result) > 0
        assert any("breaking" in note.lower() for note in result)
        assert any("api" in note.lower() for note in result)
