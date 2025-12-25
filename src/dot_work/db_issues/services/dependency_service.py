"""Dependency service for analyzing issue relationships.

Provides operations for:
- Circular dependency detection
- Impact analysis (what issues are affected by closing one)
- Dependency tree visualization
- Blocking/blocked relationship queries

Source reference: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/
"""

import logging
from dataclasses import dataclass

from dot_work.db_issues.adapters import UnitOfWork
from dot_work.db_issues.domain.entities import Dependency, DependencyType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImpactResult:
    """Result of an impact analysis query.

    Attributes:
        issue_id: The issue being analyzed
        direct_impact: Issues directly depending on this one
        total_impact: All transitively affected issues
        impact_count: Total number of affected issues
    """

    issue_id: str
    direct_impact: list[Dependency]
    total_impact: list[Dependency]
    impact_count: int


@dataclass(frozen=True)
class CycleResult:
    """Result of a circular dependency check.

    Attributes:
        has_cycle: Whether a cycle exists
        cycle_path: List of issue IDs forming the cycle (if any)
        message: Human-readable description
    """

    has_cycle: bool
    cycle_path: list[str]
    message: str


@dataclass(frozen=True)
class BlockedIssue:
    """An issue that is blocked by dependencies.

    Attributes:
        issue_id: The blocked issue ID
        blockers: List of issue IDs that are blocking this issue
    """

    issue_id: str
    blockers: list[str]


@dataclass(frozen=True)
class ReadyResult:
    """Result of ready queue calculation.

    Attributes:
        ready_issues: List of issue IDs ready to work on
        blocked_issues: List of BlockedIssue with their blockers
    """

    ready_issues: list[str]
    blocked_issues: list[BlockedIssue]


