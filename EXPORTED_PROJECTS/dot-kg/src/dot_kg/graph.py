"""Graph builder for kgshred.

Creates nodes and edges from parsed Markdown blocks.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dot_kg.db import Database, DocumentExistsError, Edge, Node
from dot_kg.ids import generate_full_id, generate_short_id
from dot_kg.parse_md import Block, BlockKind, parse_markdown
from dot_kg.search_fts import index_node

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class GraphResult:
    """Result of building a graph from a document."""

    doc_id: str
    nodes: list[Node]
    edges: list[Edge]


@dataclass
class _HeadingStackEntry:
    """Entry in the heading stack for hierarchy tracking."""

    node_pk: int
    level: int


def build_graph(
    doc_id: str,
    content: bytes,
    db: Database,
    source_path: str = "",
    *,
    force: bool = False,
) -> GraphResult:
    """Build a knowledge graph from a Markdown document.

    Creates nodes from parsed blocks and edges for:
    - contains: parent-child hierarchy
    - next: sibling ordering

    Args:
        doc_id: Document identifier.
        content: Raw Markdown content as bytes.
        db: Database to store nodes and edges.
        source_path: Optional source path for the document.
        force: If True, replace existing document. If False, raise on conflict.

    Returns:
        GraphResult with created nodes and edges.

    Raises:
        DocumentExistsError: If document exists and force=False.
    """
    logger.info(
        "Building graph for document: %s (source: %s, force: %s)", doc_id, source_path, force
    )
    blocks = list(parse_markdown(content))
    logger.debug("Parsed %d blocks from document", len(blocks))
    return build_graph_from_blocks(doc_id, content, blocks, db, source_path, force=force)


def build_graph_from_blocks(
    doc_id: str,
    content: bytes,
    blocks: Sequence[Block],
    db: Database,
    source_path: str = "",
    *,
    force: bool = False,
) -> GraphResult:
    """Build a knowledge graph from pre-parsed blocks.

    Args:
        doc_id: Document identifier.
        content: Raw document content for extracting block text.
        blocks: Pre-parsed blocks.
        db: Database to store nodes and edges.
        source_path: Optional source path for the document.
        force: If True, replace existing document. If False, raise on conflict.

    Returns:
        GraphResult with created nodes and edges.

    Raises:
        DocumentExistsError: If document exists and force=False.
    """
    logger.debug("Building graph from %d pre-parsed blocks", len(blocks))

    # Check for existing document and handle accordingly
    _ensure_document(doc_id, content, db, source_path, force=force)

    if not blocks:
        logger.debug("No blocks parsed, creating document node only")
        # Create doc node even for empty content
        doc_node = _create_doc_node(doc_id, content, db, set())
        # Index doc node for FTS (empty content)
        index_node(db, doc_node, "")
        logger.info("Created empty graph for document: %s", doc_id)
        return GraphResult(doc_id=doc_id, nodes=[doc_node], edges=[])

    # Track existing short_ids for collision resolution
    existing_ids: set[str] = set()

    # Create root doc node
    doc_node = _create_doc_node(doc_id, content, db, existing_ids)
    nodes: list[Node] = [doc_node]
    edges: list[Edge] = []

    # Index doc node for FTS
    doc_text = content.decode("utf-8", errors="replace")
    index_node(db, doc_node, doc_text)

    # Heading stack for hierarchy
    heading_stack: list[_HeadingStackEntry] = []

    # Previous sibling at each level for next edges
    prev_sibling_by_parent: dict[int, int] = {}

    logger.debug("Creating nodes and edges for %d blocks", len(blocks))

    for block in blocks:
        # Create node for this block
        node = _create_block_node(doc_id, content, block, db, existing_ids)
        nodes.append(node)

        # Index node for FTS search
        block_text = content[block.start : block.end].decode("utf-8", errors="replace")
        index_node(db, node, block_text)

        # Determine parent based on heading hierarchy
        parent_pk = _get_parent_pk(block, heading_stack, doc_node)

        # Create contains edge from parent and set parent_node_pk
        if node.node_pk is not None:
            # Update the node's parent_node_pk for direct traversal
            db.update_node_parent(node.node_pk, parent_pk)
            node.parent_node_pk = parent_pk  # Also update in-memory for return

            contains_edge = Edge(
                src_node_pk=parent_pk,
                dst_node_pk=node.node_pk,
                edge_type="contains",
            )
            db.insert_edge(contains_edge)
            edges.append(contains_edge)

            # Create next edge from previous sibling
            if parent_pk in prev_sibling_by_parent:
                prev_pk = prev_sibling_by_parent[parent_pk]
                next_edge = Edge(
                    src_node_pk=prev_pk,
                    dst_node_pk=node.node_pk,
                    edge_type="next",
                )
                db.insert_edge(next_edge)
                edges.append(next_edge)

            # Update previous sibling
            prev_sibling_by_parent[parent_pk] = node.node_pk

            # Update heading stack if this is a heading
            if block.kind == BlockKind.HEADING and block.level is not None:
                _update_heading_stack(heading_stack, node.node_pk, block.level)

    logger.info(
        "Built graph for document: %s (%d nodes, %d edges)",
        doc_id,
        len(nodes),
        len(edges),
    )
    return GraphResult(doc_id=doc_id, nodes=nodes, edges=edges)


def _ensure_document(
    doc_id: str,
    content: bytes,
    db: Database,
    source_path: str,
    *,
    force: bool = False,
) -> None:
    """Ensure document record exists in database.

    Args:
        doc_id: Document identifier.
        content: Raw document content.
        db: Database to store document.
        source_path: Source path for the document.
        force: If True, replace existing document.

    Raises:
        DocumentExistsError: If document exists and force=False.
    """
    existing = db.get_document(doc_id)
    if existing is not None:
        new_sha256 = hashlib.sha256(content).hexdigest()
        sha256_match = existing.sha256 == new_sha256

        if not force:
            logger.debug("Document already exists: %s (sha256_match: %s)", doc_id, sha256_match)
            raise DocumentExistsError(doc_id, sha256_match)

        # Force mode: delete existing and proceed
        logger.info("Force mode: deleting existing document: %s", doc_id)
        db.delete_document(doc_id)

    db.insert_document(
        doc_id=doc_id,
        source_path=source_path,
        raw=content,
    )
    logger.debug("Document record ensured: %s (%d bytes)", doc_id, len(content))


def _create_doc_node(
    doc_id: str,
    content: bytes,
    db: Database,
    existing_ids: set[str],
) -> Node:
    """Create the root document node."""
    full_id = generate_full_id(doc_id, 0, len(content), "doc", content)
    short_result = generate_short_id(full_id, existing_ids)
    existing_ids.add(short_result.short_id)

    node = Node(
        node_pk=None,
        short_id=short_result.short_id,
        full_id=full_id,
        doc_id=doc_id,
        kind="doc",
        level=None,
        title=None,
        start=0,
        end=len(content),
        parent_node_pk=None,
        meta={"nonce": short_result.nonce} if short_result.nonce > 0 else {},
    )

    return db.insert_node(node)


def _create_block_node(
    doc_id: str,
    content: bytes,
    block: Block,
    db: Database,
    existing_ids: set[str],
) -> Node:
    """Create a node from a parsed block."""
    block_content = content[block.start : block.end]
    kind = block.kind.value

    full_id = generate_full_id(doc_id, block.start, block.end, kind, block_content)
    short_result = generate_short_id(full_id, existing_ids)
    existing_ids.add(short_result.short_id)

    meta: dict[str, object] = {}
    if short_result.nonce > 0:
        meta["nonce"] = short_result.nonce
    if block.language:
        meta["language"] = block.language

    node = Node(
        node_pk=None,
        short_id=short_result.short_id,
        full_id=full_id,
        doc_id=doc_id,
        kind=kind,
        level=block.level,
        title=block.title,
        start=block.start,
        end=block.end,
        parent_node_pk=None,  # Set via edges, not direct reference
        meta=meta,
    )

    return db.insert_node(node)


def _get_parent_pk(
    block: Block,
    heading_stack: list[_HeadingStackEntry],
    doc_node: Node,
) -> int:
    """Determine parent node PK based on heading hierarchy.

    For headings, parent is the nearest heading with a lower level.
    For other blocks, parent is the most recent heading.
    If no heading applies, parent is the doc node.
    """
    if not heading_stack:
        return doc_node.node_pk  # type: ignore[return-value]

    if block.kind == BlockKind.HEADING and block.level is not None:
        # Pop headings of same or higher level
        while heading_stack and heading_stack[-1].level >= block.level:
            heading_stack.pop()

        if heading_stack:
            return heading_stack[-1].node_pk
        return doc_node.node_pk  # type: ignore[return-value]

    # For non-headings, use the most recent heading as parent
    return heading_stack[-1].node_pk


def _update_heading_stack(
    heading_stack: list[_HeadingStackEntry],
    node_pk: int,
    level: int,
) -> None:
    """Update the heading stack with a new heading."""
    heading_stack.append(_HeadingStackEntry(node_pk=node_pk, level=level))


def get_node_tree(db: Database, doc_id: str) -> list[tuple[Node, int]]:
    """Get all nodes for a document as a tree with depth.

    Args:
        db: Database connection.
        doc_id: Document identifier.

    Returns:
        List of (Node, depth) tuples in document order.
    """
    logger.debug("Building node tree for document: %s", doc_id)
    nodes = db.get_nodes_by_doc_id(doc_id)
    if not nodes:
        logger.debug("No nodes found for document: %s", doc_id)
        return []

    # Build parent-child mapping from contains edges
    children: dict[int, list[Node]] = {}
    node_by_pk: dict[int, Node] = {}

    for node in nodes:
        if node.node_pk is not None:
            node_by_pk[node.node_pk] = node
            children[node.node_pk] = []

    # Find doc node (kind='doc')
    doc_node = next((n for n in nodes if n.kind == "doc"), None)
    if not doc_node or doc_node.node_pk is None:
        return [(n, 0) for n in nodes]

    # Build children map from contains edges
    contains_edges = db.get_edges_by_type("contains")
    for edge in contains_edges:
        if edge.dst_node_pk in node_by_pk:
            child = node_by_pk[edge.dst_node_pk]
            if child.doc_id == doc_id and edge.src_node_pk in children:
                children[edge.src_node_pk].append(child)

    # Sort children by start offset
    for child_list in children.values():
        child_list.sort(key=lambda n: n.start)

    # DFS to build tree
    result: list[tuple[Node, int]] = []

    def visit(node: Node, depth: int) -> None:
        result.append((node, depth))
        if node.node_pk is not None:
            for child in children.get(node.node_pk, []):
                visit(child, depth + 1)

    visit(doc_node, 0)

    logger.debug("Built node tree for %s: %d nodes", doc_id, len(result))
    return result
