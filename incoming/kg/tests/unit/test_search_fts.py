"""Tests for FTS5 keyword search."""

from __future__ import annotations

from pathlib import Path

import pytest

from kgshred.db import Database, Node
from kgshred.search_fts import (
    SearchResult,
    _escape_fts_term,
    _extract_search_terms,
    _generate_snippet,
    _highlight_terms,
    _prepare_query,
    _truncate,
    index_node,
    search,
)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create a test database."""
    return Database(tmp_path / "test.sqlite")


@pytest.fixture
def indexed_db(db: Database) -> Database:
    """Create a database with indexed nodes."""
    # Create document
    raw = b"# Python Tutorial\n\nLearn Python programming language basics.\n\n## Variables\n\nPython variables store data.\n\n## Functions\n\nDefine reusable code blocks."
    db.insert_document("doc1", "test.md", raw)

    # Create and index nodes
    nodes = [
        Node(
            node_pk=None,
            full_id="a" * 32,
            short_id="AAAA",
            doc_id="doc1",
            kind="heading",
            title="Python Tutorial",
            level=1,
            start=0,
            end=60,
        ),
        Node(
            node_pk=None,
            full_id="b" * 32,
            short_id="BBBB",
            doc_id="doc1",
            kind="heading",
            title="Variables",
            level=2,
            start=60,
            end=100,
        ),
        Node(
            node_pk=None,
            full_id="c" * 32,
            short_id="CCCC",
            doc_id="doc1",
            kind="heading",
            title="Functions",
            level=2,
            start=100,
            end=150,
        ),
    ]

    for i, node in enumerate(nodes):
        inserted = db.insert_node(node)
        # Use the raw content for indexing
        text = raw[inserted.start : inserted.end].decode("utf-8")
        db.fts_index_node(inserted.node_pk, inserted.title, text, inserted.short_id)

    return db


class TestSearch:
    """Tests for the search function."""

    def test_search_returns_empty_for_empty_query(self, indexed_db: Database) -> None:
        """Empty query returns empty results."""
        assert search(indexed_db, "") == []
        assert search(indexed_db, "   ") == []

    def test_search_finds_by_keyword(self, indexed_db: Database) -> None:
        """Search finds nodes by keyword."""
        results = search(indexed_db, "Python")

        assert len(results) >= 1
        assert any(r.short_id == "AAAA" for r in results)

    def test_search_finds_by_title(self, indexed_db: Database) -> None:
        """Search finds nodes by title."""
        results = search(indexed_db, "Variables")

        assert len(results) >= 1
        assert any(r.short_id == "BBBB" for r in results)

    def test_search_result_has_correct_fields(self, indexed_db: Database) -> None:
        """SearchResult has all required fields."""
        results = search(indexed_db, "Python")

        assert len(results) >= 1
        result = results[0]

        assert isinstance(result, SearchResult)
        assert result.short_id
        assert result.doc_id == "doc1"
        assert result.kind in ("heading", "paragraph", "code")
        assert result.score > 0
        assert result.node is not None

    def test_search_limits_results(self, indexed_db: Database) -> None:
        """Search respects the k limit."""
        results = search(indexed_db, "Python OR Variables OR Functions", k=2)

        assert len(results) <= 2

    def test_search_returns_results_sorted_by_score(self, indexed_db: Database) -> None:
        """Results should be sorted by relevance."""
        results = search(indexed_db, "Python")

        if len(results) > 1:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)


class TestIndexNode:
    """Tests for the index_node function."""

    def test_index_node_indexes_content(self, db: Database) -> None:
        """index_node adds node to FTS index."""
        # Create document
        raw = b"# Test\n\nUnique searchable content here."
        db.insert_document("doc1", "test.md", raw)

        # Create node
        node = Node(
            node_pk=None,
            full_id="x" * 32,
            short_id="XXXX",
            doc_id="doc1",
            kind="heading",
            title="Test",
            level=1,
            start=0,
            end=len(raw),
        )
        inserted = db.insert_node(node)

        # Index it
        index_node(db, inserted, "Unique searchable content here")

        # Search for it
        results = search(db, "searchable")
        assert len(results) == 1
        assert results[0].short_id == "XXXX"

    def test_index_node_skips_node_without_pk(self, db: Database) -> None:
        """index_node does nothing if node_pk is None."""
        node = Node(
            node_pk=None,
            full_id="y" * 32,
            short_id="YYYY",
            doc_id="doc1",
            kind="heading",
            title="Test",
            level=1,
            start=0,
            end=10,
        )

        # Should not raise
        index_node(db, node, "content")


class TestPrepareQuery:
    """Tests for query preparation."""

    def test_prepare_query_empty(self) -> None:
        """Empty query returns empty string."""
        assert _prepare_query("") == ""
        assert _prepare_query("   ") == ""

    def test_prepare_query_single_word(self) -> None:
        """Single word is passed through."""
        assert _prepare_query("python") == "python"

    def test_prepare_query_multiple_words(self) -> None:
        """Multiple words joined with OR."""
        result = _prepare_query("python tutorial")
        assert "OR" in result
        assert "python" in result
        assert "tutorial" in result

    def test_prepare_query_preserves_operators(self) -> None:
        """FTS5 operators are preserved."""
        assert _prepare_query("python AND tutorial") == "python AND tutorial"
        assert _prepare_query("python OR ruby") == "python OR ruby"
        assert _prepare_query("python NOT java") == "python NOT java"

    def test_prepare_query_preserves_quotes(self) -> None:
        """Quoted phrases are preserved."""
        query = '"python tutorial"'
        assert _prepare_query(query) == query

    def test_prepare_query_escapes_special_chars(self) -> None:
        """Special characters are escaped."""
        result = _prepare_query("test@example")
        assert "@" not in result


class TestEscapeFtsTerm:
    """Tests for term escaping."""

    def test_escape_alphanumeric(self) -> None:
        """Alphanumeric terms pass through."""
        assert _escape_fts_term("python3") == "python3"

    def test_escape_removes_special_chars(self) -> None:
        """Special characters are removed."""
        assert "@" not in _escape_fts_term("test@example")
        assert "*" not in _escape_fts_term("test*")

    def test_escape_preserves_unicode(self) -> None:
        """Unicode letters are preserved."""
        assert "ñ" in _escape_fts_term("español")


class TestExtractSearchTerms:
    """Tests for term extraction."""

    def test_extract_simple_words(self) -> None:
        """Simple words are extracted."""
        terms = _extract_search_terms("python tutorial")
        assert "python" in terms
        assert "tutorial" in terms

    def test_extract_removes_operators(self) -> None:
        """Operators are not extracted."""
        terms = _extract_search_terms("python AND tutorial")
        assert "AND" not in terms
        assert "python" in terms

    def test_extract_quoted_phrases(self) -> None:
        """Quoted phrases are extracted as single terms."""
        terms = _extract_search_terms('"python tutorial" basics')
        assert "python tutorial" in terms
        assert "basics" in terms


class TestGenerateSnippet:
    """Tests for snippet generation."""

    def test_snippet_empty_text(self) -> None:
        """Empty text returns empty snippet."""
        assert _generate_snippet("", "test") == ""

    def test_snippet_no_terms(self) -> None:
        """No terms returns truncated text."""
        text = "Some content here"
        snippet = _generate_snippet(text, "", max_length=50)
        assert snippet == text

    def test_snippet_highlights_term(self) -> None:
        """Snippet highlights matching terms."""
        text = "Learn Python programming basics"
        snippet = _generate_snippet(text, "Python", max_length=100)
        assert "<<Python>>" in snippet

    def test_snippet_truncates_long_text(self) -> None:
        """Long text is truncated."""
        text = "A" * 500
        snippet = _generate_snippet(text, "missing", max_length=100)
        assert len(snippet) <= 110  # Allow for ellipsis

    def test_snippet_centers_on_match(self) -> None:
        """Snippet centers around the match."""
        text = "A" * 100 + " Python " + "B" * 100
        snippet = _generate_snippet(text, "Python", max_length=50)
        assert "<<Python>>" in snippet


class TestHighlightTerms:
    """Tests for term highlighting."""

    def test_highlight_single_term(self) -> None:
        """Single term is highlighted."""
        result = _highlight_terms("Learn Python", ["Python"])
        assert result == "Learn <<Python>>"

    def test_highlight_multiple_terms(self) -> None:
        """Multiple terms are highlighted."""
        result = _highlight_terms("Learn Python basics", ["Python", "basics"])
        assert "<<Python>>" in result
        assert "<<basics>>" in result

    def test_highlight_case_insensitive(self) -> None:
        """Highlighting is case-insensitive."""
        result = _highlight_terms("Learn PYTHON", ["python"])
        assert "<<PYTHON>>" in result


class TestTruncate:
    """Tests for text truncation."""

    def test_truncate_short_text(self) -> None:
        """Short text is not truncated."""
        text = "Short text"
        assert _truncate(text, 100) == text

    def test_truncate_long_text(self) -> None:
        """Long text is truncated with ellipsis."""
        text = "This is a longer text that needs truncation"
        result = _truncate(text, 20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_truncate_preserves_word_boundary(self) -> None:
        """Truncation preserves word boundaries."""
        text = "word1 word2 word3 word4"
        result = _truncate(text, 15)
        # Should not cut "word3" in the middle
        assert not result.endswith("wor...")


class TestSearchEdgeCases:
    """Tests for edge cases in search."""

    def test_search_special_characters(self, indexed_db: Database) -> None:
        """Search handles special characters."""
        # Should not raise
        results = search(indexed_db, "test@#$%")
        assert isinstance(results, list)

    def test_search_unicode(self, indexed_db: Database) -> None:
        """Search handles unicode."""
        results = search(indexed_db, "café")
        assert isinstance(results, list)

    def test_search_very_long_query(self, indexed_db: Database) -> None:
        """Search handles very long queries."""
        long_query = "python " * 100
        results = search(indexed_db, long_query)
        assert isinstance(results, list)
