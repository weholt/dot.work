"""Unit tests for kgshred.db module."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from kgshred.db import (
    SCHEMA_VERSION,
    Database,
    Document,
    DocumentExistsError,
    Edge,
    Node,
)

if TYPE_CHECKING:
    pass


class TestDatabase:
    """Tests for Database class."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Database creates parent directory if it doesn't exist."""
        db_path = tmp_path / "subdir" / "deep" / "db.sqlite"
        db = Database(db_path)
        db._get_connection()
        assert db_path.parent.exists()
        db.close()

    def test_init_creates_tables(self, tmp_path: Path) -> None:
        """Database creates all required tables on first connection."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        conn = db._get_connection()

        # Check tables exist
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cur.fetchall()}

        assert "documents" in tables
        assert "nodes" in tables
        assert "edges" in tables
        assert "fts_nodes" in tables
        assert "schema_version" in tables

        db.close()

    def test_pragmas_configured(self, tmp_path: Path) -> None:
        """Database configures WAL mode and other pragmas."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)

        assert db.get_pragma("journal_mode") == "wal"
        assert db.get_pragma("synchronous") == "1"  # NORMAL
        assert db.get_pragma("temp_store") == "2"  # MEMORY
        assert db.get_pragma("foreign_keys") == "1"

        db.close()

    def test_schema_version(self, tmp_path: Path) -> None:
        """Database records schema version."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)

        assert db.get_schema_version() == SCHEMA_VERSION

        db.close()

    def test_close_and_reopen(self, tmp_path: Path) -> None:
        """Database can be closed and reopened."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)
        db._get_connection()
        db.close()

        # Reopen
        db2 = Database(db_path)
        assert db2.get_schema_version() == SCHEMA_VERSION
        db2.close()

    def test_transaction_commits_on_success(self, tmp_path: Path) -> None:
        """Transaction commits changes on success."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)

        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO documents (doc_id, source_path, sha256, created_at, raw) "
                "VALUES (?, ?, ?, ?, ?)",
                ("doc1", "/test.md", "abc123", 1000, b"content"),
            )

        # Verify committed
        doc = db.get_document("doc1")
        assert doc is not None
        db.close()

    def test_transaction_rollback_on_error(self, tmp_path: Path) -> None:
        """Transaction rolls back on exception."""
        db_path = tmp_path / "test.sqlite"
        db = Database(db_path)

        with pytest.raises(ValueError):
            with db.transaction() as conn:
                conn.execute(
                    "INSERT INTO documents (doc_id, source_path, sha256, created_at, raw) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("doc1", "/test.md", "abc123", 1000, b"content"),
                )
                raise ValueError("Simulated error")

        # Verify rolled back
        doc = db.get_document("doc1")
        assert doc is None
        db.close()


class TestDocumentOperations:
    """Tests for document CRUD operations."""

    def test_insert_document(self, tmp_path: Path) -> None:
        """Insert creates a document with correct fields."""
        db = Database(tmp_path / "test.sqlite")

        doc = db.insert_document(
            doc_id="doc1",
            source_path="/path/to/file.md",
            raw=b"# Hello World",
            created_at=1700000000,
        )

        assert doc.doc_id == "doc1"
        assert doc.source_path == "/path/to/file.md"
        assert doc.created_at == 1700000000
        assert doc.raw == b"# Hello World"
        assert len(doc.sha256) == 64  # SHA256 hex digest

        db.close()

    def test_insert_document_auto_timestamp(self, tmp_path: Path) -> None:
        """Insert uses current time if created_at not specified."""
        db = Database(tmp_path / "test.sqlite")

        doc = db.insert_document(
            doc_id="doc1",
            source_path="/file.md",
            raw=b"content",
        )

        assert doc.created_at > 0
        db.close()

    def test_insert_document_duplicate_raises(self, tmp_path: Path) -> None:
        """Insert raises IntegrityError on duplicate doc_id."""
        db = Database(tmp_path / "test.sqlite")

        db.insert_document("doc1", "/a.md", b"a")

        with pytest.raises(sqlite3.IntegrityError):
            db.insert_document("doc1", "/b.md", b"b")

        db.close()

    def test_get_document_exists(self, tmp_path: Path) -> None:
        """Get returns document when it exists."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"content", 1000)

        doc = db.get_document("doc1")

        assert doc is not None
        assert doc.doc_id == "doc1"
        assert doc.source_path == "/test.md"
        db.close()

    def test_get_document_not_found(self, tmp_path: Path) -> None:
        """Get returns None when document doesn't exist."""
        db = Database(tmp_path / "test.sqlite")

        doc = db.get_document("nonexistent")

        assert doc is None
        db.close()


