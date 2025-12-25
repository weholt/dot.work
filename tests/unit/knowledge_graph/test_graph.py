"""Unit tests for kgshred.graph module."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from dot_work.knowledge_graph.db import Database
from dot_work.knowledge_graph.db import DocumentExistsError
from dot_work.knowledge_graph.graph import (
    GraphResult,
    build_graph,
    build_graph_from_blocks,
    get_node_tree,
)
from dot_work.knowledge_graph.parse_md import Block, BlockKind


@pytest.fixture
def memory_db(tmp_path: Path) -> Generator[Database, None, None]:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.sqlite"
    db = Database(db_path)
    db._get_connection()  # Initialize schema lazily
    try:
        yield db
    finally:
        db.close()


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_empty_content_creates_doc_node(self, memory_db: Database) -> None:
        """Empty content still creates a doc node."""
        result = build_graph("test-doc", b"", memory_db)

        assert result.doc_id == "test-doc"
        assert len(result.nodes) == 1
        assert result.nodes[0].kind == "doc"
        assert len(result.edges) == 0

    def test_single_heading_creates_two_nodes(self, memory_db: Database) -> None:
        """Single heading creates doc node + heading node."""
        content = b"# Title"
        result = build_graph("test-doc", content, memory_db)

        assert len(result.nodes) == 2
        assert result.nodes[0].kind == "doc"
        assert result.nodes[1].kind == "heading"
        assert result.nodes[1].level == 1
        assert result.nodes[1].title == "Title"

    def test_single_heading_creates_contains_edge(self, memory_db: Database) -> None:
        """Heading has contains edge from doc."""
        content = b"# Title"
        result = build_graph("test-doc", content, memory_db)

        assert len(result.edges) == 1
        edge = result.edges[0]
        assert edge.edge_type == "contains"
        assert edge.src_node_pk == result.nodes[0].node_pk
        assert edge.dst_node_pk == result.nodes[1].node_pk

    def test_two_h1_headings_create_next_edge(self, memory_db: Database) -> None:
        """Two H1 headings are siblings with next edge."""
        content = b"# First\n\n# Second"
        result = build_graph("test-doc", content, memory_db)

        assert len(result.nodes) == 3
        contains_edges = [e for e in result.edges if e.edge_type == "contains"]
        next_edges = [e for e in result.edges if e.edge_type == "next"]

        assert len(contains_edges) == 2
        assert len(next_edges) == 1
        assert next_edges[0].src_node_pk == result.nodes[1].node_pk
        assert next_edges[0].dst_node_pk == result.nodes[2].node_pk

    def test_h2_under_h1_creates_hierarchy(self, memory_db: Database) -> None:
        """H2 after H1 is child of H1."""
        content = b"# Parent\n\n## Child"
        result = build_graph("test-doc", content, memory_db)

        assert len(result.nodes) == 3
        doc_node = result.nodes[0]
        h1_node = result.nodes[1]
        h2_node = result.nodes[2]

        contains_edges = [e for e in result.edges if e.edge_type == "contains"]
        assert len(contains_edges) == 2

        # H1 -> contained by doc
        h1_contains = next(e for e in contains_edges if e.dst_node_pk == h1_node.node_pk)
        assert h1_contains.src_node_pk == doc_node.node_pk

        # H2 -> contained by H1
        h2_contains = next(e for e in contains_edges if e.dst_node_pk == h2_node.node_pk)
        assert h2_contains.src_node_pk == h1_node.node_pk

    def test_paragraph_under_heading_is_child(self, memory_db: Database) -> None:
        """Paragraph after heading is child of that heading."""
        content = b"# Title\n\nSome text."
        result = build_graph("test-doc", content, memory_db)

        assert len(result.nodes) == 3
        h1_node = result.nodes[1]
        para_node = result.nodes[2]

        # Paragraph contained by heading
        para_contains = next(
            e for e in result.edges
            if e.edge_type == "contains" and e.dst_node_pk == para_node.node_pk
        )
        assert para_contains.src_node_pk == h1_node.node_pk

    def test_multiple_paragraphs_have_next_edges(self, memory_db: Database) -> None:
        """Multiple paragraphs under same heading have next edges."""
        content = b"# Title\n\nFirst.\n\nSecond."
        result = build_graph("test-doc", content, memory_db)

        para_nodes = [n for n in result.nodes if n.kind == "paragraph"]
        assert len(para_nodes) == 2

        next_edges = [e for e in result.edges if e.edge_type == "next"]
        assert len(next_edges) == 1
        assert next_edges[0].src_node_pk == para_nodes[0].node_pk
        assert next_edges[0].dst_node_pk == para_nodes[1].node_pk

    def test_code_block_creates_node(self, memory_db: Database) -> None:
        """Code block creates codeblock node."""
        content = b"```python\nprint('hi')\n```"
        result = build_graph("test-doc", content, memory_db)

        assert len(result.nodes) == 2
        code_node = result.nodes[1]
        assert code_node.kind == "codeblock"
        assert code_node.meta.get("language") == "python"

    def test_complex_hierarchy(self, memory_db: Database) -> None:
        """Complex document with multiple heading levels."""
        content = b"""# H1-A

