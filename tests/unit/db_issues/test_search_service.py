"""Unit tests for SearchService FTS5 injection vulnerability (CR-073)."""

from collections.abc import Generator
from datetime import datetime, UTC

import pytest
from sqlmodel import Session, text

from dot_work.db_issues.adapters.sqlite import IssueModel
from dot_work.db_issues.services.search_service import SearchService, SearchResult


@pytest.fixture
def db_session_with_fts5(
    in_memory_db: Session,
) -> Generator[Session, None, None]:
    """Create a database session with FTS5 table and sample data.

    Args:
        in_memory_db: In-memory database session

    Yields:
        Session with FTS5 table populated with sample issues
    """
    session = in_memory_db

    # Create FTS5 virtual table
    session.exec(
        text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS issues_fts USING fts5(
            id UNINDEXED,
            title,
            description,
            content='issues',
            content_rowid='rowid'
        );
    """)
    )

    # Create triggers to keep FTS table in sync
    session.exec(
        text("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_insert AFTER INSERT ON issues BEGIN
            INSERT INTO issues_fts(rowid, id, title, description)
            VALUES (NEW.rowid, NEW.id, NEW.title, COALESCE(NEW.description, ''));
        END;
    """)
    )

    session.exec(
        text("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_update AFTER UPDATE ON issues BEGIN
            UPDATE issues_fts
            SET title = NEW.title, description = COALESCE(NEW.description, '')
            WHERE rowid = NEW.rowid;
        END;
    """)
    )

    session.exec(
        text("""
        CREATE TRIGGER IF NOT EXISTS issues_fts_delete AFTER DELETE ON issues BEGIN
            DELETE FROM issues_fts WHERE rowid = OLD.rowid;
        END;
    """)
    )

    # Fixed timestamp for consistent test data
    now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Create sample issues for testing
    sample_issues = [
        IssueModel(
            id="issue-0001",
            project_id="test-project",
            title="authentication bug in login",
            description="Critical security issue with password handling",
            status="proposed",
            priority="high",
            type="bug",
            assignees=[],
            labels=["security", "auth"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0002",
            project_id="test-project",
            title="memory leak in worker process",
            description="Memory usage grows over time",
            status="proposed",
            priority="medium",
            type="bug",
            assignees=[],
            labels=["performance"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
        IssueModel(
            id="issue-0003",
            project_id="test-project",
            title="feature add user profile",
            description="Add user profile page",
            status="proposed",
            priority="low",
            type="feature",
            assignees=[],
            labels=["enhancement"],
            created_at=now,
            updated_at=now,
            closed_at=None,
        ),
    ]

    for issue in sample_issues:
        session.add(issue)

    session.commit()

    # Populate FTS5 table
    session.exec(
        text("""
        INSERT INTO issues_fts(rowid, id, title, description)
        SELECT rowid, id, title, COALESCE(description, '')
        FROM issues;
    """)
    )
    session.commit()

    yield session


class TestSearchServiceInjection:
    """Tests for FTS5 query injection vulnerabilities."""

    def test_wildcard_prefix_rejected(self, db_session_with_fts5: Session) -> None:
        """Test that wildcard prefix queries are rejected."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("s*")

    def test_column_filter_rejected(self, db_session_with_fts5: Session) -> None:
        """Test that column filters are rejected."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("title:bug")

    def test_near_search_rejected(self, db_session_with_fts5: Session) -> None:
        """Test that NEAR proximity searches are rejected."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("bug NEAR/5 fix")

    def test_advanced_operators_rejected_by_default(self, db_session_with_fts5: Session) -> None:
        """Test that AND/OR/NOT operators are rejected by default."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="Advanced search"):
            service.search("bug AND fix")

        with pytest.raises(ValueError, match="Advanced search"):
            service.search("bug OR fix")

    def test_simple_query_accepted(self, db_session_with_fts5: Session) -> None:
        """Test that simple word queries are accepted."""
        service = SearchService(db_session_with_fts5)
        results = service.search("authentication")
        assert isinstance(results, list)
        # Should find the authentication bug issue
        assert len(results) > 0

    def test_invalid_characters_rejected(self, db_session_with_fts5: Session) -> None:
        """Test that queries with invalid characters are rejected."""
        service = SearchService(db_session_with_fts5)

        # Semicolon injection attempt
        with pytest.raises(ValueError, match="invalid characters"):
            service.search("bug; DROP TABLE")

        # Shell metacharacters
        with pytest.raises(ValueError, match="invalid characters"):
            service.search("bug|echo")

    def test_empty_query(self, db_session_with_fts5: Session) -> None:
        """Test that empty query returns empty list."""
        service = SearchService(db_session_with_fts5)
        results = service.search("")
        assert results == []

    def test_whitespace_only_query(self, db_session_with_fts5: Session) -> None:
        """Test that whitespace-only query returns empty list."""
        service = SearchService(db_session_with_fts5)
        results = service.search("   ")
        assert results == []

    def test_search_by_field_validates_field_name(self, db_session_with_fts5: Session) -> None:
        """Test that search_by_field validates the field parameter."""
        service = SearchService(db_session_with_fts5)

        # Valid fields
        results = service.search_by_field("title", "authentication")
        assert isinstance(results, list)

        # Invalid field - injection attempt
        with pytest.raises(ValueError, match="Invalid field"):
            service.search_by_field("title; DROP TABLE", "bug")

        # Invalid field - not in allowlist
        with pytest.raises(ValueError, match="Invalid field"):
            service.search_by_field("password", "bug")

    def test_search_by_field_validates_query(self, db_session_with_fts5: Session) -> None:
        """Test that search_by_field validates the query parameter."""
        service = SearchService(db_session_with_fts5)

        # Wildcard injection in query
        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search_by_field("title", "*")

        # Boolean injection in query (column filter pattern rejected)
        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search_by_field("title", "bug OR description:secret")

    def test_complex_boolean_dos_prevention(self, db_session_with_fts5: Session) -> None:
        """Test that complex queries are limited to prevent DoS."""
        service = SearchService(db_session_with_fts5)

        # Create query with too many ORs
        long_query = " OR ".join(["word"] * 15)
        with pytest.raises(ValueError, match="Too many OR"):
            service.search(long_query, allow_advanced=True)

    def test_long_query_rejected(self, db_session_with_fts5: Session) -> None:
        """Test that overly long queries are rejected."""
        service = SearchService(db_session_with_fts5)

        long_query = "word " * 300  # ~1500 characters
        with pytest.raises(ValueError, match="Query too long"):
            service.search(long_query, allow_advanced=True)

    def test_unbalanced_parentheses(self, db_session_with_fts5: Session) -> None:
        """Test that unbalanced parentheses are rejected."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="Unbalanced parentheses"):
            service.search("(bug OR fix", allow_advanced=True)

        with pytest.raises(ValueError, match="Unbalanced parentheses"):
            service.search("bug OR fix)", allow_advanced=True)

    def test_unbalanced_quotes(self, db_session_with_fts5: Session) -> None:
        """Test that unbalanced quotes are rejected."""
        service = SearchService(db_session_with_fts5)

        with pytest.raises(ValueError, match="Unbalanced quotes"):
            service.search('"bug fix', allow_advanced=True)

    def test_advanced_query_with_flag(self, db_session_with_fts5: Session) -> None:
        """Test that advanced queries work when allow_advanced=True."""
        service = SearchService(db_session_with_fts5)

        # This should work with the flag
        results = service.search("authentication AND bug", allow_advanced=True)
        assert isinstance(results, list)

    def test_phrase_search_allowed(self, db_session_with_fts5: Session) -> None:
        """Test that phrase search is allowed with advanced flag."""
        service = SearchService(db_session_with_fts5)

        results = service.search('"authentication bug"', allow_advanced=True)
        assert isinstance(results, list)