class DependencyService:
    """Service for dependency analysis and cycle detection.

    Coordinates with the dependency repository to provide
    high-level analysis operations on issue dependency graphs.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize dependency service.

        Args:
            uow: Unit of work for transaction management
        """
        self.uow = uow

    def check_circular(self, issue_id: str) -> CycleResult:
        """Check if an issue has circular dependencies.

        Analyzes both incoming and outgoing dependencies to detect
        any cycles that involve the specified issue.

        Args:
            issue_id: Issue identifier to check

        Returns:
            CycleResult with cycle information

        Examples:
            >>> service.check_circular("bd-a1b2")
            CycleResult(has_cycle=True, cycle_path=["bd-a1b2", "bd-c3d4", "bd-a1b2"], ...)
        """
        logger.debug("Checking for circular dependencies: issue_id=%s", issue_id)

        # Check if there's a path from any dependent back to the issue
        visited: set[str] = set()
        path: list[str] = []

        def find_cycle(current: str) -> list[str] | None:
            """Find cycle starting from current node using DFS."""
            if current in path:
                # Found a cycle - extract the cycle portion
                cycle_start = path.index(current)
                return path[cycle_start:] + [current]

            if current in visited:
                return None

            visited.add(current)
            path.append(current)

            # Get all outgoing dependencies from current
            deps = self.uow.graph.get_dependencies(current)

            for dep in deps:
                # Check if there's a path back to the original issue
                if self._has_path_to(dep.to_issue_id, issue_id, set()):
                    result = find_cycle(dep.to_issue_id)
                    if result:
                        return result

            path.pop()
            return None

        cycle = find_cycle(issue_id)

        if cycle:
            logger.info("Circular dependency detected: %s", " -> ".join(cycle))
            return CycleResult(
                has_cycle=True,
                cycle_path=cycle,
                message=f"Circular dependency detected: {' -> '.join(cycle)}",
            )

        return CycleResult(
            has_cycle=False,
            cycle_path=[],
            message=f"No circular dependencies found for issue {issue_id}",
        )

    def check_circular_all(self) -> list[CycleResult]:
        """Check all issues for circular dependencies.

        Performs a graph-wide analysis to find all cycles.

        Returns:
            List of CycleResult objects for issues with cycles

        Examples:
            >>> results = service.check_circular_all()
            >>> for r in results:
            ...     if r.has_cycle:
            ...         print(r.message)
        """
        logger.debug("Checking all issues for circular dependencies")

        # Get all unique issue IDs from dependencies
        all_deps = self.uow.graph.get_all_dependencies()
        all_issue_ids: set[str] = set()

        for dep in all_deps:
            all_issue_ids.add(dep.from_issue_id)
            all_issue_ids.add(dep.to_issue_id)

        results: list[CycleResult] = []
        checked: set[str] = set()

        for issue_id in all_issue_ids:
            if issue_id in checked:
                continue

            result = self.check_circular(issue_id)
            checked.add(issue_id)

            # Also mark all issues in the cycle as checked
            if result.has_cycle:
                checked.update(result.cycle_path)

            if result.has_cycle:
                results.append(result)

        logger.info("Found %d circular dependencies", len(results))
        return results

    def get_impact(self, issue_id: str) -> ImpactResult:
        """Get all issues affected if this issue closes.

        Computes the transitive closure of all issues that
        directly or indirectly depend on the specified issue.

        Args:
            issue_id: Issue to analyze

        Returns:
            ImpactResult with direct and total impact

        Examples:
            >>> impact = service.get_impact("bd-a1b2")
            >>> print(f"Impacts {impact.impact_count} issues")
            Impacts 3 issues
        """
        logger.debug("Computing impact analysis: issue_id=%s", issue_id)

        # Get direct dependents (issues that depend on this one)
        direct = self.uow.graph.get_dependents(issue_id)

        # Get all transitively affected issues
        all_impact: list[Dependency] = []
        visited: set[str] = set()

        def collect_transitive(current: str) -> None:
            """Recursively collect all dependent issues."""
            if current in visited:
                return

            visited.add(current)

            # Get all issues that depend on current
            dependents = self.uow.graph.get_dependents(current)

            for dep in dependents:
                all_impact.append(dep)
                collect_transitive(dep.from_issue_id)

        for dep in direct:
            all_impact.append(dep)
            collect_transitive(dep.from_issue_id)

        # Deduplicate while preserving order
        seen: set[tuple[str, str]] = set()
        unique_impact: list[Dependency] = []
        for dep in all_impact:
            key = (dep.from_issue_id, dep.to_issue_id)
            if key not in seen:
                seen.add(key)
                unique_impact.append(dep)

        return ImpactResult(
            issue_id=issue_id,
            direct_impact=direct,
            total_impact=unique_impact,
            impact_count=len(unique_impact),
        )

    def get_blocked_by(self, issue_id: str) -> list[Dependency]:
        """Get all issues that block this issue (transitive).

        Returns the complete chain of issues that must be completed
        before this issue can be worked on.

        Args:
            issue_id: Issue to analyze

        Returns:
            List of dependencies from blocking issues

        Examples:
            >>> blockers = service.get_blocked_by("bd-a1b2")
            >>> for dep in blockers:
            ...     print(f"{dep.from_issue_id} blocks {dep.to_issue_id}")
        """
        logger.debug("Getting blocking issues: issue_id=%s", issue_id)

        # Get direct dependencies (what this issue depends on)
        all_blocking: list[Dependency] = []
        visited: set[str] = set()

        def collect_blocking(current: str) -> None:
            """Recursively collect all blocking issues."""
            if current in visited:
                return

            visited.add(current)

            # Get all dependencies of current
            deps = self.uow.graph.get_dependencies(current)

            for dep in deps:
                all_blocking.append(dep)
                collect_blocking(dep.to_issue_id)

        collect_blocking(issue_id)

        # Deduplicate while preserving order
        seen: set[tuple[str, str]] = set()
        unique_blocking: list[Dependency] = []
        for dep in all_blocking:
            key = (dep.from_issue_id, dep.to_issue_id)
            if key not in seen:
                seen.add(key)
                unique_blocking.append(dep)

        return unique_blocking

    def get_dependency_tree(
        self, issue_id: str, max_depth: int = 5
    ) -> dict[str, list[tuple[str, str, DependencyType]]]:
        """Get dependency tree for visualization.

        Builds a tree structure showing the hierarchy of dependencies.
        Keys are issue IDs, values are lists of (from_id, to_id, type) tuples.

        Args:
            issue_id: Root issue to build tree from
            max_depth: Maximum depth to traverse (default: 5)

        Returns:
            Dictionary mapping issue IDs to their dependencies

        Examples:
            >>> tree = service.get_dependency_tree("bd-a1b2")
            >>> for parent, children in tree.items():
            ...     print(f"{parent}:")
            ...     for from_id, to_id, dep_type in children:
            ...         print(f"  {from_id} -> {to_id} ({dep_type})")
        """
        logger.debug("Building dependency tree: issue_id=%s, max_depth=%d", issue_id, max_depth)

        tree: dict[str, list[tuple[str, str, DependencyType]]] = {}
        visited: set[str] = set()

        def build_tree(current: str, depth: int) -> None:
            """Recursively build the dependency tree."""
            if depth > max_depth or current in visited:
                return

            visited.add(current)

            # Get all dependencies of current
            deps = self.uow.graph.get_dependencies(current)

            if deps:
                tree[current] = [
                    (dep.from_issue_id, dep.to_issue_id, dep.dependency_type) for dep in deps
                ]

                for dep in deps:
                    build_tree(dep.to_issue_id, depth + 1)

        build_tree(issue_id, 0)

        return tree

    def get_all_dependencies(
        self, dependency_type: DependencyType | None = None
    ) -> list[Dependency]:
        """Get all dependencies in the system, optionally filtered by type.

        Args:
            dependency_type: Optional filter by dependency type

        Returns:
            List of all dependency relationships

        Examples:
            >>> all_deps = service.get_all_dependencies()
            >>> blocks_only = service.get_all_dependencies(DependencyType.BLOCKS)
        """
        all_deps = self.uow.graph.get_all_dependencies()

        if dependency_type:
            return [d for d in all_deps if d.dependency_type == dependency_type]

        return all_deps

    def generate_mermaid(
        self, issue_id: str, max_depth: int = 5
    ) -> str:
        """Generate Mermaid diagram for dependency tree.

        Args:
            issue_id: Root issue to generate diagram from
            max_depth: Maximum depth to traverse (default: 5)

        Returns:
            Mermaid diagram as string

        Examples:
            >>> mermaid = service.generate_mermaid("bd-a1b2")
            >>> print(mermaid)
            graph TD
                bd-a1b2[bd-a1b2: Feature]
                bd-c3d4[bd-c3d4: Test]
                bd-a1b2 -->|blocks| bd-c3d4
        """
        tree = self.get_dependency_tree(issue_id, max_depth)

        if not tree:
            return f"graph TD\n    {issue_id}[{issue_id}: No dependencies]"

        lines = ["graph TD"]
        edges: set[tuple[str, str, str]] = set()
        nodes: set[str] = set()

        def build_mermaid(current: str) -> None:
            """Recursively build Mermaid diagram."""
            if current not in tree:
                return

            # Add node
            issue = self.uow.issues.get(current)
            title = issue.title[:30] if issue else "Unknown"
            label = f"{current}: {title}"
            node_id = current.replace("-", "_")
            nodes.add(f"    {node_id}[{current}: {title}]")

            # Add edges to children
            for _from_id, to_id, dep_type in tree[current]:
                child_id = to_id.replace("-", "_")
                edge_label = dep_type.value
                edge = (node_id, child_id, edge_label)
                if edge not in edges:
                    edges.add(edge)
                    lines.append(f"    {node_id} -->|{edge_label}| {child_id}")

                build_mermaid(to_id)

        build_mermaid(issue_id)

        # Add all nodes first, then edges (skip the initial "graph TD" from lines)
        result_lines = ["graph TD"] + list(nodes) + lines[1:]
        return "\n".join(result_lines)

    def suggest_cycle_fixes(self, cycles: list[CycleResult]) -> list[str]:
        """Suggest fixes for circular dependencies.

        Analyzes cycles and generates suggestions for which dependencies
        to remove to break each cycle.

        Args:
            cycles: List of cycle results to analyze

        Returns:
            List of fix suggestions

        Examples:
            >>> cycles = service.check_circular_all()
            >>> fixes = service.suggest_cycle_fixes(cycles)
            >>> for fix in fixes:
            ...     print(fix)
        """
        suggestions: list[str] = []

        for cycle in cycles:
            if not cycle.has_cycle or len(cycle.cycle_path) < 2:
                continue

            # For a cycle A -> B -> C -> A, suggest removing the last link
            # This is a heuristic - suggest removing the dependency that
            # would create the least disruption
            path = cycle.cycle_path

            if len(path) >= 2:
                # Suggest removing the last dependency in the cycle
                from_issue = path[-2]
                to_issue = path[-1]

                suggestion = (
                    f"Remove dependency: {from_issue} -> {to_issue} "
                    f"(this would break the cycle: {' -> '.join(path)})"
                )
                suggestions.append(suggestion)

        return suggestions

    def get_ready_queue(self) -> ReadyResult:
        """Get ready queue of issues with no blocking dependencies.

        An issue is "ready" if:
        1. Status is "proposed" or "in_progress"
        2. Not in "blocked" status
        3. No open "blocks" dependencies pointing to it

        Returns:
            ReadyResult with ready issue IDs and blocked issues with their blockers

        Examples:
            >>> result = service.get_ready_queue()
            >>> print(f"Ready: {len(result.ready_issues)}")
            >>> for blocked in result.blocked_issues:
            ...     print(f"{blocked.issue_id} blocked by {blocked.blockers}")
        """
        logger.debug("Calculating ready queue")

        from dot_work.db_issues.domain.entities import IssueStatus

        # Get all issues from the repository
        all_issues = self.uow.issues.list_all()

        # Get all BLOCKS dependencies
        all_deps = self.uow.graph.get_all_dependencies()
        blocks_deps = [
            d for d in all_deps if d.dependency_type == DependencyType.BLOCKS
        ]

        # Build a map: issue_id -> list of issues that block it
        # For a blocks relationship (from -> to), "from" blocks "to"
        # So "to" is blocked by "from"
        blocked_by: dict[str, set[str]] = {}
        for dep in blocks_deps:
            if dep.to_issue_id not in blocked_by:
                blocked_by[dep.to_issue_id] = set()
            blocked_by[dep.to_issue_id].add(dep.from_issue_id)

        # Also need to check if the blocking issues are open (not completed)
        # If a blocking issue is completed, it doesn't block anymore
        completed_issues: set[str] = {
            issue.id for issue in all_issues if issue.status == IssueStatus.COMPLETED
        }

        # Filter out completed blocking issues
        for issue_id in list(blocked_by.keys()):
            blockers = blocked_by[issue_id]
            active_blockers = {b for b in blockers if b not in completed_issues}
            if active_blockers:
                blocked_by[issue_id] = active_blockers
            else:
                del blocked_by[issue_id]

        ready_ids: list[str] = []
        blocked_issues: list[BlockedIssue] = []

        for issue in all_issues:
            # Skip completed and wont-fix issues
            if issue.status in (IssueStatus.COMPLETED, IssueStatus.WONT_FIX):
                continue

            # Check if issue is blocked by status
            if issue.status == IssueStatus.BLOCKED:
                # Get blockers from dependencies
                blockers = list(blocked_by.get(issue.id, []))
                blocked_issues.append(BlockedIssue(issue_id=issue.id, blockers=blockers))
                continue

            # Check if issue has active blockers via dependencies
            if issue.id in blocked_by:
                blockers = list(blocked_by[issue.id])
                blocked_issues.append(BlockedIssue(issue_id=issue.id, blockers=blockers))
                continue

            # Check status is proposed or in-progress
            if issue.status in (IssueStatus.PROPOSED, IssueStatus.IN_PROGRESS):
                ready_ids.append(issue.id)

        return ReadyResult(ready_issues=ready_ids, blocked_issues=blocked_issues)

    def _has_path_to(self, from_id: str, to_id: str, visited: set[str]) -> bool:
        """Check if there's a path from from_id to to_id.

        Internal helper for cycle detection.

        Args:
            from_id: Starting issue ID
            to_id: Target issue ID
            visited: Already-visited nodes (to prevent infinite recursion)

        Returns:
            True if a path exists, False otherwise
        """
        if from_id == to_id:
            return True

        if from_id in visited:
            return False

        visited.add(from_id)

        # Get all dependencies from from_id
        deps = self.uow.graph.get_dependencies(from_id)

        for dep in deps:
            if self._has_path_to(dep.to_issue_id, to_id, visited):
                return True

        return False


__all__ = [
    "DependencyService",
    "ImpactResult",
    "CycleResult",
    "BlockedIssue",
    "ReadyResult",
]