class TestNodeOperations:
    """Tests for node CRUD operations."""

    @pytest.fixture
    def db_with_doc(self, tmp_path: Path) -> Database:
        """Create database with a document."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"content")
        return db

    def test_insert_node(self, db_with_doc: Database) -> None:
        """Insert creates a node with assigned pk."""
        node = Node(
            node_pk=None,
            short_id="abcd",
            full_id="doc1/heading/abcd",
            doc_id="doc1",
            kind="heading",
            level=1,
            title="Test Heading",
            start=0,
            end=50,
        )

        result = db_with_doc.insert_node(node)

        assert result.node_pk is not None
        assert result.node_pk > 0
        assert result.short_id == "abcd"
        db_with_doc.close()

    def test_insert_node_with_meta(self, db_with_doc: Database) -> None:
        """Insert preserves metadata."""
        node = Node(
            node_pk=None,
            short_id="efgh",
            full_id="doc1/para/efgh",
            doc_id="doc1",
            kind="para",
            meta={"tags": ["important"], "priority": 1},
        )

        result = db_with_doc.insert_node(node)
        fetched = db_with_doc.get_node_by_short_id("efgh")

        assert fetched is not None
        assert fetched.meta == {"tags": ["important"], "priority": 1}
        db_with_doc.close()

    def test_insert_node_duplicate_short_id_raises(self, db_with_doc: Database) -> None:
        """Insert raises on duplicate short_id."""
        node1 = Node(
            node_pk=None,
            short_id="aaaa",
            full_id="doc1/h1/aaaa",
            doc_id="doc1",
            kind="heading",
        )
        node2 = Node(
            node_pk=None,
            short_id="aaaa",
            full_id="doc1/h2/aaaa-2",
            doc_id="doc1",
            kind="heading",
        )

        db_with_doc.insert_node(node1)

        with pytest.raises(sqlite3.IntegrityError):
            db_with_doc.insert_node(node2)

        db_with_doc.close()

    def test_insert_nodes_batch(self, db_with_doc: Database) -> None:
        """Batch insert creates multiple nodes."""
        nodes = [
            Node(
                node_pk=None,
                short_id=f"n{i:03d}",
                full_id=f"doc1/para/n{i:03d}",
                doc_id="doc1",
                kind="para",
                start=i * 100,
                end=(i + 1) * 100,
            )
            for i in range(5)
        ]

        result = db_with_doc.insert_nodes_batch(nodes)

        assert len(result) == 5
        assert all(n.node_pk is not None for n in result)
        assert all(n.node_pk > 0 for n in result)
        db_with_doc.close()

    def test_get_node_by_short_id(self, db_with_doc: Database) -> None:
        """Get by short_id returns correct node."""
        node = Node(
            node_pk=None,
            short_id="xyz1",
            full_id="doc1/heading/xyz1",
            doc_id="doc1",
            kind="heading",
            title="Found Me",
        )
        db_with_doc.insert_node(node)

        result = db_with_doc.get_node_by_short_id("xyz1")

        assert result is not None
        assert result.title == "Found Me"
        db_with_doc.close()

    def test_get_node_by_short_id_not_found(self, db_with_doc: Database) -> None:
        """Get returns None for nonexistent short_id."""
        result = db_with_doc.get_node_by_short_id("zzzz")

        assert result is None
        db_with_doc.close()

    def test_get_nodes_by_doc_id(self, db_with_doc: Database) -> None:
        """Get by doc_id returns all nodes for document."""
        nodes = [
            Node(
                node_pk=None,
                short_id=f"d{i}",
                full_id=f"doc1/para/d{i}",
                doc_id="doc1",
                kind="para",
                start=i * 10,
                end=i * 10 + 5,
            )
            for i in range(3)
        ]
        db_with_doc.insert_nodes_batch(nodes)

        result = db_with_doc.get_nodes_by_doc_id("doc1")

        assert len(result) == 3
        # Should be ordered by start
        assert result[0].short_id == "d0"
        assert result[1].short_id == "d1"
        assert result[2].short_id == "d2"
        db_with_doc.close()

    def test_get_node_by_pk(self, db_with_doc: Database) -> None:
        """Get by pk returns correct node."""
        node = Node(
            node_pk=None,
            short_id="pk01",
            full_id="doc1/heading/pk01",
            doc_id="doc1",
            kind="heading",
            title="Found By PK",
        )
        inserted = db_with_doc.insert_node(node)
        assert inserted.node_pk is not None

        result = db_with_doc.get_node_by_pk(inserted.node_pk)

        assert result is not None
        assert result.title == "Found By PK"
        assert result.short_id == "pk01"
        db_with_doc.close()

    def test_get_node_by_pk_not_found(self, db_with_doc: Database) -> None:
        """Get by pk returns None for nonexistent pk."""
        result = db_with_doc.get_node_by_pk(999999)

        assert result is None
        db_with_doc.close()

    def test_update_node_parent(self, db_with_doc: Database) -> None:
        """Update sets parent_node_pk correctly."""
        parent = db_with_doc.insert_node(Node(
            node_pk=None,
            short_id="prnt",
            full_id="doc1/heading/prnt",
            doc_id="doc1",
            kind="heading",
        ))
        child = db_with_doc.insert_node(Node(
            node_pk=None,
            short_id="chld",
            full_id="doc1/para/chld",
            doc_id="doc1",
            kind="para",
        ))
        assert child.parent_node_pk is None
        assert parent.node_pk is not None
        assert child.node_pk is not None

        db_with_doc.update_node_parent(child.node_pk, parent.node_pk)

        updated = db_with_doc.get_node_by_pk(child.node_pk)
        assert updated is not None
        assert updated.parent_node_pk == parent.node_pk
        db_with_doc.close()


class TestEdgeOperations:
    """Tests for edge CRUD operations."""

    @pytest.fixture
    def db_with_nodes(self, tmp_path: Path) -> tuple[Database, list[Node]]:
        """Create database with document and nodes."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"content")

        nodes = db.insert_nodes_batch([
            Node(
                node_pk=None,
                short_id=f"e{i}",
                full_id=f"doc1/para/e{i}",
                doc_id="doc1",
                kind="para",
            )
            for i in range(5)
        ])

        return db, nodes

    def test_insert_edge(self, db_with_nodes: tuple[Database, list[Node]]) -> None:
        """Insert creates an edge."""
        db, nodes = db_with_nodes

        edge = Edge(
            src_node_pk=nodes[0].node_pk,  # type: ignore
            dst_node_pk=nodes[1].node_pk,  # type: ignore
            edge_type="contains",
        )

        result = db.insert_edge(edge)

        assert result.src_node_pk == nodes[0].node_pk
        assert result.dst_node_pk == nodes[1].node_pk
        assert result.edge_type == "contains"
        assert result.weight == 1.0
        db.close()

    def test_insert_edge_with_meta(self, db_with_nodes: tuple[Database, list[Node]]) -> None:
        """Insert preserves edge metadata."""
        db, nodes = db_with_nodes

        edge = Edge(
            src_node_pk=nodes[0].node_pk,  # type: ignore
            dst_node_pk=nodes[1].node_pk,  # type: ignore
            edge_type="ref",
            weight=0.5,
            meta={"label": "see also"},
        )

        db.insert_edge(edge)

        edges = db.get_edges_by_type("ref")
        assert len(edges) == 1
        assert edges[0].meta == {"label": "see also"}
        assert edges[0].weight == 0.5
        db.close()

    def test_get_edges_by_type(self, db_with_nodes: tuple[Database, list[Node]]) -> None:
        """Get by type returns correct edges."""
        db, nodes = db_with_nodes

        # Insert different edge types
        db.insert_edge(Edge(nodes[0].node_pk, nodes[1].node_pk, "contains"))  # type: ignore
        db.insert_edge(Edge(nodes[1].node_pk, nodes[2].node_pk, "next"))  # type: ignore
        db.insert_edge(Edge(nodes[2].node_pk, nodes[3].node_pk, "next"))  # type: ignore
        db.insert_edge(Edge(nodes[0].node_pk, nodes[4].node_pk, "ref"))  # type: ignore

        next_edges = db.get_edges_by_type("next")
        assert len(next_edges) == 2

        contains_edges = db.get_edges_by_type("contains")
        assert len(contains_edges) == 1

        db.close()

    def test_get_children(self, db_with_nodes: tuple[Database, list[Node]]) -> None:
        """Get children returns nodes via 'contains' edges."""
        db, nodes = db_with_nodes

        # Parent -> children
        db.insert_edge(Edge(nodes[0].node_pk, nodes[1].node_pk, "contains"))  # type: ignore
        db.insert_edge(Edge(nodes[0].node_pk, nodes[2].node_pk, "contains"))  # type: ignore

        children = db.get_children(nodes[0].node_pk)  # type: ignore

        assert len(children) == 2
        short_ids = {c.short_id for c in children}
        assert "e1" in short_ids
        assert "e2" in short_ids
        db.close()

    def test_get_siblings(self, db_with_nodes: tuple[Database, list[Node]]) -> None:
        """Get siblings returns nodes via 'next' edges."""
        db, nodes = db_with_nodes

        # Sibling chain
        db.insert_edge(Edge(nodes[0].node_pk, nodes[1].node_pk, "next"))  # type: ignore

        siblings = db.get_siblings(nodes[0].node_pk)  # type: ignore

        assert len(siblings) == 1
        assert siblings[0].short_id == "e1"
        db.close()


