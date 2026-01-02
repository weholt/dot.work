"""Tests for version commit_parser module."""

from unittest.mock import Mock

from dot_version.commit_parser import CommitInfo, ConventionalCommitParser


def _create_mock_commit(hexsha: str, message: str, author_name: str = "Test Author") -> Mock:
    """Create a mock git commit object.

    Args:
        hexsha: Commit hash
        message: Commit message
        author_name: Author name

    Returns:
        Mock commit object
    """
    commit = Mock()
    commit.hexsha = hexsha
    commit.message = message
    commit.author.name = author_name
    commit.author.email = "test@example.com"
    commit.committed_datetime = Mock()
    commit.committed_datetime.strftime = Mock(return_value="2025-01-01")
    return commit


def test_parse_commit_basic_feature():
    """Test parsing a basic feature commit."""
    parser = ConventionalCommitParser()

    mock_commit = _create_mock_commit("abc123", "feat: add new feature")
    commit = parser.parse_commit(mock_commit)

    assert commit.commit_hash == "abc123"
    assert commit.short_hash == "abc123"
    assert commit.subject == "add new feature"
    assert commit.commit_type == "feat"
    assert commit.scope is None
    assert commit.is_breaking is False
    assert commit.author == "Test Author"
    assert commit.date == "2025-01-01"


def test_parse_commit_with_scope():
    """Test parsing a commit with scope."""
    parser = ConventionalCommitParser()

    mock_commit = _create_mock_commit("def456", "feat(ui): add button component")
    commit = parser.parse_commit(mock_commit)

    assert commit.commit_type == "feat"
    assert commit.scope == "ui"
    assert commit.subject == "add button component"
    assert commit.is_breaking is False


def test_parse_commit_breaking_change():
    """Test parsing a breaking change commit."""
    parser = ConventionalCommitParser()

    mock_commit = _create_mock_commit("ghi789", "feat!: change API")
    commit = parser.parse_commit(mock_commit)

    assert commit.commit_type == "feat"
    assert commit.is_breaking is True
    assert commit.subject == "change API"


def test_parse_commit_with_body():
    """Test parsing a commit with body."""
    parser = ConventionalCommitParser()

    message = """feat: add new feature

This is the body of the commit
with multiple lines.
"""
    mock_commit = _create_mock_commit("jkl012", message)
    commit = parser.parse_commit(mock_commit)

    assert commit.commit_type == "feat"
    assert commit.subject == "add new feature"
    assert commit.body is not None
    assert "This is the body of the commit" in commit.body


def test_parse_commit_non_conventional():
    """Test parsing a non-conventional commit."""
    parser = ConventionalCommitParser()

    mock_commit = _create_mock_commit("mno345", "Just a regular commit message")
    commit = parser.parse_commit(mock_commit)

    assert commit.commit_type == "other"  # Default type for non-conventional
    assert commit.scope is None
    assert commit.is_breaking is False
    assert commit.subject == "Just a regular commit message"


def test_group_commits_by_type():
    """Test grouping commits by type."""
    parser = ConventionalCommitParser()

    commits = [
        CommitInfo(
            commit_hash="abc123",
            short_hash="abc123",
            commit_type="feat",
            scope=None,
            subject="add new feature",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        ),
        CommitInfo(
            commit_hash="fix123",
            short_hash="fix123",
            commit_type="fix",
            scope=None,
            subject="fix bug",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        ),
        CommitInfo(
            commit_hash="feat456",
            short_hash="feat456",
            commit_type="feat",
            scope=None,
            subject="another feature",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        ),
        CommitInfo(
            commit_hash="docs789",
            short_hash="docs789",
            commit_type="docs",
            scope=None,
            subject="update readme",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        ),
    ]

    grouped = parser.group_commits_by_type(commits)

    assert len(grouped["feat"]) == 2
    assert len(grouped["fix"]) == 1
    assert len(grouped["docs"]) == 1
    assert grouped["feat"][0].subject == "add new feature"
    assert grouped["feat"][1].subject == "another feature"
