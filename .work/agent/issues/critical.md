# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

---
id: "CR-001@f8a2c1"
title: "Plaintext git credentials written in container"
description: "Docker container writes GITHUB_TOKEN to ~/.git-credentials in plaintext"
created: 2024-12-27
section: "container/provision"
tags: [security, docker, credentials]
type: security
priority: critical
status: proposed
references:
  - src/dot_work/container/provision/core.py
---

### Problem
In `core.py:591-592`, the embedded bash script writes GitHub credentials to `~/.git-credentials` in plaintext:
```bash
echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
```
While the container is ephemeral, this is a security concern if:
- The image is saved or committed
- Container logs capture the credentials
- The container fails and is debugged with inspection tools

### Affected Files
- `src/dot_work/container/provision/core.py` (line 591-592)

### Importance
**CRITICAL**: Secrets should never be written to disk in plaintext, even in ephemeral containers. This pattern can lead to credential leakage in various scenarios.

### Proposed Solution
1. Use `GIT_ASKPASS` environment variable with a helper script that echoes the token
2. Or use git credential helper in memory mode: `git config --global credential.helper 'cache --timeout=3600'`
3. Or pass credentials via environment variable that git reads directly

### Acceptance Criteria
- [ ] No plaintext credentials written to disk
- [ ] Git operations still work with GitHub authentication
- [ ] Solution documented for security review

### Notes
Related to container security practices. Consider security audit of entire bash script.

---

---
id: "CR-002@b3d5e7"
title: "Missing test coverage for container/provision core module"
description: "Core orchestration code has almost zero test coverage"
created: 2024-12-27
section: "container/provision"
tags: [testing, quality, docker]
type: test
priority: critical
status: proposed
references:
  - src/dot_work/container/provision/core.py
  - tests/unit/container/provision/test_core.py
---

### Problem
The `container/provision/core.py` module (889 lines) handles critical Docker orchestration including:
- Configuration resolution (`_resolve_config()` - 172 lines)
- Docker command building (`_build_env_args()`, `_build_volume_args()`)
- Docker image validation (`validate_docker_image()`, `validate_dockerfile_path()`)
- The main entry point (`run_from_markdown()`)

However, `test_core.py` only tests `RepoAgentError` creation (38 lines). The core business logic is untested.

### Affected Files
- `src/dot_work/container/provision/core.py`
- `tests/unit/container/provision/test_core.py`

### Importance
**CRITICAL**: This module orchestrates Docker containers that modify GitHub repositories. Bugs could:
- Create malformed Docker commands exposing secrets
- Fail silently leaving repos in inconsistent states
- Break in production with no test to catch regressions

### Proposed Solution
1. Add unit tests for `_resolve_config()` with various frontmatter scenarios
2. Add unit tests for `_build_env_args()` and `_build_volume_args()`
3. Add validation tests for `validate_docker_image()` edge cases
4. Add integration tests mocking Docker CLI

### Acceptance Criteria
- [ ] Test coverage for `_resolve_config()` ≥80%
- [ ] Test coverage for Docker command building ≥80%
- [ ] Edge cases for docker image validation tested
- [ ] Overall module coverage ≥70%

### Notes
The 175-line embedded bash script also lacks testing. Consider bats or shell-level tests.

---

---
id: "CR-003@c4f8a2"
title: "Missing logging in container/provision module"
description: "Docker orchestration has no logging making failures undebuggable"
created: 2024-12-27
section: "container/provision"
tags: [observability, logging, debugging]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/container/provision/core.py
---

### Problem
The `container/provision/core.py` module (889 lines) has zero logging statements. For a tool that orchestrates Docker, git, and external tools, logging is essential for debugging failures.

When operations fail, users cannot diagnose:
- Which configuration values were resolved
- What Docker command was generated
- Which step in the process failed
- What environment variables were passed

### Affected Files
- `src/dot_work/container/provision/core.py`

### Importance
**CRITICAL**: Without logging, production failures are undebuggable. Users will report "it didn't work" with no actionable information.

### Proposed Solution
1. Add structured logging with levels throughout the module
2. Log configuration resolution at DEBUG level
3. Log Docker commands being executed at INFO level
4. Log success/failure at appropriate levels
5. Ensure sensitive values (tokens) are masked in logs

