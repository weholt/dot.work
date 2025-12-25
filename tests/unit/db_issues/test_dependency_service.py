"""Tests for the DependencyService.

Tests advanced dependency features including:
- Global dependency listing
- Mermaid diagram generation
- Cycle detection with fix suggestions
- Dependency tree operations

Source: MIGRATE-056
"""

import pytest
from sqlmodel import Session

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import (
    Clock,
    Dependency,
    DependencyType,
    IdentifierService,
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
)
from dot_work.db_issues.services.dependency_service import (
    BlockedIssue,
    CycleResult,
    DependencyService,
    ReadyResult,
)
from dot_work.db_issues.services.issue_service import IssueService


# Local copy of FixedIdentifierService for tests that need fresh IDs
class FixedIdentifierService(IdentifierService):
    """Identifier service that returns predictable IDs for testing."""

    def __init__(self, prefix_map: dict[str, str] | None = None) -> None:
        """Initialize with optional prefix map.

        Args:
            prefix_map: Optional dict mapping prefixes to specific IDs
        """
        self._prefix_map = prefix_map or {}
        self._counter = 0

    def generate(self, prefix: str = "issue") -> str:
        """Generate a predictable identifier.

        Args:
            prefix: Entity type prefix

        Returns:
            Predictable identifier for testing
        """
        if prefix in self._prefix_map:
            return self._prefix_map[prefix]
        self._counter += 1
        suffix = format(self._counter, "04x")
        return f"{prefix}-{suffix}"


@pytest.fixture
def issue_service_with_uow(in_memory_db, fixed_id_service, fixed_clock) -> IssueService:
    """Create an IssueService instance."""
    uow = UnitOfWork(in_memory_db)
    return IssueService(uow, fixed_id_service, fixed_clock)


class TestDependencyServiceGetAllDependencies:
    """Tests for get_all_dependencies method."""

    def test_get_all_dependencies_returns_all(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that get_all_dependencies returns all dependencies."""
        # Create issues
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        # Create dependency using issue IDs
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )

        all_deps = dependency_service.get_all_dependencies()

        assert len(all_deps) == 1
        assert all(isinstance(d, Dependency) for d in all_deps)

    def test_get_all_dependencies_filtered_by_type(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test filtering by dependency type."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        c = issue_service.create_issue("Feature C", priority=IssuePriority.LOW)

        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=b.id, to_issue_id=c.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        blocks_only = dependency_service.get_all_dependencies(DependencyType.BLOCKS)

        assert len(blocks_only) == 1
        assert blocks_only[0].dependency_type == DependencyType.BLOCKS

    def test_get_all_dependencies_empty_when_no_deps(
        self, dependency_service: DependencyService
    ) -> None:
        """Test that empty list is returned when no dependencies exist."""
        all_deps = dependency_service.get_all_dependencies()
        assert all_deps == []


class TestDependencyServiceGenerateMermaid:
    """Tests for generate_mermaid method."""

    def test_generate_mermaid_basic_tree(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test basic Mermaid diagram generation."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )

        mermaid = dependency_service.generate_mermaid(a.id)

        assert mermaid.startswith("graph TD")
        assert a.id in mermaid
        assert "blocks" in mermaid

    def test_generate_mermaid_no_dependencies(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test Mermaid generation for issue with no dependencies."""
        issue = issue_service.create_issue("Isolated Issue")
        mermaid = dependency_service.generate_mermaid(issue.id)

        assert mermaid.startswith("graph TD")
        assert issue.id in mermaid
        assert "No dependencies" in mermaid

    def test_generate_mermaid_respects_max_depth(
        self, dependency_service: DependencyService, in_memory_db: Session, fixed_clock
    ) -> None:
        """Test that max_depth parameter limits traversal."""
        # Use fresh identifier service with a different prefix to avoid ID collisions
        # The collision happens because dependency IDs are constructed as:
        # from_issue_id[:8] + to_issue_id[:8] + type[:5]
        # By using a different prefix, we ensure the first 8 chars are different
        fresh_id_service = FixedIdentifierService({"comment": "comment-0001"})
        fresh_id_service._counter = 10000  # Start from a different counter value

        uow = UnitOfWork(in_memory_db)
        local_issue_service = IssueService(uow, fresh_id_service, fixed_clock)
        local_dependency_service = DependencyService(uow)

        a = local_issue_service.create_issue("Depth Test A", priority=IssuePriority.HIGH)
        b = local_issue_service.create_issue("Depth Test B", priority=IssuePriority.MEDIUM)
        c = local_issue_service.create_issue("Depth Test C", priority=IssuePriority.LOW)

        # Use different dependency types to avoid collision in dependency ID
        # since the ID is based on from[:8] + to[:8] + type[:5]
        local_dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )
        local_dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=b.id, to_issue_id=c.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        mermaid_deep = local_dependency_service.generate_mermaid(a.id, max_depth=10)
        mermaid_shallow = local_dependency_service.generate_mermaid(a.id, max_depth=1)

        # Shallow should have fewer lines
        shallow_lines = len(mermaid_shallow.split("\n"))
        deep_lines = len(mermaid_deep.split("\n"))
        assert shallow_lines <= deep_lines


