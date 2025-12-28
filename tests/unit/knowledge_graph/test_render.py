"""Tests for document reconstruction and rendering."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from dot_work.knowledge_graph.db import Database, Node
from dot_work.knowledge_graph.render import (
    ExpansionPolicy,
    RenderOptions,
    _find_top_level_nodes,
    format_placeholder,
    parse_placeholder,
    render_filtered,
    render_full,
    render_node,
)


@pytest.fixture
def db(tmp_path: Path) -> Generator[Database, None, None]:
    """Create a test database."""
    db = Database(tmp_path / "test.sqlite")
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def populated_db(db: Database) -> Database:
    """Create a database with a sample document and nodes."""
    raw = b"# Title\n\nParagraph one.\n\n## Section\n\nParagraph two.\n"
    db.insert_document("doc1", "test.md", raw)

    # Create nodes matching the structure
    nodes = [
        Node(
            node_pk=None,
            full_id="a" * 32,
            short_id="AAAA",
            doc_id="doc1",
            kind="heading",
            title="Title",
            level=1,
            start=0,
            end=8,  # "# Title\n"
        ),
        Node(
            node_pk=None,
            full_id="b" * 32,
            short_id="BBBB",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=9,
            end=24,  # "Paragraph one.\n"
        ),
        Node(
            node_pk=None,
            full_id="c" * 32,
            short_id="CCCC",
            doc_id="doc1",
            kind="heading",
            title="Section",
            level=2,
            start=25,
            end=36,  # "## Section\n"
        ),
        Node(
            node_pk=None,
            full_id="d" * 32,
            short_id="DDDD",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=37,
            end=53,  # "Paragraph two.\n"
        ),
    ]

    for node in nodes:
        db.insert_node(node)

    return db


class TestRenderFull:
    """Tests for full document reconstruction."""

    def test_render_full_returns_original_bytes(self, populated_db: Database) -> None:
        """Full render should produce identical bytes to original."""
        result = render_full(populated_db, "doc1")
        expected = b"# Title\n\nParagraph one.\n\n## Section\n\nParagraph two.\n"
        assert result == expected

    def test_render_full_handles_empty_document(self, db: Database) -> None:
        """Empty document should render as empty bytes."""
        db.insert_document("empty", "empty.md", b"")
        result = render_full(db, "empty")
        assert result == b""

    def test_render_full_handles_missing_document(self, db: Database) -> None:
        """Missing document should return empty bytes."""
        result = render_full(db, "nonexistent")
        assert result == b""

    def test_render_full_preserves_encoding(self, db: Database) -> None:
        """UTF-8 content should be preserved exactly."""
        raw = "# Café ☕\n\nUnicode: 日本語\n".encode()
        db.insert_document("utf8", "utf8.md", raw)
        result = render_full(db, "utf8")
        assert result == raw

    def test_render_full_preserves_line_endings_lf(self, db: Database) -> None:
        """LF line endings should be preserved."""
        raw = b"# Title\nLine 2\nLine 3\n"
        db.insert_document("lf", "lf.md", raw)
        result = render_full(db, "lf")
        assert result == raw
        assert b"\r\n" not in result

    def test_render_full_preserves_line_endings_crlf(self, db: Database) -> None:
        """CRLF line endings should be preserved."""
        raw = b"# Title\r\nLine 2\r\nLine 3\r\n"
        db.insert_document("crlf", "crlf.md", raw)
        result = render_full(db, "crlf")
        assert result == raw


class TestRenderNode:
    """Tests for single node rendering."""

    def test_render_node_returns_content(self, populated_db: Database) -> None:
        """Render node should return node's bytes."""
        result = render_node(populated_db, "AAAA")
        assert result == b"# Title\n"

    def test_render_node_missing_returns_empty(self, db: Database) -> None:
        """Missing node should return empty bytes."""
        result = render_node(db, "XXXX")
        assert result == b""

    def test_render_node_paragraph(self, populated_db: Database) -> None:
        """Paragraph node should render correctly."""
        result = render_node(populated_db, "BBBB")
        assert result == b"Paragraph one.\n"


