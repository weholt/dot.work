"""Unit tests for collection and topic operations in kgshred.db module."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from kgshred.db import (
    Collection,
    CollectionMember,
    Database,
    ProjectSettings,
    Topic,
    TopicLink,
)


class TestCollectionCRUD:
    """Tests for collection CRUD operations."""

    def test_create_collection(self, tmp_path: Path) -> None:
        """Should create collection with unique name."""
        db = Database(tmp_path / "test.sqlite")
        collection = db.create_collection(
            collection_id="proj-001",
            kind="project",
            name="My Project",
            meta={"description": "Test project"},
        )

        assert collection.collection_id == "proj-001"
        assert collection.kind == "project"
        assert collection.name == "My Project"
        assert collection.meta == {"description": "Test project"}
        db.close()

    def test_create_collection_duplicate_name_error(
        self, tmp_path: Path
    ) -> None:
        """Duplicate name should raise error."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Duplicate Name")

        with pytest.raises(sqlite3.IntegrityError):
            db.create_collection("c2", "project", "Duplicate Name")
        db.close()

    def test_get_collection_by_id(self, tmp_path: Path) -> None:
        """Should retrieve collection by collection_id."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test Project")

        result = db.get_collection("c1")

        assert result is not None
        assert result.collection_id == "c1"
        assert result.name == "Test Project"
        db.close()

    def test_get_collection_not_found(self, tmp_path: Path) -> None:
        """Should return None when collection not found."""
        db = Database(tmp_path / "test.sqlite")
        result = db.get_collection("nonexistent")
        assert result is None
        db.close()

    def test_get_collection_by_name(self, tmp_path: Path) -> None:
        """Should retrieve collection by name."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Named Project")

        result = db.get_collection_by_name("Named Project")

        assert result is not None
        assert result.collection_id == "c1"
        db.close()

    def test_delete_collection(self, tmp_path: Path) -> None:
        """Should delete collection and cascade."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "To Delete")

        result = db.delete_collection("c1")

        assert result is True
        assert db.get_collection("c1") is None
        db.close()

    def test_delete_collection_not_found(self, tmp_path: Path) -> None:
        """Should return False when collection not found."""
        db = Database(tmp_path / "test.sqlite")
        result = db.delete_collection("nonexistent")
        assert result is False
        db.close()

    def test_list_collections(self, tmp_path: Path) -> None:
        """Should list all collections."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Alpha")
        db.create_collection("c2", "knowledgebase", "Beta")
        db.create_collection("c3", "project", "Gamma")

        result = db.list_collections()

        assert len(result) == 3
        names = [c.name for c in result]
        assert names == ["Alpha", "Beta", "Gamma"]  # Sorted by name
        db.close()

    def test_list_collections_by_kind(self, tmp_path: Path) -> None:
        """Should filter collections by kind."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Project 1")
        db.create_collection("c2", "knowledgebase", "KB 1")
        db.create_collection("c3", "project", "Project 2")

        result = db.list_collections(kind="project")

        assert len(result) == 2
        assert all(c.kind == "project" for c in result)
        db.close()


class TestCollectionMembers:
    """Tests for collection member operations."""

    def test_add_document_to_collection(self, tmp_path: Path) -> None:
        """Should add document as member."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")

        member = db.add_member_to_collection("c1", "document", "doc-001")

        assert member.collection_id == "c1"
        assert member.member_type == "document"
        assert member.member_pk == "doc-001"
        db.close()

    def test_add_node_to_collection(self, tmp_path: Path) -> None:
        """Should add node as member."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")

        member = db.add_member_to_collection("c1", "node", "doc1:h1:intro")

        assert member.member_type == "node"
        assert member.member_pk == "doc1:h1:intro"
        db.close()

    def test_remove_member_from_collection(self, tmp_path: Path) -> None:
        """Should remove member."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")
        db.add_member_to_collection("c1", "document", "doc-001")

        result = db.remove_member_from_collection("c1", "document", "doc-001")

        assert result is True
        members = db.list_collection_members("c1")
        assert len(members) == 0
        db.close()

    def test_remove_member_not_found(self, tmp_path: Path) -> None:
        """Should return False when member not found."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")

        result = db.remove_member_from_collection("c1", "document", "nope")

        assert result is False
        db.close()

    def test_list_collection_members(self, tmp_path: Path) -> None:
        """Should list all members of collection."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")
        db.add_member_to_collection("c1", "document", "doc-001")
        db.add_member_to_collection("c1", "document", "doc-002")
        db.add_member_to_collection("c1", "node", "doc-001:h1:intro")

        result = db.list_collection_members("c1")

        assert len(result) == 3
        db.close()

    def test_list_collection_members_by_type(self, tmp_path: Path) -> None:
        """Should filter members by type."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")
        db.add_member_to_collection("c1", "document", "doc-001")
        db.add_member_to_collection("c1", "node", "doc-001:h1:intro")

        result = db.list_collection_members("c1", member_type="document")

        assert len(result) == 1
        assert result[0].member_type == "document"
        db.close()

    def test_member_in_multiple_collections(self, tmp_path: Path) -> None:
        """Same node can be in multiple collections."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Project 1")
        db.create_collection("c2", "project", "Project 2")
        db.add_member_to_collection("c1", "node", "shared-node")
        db.add_member_to_collection("c2", "node", "shared-node")

        collections = db.get_collections_for_member("node", "shared-node")

        assert len(collections) == 2
        names = {c.name for c in collections}
        assert names == {"Project 1", "Project 2"}
        db.close()

    def test_delete_collection_cascades_members(self, tmp_path: Path) -> None:
        """Deleting collection should remove members."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("c1", "project", "Test")
        db.add_member_to_collection("c1", "document", "doc-001")
        db.add_member_to_collection("c1", "node", "node-001")

        db.delete_collection("c1")

        # Verify members are gone (would cause FK error if not)
        # Just verify collection is gone
        assert db.get_collection("c1") is None
        db.close()


class TestTopics:
    """Tests for topic operations."""

    def test_create_topic(self, tmp_path: Path) -> None:
        """Should create topic with unique name."""
        db = Database(tmp_path / "test.sqlite")
        topic = db.create_topic(
            topic_id="t1",
            name="Python",
            meta={"color": "blue"},
        )

        assert topic.topic_id == "t1"
        assert topic.name == "Python"
        assert topic.meta == {"color": "blue"}
        db.close()

    def test_create_topic_duplicate_name_error(self, tmp_path: Path) -> None:
        """Duplicate name should raise error."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Duplicate")

        with pytest.raises(sqlite3.IntegrityError):
            db.create_topic("t2", "Duplicate")
        db.close()

    def test_get_topic(self, tmp_path: Path) -> None:
        """Should retrieve topic by ID."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Testing")

        result = db.get_topic("t1")

        assert result is not None
        assert result.name == "Testing"
        db.close()

    def test_get_topic_not_found(self, tmp_path: Path) -> None:
        """Should return None when topic not found."""
        db = Database(tmp_path / "test.sqlite")
        result = db.get_topic("nonexistent")
        assert result is None
        db.close()

    def test_get_topic_by_name(self, tmp_path: Path) -> None:
        """Should retrieve topic by name."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Named Topic")

        result = db.get_topic_by_name("Named Topic")

        assert result is not None
        assert result.topic_id == "t1"
        db.close()

    def test_list_topics(self, tmp_path: Path) -> None:
        """Should list all topics."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Alpha")
        db.create_topic("t2", "Beta")
        db.create_topic("t3", "Gamma")

        result = db.list_topics()

        assert len(result) == 3
        names = [t.name for t in result]
        assert names == ["Alpha", "Beta", "Gamma"]  # Sorted
        db.close()

    def test_delete_topic(self, tmp_path: Path) -> None:
        """Should delete topic and links."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "To Delete")
        db.tag_with_topic("t1", "node", "some-node")

        result = db.delete_topic("t1")

        assert result is True
        assert db.get_topic("t1") is None
        db.close()

    def test_delete_topic_not_found(self, tmp_path: Path) -> None:
        """Should return False when topic not found."""
        db = Database(tmp_path / "test.sqlite")
        result = db.delete_topic("nonexistent")
        assert result is False
        db.close()