## H2-A

Para under H2-A.

## H2-B

# H1-B

## H2-C"""
        result = build_graph("test-doc", content, memory_db)

        # Nodes: doc, H1-A, H2-A, para, H2-B, H1-B, H2-C
        assert len(result.nodes) == 7

        doc_node = result.nodes[0]
        h1_a = result.nodes[1]
        h2_a = result.nodes[2]
        para = result.nodes[3]
        h2_b = result.nodes[4]
        h1_b = result.nodes[5]
        h2_c = result.nodes[6]

        # Check hierarchy via contains edges
        contains_edges = {
            (e.src_node_pk, e.dst_node_pk): e
            for e in result.edges
            if e.edge_type == "contains"
        }

        # H1-A and H1-B under doc
        assert (doc_node.node_pk, h1_a.node_pk) in contains_edges
        assert (doc_node.node_pk, h1_b.node_pk) in contains_edges

        # H2-A and H2-B under H1-A
        assert (h1_a.node_pk, h2_a.node_pk) in contains_edges
        assert (h1_a.node_pk, h2_b.node_pk) in contains_edges

        # Para under H2-A
        assert (h2_a.node_pk, para.node_pk) in contains_edges

        # H2-C under H1-B
        assert (h1_b.node_pk, h2_c.node_pk) in contains_edges

    def test_next_edge_between_same_level_headings(self, memory_db: Database) -> None:
        """H2 siblings have next edge."""
        content = b"# H1\n\n## H2-A\n\n## H2-B"
        result = build_graph("test-doc", content, memory_db)

        h2_a = result.nodes[2]
        h2_b = result.nodes[3]

        next_edges = [e for e in result.edges if e.edge_type == "next"]
        h2_next = next(
            (e for e in next_edges if e.src_node_pk == h2_a.node_pk), None
        )
        assert h2_next is not None
        assert h2_next.dst_node_pk == h2_b.node_pk

    def test_nodes_stored_in_database(self, memory_db: Database) -> None:
        """Nodes are persisted to database."""
        content = b"# Title"
        build_graph("test-doc", content, memory_db)

        nodes = memory_db.get_nodes_by_doc_id("test-doc")
        assert len(nodes) == 2

    def test_edges_stored_in_database(self, memory_db: Database) -> None:
        """Edges are persisted to database."""
        content = b"# Title"
        build_graph("test-doc", content, memory_db)

        edges = memory_db.get_edges_by_type("contains")
        assert len(edges) == 1


class TestBuildGraphFromBlocks:
    """Tests for build_graph_from_blocks function."""

    def test_empty_blocks_creates_doc_node(self, memory_db: Database) -> None:
        """Empty block list creates only doc node."""
        result = build_graph_from_blocks("test", b"", [], memory_db)

        assert len(result.nodes) == 1
        assert result.nodes[0].kind == "doc"

    def test_preserves_block_offsets(self, memory_db: Database) -> None:
        """Node offsets match block offsets."""
        content = b"# Hello"
        blocks = [Block(kind=BlockKind.HEADING, start=0, end=7, level=1, title="Hello")]

        result = build_graph_from_blocks("test", content, blocks, memory_db)

        heading_node = result.nodes[1]
        assert heading_node.start == 0
        assert heading_node.end == 7


