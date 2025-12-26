# Medium Priority Issues (P2)

Enhancements, technical debt.

---

---
id: "SEC-007@94eb69"
title: "Security: Missing HTTPS validation in file upload"
description: "Zip file upload does not verify SSL certificates by default"
created: 2025-12-25
section: "zip"
tags: [security, ssl, https, upload]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/zip/uploader.py
  - src/dot_work/zip/uploader.py:45
---

### Problem
In `src/dot_work/zip/uploader.py` at line 45:
```python
response = requests.post(api_url, files=files, timeout=30)
```

The `requests.post()` call does not explicitly set SSL verification parameters. While `requests` does verify SSL certificates by default, this should be explicit for security-sensitive operations.

**Issues:**
1. No explicit `verify=True` parameter makes security policy unclear
2. No timeout for SSL handshake (30s timeout only applies to request)
3. No validation of `api_url` scheme (could be http:// in testing)
4. No protection against malicious server responses

### Affected Files
- `src/dot_work/zip/uploader.py` (line 45)

### Importance
**MEDIUM**: While requests defaults to secure, explicit security parameters prevent accidental misconfiguration and make security intent clear.

CVSS Score: 4.3 (Medium)
- Attack Vector: Network
- Attack Complexity: High
- Privileges Required: None
- Impact: Low (integrity of upload only)

### Proposed Solution
1. **Explicit SSL verification**:
   ```python
   response = requests.post(api_url, files=files, timeout=30, verify=True)
   ```

2. **Validate URL scheme**:
   ```python
   if not api_url.startswith('https://'):
       raise ValueError("Only HTTPS URLs are supported")
   ```

3. **Add connection timeout**:
   ```python
   response = requests.post(api_url, files=files, timeout=(10, 30))
   ```

### Acceptance Criteria
- [ ] SSL verification explicitly set to `verify=True`
- [ ] URL scheme validated to be HTTPS
- [ ] Separate connection timeout from read timeout
- [ ] Tests verify HTTP URLs are rejected
- [ ] Tests verify invalid certificates are rejected

### Notes
- Default behavior is secure, but explicit is better for security-critical code
- Consider adding certificate bundle option for enterprise environments
- Document security requirements for `api_url`

---
id: "SEC-008@94eb69"
title: "Security: Unsafe temporary file handling in editor workflows"
description: "Temp files created with predictable names and permissions"
created: 2025-12-25
section: "db-issues"
tags: [security, tempfile, race-condition]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/cli.py
  - src/dot_work/db_issues/cli.py:1209-1242
---

### Problem
In `src/dot_work/db_issues/cli.py`, temporary files for editor workflows are created using:
```python
with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".md",
    prefix="db-issues-editor-",
    delete=False,
) as f:
```

**Security issues:**
1. **`delete=False`**: Files persist if exception occurs before cleanup
2. **Predictable names**: Prefix pattern makes names guessable
3. **Default permissions**: Temp files inherit umask (often 0644, world-readable)
4. **Cleanup in finally block**: Could fail silently

**Attack scenario:**
- Attacker monitors temp directory
- Predicts temp file name from prefix
- Races to read sensitive content before user finishes editing
- Or races to replace content with malicious data

### Affected Files
- `src/dot_work/db_issues/cli.py` (lines 1209-1242, 1282-1308)

### Importance
**MEDIUM**: While local attack with timing constraints, sensitive issue content could be exposed in shared environments (CI, cloud IDEs).

CVSS Score: 3.7 (Low)
- Attack Vector: Local
- Attack Complexity: High (race condition)
- Privileges Required: Low (same user)
- Impact: Low (confidentiality of issue tracker)

### Proposed Solution
1. **Use `delete=True`** with proper context management:
   ```python
   with tempfile.NamedTemporaryFile(
       mode="w",
       suffix=".yaml",
       prefix="db-issues-edit-",
       encoding="utf-8",
   ) as f:
       # Use f.name directly, no manual cleanup
   ```

2. **Set restrictive permissions**:
   ```python
   import os
   import stat
   os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
   ```

3. **Use secure directory**: Consider temp subdir with restricted permissions

### Acceptance Criteria
- [ ] Temp files use `delete=True` where possible
- [ ] File permissions set to 0600 (owner read/write only)
- [ ] Cleanup happens even on exceptions
- [ ] Tests verify temp files are cleaned up
- [ ] Tests verify file permissions are restrictive

### Notes
- For `delete=False` cases, add robust cleanup with atexit
- Consider using `tempfile.mkstemp()` for even more control
- Document security assumptions in docstrings

---
id: "SEC-009@94eb69"
title: "Security: Missing authorization checks in database operations"
description: "No user/context validation before database modifications"
created: 2025-12-25
section: "db-issues"
tags: [security, authorization, database]
type: security
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
  - src/dot_work/db_issues/services/*
---

### Problem
The db_issues module performs database operations without any authorization checks:

**Examples:**
1. `IssueService` can create, update, delete any issue without user validation
2. No project-level access control
3. No audit trail of who made changes
4. Bulk operations lack authorization

**In `src/dot_work/db_issues/adapters/sqlite.py`:**
- `insert_issue()` - No user validation
- `update_issue()` - No user validation
- `delete_issue()` - No user validation

**Security impact:**
- Any user with CLI access can modify any issue
- No way to restrict users to specific projects
- No accountability for changes
- Could be abused in CI/CD with shared credentials

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (all mutation methods)
- `src/dot_work/db_issues/services/*.py` (service layer lacks auth)

### Importance
**MEDIUM**: While primarily a developer tool, lack of authorization becomes a risk when:
- Used in team environments with shared databases
- Integrated with web interfaces
- Used in CI/CD with elevated permissions

CVSS Score: 4.6 (Medium)
- Attack Vector: Local
- Attack Complexity: Low
- Privileges Required: Low (CLI access)
- Impact: Low (issue tracker data)

### Proposed Solution
1. **Add user context to service methods**:
   ```python
   def update_issue(self, issue_id: str, changes: dict, user: User) -> Issue:
       if not self.can_modify_issue(issue_id, user):
           raise PermissionError(...)
   ```

2. **Add project ownership**:
   ```python
   class Project:
       owner_id: str
       collaborators: list[str]
   ```

3. **Add audit logging**:
   ```python
   def _audit_log(self, action: str, entity: str, user: User):
       self.audit_log.append(AuditEntry(action, entity, user, time.now()))
   ```

4. **Make auth optional** (for single-user setups)

### Acceptance Criteria
- [ ] Service methods accept optional user context
- [ ] Project-level access control implemented
- [ ] Audit trail tracks all modifications
- [ ] Single-user mode bypasses auth for usability
- [ ] Tests verify authorization enforcement

### Notes
- Balance security with usability for developer tools
- Consider integrating with system user or git config
- Document security model in README

---
id: "PERF-004@d6e8f3"
title: "Performance: Scan metrics creates unnecessary intermediate lists"
description: "O(N) memory usage for collecting all functions"
created: 2025-12-25
section: "python_scan"
tags: [performance, memory, algorithm]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/python/scan/service.py
---

### Problem
The `_update_metrics()` method in `service.py` lines 156-169 creates a flat list of ALL functions in the codebase:
```python
all_functions: list[Any] = []
for file_entity in index.files.values():
    all_functions.extend(file_entity.functions)
    for cls in file_entity.classes:
        all_functions.extend(cls.methods)
```

This uses O(N) additional memory where N = total functions across all files. For large codebases (thousands of functions), this is wasteful since we only need to:
- Count total functions
- Calculate average complexity
- Find max complexity
- List high-complexity functions

### Affected Files
- `src/dot_work/python/scan/service.py` (lines 156-169)

### Importance
- Memory overhead scales with codebase size
- Metrics calculation uses more memory than necessary
- For large projects with 10k+ functions, this adds significant memory pressure
- All metrics can be calculated with streaming (O(1) memory)

### Proposed Solution
Use generator-based or streaming approach to calculate metrics without storing all functions:
```python
total_functions = 0
complexities = []
high_complexity = []

for file_entity in index.files.values():
    total_functions += len(file_entity.functions)
    for f in file_entity.functions:
        complexities.append(f.complexity)
    for cls in file_entity.classes:
        total_functions += len(cls.methods)
        for m in cls.methods:
            complexities.append(m.complexity)
```

Or even better, calculate aggregates incrementally without storing complexities list.

### Acceptance Criteria
- [ ] Metrics calculation uses O(1) additional memory
- [ ] No intermediate list of all functions created
- [ ] Tests verify same metrics values produced
- [ ] Performance improvement measurable on large codebases

### Notes
This is a common optimization pattern: replace "collect all, then process" with "process incrementally".

---
id: "PERF-005@e7f9a4"
title: "Performance: JSON repository uses human-readable formatting for storage"
description: "Unnecessary indent=2 increases file size and write time"
created: 2025-12-25
section: "python_scan"
tags: [performance, i/o, serialization]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/python/scan/repository.py
---

### Problem
The `save()` method in `repository.py` line 52 uses `json.dumps(data, indent=2)` which:
- Increases file size by ~30-40% due to whitespace
- Slower write time due to more bytes written
- Slower read time due to more bytes to parse
- Human formatting is unnecessary for a machine-readable cache file

Code:
```python
self.config.index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

### Affected Files
- `src/dot_work/python/scan/repository.py` (line 52)

### Importance
- Cache file larger than necessary
- Slower save/load operations
- For codebases with thousands of files, the index can be hundreds of KB
- Human readability of cache is not a requirement (it's an internal format)

### Proposed Solution
Use compact JSON formatting:
```python
# For storage (compact)
json.dumps(data, separators=(',', ':'))

# For debugging (if needed)
json.dumps(data, indent=2)
```

Or provide a configuration option for pretty printing during development.

### Acceptance Criteria
- [ ] Default storage uses compact JSON (no unnecessary whitespace)
- [ ] Optional debug mode for human-readable output
- [ ] File size reduced by ~30%
- [ ] Write/read operations measurably faster
- [ ] Tests verify data can be loaded correctly

### Notes
This is a minor optimization but adds up for frequently-written cache files. Compact JSON is still readable in editors if needed for debugging.

---
id: "PERF-006@f8a0b5"
title: "Performance: Git file scanner uses rglob without early filtering"
description: "Creates unnecessary Path objects for ignored directories"
created: 2025-12-25
section: "review"
tags: [performance, file-scanning, pathlib]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/review/git.py
---

### Problem
The `list_all_files()` function in `git.py` line 114 uses `Path.rglob("*")` which recursively walks the entire directory tree, creating Path objects for every file, then filters them out later:
```python
for item in root_path.rglob("*"):
    if item.is_file():
        # Check if any parent directory should be ignored
        rel = item.relative_to(root_path)
        parts = rel.parts
        if any(part in ignore_dirs ... for part in parts[:-1]):
            continue
```

This creates Path objects for files in ignored directories only to discard them.

### Affected Files
- `src/dot_work/review/git.py` (lines 114-125)

### Importance
- Unnecessary filesystem operations
- Creates Path objects for files that will be ignored
- For node_modules, .git, venv this can mean thousands of wasted iterations
- Slower repository scanning

### Proposed Solution
1. Use os.walk() with directory pruning (like scanner.py does)
2. Pre-check directories before recursing
3. Use explicit iteration with early continue

Example:
```python
for root, dirs, files in os.walk(root_path):
    # Prune ignored directories
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        # Process files
```

### Acceptance Criteria
- [ ] Path objects only created for non-ignored files
- [ ] Directories pruned before recursing
- [ ] Performance measurable on projects with large ignored folders
- [ ] Tests verify same files found

### Notes
The scanner.py file already uses this pattern correctly (line 61-65). This same optimization should be applied here.

---
id: "PERF-007@g9b1c6"
title: "Performance: Bulk operations lack proper database batching"
description: "Sequential operations instead of batch INSERT/UPDATE"
created: 2025-12-25
section: "db_issues"
tags: [performance, database, batch-operations]
type: performance
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/bulk_service.py
---

### Problem
The `bulk_create()` and other bulk operations in `bulk_service.py` perform sequential database operations:
```python
for idx, issue_data in enumerate(issues_data, start=1):
    issue = self.issue_service.create_issue(**issue_dict)
    issue_ids.append(issue.id)
```

Each create/update is a separate database transaction. For 100 issues, this means 100 round-trips to the database.

### Affected Files
- `src/dot_work/db_issues/services/bulk_service.py` (lines 317-333: bulk_create)
- Same pattern in bulk_close, bulk_update, bulk_label_add, bulk_label_remove

### Importance
- Bulk operations are much slower than necessary
- Each operation is a separate transaction (overhead)
- Database round-trips add latency
- For 1000 issues, this could take seconds instead of milliseconds

### Proposed Solution
1. Add batch insert methods to repository layer
2. Use executemany() for bulk SQLite operations
3. Single transaction for entire batch operation
4. Consider prepared statements for repeated operations

Example:
```python
# Repository method
def insert_issues_batch(self, issues: list[Issue]) -> list[Issue]:
    with self.transaction() as conn:
        conn.executemany(
            "INSERT INTO issues (...) VALUES (...)",
            [(i.id, i.title, ...) for i in issues]
        )
```

### Acceptance Criteria
- [ ] Bulk create uses single transaction
- [ ] Bulk operations use executemany() or equivalent
- [ ] Performance measurable: 100 issues < 100ms
- [ ] All-or-nothing semantics (transaction rollback on error)
- [ ] Tests verify batch atomicity

### Notes
SQLite supports executemany() for batch operations. The current sequential approach defeats the purpose of "bulk" operations.


---
id: "CR-003@bc5a3f"
title: "Database repository queries don't use consistent error handling"
description: "Some repository methods return None on not found, others raise exceptions"
created: 2025-12-25
section: "db-issues"
tags: [error-handling, repository-pattern, consistency]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
---

### Problem
Repository methods have inconsistent error handling patterns:
1. `get()` methods return `None` if not found (IssueRepository.get(), CommentRepository.get(), etc.)
2. `delete()` methods return `False` if not found (IssueRepository.delete(), CommentRepository.delete())
3. No methods raise the domain `NotFoundError` exception

This creates mixed contracts where callers must check for `None`/`False` instead of catching exceptions.

**Evidence:** 9 different return patterns across repositories - None for not-found, False for deletion failure, implicit success for other operations.

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (all repository classes)

### Importance
1. **Unclear contract**: Callers don't know whether to check for None/False or catch exceptions
2. **Silent failures**: `delete()` returning False could be confused with successful deletion
3. **Inconsistent with domain**: Domain layer defines `NotFoundError` (entities.py:63) that repositories don't use
4. **Principle of Least Surprise**: Similar operations should have similar error handling

### Proposed Solution
**Option A: Use domain exceptions consistently**
- Always raise `NotFoundError` when entity not found
- Always raise `DatabaseError` on database failures  
- Remove boolean return values from delete operations

**Option B: Return Result/Either type**
- Use a Result type that encapsulates success/failure
- More explicit but requires more code changes

### Acceptance Criteria
- [ ] All repository methods use consistent error handling
- [ ] Delete operations raise exception on failure instead of returning False
- [ ] Get operations raise NotFoundError instead of returning None
- [ ] All existing tests updated to expect exceptions
- [ ] Documentation updated with error handling patterns

### Notes
The domain layer defines `NotFoundError` and `DatabaseError` exceptions (lines 63, 79) but repositories don't use them. This creates a mismatch between domain and adapter layers.

---

---
id: "CR-004@4842ab"
title: "Service layer directly depends on concrete UnitOfWork implementation"
description: "Services create UnitOfWork instances without dependency injection, making testing difficult"
created: 2025-12-25
section: "db-issues"
tags: [dependency-injection, testing, architecture]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
---

### Problem
Service classes directly import and instantiate `UnitOfWork` from the adapter layer:

```python
from dot_work.db_issues.adapters.sqlite import UnitOfWork  # Direct import

def _get_uow(self) -> UnitOfWork:
    session = Session(self.engine)
    return UnitOfWork(session)
```

**Evidence:** All services (IssueService, DependencyService, EpicService, LabelService, BulkService) directly create UnitOfWork without dependency injection.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py` (imports UnitOfWork directly)
- `src/dot_work/db_issues/services/dependency_service.py`
- `src/dot_work/db_issues/services/epic_service.py`
- `src/dot_work/db_issues/services/label_service.py`
- `src/dot_work/db_issues/services/bulk_service.py`

### Importance
1. **Hard to test**: Cannot mock UnitOfWork in tests without complex patches
2. **Tight coupling**: Services are coupled to SQLite implementation
3. **Violates Dependency Inversion Principle**: Depend on concrete, not abstraction
4. **Blocks alternatives**: Can't easily swap in PostgreSQL or in-memory UoW

### Proposed Solution
**Option A: Inject UnitOfWork factory**
```python
class IssueService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory
```

**Option B: Protocol-based abstraction**
- Define `UnitOfWorkProtocol` that services depend on
- SQLite implements the protocol

### Acceptance Criteria
- [ ] Services accept UnitOfWork via constructor
- [ ] Tests can inject mock UnitOfWork
- [ ] Services don't directly import sqlite module
- [ ] All existing tests pass
- [ ] Integration tests still work with real SQLite

---

---
id: "CR-005@a782a8"
title: "Environment configuration lacks validation on target paths"
description: "Environment entries allow arbitrary target paths without validation"
created: 2025-12-25
section: "environments"
tags: [validation, configuration, security]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/environments.py
---

### Problem
The `Environment` dataclass doesn't validate that `prompt_dir` paths are well-formed. This allows entries like:
- `prompt_dir=""` (empty string)
- `prompt_dir="../../../etc"` (path traversal)
- `prompt_dir="/absolute/path"` (when expecting relative)

### Affected Files
- `src/dot_work/environments.py` (Environment dataclass)

### Importance
1. **Security**: Path traversal could write files outside intended directory
2. **Robustness**: Invalid paths cause confusing errors later
3. **User experience**: Early validation with clear errors

### Proposed Solution
Add `__post_init__` validation to Environment:
```python
def __post_init__(self):
    if not self.prompt_dir or not self.prompt_dir.strip():
        raise ValueError(f"Environment {self.name}: prompt_dir cannot be empty")
    if self.prompt_dir.startswith(".."):
        raise ValueError(f"Environment {self.name}: path traversal not allowed")
```

### Acceptance Criteria
- [ ] Environment validates prompt_dir on construction
- [ ] Path traversal attempts raise ValueError
- [ ] Empty prompt_dir raises ValueError
- [ ] Test suite verifies validation
- [ ] Clear error messages for invalid configurations

---

---
id: "CR-006@b935c0"
title: "Scan service doesn't validate input paths before scanning"
description: "Service may attempt to scan non-existent or invalid paths"
created: 2025-12-25
section: "python_scan"
tags: [validation, error-handling, scanner]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/python/scan/service.py
---

### Problem
The `ScanService.scan()` method accepts a `root_path: Path` parameter but doesn't validate:
1. The path exists
2. The path is a directory (not a file)
3. The path is within allowed bounds

The scanner handles errors gracefully (scanner.py:94-105), but the service could provide earlier validation.

### Affected Files
- `src/dot_work/python/scan/service.py` (ScanService.scan, lines 31-59)

### Importance
1. **User experience**: Clear error "path does not exist" vs generic scan error
2. **Performance**: Fail fast before walking directory tree
3. **Security**: Validate path bounds to prevent scanning unintended directories

### Proposed Solution
Add validation to `ScanService.scan()`:
```python
if not root_path.exists():
    raise FileNotFoundError(f"Scan path does not exist: {root_path}")
if not root_path.is_dir():
    raise NotADirectoryError(f"Scan path is not a directory: {root_path}")
```

### Acceptance Criteria
- [ ] Service validates path exists before scanning
- [ ] Service validates path is directory
- [ ] Clear error messages for invalid paths
- [ ] Tests verify validation behavior

---

---
id: "CR-007@2d38b2"
title: "Canonical prompt parser doesn't validate duplicate environment names"
description: "Parser allows multiple environments with same name, last one wins"
created: 2025-12-25
section: "prompts"
tags: [validation, parser, canonical-prompts]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/prompts/canonical.py
---

### Problem
The `CanonicalPromptParser._parse_environments()` method (lines 177-195) doesn't check for duplicate environment names. If YAML contains:

```yaml
environments:
  copilot:
    target: ".github/prompts/"
  copilot:  # Duplicate!
    target: ".copilot/"
```

The parser silently uses the second definition, overwriting the first.

**Evidence**: The `environments` dict (line 179) doesn't check for existing keys before adding.

### Affected Files
- `src/dot_work/prompts/canonical.py` (lines 177-195)

### Importance
1. **User error**: Typo in environment name could silently override config
2. **Debugging difficulty**: No indication that duplicate was detected
3. **Data integrity**: Silent overwrites lose configuration

### Proposed Solution
Add duplicate detection:
```python
if env_name in environments:
    raise ValueError(f"Duplicate environment name: '{env_name}'")
```

### Acceptance Criteria
- [ ] Parser raises ValueError on duplicate environment names
- [ ] Error message includes which environment was duplicated
- [ ] Tests verify duplicate detection

### Notes
The validator (lines 261-274) checks for duplicate **targets** but not duplicate **names**. These are different validations.

---

---
id: "CR-008@8e3f6d"
title: "AST scanner silently ignores syntax errors in Python files"
description: "Files with syntax errors are marked but scan doesn't report errors or fail"
created: 2025-12-25
section: "python_scan"
tags: [error-handling, ast-parsing, scanner]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/python/scan/scanner.py
---

### Problem
When scanning a file with syntax errors, `_scan_file()` returns a `FileEntity` with `has_syntax_error=True`, but the scanner doesn't:
1. Log the error
2. Count syntax errors
3. Provide a way to list files with errors
4. Fail the scan if critical files have errors

**Evidence:** Lines 94-105 return error entity but don't aggregate or report errors.

### Affected Files
- `src/dot_work/python/scan/scanner.py` (lines 94-105)
- Related: `src/dot_work/python/scan/ast_extractor.py`

### Importance
1. **Visibility**: Users don't know which files failed to parse
2. **Quality**: Syntax errors in code should be flagged
3. **CI/CD**: Should fail scans if critical files have errors
4. **Debugging**: No aggregate count of problematic files

### Proposed Solution
1. Log syntax errors at WARNING level
2. Add `get_files_with_errors()` method to `ScanService`
3. Add optional `fail_on_error` parameter to `scan()`
4. Return error summary from scan operation

### Acceptance Criteria
- [ ] Syntax errors logged during scan
- [ ] Service provides method to list files with errors
- [ ] Optional `fail_on_error` parameter causes scan to raise exception
- [ ] Error count included in scan metrics

### Notes
The current graceful degradation is useful for partial scans, but visibility into errors is important.

---

---
id: "AUDIT-GAP-002@b8c4e1"
title: "Pre-existing type errors in db_issues module from migration"
description: "50 mypy type errors in db_issues code from original migration"
created: 2025-12-25
section: "db_issues"
tags: [type-checking, mypy, migration-gap, audit]
type: refactor
priority: medium
status: proposed
references:
  - .work/agent/issues/references/AUDIT-DBISSUES-010-investigation.md
  - .work/baseline.md
  - src/dot_work/db_issues/cli.py
  - src/dot_work/db_issues/services/issue_service.py
  - src/dot_work/db_issues/services/dependency_service.py
  - src/dot_work/db_issues/services/label_service.py
---

### Problem
During AUDIT-DBISSUES-010, it was documented that 50 pre-existing mypy type errors exist in the db_issues module. These errors were introduced during the migration (MIGRATE-034 through MIGRATE-085) and have been present since then.

**Type Error Distribution:**
| File | Count | Error Types |
|------|-------|-------------|
| cli.py | 37 | attr-defined (assignee), call-overload (exec), no-redef |
| issue_service.py | 9 | attr-defined (get_dependencies, add_dependency, add_comment, generate_id) |
| dependency_service.py | 4 | assignment (list vs set for blockers) |
| label_service.py | 1 | assignment (Label | None to Label) |
| installer.py | 4 | assignment (tuple with None to tuple[str, str, str]) |

**Note:** These are **pre-existing issues from the migration**, not new regressions. They are documented in the baseline and were tracked in the original migration issues.

### Affected Files
- `src/dot_work/db_issues/cli.py` (37 errors - largest file at 209KB)
- `src/dot_work/db_issues/services/issue_service.py` (9 errors)
- `src/dot_work/db_issues/services/dependency_service.py` (4 errors)
- `src/dot_work/db_issues/services/label_service.py` (1 error)
- `src/dot_work/installer.py` (4 errors)

### Importance
**MEDIUM**: While these errors don't block functionality, they:
- Reduce type safety confidence
- Make refactoring riskier (types don't validate)
- Indicate incomplete migration to type-safe code
- May hide real bugs that type checking would catch

These are documented "known issues" rather than regressions, so they don't represent a drop in code quality from the baseline.

### Proposed Solution
1. **cli.py (37 errors):**
   - Add type stubs or fix dynamic attribute access
   - Fix exec() call-overload issues
   - Resolve no-redef conflicts

2. **issue_service.py (9 errors):**
   - Add proper type annotations for methods returning dynamically accessed attributes
   - Consider adding Protocol or dataclass for return types

3. **dependency_service.py (4 errors):**
   - Fix list vs set type mismatch for blockers field

4. **label_service.py (1 error):**
   - Fix Label | None assignment

5. **installer.py (4 errors):**
   - Fix tuple type annotations for version parsing

### Acceptance Criteria
- [ ] All 50 type errors addressed
- [ ] mypy passes cleanly on db_issues module
- [ ] No new type errors introduced
- [ ] All tests still pass (277 tests)
- [ ] Type annotations are accurate (not just suppressed with ignore)

### Notes
- These errors are documented in `.work/baseline.md` as pre-existing issues
- They were NOT introduced by recent changes
- Addressing them will improve type safety and maintainability
- Some errors may require adding `# type: ignore` comments if they're false positives
- Consider this a technical debt item rather than a critical bug


---
id: "AUDIT-GAP-005@e7f8a3"
title: "Source README.md not migrated to knowledge_graph documentation"
description: "2,808 byte README from source not present in destination docs/"
created: 2025-12-26
section: "knowledge_graph"
tags: [documentation, migration-gap, audit]
type: docs
priority: medium
status: proposed
references:
  - .work/agent/issues/references/AUDIT-KG-001-investigation.md
  - incoming/kg/README.md
---

### Problem
During AUDIT-KG-001 investigation, it was discovered that the source README.md (2,808 bytes) was NOT migrated to the destination documentation folder.

**Documentation Status:**
| Aspect | Source | Destination | Status |
|--------|--------|-------------|--------|
| README.md | 2,808 bytes | NOT in docs/ | ⚠️ **NOT MIGRATED** |
| docs/ directory | None | docs/ exists but no kg/ | N/A |

**Impact:** Valuable documentation about the knowledge graph module is missing from the destination project.

### Affected Files
- Missing: `docs/knowledge_graph/README.md` (should contain migrated content from source)
- Source: `incoming/kg/README.md` (2,808 bytes)

### Importance
**MEDIUM:** Documentation is important for:
- User onboarding and understanding the module
- Preserving knowledge about features and usage
- Maintaining consistency with other migrated modules

While the code is fully functional and tested, missing documentation makes the module harder to use and understand.

### Proposed Solution
1. Review `incoming/kg/README.md` content
2. Create `docs/knowledge_graph/README.md` with migrated content
3. Update any references from "kgshred" to "knowledge_graph"
4. Update import paths in examples
5. Add to main project documentation index if applicable

### Acceptance Criteria
- [ ] `docs/knowledge_graph/README.md` created with source content
- [ ] All "kgshred" references updated to "knowledge_graph"
- [ ] Import paths updated for dot-work structure
- [ ] Documentation links to correct modules
- [ ] Content is accurate and helpful

### Notes
- This is a documentation gap, not a functional issue
- The code works perfectly - only docs are missing
- Source README is 2,808 bytes of valuable content
- See investigation: `.work/agent/issues/references/AUDIT-KG-001-investigation.md`

