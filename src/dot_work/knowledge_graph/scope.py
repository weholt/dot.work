"""Shared scope filtering utilities for knowledge graph search.

Provides common dataclass and functions for filtering search results by
project membership, topics, and shared status.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dot_work.knowledge_graph.db import Database, Node


logger = logging.getLogger(__name__)


@dataclass
class ScopeFilter:
    """Scope filter for limiting search results.

    Attributes:
        project: Collection name to scope by (only members).
        topics: Topic names to include (OR logic).
        exclude_topics: Topic names to exclude.
        include_shared: Include nodes tagged with 'shared' topic.
    """

    project: str | None = None
    topics: list[str] = field(default_factory=list)
    exclude_topics: list[str] = field(default_factory=list)
    include_shared: bool = False


def build_scope_sets(
    db: Database,
    scope: ScopeFilter,
) -> tuple[set[str] | None, set[str] | None, set[str], str | None]:
    """Build sets for scope filtering.

    Returns:
        Tuple of (scope_members, scope_topic_ids, exclude_topic_ids, shared_topic_id).
        scope_members: Set of full_ids in the project, or None if no project filter.
        scope_topic_ids: Set of topic_ids to include, or None if no topic filter.
        exclude_topic_ids: Set of topic_ids to exclude.
        shared_topic_id: ID of 'shared' topic if include_shared is True.

    Raises:
        ValueError: If project or topic name not found.
    """
    scope_members: set[str] | None = None
    scope_topic_ids: set[str] | None = None
    exclude_topic_ids: set[str] = set()
    shared_topic_id: str | None = None

    # Build project membership set
    if scope.project:
        collection = db.get_collection_by_name(scope.project)
        if collection is None:
            logger.debug(f"Project not found: {scope.project}")
            raise ValueError("Project not found")
        members = db.list_collection_members(collection.collection_id, member_type="node")
        scope_members = {m.member_pk for m in members}

    # Build topic inclusion set
    if scope.topics:
        scope_topic_ids = set()
        for topic_name in scope.topics:
            topic = db.get_topic_by_name(topic_name)
            if topic is None:
                logger.debug(f"Topic not found: {topic_name}")
                raise ValueError("Topic not found")
            scope_topic_ids.add(topic.topic_id)

    # Build topic exclusion set
    for topic_name in scope.exclude_topics:
        topic = db.get_topic_by_name(topic_name)
        if topic is None:
            logger.debug(f"Topic not found: {topic_name}")
            raise ValueError("Topic not found")
        exclude_topic_ids.add(topic.topic_id)

    # Get shared topic ID
    if scope.include_shared:
        shared = db.get_topic_by_name("shared")
        if shared:
            shared_topic_id = shared.topic_id

    return scope_members, scope_topic_ids, exclude_topic_ids, shared_topic_id


def node_matches_scope(
    db: Database,
    node: Node,
    scope_members: set[str] | None,
    scope_topic_ids: set[str] | None,
    exclude_topic_ids: set[str],
    shared_topic_id: str | None,
) -> bool:
    """Check if a node matches the scope filter.

    Args:
        db: Database connection.
        node: Node to check.
        scope_members: Set of full_ids in the project, or None if no filter.
        scope_topic_ids: Set of topic_ids to include, or None if no filter.
        exclude_topic_ids: Set of topic_ids to exclude.
        shared_topic_id: ID of 'shared' topic for include_shared.

    Returns:
        True if the node matches the scope, False otherwise.
    """
    # Check project membership
    if scope_members is not None:
        if node.full_id not in scope_members:
            # Check if include_shared and node is tagged 'shared'
            if shared_topic_id:
                node_topics = db.list_topics_for_target("node", node.full_id)
                if any(t.topic_id == shared_topic_id for t, _ in node_topics):
                    pass  # Allow shared nodes through
                else:
                    return False
            else:
                return False

    # Get node's topics for topic filtering
    if scope_topic_ids or exclude_topic_ids:
        node_topics = db.list_topics_for_target("node", node.full_id)
        node_topic_ids = {t.topic_id for t, _ in node_topics}

        # Check topic inclusion (OR logic)
        if scope_topic_ids:
            if not (node_topic_ids & scope_topic_ids):
                # No matching include topics
                # But allow if shared and include_shared
                if shared_topic_id and shared_topic_id in node_topic_ids:
                    pass
                else:
                    return False

        # Check topic exclusion
        if exclude_topic_ids:
            if node_topic_ids & exclude_topic_ids:
                return False

    return True


__all__ = ["ScopeFilter", "build_scope_sets", "node_matches_scope"]