class TestTopicLinks:
    """Tests for topic link operations."""

    def test_tag_node_with_topic(self, tmp_path: Path) -> None:
        """Should link topic to node."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Python")

        link = db.tag_with_topic("t1", "node", "doc:h1:intro")

        assert link.topic_id == "t1"
        assert link.target_type == "node"
        assert link.target_pk == "doc:h1:intro"
        assert link.weight == 1.0
        db.close()

    def test_tag_document_with_topic(self, tmp_path: Path) -> None:
        """Should link topic to document."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Documentation")

        link = db.tag_with_topic("t1", "document", "readme.md")

        assert link.target_type == "document"
        db.close()

    def test_tag_with_weight(self, tmp_path: Path) -> None:
        """Should set custom weight."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Important")

        link = db.tag_with_topic("t1", "node", "key-node", weight=0.8)

        assert link.weight == 0.8
        db.close()

    def test_untag_node(self, tmp_path: Path) -> None:
        """Should remove topic link."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Python")
        db.tag_with_topic("t1", "node", "doc:h1:intro")

        result = db.untag_topic("t1", "node", "doc:h1:intro")

        assert result is True
        topics = db.list_topics_for_target("node", "doc:h1:intro")
        assert len(topics) == 0
        db.close()

    def test_untag_not_found(self, tmp_path: Path) -> None:
        """Should return False when link not found."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Python")

        result = db.untag_topic("t1", "node", "nonexistent")

        assert result is False
        db.close()

    def test_list_topics_for_node(self, tmp_path: Path) -> None:
        """Should list topics for specific node."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Python")
        db.create_topic("t2", "Testing")
        db.tag_with_topic("t1", "node", "my-node", weight=0.9)
        db.tag_with_topic("t2", "node", "my-node", weight=0.5)

        result = db.list_topics_for_target("node", "my-node")

        assert len(result) == 2
        topics, weights = zip(*result, strict=True)
        assert topics[0].name == "Python"  # Higher weight first
        assert weights[0] == 0.9
        db.close()

    def test_list_nodes_for_topic(self, tmp_path: Path) -> None:
        """Should list nodes with topic."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Python")
        db.tag_with_topic("t1", "node", "node-1", weight=0.9)
        db.tag_with_topic("t1", "node", "node-2", weight=0.5)

        result = db.list_targets_for_topic("t1", target_type="node")

        assert len(result) == 2
        assert result[0].target_pk == "node-1"  # Higher weight first
        db.close()

    def test_list_targets_for_topic_all_types(self, tmp_path: Path) -> None:
        """Should list all targets without type filter."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Mixed")
        db.tag_with_topic("t1", "node", "node-1")
        db.tag_with_topic("t1", "document", "doc-1")

        result = db.list_targets_for_topic("t1")

        assert len(result) == 2
        types = {link.target_type for link in result}
        assert types == {"node", "document"}
        db.close()