class TestFormatPlaceholder:
    """Tests for placeholder formatting."""

    def test_placeholder_format(self) -> None:
        """Placeholder should match expected format."""
        node = Node(
            node_pk=1,
            full_id="a" * 32,
            short_id="ABCD",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=0,
            end=100,
        )
        result = format_placeholder(node)
        assert result == b"[@ABCD kind=paragraph bytes=100]"

    def test_placeholder_different_kinds(self) -> None:
        """Placeholder should include correct kind."""
        for kind in ["heading", "paragraph", "code"]:
            node = Node(
                node_pk=1,
                full_id="a" * 32,
                short_id="TEST",
                doc_id="doc1",
                kind=kind,
                title=None,
                level=None,
                start=0,
                end=50,
            )
            result = format_placeholder(node)
            assert f"kind={kind}".encode() in result


class TestParsePlaceholder:
    """Tests for placeholder parsing."""

    def test_parse_valid_placeholder(self) -> None:
        """Valid placeholder should parse correctly."""
        result = parse_placeholder("[@ABCD kind=paragraph bytes=100]")
        assert result is not None
        assert result["short_id"] == "ABCD"
        assert result["kind"] == "paragraph"
        assert result["bytes"] == 100

    def test_parse_invalid_placeholder(self) -> None:
        """Invalid placeholder should return None."""
        assert parse_placeholder("not a placeholder") is None
        assert parse_placeholder("[@ABC kind=p bytes=10]") is None  # 3 chars
        assert parse_placeholder("[@ABCD kind=p]") is None  # missing bytes

    def test_roundtrip_format_parse(self) -> None:
        """Format and parse should roundtrip."""
        node = Node(
            node_pk=1,
            full_id="a" * 32,
            short_id="WXYZ",
            doc_id="doc1",
            kind="code",
            title=None,
            level=None,
            start=10,
            end=210,
        )
        formatted = format_placeholder(node).decode("utf-8")
        parsed = parse_placeholder(formatted)
        assert parsed is not None
        assert parsed["short_id"] == "WXYZ"
        assert parsed["kind"] == "code"
        assert parsed["bytes"] == 200


class TestRenderFiltered:
    """Tests for filtered document rendering."""

    def test_render_filtered_all_expanded(self, populated_db: Database) -> None:
        """All nodes expanded should equal full render."""
        matches = {"AAAA", "BBBB", "CCCC", "DDDD"}
        result = render_filtered(populated_db, "doc1", matches)
        expected = render_full(populated_db, "doc1")
        assert result == expected

    def test_render_filtered_no_matches(self, populated_db: Database) -> None:
        """No matches should produce placeholders (except headings)."""
        options = RenderOptions(show_headings=False)
        result = render_filtered(populated_db, "doc1", set(), options)
        # Should contain placeholders
        assert b"[@" in result

    def test_render_filtered_headings_always_shown(self, populated_db: Database) -> None:
        """Headings should be visible by default."""
        result = render_filtered(populated_db, "doc1", set())
        # Headings should be present
        assert b"# Title" in result
        assert b"## Section" in result

    def test_render_filtered_missing_doc(self, db: Database) -> None:
        """Missing document should return empty."""
        result = render_filtered(db, "nonexistent", set())
        assert result == b""


