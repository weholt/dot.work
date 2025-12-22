"""Integration tests for kgshred.db module."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

import pytest

from dot_work.knowledge_graph.db import Database, Edge, Node


@pytest.mark.integration
class TestDatabasePersistence:
    """Tests for database persistence across sessions."""

    def test_data_persists_across_connections(self, tmp_path: Path) -> None:
        """Data persists after closing and reopening database."""
        db_path = tmp_path / "persist.sqlite"

        # First session - create data
        db1 = Database(db_path)
        db1.insert_document("doc1", "/test.md", b"# Test Content")
        node = db1.insert_node(Node(
            node_pk=None,
            short_id="pers",
            full_id="doc1/h1/pers",
            doc_id="doc1",
            kind="heading",
            title="Persistent Node",
        ))
        db1.fts_index_node(node.node_pk, "Persistent Node", "This should persist", "pers")  # type: ignore
        db1.close()

        # Second session - verify data
        db2 = Database(db_path)
        doc = db2.get_document("doc1")
        assert doc is not None
        assert doc.source_path == "/test.md"

        fetched_node = db2.get_node_by_short_id("pers")
        assert fetched_node is not None
        assert fetched_node.title == "Persistent Node"

        # FTS should also persist
        results = db2.fts_search("persist")
        assert len(results) >= 1

        db2.close()


@pytest.mark.integration
class TestDatabaseConcurrency:
    """Tests for concurrent database access."""

    def test_concurrent_reads(self, tmp_path: Path) -> None:
        """Multiple threads can read simultaneously."""
        db_path = tmp_path / "concurrent.sqlite"

        # Setup data
        db = Database(db_path)
        db.insert_document("doc1", "/test.md", b"content")
        db.insert_nodes_batch([
            Node(
                node_pk=None,
                short_id=f"c{i:03d}",
                full_id=f"doc1/para/c{i:03d}",
                doc_id="doc1",
                kind="para",
            )
            for i in range(100)
        ])
        db.close()

        results: list[int] = []
        errors: list[Exception] = []

        def read_nodes() -> None:
            try:
                thread_db = Database(db_path)
                nodes = thread_db.get_nodes_by_doc_id("doc1")
                results.append(len(nodes))
                thread_db.close()
            except Exception as e:
                errors.append(e)

        # Start multiple reader threads
        threads = [threading.Thread(target=read_nodes) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert all(r == 100 for r in results)

    def test_wal_mode_enabled(self, tmp_path: Path) -> None:
        """WAL mode is enabled for better concurrency."""
        db_path = tmp_path / "wal.sqlite"
        db = Database(db_path)

        mode = db.get_pragma("journal_mode")
        assert mode == "wal"

        db.close()


@pytest.mark.integration
class TestLargeDocuments:
    """Tests for handling large documents."""

    def test_large_document_insert(self, tmp_path: Path) -> None:
        """Large documents can be inserted and retrieved."""
        db_path = tmp_path / "large.sqlite"
        db = Database(db_path)

        # 1MB document
        large_content = b"# " + b"A" * (1024 * 1024)

        doc = db.insert_document("large", "/large.md", large_content)
        assert len(doc.raw) > 1024 * 1024

        fetched = db.get_document("large")
        assert fetched is not None
        assert fetched.raw == large_content

        db.close()

    def test_many_nodes(self, tmp_path: Path) -> None:
        """Can insert and query many nodes."""
        db_path = tmp_path / "many.sqlite"
        db = Database(db_path)
        db.insert_document("doc1", "/test.md", b"content")

        # Insert 1000 nodes
        nodes = [
            Node(
                node_pk=None,
                short_id=f"m{i:04d}",
                full_id=f"doc1/para/m{i:04d}",
                doc_id="doc1",
                kind="para",
                start=i * 10,
                end=i * 10 + 5,
            )
            for i in range(1000)
        ]

        result = db.insert_nodes_batch(nodes)
        assert len(result) == 1000

        fetched = db.get_nodes_by_doc_id("doc1")
        assert len(fetched) == 1000

        db.close()


@pytest.mark.integration
class TestFTSPerformance:
    """Tests for FTS search performance."""

    def test_fts_with_many_nodes(self, tmp_path: Path) -> None:
        """FTS performs well with many indexed nodes."""
        db_path = tmp_path / "fts_perf.sqlite"
        db = Database(db_path)
        db.insert_document("doc1", "/test.md", b"content")

        # Insert and index 500 nodes
        nodes = db.insert_nodes_batch([
            Node(
                node_pk=None,
                short_id=f"f{i:04d}",
                full_id=f"doc1/para/f{i:04d}",
                doc_id="doc1",
                kind="para",
                title=f"Topic {i % 10}",
            )
            for i in range(500)
        ])

        for node in nodes:
            db.fts_index_node(
                node.node_pk,  # type: ignore
                node.title,
                f"Content about topic {(node.node_pk or 0) % 10} with keywords",
                node.short_id,
            )

        # Search should complete quickly
        start = time.time()
        results = db.fts_search("topic 5", limit=20)
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 1.0  # Should be fast

        db.close()


@pytest.mark.integration
class TestTransactionIsolation:
    """Tests for transaction isolation."""

    def test_uncommitted_changes_not_visible(self, tmp_path: Path) -> None:
        """Uncommitted changes are not visible to other connections."""
        db_path = tmp_path / "isolation.sqlite"

        # Create database with WAL mode
        db1 = Database(db_path)
        db1._get_connection()  # Initialize
        db1.close()

        # Connection 1 starts a transaction
        conn1 = sqlite3.connect(db_path)
        conn1.execute("BEGIN TRANSACTION")
        conn1.execute(
            "INSERT INTO documents (doc_id, source_path, sha256, created_at, raw) "
            "VALUES (?, ?, ?, ?, ?)",
            ("iso1", "/test.md", "abc", 1000, b"test"),
        )
        # NOT committed

        # Connection 2 should not see it
        db2 = Database(db_path)
        doc = db2.get_document("iso1")
        assert doc is None

        # Commit and verify
        conn1.commit()
        conn1.close()

        doc = db2.get_document("iso1")
        assert doc is not None

        db2.close()