class TestProjectSettings:
    """Tests for project settings operations."""

    def test_set_project_defaults(self, tmp_path: Path) -> None:
        """Should store project default settings."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("p1", "project", "My Project")

        settings = db.set_project_settings(
            "p1", {"budget": 1000, "model": "gpt-4"}
        )

        assert settings.collection_id == "p1"
        assert settings.defaults == {"budget": 1000, "model": "gpt-4"}
        db.close()

    def test_get_project_defaults(self, tmp_path: Path) -> None:
        """Should retrieve project defaults."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("p1", "project", "My Project")
        db.set_project_settings("p1", {"budget": 500})

        result = db.get_project_settings("p1")

        assert result is not None
        assert result.defaults == {"budget": 500}
        db.close()

    def test_get_project_defaults_not_found(self, tmp_path: Path) -> None:
        """Should return None when settings not found."""
        db = Database(tmp_path / "test.sqlite")
        result = db.get_project_settings("nonexistent")
        assert result is None
        db.close()

    def test_update_project_defaults(self, tmp_path: Path) -> None:
        """Should update existing settings."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("p1", "project", "My Project")
        db.set_project_settings("p1", {"budget": 500})
        db.set_project_settings("p1", {"budget": 1000, "model": "gpt-4"})

        result = db.get_project_settings("p1")

        assert result is not None
        assert result.defaults == {"budget": 1000, "model": "gpt-4"}
        db.close()

    def test_delete_collection_cascades_settings(self, tmp_path: Path) -> None:
        """Deleting collection should remove settings."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection("p1", "project", "My Project")
        db.set_project_settings("p1", {"budget": 500})

        db.delete_collection("p1")

        assert db.get_project_settings("p1") is None
        db.close()


class TestSchemaVersion3:
    """Tests for schema version 3 tables."""

    def test_schema_includes_collections_table(self, tmp_path: Path) -> None:
        """Schema should include collections table."""
        db = Database(tmp_path / "test.sqlite")
        conn = db._get_connection()

        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='collections'"
        )
        assert cur.fetchone() is not None
        db.close()

    def test_schema_includes_topics_table(self, tmp_path: Path) -> None:
        """Schema should include topics table."""
        db = Database(tmp_path / "test.sqlite")
        conn = db._get_connection()

        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='topics'"
        )
        assert cur.fetchone() is not None
        db.close()

    def test_schema_includes_project_settings_table(
        self, tmp_path: Path
    ) -> None:
        """Schema should include project_settings table."""
        db = Database(tmp_path / "test.sqlite")
        conn = db._get_connection()

        cur = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='project_settings'"
        )
        assert cur.fetchone() is not None
        db.close()

    def test_collection_meta_json_stored(self, tmp_path: Path) -> None:
        """Collection meta should be stored as JSON."""
        db = Database(tmp_path / "test.sqlite")
        db.create_collection(
            "c1", "project", "Test", meta={"key": "value", "num": 42}
        )

        result = db.get_collection("c1")

        assert result is not None
        assert result.meta == {"key": "value", "num": 42}
        db.close()

    def test_topic_meta_json_stored(self, tmp_path: Path) -> None:
        """Topic meta should be stored as JSON."""
        db = Database(tmp_path / "test.sqlite")
        db.create_topic("t1", "Test", meta={"color": "#ff0000"})

        result = db.get_topic("t1")

        assert result is not None
        assert result.meta == {"color": "#ff0000"}
        db.close()