class TestFTSOperations:
    """Tests for full-text search operations."""

    @pytest.fixture
    def db_with_indexed_nodes(self, tmp_path: Path) -> Database:
        """Create database with indexed nodes."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"content")

        nodes = db.insert_nodes_batch([
            Node(
                node_pk=None,
                short_id="head1",
                full_id="doc1/h1/head1",
                doc_id="doc1",
                kind="heading",
                title="Python Programming",
            ),
            Node(
                node_pk=None,
                short_id="para1",
                full_id="doc1/para/para1",
                doc_id="doc1",
                kind="para",
            ),
            Node(
                node_pk=None,
                short_id="head2",
                full_id="doc1/h2/head2",
                doc_id="doc1",
                kind="heading",
                title="JavaScript Basics",
            ),
        ])

        # Index nodes
        db.fts_index_node(nodes[0].node_pk, "Python Programming", "Learn Python language basics", "head1")  # type: ignore
        db.fts_index_node(nodes[1].node_pk, None, "Variables and functions in Python", "para1")  # type: ignore
        db.fts_index_node(nodes[2].node_pk, "JavaScript Basics", "Learn JavaScript for web", "head2")  # type: ignore

        return db

    def test_fts_index_node(self, tmp_path: Path) -> None:
        """FTS index stores node content."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"content")

        node = db.insert_node(Node(
            node_pk=None,
            short_id="test",
            full_id="doc1/h1/test",
            doc_id="doc1",
            kind="heading",
        ))

        # Should not raise
        db.fts_index_node(node.node_pk, "Title", "Content text", "test")  # type: ignore

        # Verify indexed
        conn = db._get_connection()
        cur = conn.execute("SELECT COUNT(*) FROM fts_nodes")
        assert cur.fetchone()[0] == 1

        db.close()

    def test_fts_search_finds_match(self, db_with_indexed_nodes: Database) -> None:
        """FTS search finds matching nodes."""
        results = db_with_indexed_nodes.fts_search("Python")

        assert len(results) >= 1
        titles = [node.title for node, _ in results if node.title]
        assert "Python Programming" in titles

        db_with_indexed_nodes.close()

    def test_fts_search_returns_score(self, db_with_indexed_nodes: Database) -> None:
        """FTS search returns relevance score."""
        results = db_with_indexed_nodes.fts_search("Python")

        assert len(results) >= 1
        node, score = results[0]
        assert isinstance(score, float)

        db_with_indexed_nodes.close()

    def test_fts_search_no_match(self, db_with_indexed_nodes: Database) -> None:
        """FTS search returns empty list for no match."""
        results = db_with_indexed_nodes.fts_search("Rust programming")

        assert len(results) == 0

        db_with_indexed_nodes.close()

    def test_fts_search_limit(self, db_with_indexed_nodes: Database) -> None:
        """FTS search respects limit parameter."""
        results = db_with_indexed_nodes.fts_search("Python", limit=1)

        assert len(results) <= 1

        db_with_indexed_nodes.close()


