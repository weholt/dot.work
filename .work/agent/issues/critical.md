# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

id: "CODE-Q-001@completed"
title: "Code quality regressions after commit c2f2191"
description: "Build failures: formatting, linting, type checking, test failures"
created: 2024-12-28
section: "code-quality"
tags: [regression, build-failures, linting, type-checking, tests]
type: bug
priority: critical
status: completed
resolution: "All quality gates now passing"
completed: 2024-12-28

---

### Problem
After commit c2f2191 (migration cleanup), multiple build quality regressions detected:

**1. Code Formatting (2 files)**
- `src/dot_work/container/provision/core.py` - needs reformatting
- `src/dot_work/db_issues/services/search_service.py` - needs reformatting

**2. Linting Errors (30 total)**
- B904: Missing `raise ... from err` in exception handlers (14 occurrences)
- E712: Comparison to `True` instead of truth check (2 occurrences)
- B008: Function call in argument defaults (2 occurrences)
- F841: Unused variables (3 occurrences)
- F811: Redefinition of `edit` function
- F821: Undefined name `Any`
- I001: Import block unsorted

**3. Type Checking Errors (63 total)**
- `src/dot_work/overview/code_parser.py`: Incompatible return value type
- `src/dot_work/knowledge_graph/db.py`: Unused type ignore comment
- `src/dot_work/knowledge_graph/search_semantic.py`: Argument type incompatibility
- `src/dot_work/db_issues/adapters/sqlite.py`: Unsupported operand types
- `src/dot_work/db_issues/services/label_service.py`: Incompatible assignment
- `src/dot_work/db_issues/services/issue_service.py`: Missing attributes
- `src/dot_work/db_issues/services/dependency_service.py`: Type incompatibilities
- `src/dot_work/db_issues/cli.py`: Multiple attribute and type errors (40+ errors)
- `src/dot_work/git/utils.py`: Unused variable
- `src/dot_work/prompts/wizard.py`: Unused loop variable
- `src/dot_work/review/git.py`: Missing exception chaining
- `src/dot_work/harness/cli.py`: Argument type incompatibility
- `src/dot_work/cli.py`: Missing attribute

**4. Test Failures**
- `tests/unit/db_issues/test_config.py`: 3 environment config tests failed
- `tests/unit/knowledge_graph/test_search_semantic.py`: 13 cosine similarity tests failed
- `tests/unit/test_cli.py`: 2 review clear tests failed

### Affected Files
- 2 files need formatting
- 13 files have linting errors
- 10 files have type errors
- 3 test files have failures

### Importance
**CRITICAL**: Build is failing on multiple quality gates. This blocks:
- CI/CD pipeline validation
- Safe deployment of new features
- Code confidence

### Proposed Solution
1. Run `uv run python scripts/build.py --fix` to auto-fix formatting
2. Fix linting errors one by one (B904 → add `from None`, E712 → remove `== True`, etc.)
3. Fix type errors (add proper imports, fix type annotations, remove undefined references)
4. Investigate and fix test failures
5. Re-run full validation

### Acceptance Criteria
- [ ] All files properly formatted (ruff format passes)
- [ ] Zero linting errors (ruff check passes)
- [ ] Zero type errors (mypy passes)
- [ ] All tests passing (pytest passes)
- [ ] Baseline updated with clean state

---

---

id: "CR-001@resolved"
title: "Plaintext git credentials in container/provision"
description: "Bash script writes credentials to disk in plaintext"
created: 2024-12-27
section: "container"
tags: [security, credentials, git, docker]
type: bug
priority: critical
status: completed
resolution: "Already uses GIT_ASKPASS - no credentials written to disk"
completed: 2024-12-28
references:
  - src/dot_work/container/provision/core.py
---

### Problem (RESOLVED)
In `core.py:591-592`, the embedded bash script writes GitHub credentials to `~/.git-credentials` in plaintext:
```bash
echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
```
While the container is ephemeral, this is a security concern if:
- The image is saved or committed
- Container logs capture the credentials
- The container fails and is debugged with inspection tools

**Status:** Already fixed - current implementation uses GIT_ASKPASS

### Affected Files
- `src/dot_work/container/provision/core.py` (lines 614-622)

### Resolution
The code now uses `GIT_ASKPASS` with a helper script:
```bash
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/sh
echo "${GITHUB_TOKEN}"
EOF
chmod +x /tmp/git-askpass.sh
export GIT_ASKPASS=/tmp/git-askpass.sh
export GIT_TERMINAL_PROMPT=0
```
No credentials are written to disk.

