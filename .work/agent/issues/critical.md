# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

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
id: "PERF-001@f1a2b3"
title: "N+1 Query in IssueGraphRepository.has_cycle()"
description: "Cycle detection performs O(N) database queries for single check"
created: 2024-12-27
section: "db_issues"
tags: [performance, database, n-plus-one, cycle-detection, algorithm]
type: refactor
priority: critical
status: completed
resolution: "Fixed by loading all dependencies in single query and using in-memory DFS"
completed: 2024-12-28
references:
  - src/dot_work/db_issues/adapters/sqlite.py
  - tests/unit/db_issues/test_cycle_detection_n_plus_one.py
---

### Problem (COMPLETED)
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