class TestGetNodeTree:
    """Tests for get_node_tree function."""

    def test_empty_doc_returns_empty(self, memory_db: Database) -> None:
        """No nodes returns empty list."""
        result = get_node_tree(memory_db, "nonexistent")
        assert result == []

    def test_single_node_returns_with_depth_zero(self, memory_db: Database) -> None:
        """Doc node alone has depth 0."""
        build_graph("test", b"", memory_db)
        tree = get_node_tree(memory_db, "test")

        assert len(tree) == 1
        assert tree[0][0].kind == "doc"
        assert tree[0][1] == 0

    def test_hierarchy_shows_correct_depths(self, memory_db: Database) -> None:
        """Nodes have correct depth in tree."""
        content = b"# H1\n\n## H2\n\nPara"
        build_graph("test", content, memory_db)
        tree = get_node_tree(memory_db, "test")

        assert len(tree) == 4
        depths = [depth for _, depth in tree]
        kinds = [node.kind for node, _ in tree]

        # doc=0, h1=1, h2=2, para=3
        assert depths == [0, 1, 2, 3]
        assert kinds == ["doc", "heading", "heading", "paragraph"]

    def test_siblings_same_depth(self, memory_db: Database) -> None:
        """Sibling headings have same depth."""
        content = b"# H1-A\n\n# H1-B"
        build_graph("test", content, memory_db)
        tree = get_node_tree(memory_db, "test")

        assert len(tree) == 3
        # Both H1s at depth 1
        assert tree[1][1] == 1
        assert tree[2][1] == 1


class TestGraphResult:
    """Tests for GraphResult dataclass."""

    def test_graph_result_creation(self) -> None:
        """GraphResult can be created."""
        result = GraphResult(doc_id="test", nodes=[], edges=[])
        assert result.doc_id == "test"
        assert result.nodes == []
        assert result.edges == []


class TestNodeIdGeneration:
    """Tests for node ID generation in graph building."""

    def test_nodes_have_unique_short_ids(self, memory_db: Database) -> None:
        """All nodes have unique short IDs."""
        content = b"# H1\n\n## H2\n\nPara"
        result = build_graph("test", content, memory_db)

        short_ids = [n.short_id for n in result.nodes]
        assert len(short_ids) == len(set(short_ids))

    def test_nodes_have_full_ids(self, memory_db: Database) -> None:
        """All nodes have 32-char full IDs."""
        content = b"# Title"
        result = build_graph("test", content, memory_db)

        for node in result.nodes:
            assert len(node.full_id) == 32
            assert all(c in "0123456789abcdef" for c in node.full_id)

    def test_nonce_stored_in_meta_on_collision(self, memory_db: Database) -> None:
        """Collision nonce stored in node meta."""
        # Create identical content to force collision potential
        content = b"# Title\n\n# Title"
        result = build_graph("test", content, memory_db)

        # Most nodes won't have collision, but check meta structure
        for node in result.nodes:
            if "nonce" in node.meta:
                assert isinstance(node.meta["nonce"], int)
                assert node.meta["nonce"] > 0


class TestEdgeTypes:
    """Tests for edge type creation."""

    def test_contains_edge_type(self, memory_db: Database) -> None:
        """Contains edges have correct type."""
        content = b"# Title"
        result = build_graph("test", content, memory_db)

        contains = [e for e in result.edges if e.edge_type == "contains"]
        assert len(contains) == 1

    def test_next_edge_type(self, memory_db: Database) -> None:
        """Next edges have correct type."""
        content = b"# A\n\n# B"
        result = build_graph("test", content, memory_db)

        next_edges = [e for e in result.edges if e.edge_type == "next"]
        assert len(next_edges) == 1