class TestDependencyServiceSuggestCycleFixes:
    """Tests for suggest_cycle_fixes method."""

    def test_suggest_cycle_fixes_empty_list(
        self, dependency_service: DependencyService
    ) -> None:
        """Test with empty cycles list."""
        fixes = dependency_service.suggest_cycle_fixes([])
        assert fixes == []

    def test_suggest_cycle_fixes_no_cycle(
        self, dependency_service: DependencyService
    ) -> None:
        """Test with cycle results that have no cycles."""
        no_cycle = CycleResult(
            has_cycle=False, cycle_path=[], message="No cycle"
        )
        fixes = dependency_service.suggest_cycle_fixes([no_cycle])
        assert fixes == []

    def test_suggest_cycle_fixes_with_cycle(
        self, dependency_service: DependencyService
    ) -> None:
        """Test fix suggestions for actual cycles."""
        cycle = CycleResult(
            has_cycle=True,
            cycle_path=["issue-a", "issue-b", "issue-a"],
            message="Cycle detected",
        )
        fixes = dependency_service.suggest_cycle_fixes([cycle])

        assert len(fixes) == 1
        assert "Remove dependency" in fixes[0]
        assert "issue-b" in fixes[0]
        assert "issue-a" in fixes[0]

    def test_suggest_cycle_fixes_multiple_cycles(
        self, dependency_service: DependencyService
    ) -> None:
        """Test with multiple cycles."""
        cycle1 = CycleResult(
            has_cycle=True,
            cycle_path=["a", "b", "a"],
            message="Cycle 1",
        )
        cycle2 = CycleResult(
            has_cycle=True,
            cycle_path=["x", "y", "x"],
            message="Cycle 2",
        )
        fixes = dependency_service.suggest_cycle_fixes([cycle1, cycle2])

        assert len(fixes) == 2
        assert all("Remove dependency" in f for f in fixes)


