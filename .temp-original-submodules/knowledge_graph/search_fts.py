"""FTS5 keyword search for kgshred.

Provides full-text search using SQLite FTS5 with BM25 ranking.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dot_work.knowledge_graph.db import Database, Node

from dot_work.knowledge_graph.scope import ScopeFilter, build_scope_sets, node_matches_scope

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
        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = build_scope_sets(
            db, scope
        )

    # Fetch more results if filtering, then apply scope
    fetch_limit = k * 3 if scope else k
    results = db.fts_search(safe_query, limit=fetch_limit)

    search_results: list[SearchResult] = []
    for node, score in results:
        # Apply scope filtering
        if scope and not node_matches_scope(
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

    # Use list for efficient building (PERF-016)
    parts = []
    if context_start > 0:
        parts.append("...")
    parts.append(text[context_start:context_end])
    if context_end < len(text):
        parts.append("...")

    # Single join instead of multiple concatenations
    snippet = "".join(parts)

    # Highlight terms (already optimized with single-pass pattern)
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
    """Add highlight markers around terms.

    Uses single-pass replacement with pre-compiled alternation pattern
    for efficiency (PERF-016).
    """
    if not terms:
        return text

    # Single pre-compiled alternation pattern for all terms
    # This avoids N pattern compilations and N passes over text
    pattern = re.compile("|".join(map(re.escape, terms)), re.IGNORECASE)

    # Single-pass replacement with markers
    return pattern.sub(lambda m: f"<<{m.group(0)}>>", text)


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