class TestDataclasses:
    """Tests for dataclass definitions."""

    def test_document_dataclass(self) -> None:
        """Document dataclass holds correct fields."""
        doc = Document(
            doc_id="test",
            source_path="/path.md",
            sha256="abc123",
            created_at=1000,
            raw=b"content",
        )

        assert doc.doc_id == "test"
        assert doc.source_path == "/path.md"
        assert doc.raw == b"content"

    def test_node_dataclass_defaults(self) -> None:
        """Node dataclass has correct defaults."""
        node = Node(
            node_pk=None,
            short_id="test",
            full_id="doc1/test",
            doc_id="doc1",
            kind="para",
        )

        assert node.level is None
        assert node.title is None
        assert node.start == 0
        assert node.end == 0
        assert node.parent_node_pk is None
        assert node.meta == {}

    def test_edge_dataclass_defaults(self) -> None:
        """Edge dataclass has correct defaults."""
        edge = Edge(src_node_pk=1, dst_node_pk=2, edge_type="contains")

        assert edge.weight == 1.0
        assert edge.meta == {}


class TestDeleteDocument:
    """Tests for delete_document method."""

    @pytest.fixture
    def db_with_graph(self, tmp_path: Path) -> Database:
        """Create database with a document, nodes, edges, and FTS entries."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/test.md", b"# Hello\n\nWorld")

        nodes = db.insert_nodes_batch([
            Node(
                node_pk=None,
                short_id="doc0",
                full_id="doc1/doc/doc0",
                doc_id="doc1",
                kind="doc",
            ),
            Node(
                node_pk=None,
                short_id="head",
                full_id="doc1/heading/head",
                doc_id="doc1",
                kind="heading",
                title="Hello",
            ),
            Node(
                node_pk=None,
                short_id="para",
                full_id="doc1/para/para",
                doc_id="doc1",
                kind="paragraph",
            ),
        ])

        # Add edges
        db.insert_edge(Edge(nodes[0].node_pk, nodes[1].node_pk, "contains"))  # type: ignore
        db.insert_edge(Edge(nodes[1].node_pk, nodes[2].node_pk, "contains"))  # type: ignore

        # Add FTS entries
        for node in nodes:
            db.fts_index_node(node.node_pk, node.title, "text", node.short_id)  # type: ignore

        return db

    def test_delete_document_removes_document(self, db_with_graph: Database) -> None:
        """Delete removes the document record."""
        result = db_with_graph.delete_document("doc1")

        assert result is True
        assert db_with_graph.get_document("doc1") is None
        db_with_graph.close()

    def test_delete_document_removes_nodes(self, db_with_graph: Database) -> None:
        """Delete removes all nodes for the document."""
        db_with_graph.delete_document("doc1")

        nodes = db_with_graph.get_nodes_by_doc_id("doc1")
        assert len(nodes) == 0
        db_with_graph.close()

    def test_delete_document_removes_edges(self, db_with_graph: Database) -> None:
        """Delete removes all edges for the document."""
        db_with_graph.delete_document("doc1")

        edges = db_with_graph.get_edges_by_type("contains")
        assert len(edges) == 0
        db_with_graph.close()

    def test_delete_document_removes_fts_entries(self, db_with_graph: Database) -> None:
        """Delete removes FTS index entries."""
        db_with_graph.delete_document("doc1")

        results = db_with_graph.fts_search("Hello")
        assert len(results) == 0
        db_with_graph.close()

    def test_delete_document_not_found_returns_false(self, tmp_path: Path) -> None:
        """Delete returns False for nonexistent document."""
        db = Database(tmp_path / "test.sqlite")
        db._get_connection()

        result = db.delete_document("nonexistent")

        assert result is False
        db.close()

    def test_delete_document_preserves_other_documents(self, tmp_path: Path) -> None:
        """Delete only removes specified document, not others."""
        db = Database(tmp_path / "test.sqlite")
        db.insert_document("doc1", "/a.md", b"content1")
        db.insert_document("doc2", "/b.md", b"content2")

        db.delete_document("doc1")

        assert db.get_document("doc1") is None
        assert db.get_document("doc2") is not None
        db.close()


class TestDocumentExistsError:
    """Tests for DocumentExistsError exception."""

    def test_error_with_sha256_match(self) -> None:
        """Error message for unchanged content."""
        error = DocumentExistsError("doc1", sha256_match=True)

        assert error.doc_id == "doc1"
        assert error.sha256_match is True
        assert "already exists with same content" in str(error)

    def test_error_with_sha256_mismatch(self) -> None:
        """Error message for changed content."""
        error = DocumentExistsError("doc1", sha256_match=False)

        assert error.doc_id == "doc1"
        assert error.sha256_match is False
        assert "--force" in str(error)
