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
]