class TestParagraphWithoutHeading:
    """Tests for paragraphs when no heading exists."""

    def test_paragraph_directly_under_doc(self, memory_db: Database) -> None:
        """Paragraph without heading is child of doc."""
        content = b"Just some text."
        result = build_graph("test", content, memory_db)

        assert len(result.nodes) == 2
        doc_node = result.nodes[0]
        para_node = result.nodes[1]

        # Para contained by doc
        contains_edge = result.edges[0]
        assert contains_edge.src_node_pk == doc_node.node_pk
        assert contains_edge.dst_node_pk == para_node.node_pk

    def test_multiple_paragraphs_no_heading(self, memory_db: Database) -> None:
        """Multiple paragraphs without heading are siblings under doc."""
        content = b"First.\n\nSecond."
        result = build_graph("test", content, memory_db)

        assert len(result.nodes) == 3
        doc_node = result.nodes[0]

        # Both contained by doc
        contains_edges = [e for e in result.edges if e.edge_type == "contains"]
        assert all(e.src_node_pk == doc_node.node_pk for e in contains_edges)

        # Next edge between paragraphs
        next_edges = [e for e in result.edges if e.edge_type == "next"]
        assert len(next_edges) == 1


class TestFTSIndexingDuringBuild:
    """Tests for FTS indexing during graph building."""

    def test_search_finds_heading_after_build(self, memory_db: Database) -> None:
        """FTS search should find heading content after build_graph."""
        content = b"# Python Programming Guide\n\nLearn Python basics."
        build_graph("test-doc", content, memory_db)

        # Search should find the heading
        results = memory_db.fts_search("Python", limit=10)
        assert len(results) >= 1

        # Should find the heading node
        titles = [node.title for node, _ in results if node.title]
        assert "Python Programming Guide" in titles

    def test_search_finds_paragraph_after_build(self, memory_db: Database) -> None:
        """FTS search should find paragraph content after build_graph."""
        content = b"# Title\n\nThis is about JavaScript frameworks."
        build_graph("test-doc", content, memory_db)

        results = memory_db.fts_search("JavaScript", limit=10)
        assert len(results) >= 1

        # Should find a paragraph node
        kinds = [node.kind for node, _ in results]
        assert "paragraph" in kinds

    def test_search_finds_code_block_after_build(self, memory_db: Database) -> None:
        """FTS search should find code block content after build_graph."""
        content = b"# Code\n\n```python\ndef hello_world():\n    pass\n```"
        build_graph("test-doc", content, memory_db)

        results = memory_db.fts_search("hello_world", limit=10)
        assert len(results) >= 1

        kinds = [node.kind for node, _ in results]
        assert "codeblock" in kinds

    def test_empty_doc_is_indexed(self, memory_db: Database) -> None:
        """Even empty documents should be indexed without error."""
        build_graph("empty-doc", b"", memory_db)

        # Doc node should exist and be searchable (though no content)
        nodes = memory_db.get_nodes_by_doc_id("empty-doc")
        assert len(nodes) == 1
        assert nodes[0].kind == "doc"


