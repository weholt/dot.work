"""Full-text search service using SQLite FTS5.

Provides search functionality with BM25 ranking and snippet highlighting.

Security: All user queries are validated to prevent FTS5 injection attacks.
Wildcards, column filters, and NEAR searches are blocked. Advanced operators
(AND, OR, NOT) require explicit opt-in via allow_advanced parameter.

Source: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/src/issue_tracker/services/
"""

import re
from dataclasses import dataclass

from sqlmodel import Session, text

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

# Allowed field names for search_by_field
_ALLOWED_FIELDS = {"title", "description", "labels"}


@dataclass
class SearchResult:
    """Search result with relevance ranking."""

    issue_id: str
    rank: float
    snippet: str


class SearchService:
    """Service for full-text search using FTS5."""

    def __init__(self, session: Session) -> None:
        """Initialize search service.

        Args:
            session: SQLModel session for database access
        """
        self.session = session

    def search(
        self,
        query: str,
        limit: int = 20,
        include_closed: bool = False,
        *,
        allow_advanced: bool = False,
        _trusted_column_filter: bool = False,
    ) -> list[SearchResult]:
        """Search issues using FTS5 full-text search.

        Args:
            query: Search query (supports FTS5 syntax when allow_advanced=True)
            limit: Maximum number of results
            include_closed: Whether to include closed issues
            allow_advanced: Allow FTS5 operators (AND, OR, NOT, quotes, parentheses).
                Default is False for security. Only enable in trusted contexts.
            _trusted_column_filter: Internal flag for queries with manually constructed
                column filters. Used by search_by_field after validating field name.

        Returns:
            List of SearchResult objects ordered by relevance

        Raises:
            ValueError: If query contains invalid or dangerous syntax.

        Examples:
            >>> service.search("authentication bug")
            >>> service.search("bug fix", allow_advanced=True)  # Allows AND/OR
            >>> service.search('"exact phrase"', allow_advanced=True)  # Phrase search
        """
        # Validate and sanitize query for security
        safe_query = _prepare_query(
            query, allow_advanced=allow_advanced, _trusted_column_filter=_trusted_column_filter
        )

        if not safe_query:
            return []

        # Build FTS5 query
        sql = text("""
            SELECT
                fts.id as issue_id,
                bm25(issues_fts) as rank,
                snippet(issues_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
                i.status
            FROM issues_fts fts
            JOIN issues i ON fts.id = i.id
            WHERE issues_fts MATCH :query
        """)

        if not include_closed:
            sql = text(str(sql) + " AND i.status != 'closed'")

        sql = text(str(sql) + " ORDER BY rank LIMIT :limit")

        results = self.session.exec(sql, params={"query": safe_query, "limit": limit})  # type: ignore[call-overload]

        return [
            SearchResult(issue_id=row.issue_id, rank=float(row.rank), snippet=row.snippet)
            for row in results
        ]

    def search_by_field(self, field: str, query: str, limit: int = 20) -> list[SearchResult]:
        """Search specific field using FTS5.

        Args:
            field: Field to search (title, description, labels)
            query: Search query
            limit: Maximum number of results

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If field name is invalid or query contains dangerous syntax.
        """
        # Validate field name against allowlist
        if field not in _ALLOWED_FIELDS:
            raise ValueError(f"Invalid field: '{field}'. Allowed fields: {sorted(_ALLOWED_FIELDS)}")

        # Validate query first (before adding column filter)
        safe_query = _prepare_query(query, allow_advanced=False)

        if not safe_query:
            return []

        # Construct FTS5 query with validated column filter
        # Note: We manually construct the column filter syntax since we validated
        # both the field name and query separately
        fts_query = f"{field}:{safe_query}"

        # Use search with allow_advanced=True and _trusted_column_filter=True
        # since we already validated both components
        return self.search(fts_query, limit=limit, allow_advanced=True, _trusted_column_filter=True)

    def rebuild_index(self) -> int:
        """Rebuild the FTS5 index from scratch.

        Returns:
            Number of issues indexed
        """
        # Clear existing FTS data
        self.session.exec(text("DELETE FROM issues_fts;"))  # type: ignore[call-overload]

        # Rebuild from issues table
        self.session.exec(  # type: ignore[call-overload]
            text("""
            INSERT INTO issues_fts(rowid, id, title, description)
            SELECT rowid, id, title, COALESCE(description, '')
            FROM issues;
        """)
        )

        self.session.commit()

        # Count indexed issues
        count_result = self.session.exec(text("SELECT COUNT(*) as cnt FROM issues_fts;"))  # type: ignore[call-overload]
        return count_result.first().cnt if count_result else 0


