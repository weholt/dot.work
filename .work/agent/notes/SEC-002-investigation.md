# SEC-002@94eb69 Investigation: SQL injection risk in FTS5 search

## Issue
SQL injection via FTS5 search query in knowledge_graph module.

## Vulnerability Location
- **File:** `src/dot_work/knowledge_graph/search_fts.py`
- **Function:** `_prepare_query()` (lines 150-174)
- **Called from:** `search()` (line 72)

## Root Cause

### The Vulnerable Code (lines 160-165)
```python
# Check if query uses FTS5 operators (AND, OR, NOT, quotes, etc.)
has_operators = bool(re.search(r'\b(AND|OR|NOT)\b|"[^"]+"|[()]', query, re.IGNORECASE))

if has_operators:
    # Trust user-provided FTS5 syntax
    return query  # VULNERABILITY - NO VALIDATION!
```

**Line 165 is the vulnerability:** When FTS5 operators are detected, the function returns the user input **completely unvalidated**.

### Why Parameterized Queries Don't Help

The `fts_search()` function in `db.py` line 952 uses:
```python
WHERE fts_nodes MATCH ?
```

The `?` parameter contains the entire FTS5 query string. SQLite FTS5's MATCH operator doesn't support parameterization of the query structure - it treats the parameter as a raw FTS5 query expression.

### Attack Vectors

1. **Information Disclosure**
   - Query: `"secret" OR 1=1`
   - Result: Matches all documents, leaking entire database

2. **Column Filter Bypass**
   - Query: `email: *" OR "*`
   - Result: Bypasses column-specific filters

3. **DoS (Denial of Service)**
   - Query: `* NEAR/2 * NEAR/2 *`
   - Result: Expensive query that hangs the database

4. **Phrase Search Wildcards**
   - Query: `"*"`
   - Result: Matches all documents

5. **Parenthesis Injection**
   - Query: `term) OR (1=1`
   - Result: Breaks query structure, leaks data

## Current Escaping (Insufficient)

```python
def _escape_fts_term(term: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", term, flags=re.UNICODE)
    return clean.strip()
```

This only:
- Removes non-alphanumeric characters
- Is only used for simple queries (no operators)
- **Does NOT escape FTS5 special characters**

## Proposed Solution

### 1. Strict Input Validation (Whitelist)

**Approach:** Reject-by-default for simple searches, require explicit opt-in for advanced.

```python
SIMPLE_QUERY_PATTERN = re.compile(r'^[\w\s\-\.]+$', re.UNICODE)

def _prepare_query(query: str, allow_advanced: bool = False) -> str:
    query = query.strip()

    if not query:
        return ""

    # Check for FTS5 operators
    has_operators = bool(re.search(r'\b(AND|OR|NOT)\b|"[^"]+"|[()]', query, re.IGNORECASE))

    if has_operators:
        if not allow_advanced:
            raise ValueError(
                "Advanced search syntax (AND, OR, NOT, quotes, parentheses) "
                "is not allowed. Use simple word search."
            )
        # Even with allow_advanced, validate structure
        return _validate_advanced_query(query)

    # Simple query: whitelist validation
    if not SIMPLE_QUERY_PATTERN.match(query):
        raise ValueError(
            "Query contains invalid characters. "
            "Use only letters, numbers, spaces, hyphens, and periods."
        )

    # Split and rejoin with OR (safe because we validated)
    words = query.split()
    if len(words) == 1:
        return words[0]
    return " OR ".join(words)
```

### 2. Advanced Query Validation

```python
def _validate_advanced_query(query: str) -> str:
    """Validate and sanitize advanced FTS5 query."""
    # Check for dangerous patterns
    dangerous = [
        r'\*',           # Wildcards
        r'\bNEAR\b',     # Proximity searches (DoS risk)
        r'::\s*\w+',     # Column filters with colons
        r'\(\s*\)',      # Empty parentheses
    ]

    for pattern in dangerous:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError(f"Query contains prohibited syntax: {pattern}")

    # Check for balanced parentheses
    if query.count('(') != query.count(')'):
        raise ValueError("Unbalanced parentheses in query")

    # Check for balanced quotes
    if query.count('"') % 2 != 0:
        raise ValueError("Unbalanced quotes in query")

    # Limit query complexity
    if len(query) > 500:
        raise ValueError("Query too long (max 500 characters)")

    if query.count(' OR ') > 10:
        raise ValueError("Too many OR conditions (max 10)")

    return query
```

### 3. Alternative: FTS5 Query Escaping

Another approach is to properly escape FTS5 special characters:

```python
def _escape_fts_term(term: str) -> str:
    """Escape a single term for FTS5 by quoting it."""
    # Double any existing quotes
    escaped = term.replace('"', '""')
    # Wrap in quotes to prevent FTS5 interpretation
    return f'"{escaped}"'
```

### 4. Tests Required

```python
def test_simple_queries_allowed():
    assert _prepare_query("hello") == "hello"
    assert _prepare_query("hello world") == "hello OR world"

def test_injection_attempts_blocked():
    with pytest.raises(ValueError):
        _prepare_query('hello OR 1=1')

    with pytest.raises(ValueError):
        _prepare_query('"secret" OR "*"')

    with pytest.raises(ValueError):
        _prepare_query('email: *')

def test_advanced_rejected_by_default():
    with pytest.raises(ValueError):
        _prepare_query('hello AND world')

def test_advanced_with_allow_advanced():
    # Safe advanced query
    result = _prepare_query('hello AND world', allow_advanced=True)
    assert 'hello' in result and 'world' in result

    # Dangerous advanced query blocked even with allow_advanced
    with pytest.raises(ValueError):
        _prepare_query('* NEAR/2 *', allow_advanced=True)
```

## Acceptance Criteria

- [x] Vulnerability identified and documented
- [ ] Simple queries use whitelist validation
- [ ] FTS5 operators (AND, OR, NOT, quotes, parentheses) rejected by default
- [ ] Advanced queries require explicit `allow_advanced=True` flag
- [ ] Even advanced queries validate against dangerous patterns (wildcards, NEAR, column filters)
- [ ] Parentheses and quotes are balanced
- [ ] Query complexity is limited
- [ ] Tests verify injection attempts are blocked
- [ ] All existing tests still pass
- [ ] Documentation updated with security guidance

## Implementation Priority

1. **Critical:** Implement whitelist validation for simple queries (no FTS5 syntax)
2. **Critical:** Reject FTS5 operators by default
3. **High:** Add `allow_advanced` parameter for trusted contexts
4. **High:** Add tests for injection prevention
5. **Medium:** Add query complexity limits
6. **Medium:** Update CLI/API documentation

## Related Issues

- SEC-003: Git command injection (similar pattern - unvalidated user input)
- memory_leak.md: Security patterns for input validation