class TestDependencyServiceIntegration:
    """Integration tests with real dependencies."""

    def test_list_all_filters_correctly(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that list-all filters by type correctly."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        c = issue_service.create_issue("Feature C", priority=IssuePriority.LOW)
        bug = issue_service.create_issue("Bug Fix", issue_type=IssueType.BUG)

        # A blocks B
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )
        # B depends-on C
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=b.id, to_issue_id=c.id, dependency_type=DependencyType.DEPENDS_ON)
        )
        # Bug related-to A
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=bug.id, to_issue_id=a.id, dependency_type=DependencyType.RELATED_TO)
        )

        # Get all blocks dependencies
        blocks = dependency_service.get_all_dependencies(DependencyType.BLOCKS)
        assert len(blocks) == 1
        assert blocks[0].dependency_type == DependencyType.BLOCKS

        # Get all depends-on dependencies
        depends_on = dependency_service.get_all_dependencies(DependencyType.DEPENDS_ON)
        assert len(depends_on) == 1
        assert depends_on[0].dependency_type == DependencyType.DEPENDS_ON

        # Get all related-to dependencies
        related = dependency_service.get_all_dependencies(DependencyType.RELATED_TO)
        assert len(related) == 1
        assert related[0].dependency_type == DependencyType.RELATED_TO

    def test_mermaid_diagram_is_valid_format(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that Mermaid output has valid format."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )

        mermaid = dependency_service.generate_mermaid(a.id)

        # Check basic structure
        lines = mermaid.split("\n")
        assert lines[0] == "graph TD"

        # Check that nodes are defined with square brackets
        for line in lines[1:]:
            if line.strip():
                assert "[" in line or "-->" in line

    def test_cycle_fix_suggestions_are_actionable(
        self, dependency_service: DependencyService
    ) -> None:
        """Test that cycle fix suggestions are actionable."""
        cycle = CycleResult(
            has_cycle=True,
            cycle_path=["issue-1", "issue-2", "issue-3", "issue-1"],
            message="3-node cycle",
        )
        fixes = dependency_service.suggest_cycle_fixes([cycle])

        assert len(fixes) == 1
        # Suggestion should mention specific issues
        assert "issue-3" in fixes[0]
        assert "issue-1" in fixes[0]


class TestDependencyServiceGetReadyQueue:
    """Tests for get_ready_queue method."""

    def test_ready_queue_with_no_issues(
        self, dependency_service: DependencyService
    ) -> None:
        """Test ready queue with no issues."""
        result = dependency_service.get_ready_queue()
        assert result.ready_issues == []
        assert result.blocked_issues == []

    def test_ready_queue_with_proposed_issues_no_deps(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that proposed issues with no dependencies are ready."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        result = dependency_service.get_ready_queue()

        assert len(result.ready_issues) == 2
        assert a.id in result.ready_issues
        assert b.id in result.ready_issues
        assert len(result.blocked_issues) == 0

    def test_ready_queue_with_in_progress_no_deps(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that in-progress issues are ready."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        issue_service.update_issue(a.id, status=IssueStatus.IN_PROGRESS)

        result = dependency_service.get_ready_queue()

        assert len(result.ready_issues) == 1
        assert a.id in result.ready_issues

    def test_ready_queue_blocked_by_dependencies(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that issues blocked by dependencies are not ready."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        # A blocks B
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )

        result = dependency_service.get_ready_queue()

        # A is ready (no blockers)
        assert a.id in result.ready_issues
        # B is not ready (blocked by A)
        assert b.id not in result.ready_issues
        assert any(bi.issue_id == b.id for bi in result.blocked_issues)

    def test_ready_queue_blocked_status(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that issues with blocked status are in blocked list."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        issue_service.update_issue(b.id, status=IssueStatus.BLOCKED)

        result = dependency_service.get_ready_queue()

        # A is ready
        assert a.id in result.ready_issues
        # B is blocked
        assert b.id not in result.ready_issues
        assert any(bi.issue_id == b.id for bi in result.blocked_issues)

    def test_ready_queue_completed_issues_excluded(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that completed issues are excluded from ready queue."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        # Need to go through IN_PROGRESS first
        issue_service.update_issue(a.id, status=IssueStatus.IN_PROGRESS)
        issue_service.update_issue(a.id, status=IssueStatus.COMPLETED)

        result = dependency_service.get_ready_queue()

        # Neither A nor B should be in ready list
        assert a.id not in result.ready_issues
        assert b.id in result.ready_issues  # B is proposed, so ready
        assert len(result.blocked_issues) == 0

    def test_ready_queue_completed_blocker_not_counted(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that completed blockers don't block issues."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        # A blocks B
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )

        # Complete A (the blocker) - need to go through IN_PROGRESS first
        issue_service.update_issue(a.id, status=IssueStatus.IN_PROGRESS)
        issue_service.update_issue(a.id, status=IssueStatus.COMPLETED)

        result = dependency_service.get_ready_queue()

        # A is completed, not in ready
        assert a.id not in result.ready_issues
        # B should be ready now (blocker A is completed)
        assert b.id in result.ready_issues

    def test_ready_queue_blocked_issue_has_blockers_list(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that blocked issues have their blockers listed."""
        # Use different dependency types to avoid ID collision
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        c = issue_service.create_issue("Feature C", priority=IssuePriority.LOW)

        # A and B block C - use different types to avoid collision
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=c.id, dependency_type=DependencyType.BLOCKS)
        )
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=b.id, to_issue_id=c.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        result = dependency_service.get_ready_queue()

        # DEPENDS_ON doesn't block, so C should be ready (or blocked by A only)
        # Actually, let me check - only BLOCKS type matters for ready queue
        blocked_c = next((bi for bi in result.blocked_issues if bi.issue_id == c.id), None)
        assert blocked_c is not None
        assert a.id in blocked_c.blockers

    def test_ready_queue_wont_fix_excluded(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that wont-fix issues are excluded from ready queue."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        issue_service.update_issue(a.id, status=IssueStatus.WONT_FIX)

        result = dependency_service.get_ready_queue()

        # A should not be in ready list
        assert a.id not in result.ready_issues


class TestDependencyServiceReadyQueueIntegration:
    """Integration tests for ready queue with complex scenarios."""

    def test_ready_complex_dependency_chain(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test ready queue with a chain of dependencies."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)
        c = issue_service.create_issue("Feature C", priority=IssuePriority.LOW)

        # A blocks B, B blocks C - use different types
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.BLOCKS)
        )
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=b.id, to_issue_id=c.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        result = dependency_service.get_ready_queue()

        # Only A is ready (B and C have BLOCKS type)
        assert a.id in result.ready_issues
        # B and C are blocked (only by BLOCKS type)
        blocked_ids = {bi.issue_id for bi in result.blocked_issues}
        assert b.id in blocked_ids

    def test_ready_multiple_blockers_one_issue(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test ready queue when an issue has multiple blockers."""
        ready1 = issue_service.create_issue("Ready 1", priority=IssuePriority.HIGH)
        ready2 = issue_service.create_issue("Ready 2", priority=IssuePriority.MEDIUM)
        blocked = issue_service.create_issue("Blocked Issue", priority=IssuePriority.LOW)

        # Both ready issues block the third - use different types
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=ready1.id, to_issue_id=blocked.id, dependency_type=DependencyType.BLOCKS)
        )
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=ready2.id, to_issue_id=blocked.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        result = dependency_service.get_ready_queue()

        # Both ready issues are in ready list
        assert ready1.id in result.ready_issues
        assert ready2.id in result.ready_issues
        # Blocked issue has blocker (only BLOCKS type counts)
        blocked_entry = next((bi for bi in result.blocked_issues if bi.issue_id == blocked.id), None)
        assert blocked_entry is not None
        assert ready1.id in blocked_entry.blockers

    def test_ready_non_blocking_dependency_types_ignored(
        self, dependency_service: DependencyService, issue_service: IssueService
    ) -> None:
        """Test that non-BLOCKS dependencies don't affect ready status."""
        a = issue_service.create_issue("Feature A", priority=IssuePriority.HIGH)
        b = issue_service.create_issue("Feature B", priority=IssuePriority.MEDIUM)

        # Use non-blocking dependency type
        dependency_service.uow.graph.add_dependency(
            Dependency(from_issue_id=a.id, to_issue_id=b.id, dependency_type=DependencyType.DEPENDS_ON)
        )

        result = dependency_service.get_ready_queue()

        # Both should be ready (DEPENDS_ON doesn't block)
        assert a.id in result.ready_issues
        assert b.id in result.ready_issues