### Acceptance Criteria
- [ ] Logging added for configuration resolution
- [ ] Logging added for Docker build/run
- [ ] Logging added for git operations
- [ ] Sensitive values masked in log output
- [ ] Debug mode exposes detailed trace

### Notes
AGENTS.md requires using `logging` not `print()`. The module currently uses `print()` for dry-run output.

---

---
id: "CR-004@d2e6b9"
title: "Global mutable state in review config.py violates AGENTS.md"
description: "settings = Config.from_env() creates untestable global singleton"
created: 2024-12-27
section: "review"
tags: [architecture, testing, global-state]
type: bug
priority: critical
status: proposed
references:
  - src/dot_work/review/config.py
---

### Problem
In `config.py:30`, `settings = Config.from_env()` creates a global singleton at module import time. This:
1. Makes configuration non-testable without monkeypatching
2. Violates AGENTS.md prohibition on global state
3. Captures environment variables at import time (stale config if env vars change)
4. Prevents thread-safe reconfiguration

### Affected Files
- `src/dot_work/review/config.py` (line 30)

### Importance
**CRITICAL**: Global state makes the module untestable and prevents dynamic configuration. This pattern is explicitly forbidden in AGENTS.md.

### Proposed Solution
1. Remove global `settings` singleton
2. Pass config via dependency injection to functions that need it
3. Create config on-demand or accept as parameter
4. Consider using a factory function that reads env at call time

### Acceptance Criteria
- [ ] No global mutable state at module level
- [ ] Config can be overridden for testing
- [ ] Environment changes are reflected without restart
- [ ] All existing functionality preserved

### Notes
This is a pattern violation that affects testability. Should be fixed before adding more tests.

---

---
id: "CR-073@a8b4c2"
title: "SQL Injection Vulnerability in SearchService FTS5 Query"
description: "FTS5 MATCH clause accepts unvalidated user input enabling advanced query abuse"
created: 2024-12-27
section: "db_issues"
tags: [security, sql-injection, fts5, search]
type: security
priority: critical
status: proposed
references:
  - src/dot_work/db_issues/services/search_service.py
---

### Problem
In `search_service.py:52-68`, the `search()` method passes user-provided `query` parameter directly to FTS5 `MATCH` clause without validation or sanitization. The query is passed to SQL as `params={"query": query}`.

While SQL parameter binding protects against standard SQL injection, FTS5 syntax allows special operators (`NEAR`, `OR`, `AND`, `NOT`, prefix searches `term*`, column filters `title:term`, etc.) that can be abused to:

1. Search for sensitive patterns across all columns bypassing `include_closed=False`
2. Execute complex boolean logic to bypass intended restrictions  
3. Potentially cause DoS via expensive queries (NEAR with large distances, complex boolean expressions)

There is NO query validation or sanitization before the query is passed to FTS5.

### Affected Files
- `src/dot_work/db_issues/services/search_service.py` (lines 52-68)

### Importance
**CRITICAL**: FTS5 query injection can lead to:
- Unauthorized data disclosure via advanced search operators
- Bypass of access controls (search closed issues even when restricted)
- Performance degradation and DoS via complex queries
- Potential privacy violations

### Proposed Solution
1. Add FTS5 query parser to validate and sanitize operators
2. Limit allowed operators to `AND`, `OR`, and basic term matching
3. Strip or escape column filters (`title:`, `description:`) unless explicitly allowed
4. Add query complexity limits (max operators, max length, max term count)
5. Implement allowlist of permitted FTS5 syntax

### Acceptance Criteria
- [ ] FTS5 query parser validates all user input
- [ ] Dangerous operators (NEAR, column filters, complex booleans) blocked or restricted
- [ ] Query complexity limits enforced (length, operator count)
- [ ] `include_closed=False` parameter cannot be bypassed
- [ ] Unit tests for injection attempts
- [ ] Integration tests verify no search bypass

### Notes
FTS5 has rich query syntax that was designed for power users but creates security concerns when exposed to untrusted input. Consider whether advanced FTS5 features are needed for the use case, or if simpler keyword matching suffices.

---

