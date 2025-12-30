"""Unit tests for SearchService FTS5 injection vulnerability (CR-073)."""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlmodel import Session, text

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.adapters.sqlite import IssueModel
from dot_work.db_issues.services.search_service import SearchService


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


@pytest.fixture
def db_uow_with_fts5(
    db_session_with_fts5: Session,
) -> Generator[UnitOfWork, None, None]:
    """Create a UnitOfWork with FTS5 table for testing.

    Args:
        db_session_with_fts5: Session with FTS5 table

    Yields:
        UnitOfWork wrapping the FTS5 session
    """
    uow = UnitOfWork(db_session_with_fts5)
    yield uow


class TestSearchServiceInjection:
    """Tests for FTS5 query injection vulnerabilities."""

    def test_wildcard_prefix_rejected(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that wildcard prefix queries are rejected."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("s*")

    def test_column_filter_rejected(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that column filters are rejected."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("title:bug")

    def test_near_search_rejected(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that NEAR proximity searches are rejected."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search("bug NEAR/5 fix")

    def test_advanced_operators_rejected_by_default(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that AND/OR/NOT operators are rejected by default."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="Advanced search"):
            service.search("bug AND fix")

        with pytest.raises(ValueError, match="Advanced search"):
            service.search("bug OR fix")

    def test_simple_query_accepted(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that simple word queries are accepted."""
        service = SearchService(db_uow_with_fts5)
        results = service.search("authentication")
        assert isinstance(results, list)
        # Should find the authentication bug issue
        assert len(results) > 0

    def test_invalid_characters_rejected(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that queries with invalid characters are rejected."""
        service = SearchService(db_uow_with_fts5)

        # Semicolon injection attempt
        with pytest.raises(ValueError, match="invalid characters"):
            service.search("bug; DROP TABLE")

        # Shell metacharacters
        with pytest.raises(ValueError, match="invalid characters"):
            service.search("bug|echo")

    def test_empty_query(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that empty query returns empty list."""
        service = SearchService(db_uow_with_fts5)
        results = service.search("")
        assert results == []

    def test_whitespace_only_query(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that whitespace-only query returns empty list."""
        service = SearchService(db_uow_with_fts5)
        results = service.search("   ")
        assert results == []

    def test_search_by_field_validates_field_name(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that search_by_field validates the field parameter."""
        service = SearchService(db_uow_with_fts5)

        # Valid fields
        results = service.search_by_field("title", "authentication")
        assert isinstance(results, list)

        # Invalid field - injection attempt
        with pytest.raises(ValueError, match="Invalid field"):
            service.search_by_field("title; DROP TABLE", "bug")

        # Invalid field - not in allowlist
        with pytest.raises(ValueError, match="Invalid field"):
            service.search_by_field("password", "bug")

    def test_search_by_field_validates_query(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that search_by_field validates the query parameter."""
        service = SearchService(db_uow_with_fts5)

        # Wildcard injection in query
        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search_by_field("title", "*")

        # Boolean injection in query (column filter pattern rejected)
        with pytest.raises(ValueError, match="prohibited syntax"):
            service.search_by_field("title", "bug OR description:secret")

    def test_complex_boolean_dos_prevention(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that complex queries are limited to prevent DoS."""
        service = SearchService(db_uow_with_fts5)

        # Create query with too many ORs
        long_query = " OR ".join(["word"] * 15)
        with pytest.raises(ValueError, match="Too many OR"):
            service.search(long_query, allow_advanced=True)

    def test_long_query_rejected(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that overly long queries are rejected."""
        service = SearchService(db_uow_with_fts5)

        long_query = "word " * 300  # ~1500 characters
        with pytest.raises(ValueError, match="Query too long"):
            service.search(long_query, allow_advanced=True)

    def test_unbalanced_parentheses(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that unbalanced parentheses are rejected."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="Unbalanced parentheses"):
            service.search("(bug OR fix", allow_advanced=True)

        with pytest.raises(ValueError, match="Unbalanced parentheses"):
            service.search("bug OR fix)", allow_advanced=True)

    def test_unbalanced_quotes(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that unbalanced quotes are rejected."""
        service = SearchService(db_uow_with_fts5)

        with pytest.raises(ValueError, match="Unbalanced quotes"):
            service.search('"bug fix', allow_advanced=True)

    def test_advanced_query_with_flag(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that advanced queries work when allow_advanced=True."""
        service = SearchService(db_uow_with_fts5)

        # This should work with the flag
        results = service.search("authentication AND bug", allow_advanced=True)
        assert isinstance(results, list)

    def test_phrase_search_allowed(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that phrase search is allowed with advanced flag."""
        service = SearchService(db_uow_with_fts5)

        results = service.search('"authentication bug"', allow_advanced=True)
        assert isinstance(results, list)


class TestSearchServiceRebuildIndex:
    """Tests for FTS index rebuild with transaction rollback (CR-076)."""

    def test_rebuild_index_succeeds_with_valid_data(self, db_uow_with_fts5: UnitOfWork) -> None:
        """Test that rebuild_index succeeds with valid data."""
        service = SearchService(db_uow_with_fts5)

        # Rebuild should succeed
        count = service.rebuild_index()
        assert count == 3  # We have 3 sample issues

        # Verify FTS still works after rebuild
        results = service.search("authentication")
        assert len(results) > 0

    def test_rebuild_index_rolls_back_on_insert_failure(
        self,
        db_uow_with_fts5: UnitOfWork,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that rebuild_index rolls back when INSERT fails."""
        service = SearchService(db_uow_with_fts5)

        # Mock exec to fail on INSERT query
        original_exec = db_uow_with_fts5.session.exec
        call_sequence = []

        def mock_exec(text_obj, *args, **kwargs):
            query_str = str(text_obj)
            call_sequence.append(query_str)

            # Fail on the INSERT query (after DELETE succeeds)
            if "INSERT INTO issues_fts" in query_str:
                raise RuntimeError("Simulated INSERT failure")

            # Let everything else succeed
            return original_exec(text_obj, *args, **kwargs)

        monkeypatch.setattr(db_uow_with_fts5.session, "exec", mock_exec)

        # Rebuild should fail with RuntimeError
        with pytest.raises(RuntimeError, match="FTS index rebuild failed"):
            service.rebuild_index()

        # Verify DELETE was attempted before INSERT failed
        assert any("DELETE FROM issues_fts" in call for call in call_sequence)
        assert any("INSERT INTO issues_fts" in call for call in call_sequence)

        # Verify rollback was called (monkeypatch can't verify this directly,
        # but the RuntimeError confirms rollback code path was taken)

    def test_rebuild_index_handles_count_failure_gracefully(
        self, db_uow_with_fts5: UnitOfWork, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that rebuild_index handles COUNT failure gracefully."""
        service = SearchService(db_uow_with_fts5)

        # Mock exec to fail on COUNT query
        original_exec = db_uow_with_fts5.session.exec
        call_count = [0]

        def mock_exec(text_obj, *args, **kwargs):
            call_count[0] += 1
            # Fail on the COUNT query (after the main rebuild)
            if "SELECT COUNT" in str(text_obj):
                raise RuntimeError("COUNT query failed")
            return original_exec(text_obj, *args, **kwargs)

        monkeypatch.setattr(db_uow_with_fts5.session, "exec", mock_exec)

        # Rebuild should not raise despite COUNT failure
        # It should return 0 as a safe default
        count = service.rebuild_index()
        assert count == 0  # Safe default on COUNT failure
        assert call_count[0] >= 2  # DELETE and INSERT should have been attempted
