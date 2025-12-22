"""Tests for version commit_parser module."""

from dot_work.version.commit_parser import CommitInfo, ConventionalCommitParser


def test_parse_commit_basic_feature():
    """Test parsing a basic feature commit."""
    parser = ConventionalCommitParser()

    commit = parser.parse_commit(
        hash="abc123",
        message="feat: add new feature",
        author="Test Author",
        date="2025-01-01"
    )

    assert commit.hash == "abc123"
    assert commit.short_hash == "abc123"
    assert commit.message == "feat: add new feature"
    assert commit.subject == "add new feature"
    assert commit.commit_type == "feat"
    assert commit.scope is None
    assert commit.breaking is False
    assert commit.author == "Test Author"
    assert commit.date == "2025-01-01"


def test_parse_commit_with_scope():
    """Test parsing a commit with scope."""
    parser = ConventionalCommitParser()

    commit = parser.parse_commit(
        hash="def456",
        message="feat(ui): add button component",
        author="Test Author",
        date="2025-01-01"
    )

    assert commit.commit_type == "feat"
    assert commit.scope == "ui"
    assert commit.subject == "add button component"
    assert commit.breaking is False


def test_parse_commit_breaking_change():
    """Test parsing a breaking change commit."""
    parser = ConventionalCommitParser()

    commit = parser.parse_commit(
        hash="ghi789",
        message="feat!: change API",
        author="Test Author",
        date="2025-01-01"
    )

    assert commit.commit_type == "feat"
    assert commit.breaking is True
    assert commit.subject == "change API"


def test_parse_commit_with_body():
    """Test parsing a commit with body."""
    parser = ConventionalCommitParser()

    message = """feat: add new feature

This is the body of the commit
with multiple lines.
"""
    commit = parser.parse_commit(
        hash="jkl012",
        message=message,
        author="Test Author",
        date="2025-01-01"
    )

    assert commit.commit_type == "feat"
    assert commit.subject == "add new feature"
    assert commit.body is not None
    assert "This is the body of the commit" in commit.body


def test_parse_commit_non_conventional():
    """Test parsing a non-conventional commit."""
    parser = ConventionalCommitParser()

    commit = parser.parse_commit(
        hash="mno345",
        message="Just a regular commit message",
        author="Test Author",
        date="2025-01-01"
    )

    assert commit.commit_type == "chore"  # Default type
    assert commit.scope is None
    assert commit.breaking is False
    assert commit.subject == "Just a regular commit message"


def test_group_commits_by_type(mock_commit_info):
    """Test grouping commits by type."""
    parser = ConventionalCommitParser()

    commits = [
        mock_commit_info,  # feat type
        CommitInfo(
            hash="fix123",
            short_hash="fix123",
            message="fix: fix bug",
            subject="fix bug",
            commit_type="fix",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        ),
        CommitInfo(
            hash="feat456",
            short_hash="feat456",
            message="feat: another feature",
            subject="another feature",
            commit_type="feat",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        ),
        CommitInfo(
            hash="docs789",
            short_hash="docs789",
            message="docs: update readme",
            subject="update readme",
            commit_type="docs",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        ),
    ]

    grouped = parser.group_commits_by_type(commits)

    assert len(grouped["feat"]) == 2
    assert len(grouped["fix"]) == 1
    assert len(grouped["docs"]) == 1
    assert grouped["feat"][0].subject == "add new feature"
    assert grouped["feat"][1].subject == "another feature"