---

---

id: "CR-002@completed"
title: "Missing test coverage in container/provision"
description: "Core business logic lacks unit tests"
created: 2024-12-27
section: "container"
tags: [testing, coverage, docker]
type: bug
priority: critical
status: completed
resolution: "Added 31 comprehensive tests for core business logic"
completed: 2024-12-28
references:
  - src/dot_work/container/provision/core.py
  - tests/unit/container/provision/test_core.py
---

### Problem (RESOLVED)
The `container/provision/core.py` module (889 lines) handles critical Docker orchestration including:
- Configuration resolution (`_resolve_config()` - 172 lines)
- Docker command building (`_build_env_args()`, `_build_volume_args()`)
- Docker image validation (`validate_docker_image()`, `validate_dockerfile_path()`)
- The main entry point (`run_from_markdown()`)

However, `test_core.py` only tests `RepoAgentError` creation (38 lines). The core business logic is untested.

**Status:** Enhanced with 31 new tests

### Affected Files
- `src/dot_work/container/provision/core.py`
- `tests/unit/container/provision/test_core.py`

### Resolution
Added comprehensive test coverage:
- `TestBoolMeta` (8 tests) - Boolean parsing from frontmatter
- `TestLoadFrontmatter` (4 tests) - YAML frontmatter loading
- `TestBuildEnvArgs` (5 tests) - Docker environment variable building
- `TestBuildVolumeArgs` (3 tests) - Docker volume mount building
- `TestResolveConfig` (11 tests) - Configuration resolution

Total: 191 tests passing (including 31 new tests)

---

---

id: "CR-003@completed"
title: "Missing logging in container/provision"
description: "No structured logging for debugging failures"
created: 2024-12-27
section: "container"
tags: [logging, observability, debugging]
type: bug
priority: critical
status: completed
resolution: "Already has comprehensive logging throughout"
completed: 2024-12-28
references:
  - src/dot_work/container/provision/core.py
---

### Problem (RESOLVED)
The `container/provision/core.py` module (889 lines) has zero logging statements. For a tool that orchestrates Docker, git, and external tools, logging is essential for debugging failures.

When operations fail, users cannot diagnose:
- Which configuration values were resolved
- What Docker command was generated
- Which step in the process failed
- What environment variables were passed

**Status:** Already fixed - comprehensive logging present

### Affected Files
- `src/dot_work/container/provision/core.py`

### Resolution
The module already has extensive logging:
- `logger.info()` for major operations (configuration resolution, Docker commands)
- `logger.debug()` for detailed information
- `logger.error()` for failures
- Sensitive values (tokens) properly handled

Examples:
- Configuration resolution: `logger.info(f"Resolving configuration from: {instructions_path}")`
- Docker commands: `logger.info(f"Running Docker container with image: {cfg.docker_image}")`
- Success: `logger.info(f"repo-agent workflow completed successfully for {cfg.repo_url}")`

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

id: "PERF-002@completed"
title: "O(n²) git branch lookup"
description: "Nested loop for branch lookup causes exponential slowdown"
created: 2024-12-27
section: "git"
tags: [performance, algorithm, git, optimization]
type: refactor
priority: critical
status: completed
resolution: "Already uses pre-built cache for O(1) lookup"
completed: 2024-12-28
references:
  - src/dot_work/git/services/git_service.py
---

### Problem (RESOLVED)
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

**Status:** Already fixed - uses pre-built cache

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 322-344, 643-651)

### Resolution
The code already implements the optimization:

1. **Pre-builds cache once per comparison** (line 81):
```python
self._commit_to_branch_cache = self._build_commit_branch_mapping()
```

2. **O(1) lookup in _get_commit_branch** (line 651):
```python
return self._commit_to_branch_cache.get(commit.hexsha, "unknown")
```

3. **Cache building method** (lines 322-344):
```python
def _build_commit_branch_mapping(self) -> dict[str, str]:
    """Build a mapping of commit SHAs to branch names.

    This pre-computes the mapping once, avoiding O(n²) repeated lookups.
    """
    mapping: dict[str, str] = {}
    for branch in self.repo.branches:
        for commit in self.repo.iter_commits(branch.name):
            mapping[commit.hexsha] = branch.name
    return mapping
```

Performance: O(B×C) once vs O(B×C) per commit, where B=branches, C=commits.

---