---
id: "CR-074@b9c5d3"
title: "Directory Traversal via DOT_WORK_DB_ISSUES_PATH Environment Variable"
description: "Environment variable accepts arbitrary paths without validation enabling file system attacks"
created: 2024-12-27
section: "db_issues"
tags: [security, path-traversal, environment-variables, configuration]
type: security
priority: critical
status: proposed
references:
  - src/dot_work/db_issues/config.py
---

### Problem
In `config.py:24-34`, `DbIssuesConfig.from_env()` accepts arbitrary path from `DOT_WORK_DB_ISSUES_PATH` environment variable without validation:

```python
@classmethod
def from_env(cls) -> "DbIssuesConfig":
    base = os.getenv("DOT_WORK_DB_ISSUES_PATH")
    return cls(base_path=Path(base) if base else Path(".work/db-issues"))
```

An attacker can set `DOT_WORK_DB_ISSUES_PATH=../../../../etc/` or `../../.ssh/` or `/tmp/malicious/` to:

1. Overwrite system files during database operations (SQLite file creation/writes)
2. Read sensitive files through SQLite database interface
3. Create malicious files in arbitrary locations
4. Perform directory traversal to access files outside project boundary

**No validation checks:**
- Path is absolute or within safe directory
- Path contains `..` sequences
- Path points to sensitive system locations

### Affected Files
- `src/dot_work/db_issues/config.py` (lines 24-34)

### Importance
**CRITICAL**: Arbitrary file path control enables:
- Overwrite critical system files (e.g., `/etc/passwd` if permissions allow)
- Create SQLite databases in sensitive locations then read/write arbitrary data
- Bypass project isolation by accessing other users' data
- Privilege escalation via file manipulation in multi-user environments

### Proposed Solution
1. Validate path is within current working directory or explicitly allowed location
2. Use `Path.resolve().is_relative_to()` to check path containment (Python 3.9+) or manual validation
3. Reject paths containing `..` sequences
4. Validate resolved path is under project root or home directory
5. Add warning if path points outside current project
6. Consider only accepting relative paths from project root

### Acceptance Criteria
- [ ] Path validated to be within safe directory
- [ ] Paths with `..` rejected or resolved and checked
- [ ] Absolute paths restricted to known safe locations
- [ ] Security warning for out-of-project paths
- [ ] Unit tests for path traversal attempts
- [ ] Integration tests verify directory enforcement

### Notes
Environment variables are a common source of security vulnerabilities. Best practice is to either:
- Accept only relative paths from a known safe base directory
- Explicitly whitelist allowed absolute paths
- Resolve and validate against project boundary

---
id: "PERF-001@f1a2b3"
title: "N+1 Query in IssueGraphRepository.has_cycle()"
description: "Cycle detection performs O(N) database queries for single check"
created: 2024-12-27
section: "db_issues"
tags: [performance, database, n-plus-one, cycle-detection, algorithm]
type: refactor
priority: critical
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
In `sqlite.py:1089-1107`, `has_cycle()` uses DFS with N+1 database query pattern:

```python
def has_cycle(self, from_issue_id: str, to_issue_id: str) -> bool:
    def dfs(current: str) -> bool:
        # N+1 QUERY: New database query for EVERY recursive call
        statement = select(DependencyModel).where(DependencyModel.from_issue_id == current)
        models = self.session.exec(statement).all()
        
        for model in models:
            if dfs(model.to_issue_id):  # Recursive call = another query
                return True
        return False
    
    return dfs(to_issue_id)
```

**Performance issue:**
- DFS cycle detection executes O(N) database queries for a single cycle check
- Each recursive level triggers a SELECT query to get dependencies
- Called during every dependency addition to prevent cycles
- Graph with 100 dependencies = 100+ database queries
- 1000 dependencies = 1000+ database queries

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (lines 1089-1107)

### Importance
**CRITICAL**: Exponential performance degradation prevents scaling beyond hundreds of issues:
- Dependency operations become exponentially slow as issue count grows
- 100 issues: ~100ms cycle detection
- 1000 issues: ~1000ms (1 second) for single dependency check
- 10000 issues: ~10+ seconds per dependency add
- Database connection pool exhausted under concurrent operations
- Makes large-scale issue tracking unusable

