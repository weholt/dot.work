"""Tests for EpicService business logic layer."""

from datetime import UTC, datetime

import pytest

from dot_work.db_issues.domain.entities import Clock, Epic, EpicStatus
from dot_work.db_issues.services import EpicService


class TestEpicServiceCreate:
    """Tests for epic creation."""

    def test_create_epic_generates_id(
        self, epic_service: EpicService, fixed_clock: Clock
    ) -> None:
        """Test that creating an epic generates an ID."""
        epic = epic_service.create_epic("Test Epic")

        assert epic.id is not None
        assert epic.id.startswith("epic-")
        assert epic.title == "Test Epic"
        assert epic.status == EpicStatus.OPEN

    def test_create_epic_with_custom_id(self, epic_service: EpicService) -> None:
        """Test creating an epic with a custom ID."""
        epic = epic_service.create_epic("Custom Epic", custom_id="CUSTOM-001")

        assert epic.id == "CUSTOM-001"
        assert epic.title == "Custom Epic"

    def test_create_epic_with_parent(
        self, epic_service: EpicService, fixed_clock: Clock
    ) -> None:
        """Test creating an epic with a parent."""
        parent = epic_service.create_epic("Parent Epic")
        child = epic_service.create_epic("Child Epic", parent_epic_id=parent.id)

        assert child.parent_epic_id == parent.id

    def test_create_epic_with_nonexistent_parent_raises(
        self, epic_service: EpicService
    ) -> None:
        """Test that creating an epic with nonexistent parent raises ValueError."""
        with pytest.raises(ValueError, match="Parent epic"):
            epic_service.create_epic("Child Epic", parent_epic_id="nonexistent")

    def test_create_epic_detects_cycle(self, epic_service: EpicService) -> None:
        """Test that creating a cycle in epic hierarchy is prevented."""
        grandparent = epic_service.create_epic("Grandparent")
        parent = epic_service.create_epic("Parent", parent_epic_id=grandparent.id)
        child = epic_service.create_epic("Child", parent_epic_id=parent.id)

        # Try to create a cycle by making grandparent a child of child
        # This would create: grandparent -> parent -> child -> grandparent (cycle!)
        with pytest.raises(ValueError, match="cycle"):
            epic_service.add_child_epic(child.id, grandparent.id)