def _prepare_query(
    query: str, allow_advanced: bool = False, _trusted_column_filter: bool = False
) -> str:
    """Prepare and validate query for FTS5.

    This function implements strict security validation to prevent SQL injection
    via FTS5 query syntax.

    Args:
        query: Raw user search query.
        allow_advanced: Allow FTS5 operators (AND, OR, NOT, quotes, parentheses).
            Default is False for security. Only enable in trusted contexts.
        _trusted_column_filter: Internal flag for queries with manually constructed
            column filters. Used by search_by_field after validating field name.

    Returns:
        Safe query string for FTS5.

    Raises:
        ValueError: If query contains invalid or dangerous syntax.
    """
    query = query.strip()

    if not query:
        return ""

    # Check query length FIRST (before any transformations)
    if len(query) > 500:
        raise ValueError("Query too long (maximum 500 characters)")

    # Check for dangerous patterns that are NEVER allowed
    # Skip column filter check if _trusted_column_filter=True (internal use only)
    dangerous_patterns = (
        [p for p in _DANGEROUS_PATTERNS if p != r"\w+:"]
        if _trusted_column_filter
        else _DANGEROUS_PATTERNS
    )

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(
                "Query contains prohibited syntax. Wildcards and NEAR searches are not allowed."
            )

    # Check for unbalanced quotes (even in simple mode)
    if query.count('"') % 2 != 0:
        raise ValueError("Unbalanced quotes in query")

    # Check if query uses FTS5 operators (including column filters with :)
    # When _trusted_column_filter=True, column filters are allowed
    has_column_filter = bool(re.search(r"\w+:", query)) if _trusted_column_filter else False
    has_operators = bool(_FTS5_OPERATOR_PATTERN.search(query)) or has_column_filter

    if has_operators:
        if not allow_advanced:
            raise ValueError(
                "Advanced search syntax (AND, OR, NOT, quotes, parentheses) "
                "is not allowed. Use simple word search with letters, numbers, "
                "spaces, hyphens, and periods only."
            )
        # Validate advanced query structure
        return _validate_advanced_query(query, _trusted_column_filter=_trusted_column_filter)

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


def _validate_advanced_query(query: str, _trusted_column_filter: bool = False) -> str:
    """Validate advanced FTS5 query structure.

    This function validates queries that use FTS5 operators, checking for
    dangerous patterns that could cause injection or DoS attacks.

    Args:
        query: Query with FTS5 operators.
        _trusted_column_filter: Internal flag for queries with manually constructed
            column filters.

    Returns:
        The validated query.

    Raises:
        ValueError: If query contains dangerous patterns or structural issues.
    """
    # Check for dangerous patterns that are never allowed (double-check)
    # Skip column filter check if _trusted_column_filter=True (internal use only)
    dangerous_patterns = (
        [p for p in _DANGEROUS_PATTERNS if p != r"\w+:"]
        if _trusted_column_filter
        else _DANGEROUS_PATTERNS
    )

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(
                "Query contains prohibited syntax. Wildcards and NEAR searches are not allowed."
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


__all__ = ["SearchService", "SearchResult"]