class TestDuplicateIngestHandling:
    """Tests for duplicate document ingest handling."""

    def test_duplicate_ingest_same_content_raises(self, memory_db: Database) -> None:
        """Re-ingesting same content raises DocumentExistsError with sha256_match=True."""
        content = b"# Hello World"
        build_graph("test-doc", content, memory_db)

        with pytest.raises(DocumentExistsError) as exc_info:
            build_graph("test-doc", content, memory_db)

        assert exc_info.value.sha256_match is True

    def test_duplicate_ingest_different_content_raises(self, memory_db: Database) -> None:
        """Re-ingesting different content raises DocumentExistsError with sha256_match=False."""
        build_graph("test-doc", b"# Version 1", memory_db)

        with pytest.raises(DocumentExistsError) as exc_info:
            build_graph("test-doc", b"# Version 2", memory_db)

        assert exc_info.value.sha256_match is False

    def test_force_replaces_document(self, memory_db: Database) -> None:
        """Force mode replaces existing document."""
        build_graph("test-doc", b"# Version 1", memory_db)

        # Force should succeed
        result = build_graph("test-doc", b"# Version 2", memory_db, force=True)

        assert result.doc_id == "test-doc"
        doc = memory_db.get_document("test-doc")
        assert doc is not None
        assert doc.raw == b"# Version 2"

    def test_force_clears_old_nodes(self, memory_db: Database) -> None:
        """Force mode removes old nodes before creating new ones."""
        build_graph("test-doc", b"# A\n\n## B\n\nParagraph", memory_db)
        old_nodes = memory_db.get_nodes_by_doc_id("test-doc")
        assert len(old_nodes) == 4  # doc, h1, h2, para

        # Force with simpler content
        build_graph("test-doc", b"# Simple", memory_db, force=True)
        new_nodes = memory_db.get_nodes_by_doc_id("test-doc")

        assert len(new_nodes) == 2  # doc, h1

    def test_force_clears_old_fts_entries(self, memory_db: Database) -> None:
        """Force mode clears old FTS entries."""
        build_graph("test-doc", b"# Unique Python Content", memory_db)

        # Should find old content
        results_before = memory_db.fts_search("Python")
        assert len(results_before) >= 1

        # Force with different content
        build_graph("test-doc", b"# Different Topic", memory_db, force=True)

        # Old content should not be found
        results_after = memory_db.fts_search("Python")
        assert len(results_after) == 0

    def test_force_same_content_succeeds(self, memory_db: Database) -> None:
        """Force mode succeeds even with same content."""
        content = b"# Same Content"
        build_graph("test-doc", content, memory_db)

        # Force should work even with identical content
        result = build_graph("test-doc", content, memory_db, force=True)

        assert result.doc_id == "test-doc"
        assert len(result.nodes) == 2


class TestParentNodePk:
    """Tests for parent_node_pk field population."""

    def test_doc_node_has_no_parent(self, memory_db: Database) -> None:
        """Doc node should have parent_node_pk = None."""
        result = build_graph("test-doc", b"# Hello", memory_db)

        doc_node = result.nodes[0]
        assert doc_node.kind == "doc"
        assert doc_node.parent_node_pk is None

    def test_heading_has_doc_as_parent(self, memory_db: Database) -> None:
        """Top-level heading should have doc as parent."""
        result = build_graph("test-doc", b"# Title", memory_db)

        doc_node = result.nodes[0]
        h1_node = result.nodes[1]

        assert h1_node.parent_node_pk == doc_node.node_pk

    def test_h2_has_h1_as_parent(self, memory_db: Database) -> None:
        """H2 under H1 should have H1 as parent."""
        result = build_graph("test-doc", b"# Parent\n\n## Child", memory_db)

        h1_node = result.nodes[1]
        h2_node = result.nodes[2]

        assert h2_node.parent_node_pk == h1_node.node_pk

    def test_paragraph_has_heading_as_parent(self, memory_db: Database) -> None:
        """Paragraph under heading should have heading as parent."""
        result = build_graph("test-doc", b"# Title\n\nSome text.", memory_db)

        h1_node = result.nodes[1]
        para_node = result.nodes[2]

        assert para_node.parent_node_pk == h1_node.node_pk

    def test_paragraph_without_heading_has_doc_as_parent(self, memory_db: Database) -> None:
        """Paragraph without heading should have doc as parent."""
        result = build_graph("test-doc", b"Just text.", memory_db)

        doc_node = result.nodes[0]
        para_node = result.nodes[1]

        assert para_node.parent_node_pk == doc_node.node_pk

    def test_parent_node_pk_persisted_to_database(self, memory_db: Database) -> None:
        """parent_node_pk should be saved to database."""
        build_graph("test-doc", b"# Title\n\nParagraph", memory_db)

        nodes = memory_db.get_nodes_by_doc_id("test-doc")
        doc_node = next(n for n in nodes if n.kind == "doc")
        h1_node = next(n for n in nodes if n.kind == "heading")
        para_node = next(n for n in nodes if n.kind == "paragraph")

        # Verify database values
        assert doc_node.parent_node_pk is None
        assert h1_node.parent_node_pk == doc_node.node_pk
        assert para_node.parent_node_pk == h1_node.node_pk