class TestEpicServiceGet:
    """Tests for epic retrieval."""

    def test_get_epic_returns_epic(
        self, epic_service: EpicService, fixed_clock: Clock
    ) -> None:
        """Test that get_epic returns the epic."""
        created = epic_service.create_epic("Test Epic")
        retrieved = epic_service.get_epic(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Epic"

    def test_get_epic_returns_none_for_nonexistent(
        self, epic_service: EpicService
    ) -> None:
        """Test that get_epic returns None for nonexistent ID."""
        result = epic_service.get_epic("nonexistent-id")
        assert result is None


class TestEpicServiceList:
    """Tests for epic listing."""

    def test_list_epics_returns_all(
        self, epic_service: EpicService, fixed_clock: Clock
    ) -> None:
        """Test that list_epics returns all created epics."""
        epic_service.create_epic("Epic 1")
        epic_service.create_epic("Epic 2")
        epic_service.create_epic("Epic 3")

        epics = epic_service.list_epics()
        assert len(epics) == 3
        titles = [e.title for e in epics]
        assert "Epic 1" in titles
        assert "Epic 2" in titles
        assert "Epic 3" in titles

    def test_list_epics_filters_by_status(
        self, epic_service: EpicService, fixed_clock: Clock
    ) -> None:
        """Test that list_epics filters by status."""
        epic_service.create_epic("Open Epic")
        epic2 = epic_service.create_epic("In Progress Epic")
        epic_service.update_epic(epic2.id, status=EpicStatus.IN_PROGRESS)

        all_epics = epic_service.list_epics()
        open_epics = epic_service.list_epics(status=EpicStatus.OPEN)

        assert len(all_epics) == 2
        assert len(open_epics) == 1
        assert open_epics[0].title == "Open Epic"


class TestEpicServiceUpdate:
    """Tests for epic updates."""

    def test_update_epic_title(self, epic_service: EpicService) -> None:
        """Test updating epic title."""
        epic = epic_service.create_epic("Original Title")
        updated = epic_service.update_epic(epic.id, title="New Title")

        assert updated is not None
        assert updated.title == "New Title"

    def test_update_epic_description(self, epic_service: EpicService) -> None:
        """Test updating epic description."""
        epic = epic_service.create_epic("Test Epic")
        updated = epic_service.update_epic(epic.id, description="New description")

        assert updated is not None
        assert updated.description == "New description"

    def test_update_epic_status(self, epic_service: EpicService) -> None:
        """Test updating epic status."""
        epic = epic_service.create_epic("Test Epic")
        updated = epic_service.update_epic(epic.id, status=EpicStatus.IN_PROGRESS)

        assert updated is not None
        assert updated.status == EpicStatus.IN_PROGRESS

    def test_update_epic_sets_closed_at_on_completion(
        self, epic_service: EpicService
    ) -> None:
        """Test that closing an epic sets closed_at timestamp."""
        epic = epic_service.create_epic("Test Epic")
        assert epic.closed_at is None

        updated = epic_service.update_epic(epic.id, status=EpicStatus.COMPLETED)
        assert updated is not None
        assert updated.closed_at is not None

    def test_update_nonexistent_epic_returns_none(
        self, epic_service: EpicService
    ) -> None:
        """Test that updating a nonexistent epic returns None."""
        result = epic_service.update_epic("nonexistent", title="New Title")
        assert result is None


class TestEpicServiceDelete:
    """Tests for epic deletion."""

    def test_delete_epic(self, epic_service: EpicService) -> None:
        """Test deleting an epic."""
        epic = epic_service.create_epic("Test Epic")
        deleted = epic_service.delete_epic(epic.id)

        assert deleted is True
        retrieved = epic_service.get_epic(epic.id)
        assert retrieved is None

    def test_delete_nonexistent_epic_returns_false(
        self, epic_service: EpicService
    ) -> None:
        """Test that deleting a nonexistent epic returns False."""
        deleted = epic_service.delete_epic("nonexistent")
        assert deleted is False


class TestEpicServiceChildRelationships:
    """Tests for child epic relationship management."""

    def test_add_child_epic(self, epic_service: EpicService) -> None:
        """Test adding a child epic to a parent."""
        parent = epic_service.create_epic("Parent Epic")
        child = epic_service.create_epic("Child Epic")

        success = epic_service.add_child_epic(parent.id, child.id)

        assert success is True
        retrieved_child = epic_service.get_epic(child.id)
        assert retrieved_child is not None
        assert retrieved_child.parent_epic_id == parent.id

    def test_add_child_epic_with_nonexistent_parent_returns_false(
        self, epic_service: EpicService
    ) -> None:
        """Test adding child with nonexistent parent returns False."""
        child = epic_service.create_epic("Child Epic")
        success = epic_service.add_child_epic("nonexistent", child.id)
        assert success is False

    def test_add_child_epic_with_nonexistent_child_returns_false(
        self, epic_service: EpicService
    ) -> None:
        """Test adding nonexistent child returns False."""
        parent = epic_service.create_epic("Parent Epic")
        success = epic_service.add_child_epic(parent.id, "nonexistent")
        assert success is False

    def test_add_child_epic_detects_cycle(self, epic_service: EpicService) -> None:
        """Test that adding a child that would create a cycle raises ValueError."""
        grandparent = epic_service.create_epic("Grandparent")
        parent = epic_service.create_epic("Parent")
        child = epic_service.create_epic("Child")

        epic_service.add_child_epic(grandparent.id, parent.id)
        epic_service.add_child_epic(parent.id, child.id)

        # Try to make grandparent a child of child - creates cycle
        with pytest.raises(ValueError, match="cycle"):
            epic_service.add_child_epic(child.id, grandparent.id)

    def test_remove_child_epic(self, epic_service: EpicService) -> None:
        """Test removing a child epic from its parent."""
        parent = epic_service.create_epic("Parent Epic")
        child = epic_service.create_epic("Child Epic")

        epic_service.add_child_epic(parent.id, child.id)
        success = epic_service.remove_child_epic(child.id)

        assert success is True
        retrieved_child = epic_service.get_epic(child.id)
        assert retrieved_child is not None
        assert retrieved_child.parent_epic_id is None

    def test_remove_child_epic_without_parent_returns_false(
        self, epic_service: EpicService
    ) -> None:
        """Test removing a child that has no parent returns False."""
        child = epic_service.create_epic("Child Epic")
        success = epic_service.remove_child_epic(child.id)
        assert success is False

    def test_remove_nonexistent_child_epic_returns_false(
        self, epic_service: EpicService
    ) -> None:
        """Test removing a nonexistent child epic returns False."""
        success = epic_service.remove_child_epic("nonexistent")
        assert success is False

    def test_list_child_epics(self, epic_service: EpicService) -> None:
        """Test listing child epics."""
        parent = epic_service.create_epic("Parent Epic")
        child1 = epic_service.create_epic("Child 1")
        child2 = epic_service.create_epic("Child 2")
        unrelated = epic_service.create_epic("Unrelated Epic")

        epic_service.add_child_epic(parent.id, child1.id)
        epic_service.add_child_epic(parent.id, child2.id)

        children = epic_service.list_child_epics(parent.id)

        assert len(children) == 2
        child_ids = [c.id for c in children]
        assert child1.id in child_ids
        assert child2.id in child_ids
        assert unrelated.id not in child_ids

    def test_list_child_epics_empty_for_parent_without_children(
        self, epic_service: EpicService
    ) -> None:
        """Test that listing children for parent with no children returns empty list."""
        parent = epic_service.create_epic("Parent Epic")
        children = epic_service.list_child_epics(parent.id)
        assert len(children) == 0