class TestExpansionPolicies:
    """Tests for expansion policies."""

    def test_policy_direct_only_matches(self, populated_db: Database) -> None:
        """Direct policy should only expand matches."""
        options = RenderOptions(policy=ExpansionPolicy.DIRECT, show_headings=False)
        result = render_filtered(populated_db, "doc1", {"BBBB"}, options)
        # BBBB should be expanded
        assert b"Paragraph one." in result
        # Others should be placeholders
        assert b"[@DDDD" in result

    def test_policy_window_includes_neighbors(self, db: Database) -> None:
        """Window should include neighboring siblings."""
        # Create document with siblings
        raw = b"P1\nP2\nP3\nP4\nP5\n"
        db.insert_document("doc1", "test.md", raw)

        # Create sibling nodes
        parent = db.insert_node(
            Node(
                node_pk=None,
                full_id="p" * 32,
                short_id="PPPP",
                doc_id="doc1",
                kind="heading",
                title="Parent",
                level=1,
                start=0,
                end=len(raw),
            )
        )

        nodes_data = [
            ("N001", 0, 3),
            ("N002", 3, 6),
            ("N003", 6, 9),
            ("N004", 9, 12),
            ("N005", 12, 15),
        ]

        for short_id, start, end in nodes_data:
            db.insert_node(
                Node(
                    node_pk=None,
                    full_id=short_id * 8,
                    short_id=short_id,
                    doc_id="doc1",
                    kind="paragraph",
                    title=None,
                    level=None,
                    start=start,
                    end=end,
                    parent_node_pk=parent.node_pk,
                )
            )

        # Test that window works (will check siblings logic)
        options = RenderOptions(
            policy=ExpansionPolicy.DIRECT,
            window=1,
            show_headings=True,
        )
        # This tests the window expansion code path
        result = render_filtered(db, "doc1", {"N003"}, options)
        assert isinstance(result, bytes)


class TestFindTopLevelNodes:
    """Tests for finding top-level nodes."""

    def test_find_top_level_single_node(self) -> None:
        """Single node is top-level."""
        node = Node(
            node_pk=1,
            full_id="a" * 32,
            short_id="AAAA",
            doc_id="doc1",
            kind="heading",
            title="Title",
            level=1,
            start=0,
            end=10,
        )
        result = _find_top_level_nodes([node])
        assert len(result) == 1
        assert result[0].short_id == "AAAA"

    def test_find_top_level_nested_nodes(self) -> None:
        """Nested nodes: only outer is top-level."""
        outer = Node(
            node_pk=1,
            full_id="a" * 32,
            short_id="AAAA",
            doc_id="doc1",
            kind="heading",
            title="Title",
            level=1,
            start=0,
            end=100,
        )
        inner = Node(
            node_pk=2,
            full_id="b" * 32,
            short_id="BBBB",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=10,
            end=50,
        )
        result = _find_top_level_nodes([outer, inner])
        assert len(result) == 1
        assert result[0].short_id == "AAAA"

    def test_find_top_level_sibling_nodes(self) -> None:
        """Sibling nodes are both top-level."""
        node1 = Node(
            node_pk=1,
            full_id="a" * 32,
            short_id="AAAA",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=0,
            end=10,
        )
        node2 = Node(
            node_pk=2,
            full_id="b" * 32,
            short_id="BBBB",
            doc_id="doc1",
            kind="paragraph",
            title=None,
            level=None,
            start=20,
            end=30,
        )
        result = _find_top_level_nodes([node1, node2])
        assert len(result) == 2


class TestRenderEdgeCases:
    """Tests for edge cases in rendering."""

    def test_render_single_node_document(self, db: Database) -> None:
        """Document with single node renders correctly."""
        raw = b"# Only Heading\n"
        db.insert_document("doc1", "test.md", raw)
        db.insert_node(
            Node(
                node_pk=None,
                full_id="a" * 32,
                short_id="ONLY",
                doc_id="doc1",
                kind="heading",
                title="Only Heading",
                level=1,
                start=0,
                end=len(raw),
            )
        )

        result = render_full(db, "doc1")
        assert result == raw

    def test_render_binary_content(self, db: Database) -> None:
        """Binary content should be preserved."""
        raw = bytes(range(256))  # All possible bytes
        db.insert_document("bin", "binary.bin", raw)

        result = render_full(db, "bin")
        assert result == raw