### Proposed Solution
Load all dependencies in single query upfront, build in-memory adjacency list, perform DFS in memory:

```python
def has_cycle(self, from_issue_id: str, to_issue_id: str) -> bool:
    # Single query to load all dependencies
    all_deps = self.session.exec(select(DependencyModel).all())
    
    # Build adjacency list in memory
    adj = defaultdict(list)
    for dep in all_deps:
        adj[dep.from_issue_id].append(dep.to_issue_id)
    
    # DFS in-memory (O(V+E) with no DB queries)
    def dfs(current: str, visited: set) -> bool:
        if current == from_issue_id:
            return True
        if current in visited:
            return False
        visited.add(current)
        return any(dfs(neighbor, visited) for neighbor in adj[current])
    
    return dfs(to_issue_id, set())
```

### Acceptance Criteria
- [ ] Single database query for all dependencies
- [ ] In-memory adjacency list built once
- [ ] Cycle detection runs in O(V+E) without DB queries
- [ ] Performance test: 1000 deps < 10ms
- [ ] Existing functionality preserved

### Notes
This is a classic N+1 query problem. The optimization eliminates O(N) database roundtrips and should provide 100-1000x speedup for large graphs.

---
id: "PERF-002@g2h3i4"
title: "O(n²) Algorithm in _get_commit_branch()"
description: "Git branch lookup iterates all commits per branch for each commit"
created: 2024-12-27
section: "git"
tags: [performance, algorithm, o-n-squared, git, branch-detection]
type: refactor
priority: critical
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:621-622`, `_get_commit_branch()` has O(n²) nested loop:

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    # O(n²) nested loop
    for branch in self.repo.branches:  # Iterate all branches (N)
        if commit.hexsha in [c.hexsha for c in self.repo.iter_commits(branch.name)]:
            # For EACH branch, iterate ALL commits in that branch (M)
            # Total: N × M operations
            return branch.name
```

**Performance issue:**
- For every commit check, iterates through all branches (N)
- For each branch, builds list of ALL commits (M commits per branch average)
- Total complexity: O(num_branches × avg_commits_per_branch)
- Called for EVERY commit in comparison (100-1000+ times)

**Example costs:**
- Large repo (100 branches × 500 commits avg) = 50,000 operations per commit
- 100 commits × 50,000 ops/commit = 5,000,000 operations
- 1000 commits = 50,000,000+ operations
- Can cause 10+ second delays for branch-based analysis

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 621-622)

### Importance
**CRITICAL**: Makes git analysis unusable for large repositories:
- Git comparison becomes exponentially slow as repo grows
- CPU time wasted on redundant commit traversals
- Blocks users from analyzing significant code changes
- Makes the tool unusable for enterprise-scale repos

### Proposed Solution
Use git's built-in branch --contains (O(log N) via commit graph) or pre-build commit-to-branch mapping:

```python
def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    # Pre-build commit-to-branch mapping once per comparison
    commit_to_branch = {}
    for branch in self.repo.branches:
        for commit in self.repo.iter_commits(branch.name):
            commit_to_branch[commit.hexsha] = branch.name
    
    # Use mapping for O(1) lookups in analyze_commit()
    commits = self._get_commits_between_refs(from_ref, to_ref)
    for commit in commits:
        # Now O(1) lookup
        branch = commit_to_branch.get(commit.hexsha, "unknown")
```

Or use git's optimized --contains check:

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    # Use git's optimized --contains (O(log N) via commit graph)
    for branch in self.repo.branches:
        try:
            if commit.hexsha in self.repo.git.branch('--contains', commit.hexsha, '--list').split():
                return branch.name
        except Exception:
            continue
    return "unknown"
```

### Acceptance Criteria
- [ ] Commit-to-branch mapping built once per comparison
- [ ] O(1) branch lookup for each commit
- [ ] Performance test: 1000 commits < 5 seconds
- [ ] Memory usage reasonable for pre-built map
- [ ] Alternative git-based --contains approach considered

### Notes
This is a textbook O(n²) algorithm problem. Pre-building the commit-to-branch map should provide 100-1000x speedup for large repositories. The memory overhead is acceptable compared to the performance gain.

---