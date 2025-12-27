"""FTS5 keyword search for kgshred.

Provides full-text search using SQLite FTS5 with BM25 ranking.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dot_work.knowledge_graph.db import Database, Node


logger = logging.getLogger(__name__)


# Whitelist pattern for simple queries (no FTS5 operators)
_SIMPLE_QUERY_PATTERN = re.compile(r"^[\w\s\-\.]+$", re.UNICODE)

# Patterns for detecting FTS5 operators
_FTS5_OPERATOR_PATTERN = re.compile(r'\b(AND|OR|NOT)\b|"[^"]+"|[()]', re.IGNORECASE)

# Dangerous patterns that are never allowed, even with allow_advanced=True
_DANGEROUS_PATTERNS = [
    r"\*",  # Wildcards (can match everything)
    r"\bNEAR\b",  # Proximity searches (DoS risk)
    r"\w+:",  # Column filters with colons (can bypass filters) - catches `title:term` style
]


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


@dataclass
class SearchResult:
    """Result from a full-text search."""

    short_id: str
    title: str | None
    snippet: str
    score: float
    node: Node
    doc_id: str
    kind: str


def search(
    db: Database,
    query: str,
    k: int = 20,
    snippet_length: int = 150,
    scope: ScopeFilter | None = None,
    *,
    allow_advanced: bool = False,
) -> list[SearchResult]:
    """Search for nodes matching the query.

    Args:
        db: Database connection.
        query: Search query.
        k: Maximum number of results.
        snippet_length: Maximum length of snippet.
        scope: Optional scope filter to limit results.
        allow_advanced: Allow FTS5 operators (AND, OR, NOT, quotes, parentheses).
            Default is False for security. Only enable in trusted contexts.

    Returns:
        List of SearchResult, sorted by relevance (best first).

    Raises:
        ValueError: If scope specifies unknown project or topic, or if query
            contains invalid/injected syntax.
    """
    if not query or not query.strip():
        return []

    # Escape and validate query for security
    safe_query = _prepare_query(query, allow_advanced=allow_advanced)

    if not safe_query:
        return []

    # Pre-compute scope membership for filtering
    scope_members: set[str] | None = None
    scope_topics: set[str] | None = None
    exclude_topic_ids: set[str] = set()
    shared_topic_id: str | None = None

    if scope:
        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = _build_scope_sets(
            db, scope
        )

    # Fetch more results if filtering, then apply scope
    fetch_limit = k * 3 if scope else k
    results = db.fts_search(safe_query, limit=fetch_limit)

    search_results: list[SearchResult] = []
    for node, score in results:
        # Apply scope filtering
        if scope and not _node_matches_scope(
            db,
            node,
            scope_members,
            scope_topics,
            exclude_topic_ids,
            shared_topic_id,
        ):
            continue

        # Get text content for snippet
        text = _get_node_text(db, node)
        snippet = _generate_snippet(text, query, snippet_length)

        search_results.append(
            SearchResult(
                short_id=node.short_id,
                title=node.title,
                snippet=snippet,
                score=abs(score),  # BM25 returns negative scores
                node=node,
                doc_id=node.doc_id,
                kind=node.kind,
            )
        )

        if len(search_results) >= k:
            break

    return search_results


def index_node(
    db: Database,
    node: Node,
    text: str,
) -> None:
    """Index a node for full-text search.

    Args:
        db: Database connection.
        node: Node to index.
        text: Text content of the node.
    """
    if node.node_pk is None:
        return

    db.fts_index_node(
        node_pk=node.node_pk,
        title=node.title,
        text=text,
        short_id=node.short_id,
    )


def _prepare_query(query: str, allow_advanced: bool = False) -> str:
    """Prepare and validate query for FTS5.

    This function implements strict security validation to prevent SQL injection
    via FTS5 query syntax.

    Args:
        query: Raw user search query.
        allow_advanced: Allow FTS5 operators (AND, OR, NOT, quotes, parentheses).
            Default is False for security. Only enable in trusted contexts.

    Returns:
        Safe query string for FTS5.

    Raises:
        ValueError: If query contains invalid or dangerous syntax.
    """
    query = query.strip()

    if not query:
        return ""

    # Check for dangerous patterns that are NEVER allowed
    # This check happens first, before any other validation
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(
                f"Query contains prohibited syntax: {pattern}. "
                "Wildcards, NEAR searches, and column filters are not allowed."
            )

    # Check if query uses FTS5 operators
    has_operators = bool(_FTS5_OPERATOR_PATTERN.search(query))

    if has_operators:
        if not allow_advanced:
            raise ValueError(
                "Advanced search syntax (AND, OR, NOT, quotes, parentheses) "
                "is not allowed. Use simple word search with letters, numbers, "
                "spaces, hyphens, and periods only."
            )
        # Validate advanced query structure
        return _validate_advanced_query(query)

    # Simple query: whitelist validation
    if not _SIMPLE_QUERY_PATTERN.match(query):
        raise ValueError(
            "Query contains invalid characters. "
            "Use only letters, numbers, spaces, hyphens, and periods."
        )

    # Simple query: treat as implicit OR between words
    words = query.split()
    if len(words) == 1:
        return words[0]

    # Multiple words: join with OR (safe because we validated with whitelist)
    return " OR ".join(words)


def _validate_advanced_query(query: str) -> str:
    """Validate advanced FTS5 query structure.

    This function validates queries that use FTS5 operators, checking for
    dangerous patterns that could cause injection or DoS attacks.

    Args:
        query: Query with FTS5 operators.

    Returns:
        The validated query.

    Raises:
        ValueError: If query contains dangerous patterns or structural issues.
    """
    # Check for dangerous patterns that are never allowed
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(
                f"Query contains prohibited syntax: {pattern}. "
                "Wildcards, NEAR searches, and column filters are not allowed."
            )

    # Check for balanced parentheses
    if query.count("(") != query.count(")"):
        raise ValueError("Unbalanced parentheses in query")

    # Check for balanced quotes
    if query.count('"') % 2 != 0:
        raise ValueError("Unbalanced quotes in query")

    # Limit query complexity to prevent DoS
    if len(query) > 500:
        raise ValueError("Query too long (maximum 500 characters)")

    if query.count(" OR ") > 10:
        raise ValueError("Too many OR conditions (maximum 10)")

    return query


def _get_node_text(db: Database, node: Node) -> str:
    """Get text content for a node."""
    doc = db.get_document(node.doc_id)
    if not doc:
        return ""

    raw = doc.raw[node.start : node.end]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _generate_snippet(
    text: str,
    query: str,
    max_length: int = 150,
) -> str:
    """Generate a snippet with query terms highlighted.

    Args:
        text: Full text content.
        query: Search query.
        max_length: Maximum snippet length.

    Returns:
        Snippet string with <<term>> markers for highlights.
    """
    if not text:
        return ""

    # Extract search terms (ignore operators)
    terms = _extract_search_terms(query)

    if not terms:
        # No terms to highlight, just truncate
        return _truncate(text, max_length)

    # Find first occurrence of any term
    text_lower = text.lower()
    first_pos = len(text)

    for term in terms:
        pos = text_lower.find(term.lower())
        if pos != -1 and pos < first_pos:
            first_pos = pos

    if first_pos == len(text):
        # No terms found, return start of text
        return _truncate(text, max_length)

    # Extract context around first match
    context_start = max(0, first_pos - 30)
    context_end = min(len(text), first_pos + max_length - 30)

    snippet = text[context_start:context_end]

    # Add ellipsis if truncated
    if context_start > 0:
        snippet = "..." + snippet
    if context_end < len(text):
        snippet = snippet + "..."

    # Highlight terms
    snippet = _highlight_terms(snippet, terms)

    return snippet


def _extract_search_terms(query: str) -> list[str]:
    """Extract individual search terms from query."""
    # Remove operators
    clean = re.sub(r"\b(AND|OR|NOT)\b", " ", query, flags=re.IGNORECASE)

    # Extract quoted phrases
    phrases = re.findall(r'"([^"]+)"', clean)

    # Remove quoted phrases and split remaining
    clean = re.sub(r'"[^"]*"', " ", clean)
    words = [w.strip() for w in clean.split() if w.strip()]

    return phrases + words


def _highlight_terms(text: str, terms: list[str]) -> str:
    """Add highlight markers around terms."""
    result = text

    for term in terms:
        # Case-insensitive replacement with markers
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(lambda m: f"<<{m.group(0)}>>", result)

    return result


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max length, preserving word boundaries."""
    if len(text) <= max_length:
        return text

    # Find last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")

    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated + "..."


def _build_scope_sets(
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


def _node_matches_scope(
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
