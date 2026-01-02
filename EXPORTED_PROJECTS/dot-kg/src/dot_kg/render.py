"""Document reconstruction and rendering for kgshred.

Provides full and filtered document reconstruction from the span graph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Set

    from dot_kg.db import Database, Node


class ExpansionPolicy(Enum):
    """Policy for expanding nodes in filtered renders."""

    DIRECT = "direct"  # Only matching nodes
    DIRECT_ANCESTORS = "direct+ancestors"  # Include path to root
    DIRECT_ANCESTORS_SIBLINGS = "direct+ancestors+siblings"  # Include siblings


@dataclass
class RenderOptions:
    """Options for filtered rendering."""

    policy: ExpansionPolicy = ExpansionPolicy.DIRECT
    window: int = 0  # Number of prev/next siblings to include
    show_headings: bool = True  # Always show heading titles


def render_full(db: Database, doc_id: str) -> bytes:
    """Render a document fully, reconstructing original bytes.

    Args:
        db: Database connection.
        doc_id: Document ID to render.

    Returns:
        Original document bytes, exactly as ingested.
    """
    doc = db.get_document(doc_id)
    if not doc:
        return b""

    return doc.raw


def render_filtered(
    db: Database,
    doc_id: str,
    matches: Set[str],
    options: RenderOptions | None = None,
) -> bytes:
    """Render a document with selective expansion.

    Args:
        db: Database connection.
        doc_id: Document ID to render.
        matches: Set of short_ids that should be expanded.
        options: Rendering options (policy, window, etc.).

    Returns:
        Rendered document with placeholders for collapsed nodes.
    """
    if options is None:
        options = RenderOptions()

    doc = db.get_document(doc_id)
    if not doc:
        return b""

    # Get all nodes for this document
    nodes = db.get_nodes_by_doc_id(doc_id)
    if not nodes:
        return doc.raw

    # Build expansion set based on policy
    expanded = _compute_expanded_set(db, nodes, matches, options)

    # Sort nodes by start position for rendering
    sorted_nodes = sorted(nodes, key=lambda n: (n.start, -n.end))

    # Render nodes
    return _render_nodes(doc.raw, sorted_nodes, expanded, options)


def render_node(db: Database, short_id: str) -> bytes:
    """Render a single node's content.

    Args:
        db: Database connection.
        short_id: Short ID of the node to render.

    Returns:
        Node's raw bytes.
    """
    node = db.get_node_by_short_id(short_id)
    if not node:
        return b""

    doc = db.get_document(node.doc_id)
    if not doc:
        return b""

    return doc.raw[node.start : node.end]


def format_placeholder(node: Node) -> bytes:
    """Format a placeholder for a collapsed node.

    Args:
        node: Node to create placeholder for.

    Returns:
        Placeholder bytes in format [@ABCD kind=X bytes=N].
    """
    byte_count = node.end - node.start
    placeholder = f"[@{node.short_id} kind={node.kind} bytes={byte_count}]"
    return placeholder.encode("utf-8")


def parse_placeholder(text: str) -> dict[str, str | int] | None:
    """Parse a placeholder string.

    TODO: Used by LLM expansion workflows (kg ask, kg pack) where an LLM
    may request expansion of specific placeholders. Complements format_placeholder().
    Currently tested but not called from production code.

    Args:
        text: Placeholder text to parse.

    Returns:
        Dict with short_id, kind, bytes or None if invalid.
    """
    pattern = r"\[@([A-Z0-9]{4}) kind=(\w+) bytes=(\d+)\]"
    match = re.match(pattern, text)
    if not match:
        return None

    return {
        "short_id": match.group(1),
        "kind": match.group(2),
        "bytes": int(match.group(3)),
    }


def _compute_expanded_set(
    db: Database,
    nodes: list[Node],
    matches: Set[str],
    options: RenderOptions,
) -> set[str]:
    """Compute the set of nodes to expand based on policy."""
    expanded: set[str] = set(matches)

    if options.policy == ExpansionPolicy.DIRECT:
        pass  # Only matches

    elif options.policy == ExpansionPolicy.DIRECT_ANCESTORS:
        # Add ancestors for each match
        for node in nodes:
            if node.short_id in matches:
                expanded.update(_get_ancestor_ids(db, node))

    elif options.policy == ExpansionPolicy.DIRECT_ANCESTORS_SIBLINGS:
        # Add ancestors and their siblings
        for node in nodes:
            if node.short_id in matches:
                ancestors = _get_ancestor_ids(db, node)
                expanded.update(ancestors)
                # Add siblings of ancestors
                for ancestor_id in ancestors:
                    expanded.update(_get_sibling_ids(db, ancestor_id))

    # Apply window expansion
    if options.window > 0:
        window_nodes: set[str] = set()
        for node in nodes:
            if node.short_id in expanded:
                window_nodes.update(_get_window_siblings(db, node, options.window))
        expanded.update(window_nodes)

    # Always include headings if option set
    if options.show_headings:
        for node in nodes:
            if node.kind == "heading":
                expanded.add(node.short_id)

    return expanded


def _get_ancestor_ids(db: Database, node: Node) -> set[str]:
    """Get short_ids of all ancestors of a node."""
    ancestors: set[str] = set()

    current_pk = node.parent_node_pk
    while current_pk is not None:
        # Find parent node
        parent = _find_node_by_pk(db, node.doc_id, current_pk)
        if parent:
            ancestors.add(parent.short_id)
            current_pk = parent.parent_node_pk
        else:
            break

    return ancestors


def _get_sibling_ids(db: Database, short_id: str) -> set[str]:
    """Get short_ids of siblings of a node."""
    siblings: set[str] = set()

    node = db.get_node_by_short_id(short_id)
    if not node or node.node_pk is None:
        return siblings

    sibling_nodes = db.get_siblings(node.node_pk)
    for sibling in sibling_nodes:
        siblings.add(sibling.short_id)

    return siblings


def _get_window_siblings(db: Database, node: Node, window: int) -> set[str]:
    """Get short_ids of nodes within window distance."""
    siblings: set[str] = set()

    if node.node_pk is None:
        return siblings

    all_siblings = db.get_siblings(node.node_pk)
    # Include up to 'window' nodes on each side
    # Siblings are already in order from get_siblings

    # Find this node's position among siblings
    node_idx = -1
    for i, sib in enumerate(all_siblings):
        if sib.short_id == node.short_id:
            node_idx = i
            break

    if node_idx < 0:
        return siblings

    # Get window before and after
    start = max(0, node_idx - window)
    end = min(len(all_siblings), node_idx + window + 1)

    for i in range(start, end):
        siblings.add(all_siblings[i].short_id)

    return siblings


def _find_node_by_pk(db: Database, doc_id: str, pk: int) -> Node | None:
    """Find a node by its primary key.

    Args:
        db: Database connection.
        doc_id: Document ID (unused, kept for API compatibility).
        pk: Node primary key.

    Returns:
        Node if found, None otherwise.
    """
    return db.get_node_by_pk(pk)


def _render_nodes(
    raw: bytes,
    nodes: list[Node],
    expanded: set[str],
    options: RenderOptions,
) -> bytes:
    """Render nodes with expansion/placeholder logic."""
    # Find top-level nodes (those not contained by other nodes in the list)
    top_level = _find_top_level_nodes(nodes)

    if not top_level:
        return raw

    result = bytearray()
    pos = 0

    for node in top_level:
        # Add any content before this node
        if node.start > pos:
            result.extend(raw[pos : node.start])

        # Render this node
        if node.short_id in expanded:
            # Expand: render content verbatim
            result.extend(raw[node.start : node.end])
        else:
            # Collapse: emit placeholder
            # For headings, emit the heading line then placeholder for rest
            if node.kind == "heading" and options.show_headings:
                result.extend(raw[node.start : node.end])
            else:
                result.extend(format_placeholder(node))

        pos = node.end

    # Add any remaining content
    if pos < len(raw):
        result.extend(raw[pos:])

    return bytes(result)


def _find_top_level_nodes(nodes: list[Node]) -> list[Node]:
    """Find nodes that are not contained by other nodes."""
    # A node is top-level if no other node contains it
    # (i.e., no other node has start <= this.start and end >= this.end)

    top_level: list[Node] = []

    for node in nodes:
        is_top = True
        for other in nodes:
            if other.node_pk == node.node_pk:
                continue
            # Check if 'other' contains 'node'
            if other.start <= node.start and other.end >= node.end:
                # But they must not be equal spans
                if other.start < node.start or other.end > node.end:
                    is_top = False
                    break

        if is_top:
            top_level.append(node)

    # Sort by start position
    return sorted(top_level, key=lambda n: n.start)
