"""Tests for scope-aware retrieval in search_fts and search_semantic."""

from __future__ import annotations

from pathlib import Path

import pytest

from kgshred.db import Database, Node
from kgshred.search_fts import ScopeFilter, search
from kgshred.search_semantic import ScopeFilter as SemanticScopeFilter


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create a database with test data including collections and topics."""
    database = Database(tmp_path / "test.db")

    # Create test documents
    doc1_raw = b"# Project A\nThis is about Python programming."
    doc2_raw = b"# Project B\nThis is about Rust development."
    doc3_raw = b"# Shared Knowledge\nThis is shared across projects."

    database.insert_document("doc1", "/test/doc1.md", doc1_raw)
    database.insert_document("doc2", "/test/doc2.md", doc2_raw)
    database.insert_document("doc3", "/test/doc3.md", doc3_raw)

    # Create test nodes
    node1 = database.insert_node(
        Node(
            node_pk=None,
            full_id="full-n001",
            short_id="N001",
            doc_id="doc1",
            kind="heading",
            level=1,
            title="Python Guide",
            start=0,
            end=50,
        )
    )
    node2 = database.insert_node(
        Node(
            node_pk=None,
            full_id="full-n002",
            short_id="N002",
            doc_id="doc1",
            kind="paragraph",
            level=0,
            title=None,
            start=50,
            end=100,
        )
    )
    node3 = database.insert_node(
        Node(
            node_pk=None,
            full_id="full-n003",
            short_id="N003",
            doc_id="doc2",
            kind="heading",
            level=1,
            title="Rust Guide",
            start=0,
            end=50,
        )
    )
    node4 = database.insert_node(
        Node(
            node_pk=None,
            full_id="full-n004",
            short_id="N004",
            doc_id="doc3",
            kind="heading",
            level=1,
            title="Shared Content",
            start=0,
            end=60,
        )
    )

    # Index nodes for FTS
    database.fts_index_node(node1.node_pk, "Python Guide", "Python programming tutorial", "N001")
    database.fts_index_node(node2.node_pk, None, "Python is a great language", "N002")
    database.fts_index_node(node3.node_pk, "Rust Guide", "Rust programming tutorial", "N003")
    database.fts_index_node(node4.node_pk, "Shared Content", "Shared programming knowledge", "N004")

    # Create collections (projects)
    database.create_collection("proj-a", "project", "Project A")
    database.create_collection("proj-b", "project", "Project B")

    # Add nodes to collections using full_id (the stable identifier)
    database.add_member_to_collection("proj-a", "node", node1.full_id)
    database.add_member_to_collection("proj-a", "node", node2.full_id)
    database.add_member_to_collection("proj-b", "node", node3.full_id)

    # Create topics
    database.create_topic("topic-python", "python")
    database.create_topic("topic-rust", "rust")
    database.create_topic("topic-shared", "shared")
    database.create_topic("topic-deprecated", "deprecated")

    # Tag nodes with topics using full_id (the stable identifier)
    database.tag_with_topic("topic-python", "node", node1.full_id)
    database.tag_with_topic("topic-python", "node", node2.full_id)
    database.tag_with_topic("topic-rust", "node", node3.full_id)
    database.tag_with_topic("topic-shared", "node", node4.full_id)

    return database


class TestFTSProjectScoping:
    """Test FTS search with project scope filter."""

    def test_search_scoped_to_project(self, db: Database) -> None:
        """Search with --project should only return project members."""
        scope = ScopeFilter(project="Project A")
        results = search(db, "Python", scope=scope)

        # Should only return nodes from Project A
        short_ids = {r.node.short_id for r in results}
        assert "N001" in short_ids or "N002" in short_ids
        assert "N003" not in short_ids  # Project B node

    def test_search_excludes_non_members(self, db: Database) -> None:
        """Non-member nodes should not appear in scoped search."""
        scope = ScopeFilter(project="Project B")
        results = search(db, "programming", scope=scope)

        short_ids = {r.node.short_id for r in results}
        # Only Project B member should appear
        assert "N001" not in short_ids
        assert "N002" not in short_ids

    def test_search_project_not_found_error(self, db: Database) -> None:
        """Unknown project name should raise error."""
        scope = ScopeFilter(project="Nonexistent Project")
        with pytest.raises(ValueError, match="Project not found"):
            search(db, "Python", scope=scope)


class TestFTSTopicFiltering:
    """Test FTS search with topic filters."""

    def test_search_with_topic_filter(self, db: Database) -> None:
        """--topic should limit to tagged nodes."""
        scope = ScopeFilter(topics=["python"])
        results = search(db, "programming", scope=scope)

        short_ids = {r.node.short_id for r in results}
        # Only Python-tagged nodes
        for short_id in short_ids:
            assert short_id in ("N001", "N002")

    def test_search_with_multiple_topics(self, db: Database) -> None:
        """Multiple --topic should be OR (union)."""
        scope = ScopeFilter(topics=["python", "rust"])
        results = search(db, "programming", scope=scope)

        short_ids = {r.node.short_id for r in results}
        # Should include both Python and Rust tagged nodes
        assert any(sid in short_ids for sid in ("N001", "N002", "N003"))

    def test_search_exclude_topic(self, db: Database) -> None:
        """--exclude-topic should remove matching nodes."""
        scope = ScopeFilter(exclude_topics=["rust"])
        results = search(db, "programming", scope=scope)

        short_ids = {r.node.short_id for r in results}
        # Rust node should be excluded
        assert "N003" not in short_ids

    def test_search_include_shared(self, db: Database) -> None:
        """--include-shared should add 'shared' tagged nodes."""
        scope = ScopeFilter(project="Project A", include_shared=True)
        results = search(db, "programming", scope=scope)

        short_ids = {r.node.short_id for r in results}
        # Should include shared node even though not in Project A
        assert "N004" in short_ids


class TestFTSScopeCombinations:
    """Test FTS search with combined scope filters."""

    def test_search_project_and_topic(self, db: Database) -> None:
        """Project + topic should intersect filters."""
        scope = ScopeFilter(project="Project A", topics=["python"])
        results = search(db, "Python", scope=scope)

        # Should only return nodes in Project A AND tagged python
        for r in results:
            assert r.node.short_id in ("N001", "N002")

    def test_search_project_topic_exclude(self, db: Database) -> None:
        """All filters should combine correctly."""
        scope = ScopeFilter(
            project="Project A",
            topics=["python"],
            exclude_topics=["deprecated"],
        )
        results = search(db, "programming", scope=scope)

        # Results should be in Project A, tagged python, not tagged deprecated
        for r in results:
            assert r.node.short_id in ("N001", "N002")

    def test_search_global_default(self, db: Database) -> None:
        """No scope should search all content."""
        results = search(db, "programming")

        # Should return results from all documents
        assert len(results) >= 1


class TestFTSEdgeCases:
    """Test FTS search edge cases."""

    def test_search_scope_empty_project(self, db: Database) -> None:
        """Empty project should return empty results."""
        # Create an empty project
        db.create_collection("empty-proj", "project", "Empty Project")

        scope = ScopeFilter(project="Empty Project")
        results = search(db, "Python", scope=scope)

        assert results == []

    def test_search_scope_no_matches(self, db: Database) -> None:
        """Scope with no matching nodes should return empty."""
        db.create_topic("topic-rare", "rare-topic")

        scope = ScopeFilter(topics=["rare-topic"])
        results = search(db, "Python", scope=scope)

        assert results == []

    def test_search_topic_not_found_error(self, db: Database) -> None:
        """Unknown topic name should raise error."""
        scope = ScopeFilter(topics=["nonexistent-topic"])
        with pytest.raises(ValueError, match="Topic not found"):
            search(db, "Python", scope=scope)


class TestSemanticScoping:
    """Test semantic search with scope filters."""

    def test_semantic_scope_filter_exists(self) -> None:
        """ScopeFilter should be available for semantic search."""
        scope = SemanticScopeFilter(project="test")
        assert scope.project == "test"
        assert scope.topics == []
        assert scope.exclude_topics == []
        assert scope.include_shared is False

    def test_semantic_scope_filter_with_all_options(self) -> None:
        """ScopeFilter should accept all options."""
        scope = SemanticScopeFilter(
            project="my-project",
            topics=["topic1", "topic2"],
            exclude_topics=["bad-topic"],
            include_shared=True,
        )
        assert scope.project == "my-project"
        assert scope.topics == ["topic1", "topic2"]
        assert scope.exclude_topics == ["bad-topic"]
        assert scope.include_shared is True


class TestScopeFilterDataclass:
    """Test ScopeFilter dataclass behavior."""

    def test_scope_filter_defaults(self) -> None:
        """ScopeFilter should have sensible defaults."""
        scope = ScopeFilter()
        assert scope.project is None
        assert scope.topics == []
        assert scope.exclude_topics == []
        assert scope.include_shared is False

    def test_scope_filter_with_project_only(self) -> None:
        """ScopeFilter with project only."""
        scope = ScopeFilter(project="test-project")
        assert scope.project == "test-project"
        assert scope.topics == []

    def test_scope_filter_with_topics_only(self) -> None:
        """ScopeFilter with topics only."""
        scope = ScopeFilter(topics=["topic1", "topic2"])
        assert scope.project is None
        assert scope.topics == ["topic1", "topic2"]

    def test_scope_filter_mutable_defaults(self) -> None:
        """ScopeFilter lists should not share state."""
        scope1 = ScopeFilter()
        scope2 = ScopeFilter()
        scope1.topics.append("test")
        assert scope2.topics == []  # Should not be affected
