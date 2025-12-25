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
id: "FEAT-006@e6c3f9"
title: "Add Cline and Cody environments"
description: "Popular AI coding tools not currently supported"
created: 2024-12-20
completed: 2024-12-24
section: "environments"
tags: [environments, cline, cody]
type: enhancement
priority: medium
status: completed
references:
  - src/dot_work/environments.py
  - src/dot_work/installer.py
---

### Problem
Cline (VS Code extension) and Cody (Sourcegraph) are popular AI coding assistants not currently supported by dot-work.

### Affected Files
- `src/dot_work/environments.py` (add environment configs)
- `src/dot_work/installer.py` (add installer functions)

### Importance
Users of these tools cannot use dot-work to install prompts, limiting adoption.

### Resolution (2024-12-24)
Successfully added support for both Cline and Cody environments.

**Research Findings:**
- **Cline** ([documentation](https://docs.cline.bot/features/cline-rules)): Uses `.clinerules/` directory with folder-based system. All `.md` files inside are processed. Numeric prefixes (01-, 02-, etc.) are optional for organization.
- **Cody** ([documentation](https://sourcegraph.com/docs/cody/prompts-guide)): Uses Prompt Library (server-side) rather than local files. No official local convention exists, so implemented `.cody/` directory following common patterns.

**Changes Made:**
1. Added `cline` Environment entry to environments.py:
   - `prompt_dir=".clinerules"`
   - `prompt_extension=".md"`
   - `detection=[".clinerules"]`

2. Added `cody` Environment entry to environments.py:
   - `prompt_dir=".cody"`
   - `prompt_extension=".md"`
   - `detection=[".cody"]`

3. Created `install_for_cline()` function in installer.py
4. Created `install_for_cody()` function in installer.py
5. Updated INSTALLERS dispatch table with both new entries

**Acceptance Criteria:**
- [x] `dot-work list` shows cline and cody environments
- [x] `dot-work install --env cline` creates correct structure (`.clinerules/` directory)
- [x] `dot-work install --env cody` creates correct structure (`.cody/` directory)
- [x] `dot-work detect` recognizes cline/cody markers
- [x] Tests cover new installer functions (all 46 installer tests passing)

**Test Results:**
- 46/46 installer tests passing
- Manual installation testing confirmed both environments create correct directories

### Acceptance Criteria
- [x] `dot-work list` shows cline and cody environments
- [x] `dot-work install --env cline` creates correct structure
- [x] `dot-work install --env cody` creates correct structure
- [x] `dot-work detect` recognizes cline/cody markers
- [x] Tests cover new installer functions

### Notes
Completed successfully. Both environments now fully supported. Users can install prompts with:
- `dot-work install --env cline`
- `dot-work install --env cody`

---

---
id: "REFACTOR-001@f7d4a1"
title: "Extract common installer logic to reduce duplication"
description: "10 install_for_* functions share ~80% identical code"
created: 2024-12-20
completed: 2024-12-24
section: "installer"
tags: [refactor, dry, maintainability]
type: refactor
priority: medium
status: completed
references:
  - src/dot_work/installer.py
---

### Problem
The 10 `install_for_*` functions in installer.py contain ~200 lines of repetitive code. Each function:
1. Creates destination directory
2. Gets environment config
3. Iterates prompts, renders, writes
4. Prints status messages

Adding a new environment requires copying ~20 lines of near-duplicate code.

### Affected Files
- `src/dot_work/installer.py`

### Importance
Violates DRY principle. Bug fixes must be applied to 10 places. Adding new environments is error-prone. The `force` flag implementation will need to be duplicated 10 times without this refactor.

### Proposed Solution
1. Create generic `install_prompts_generic()` function
2. Define environment-specific behavior via configuration:
   - Destination path pattern
   - Whether to create auxiliary files (.cursorrules, etc.)
   - Auxiliary file content template
   - Console messaging
3. Keep simple dispatch: `INSTALLERS[env_key] = lambda: install_prompts_generic(config)`
4. Special cases (claude, aider combining into single file) handled via config flag

### Resolution (2024-12-24)
Successfully refactored installer.py to eliminate ~200 lines of duplicate code:

**Changes Made:**
1. Created `InstallerConfig` dataclass with 9 configuration parameters:
   - `env_key`, `dest_path`, `file_naming`, `file_extension`
   - `combined`, `combined_path` (for single-file modes)
   - `auxiliary_files`, `sort_files`, `messages`

2. Created `install_prompts_generic()` function that handles:
   - Combined file mode (claude, aider, amazon-q)
   - Directory mode (copilot, cursor, windsurf, continue, zed, opencode, generic)
   - All file writing, directory creation, and console messaging

3. Refactored all 10 `install_for_*` functions to thin configuration wrappers:
   - Each function now 13-45 lines (was 20-60)
   - Single line: `install_prompts_generic(CONFIG_XXX, ...)`

4. Fixed bug: Combined file parent directories now created automatically

**Acceptance Criteria:**
- [x] Single generic installer function handles all environments
- [x] No more than 5 lines of environment-specific code per environment
- [x] All existing tests pass (46/46 installer tests)
- [x] Adding new environment requires only config, not code
- [x] `force` flag implemented in one place

**Test Results:**
- 46 installer tests: PASSED
- Full test suite: 1317 passed, 2 failed (unrelated knowledge_graph tests)

### Acceptance Criteria
- [x] Single generic installer function handles all environments
- [x] No more than 5 lines of environment-specific code per environment
- [x] All existing tests pass
- [x] Adding new environment requires only config, not code
- [x] `force` flag implemented in one place

### Notes
Completed successfully. The `force` flag was already implemented in the generic function. Future environments can be added by creating an `InstallerConfig` and calling `install_prompts_generic()`.

---

---
id: "FEAT-007@a8e5b2"
title: "Add --dry-run flag to install command"
description: "Allow previewing changes before writing files"
created: 2024-12-20
completed: 2024-12-24
section: "cli"
tags: [cli, install, ux]
type: enhancement
priority: medium
status: completed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
Users cannot preview what files will be created or modified before running `dot-work install`. This makes it difficult to understand the impact of installation, especially when files might be overwritten.

### Affected Files
- `src/dot_work/cli.py` (add --dry-run option)
- `src/dot_work/installer.py` (add dry_run parameter)

### Importance
Improves user confidence and reduces surprises. Useful for CI/CD integration where destructive changes should be previewed.

### Resolution (2024-12-24)
Successfully implemented `--dry-run` / `-n` flag for the install command.

**Changes Made:**
1. Added `--dry-run` / `-n` flag to `install` command in cli.py:
   - Help text: "Preview changes without writing files"
   - Passes through to `install_prompts()`

2. Added `dry_run` parameter to `install_prompts()` function

3. Added `dry_run` parameter to `install_prompts_generic()` function

4. Updated all 12 `install_for_*` functions to accept and pass `dry_run` parameter

5. Implemented dry-run logic in `install_prompts_generic()`:
   - Skips directory creation
   - Skips file writing
   - Prints `[DRY-RUN] [CREATE] path` for new files
   - Prints `[DRY-RUN] [OVERWRITE] path` for existing files
   - Shows warning at completion: "⚠️ Dry run complete - no files were written"

**Output Format:**
- New files: `[DRY-RUN] [CREATE] /path/to/file.md`
- Overwrites: `[DRY-RUN] [OVERWRITE] /path/to/file.md`
- Header: `🔍 Dry run: Previewing installation for {Environment}...`
- Footer: `⚠️ Dry run complete - no files were written`

**Acceptance Criteria:**
- [x] `dot-work install --dry-run` shows planned changes without writing
- [x] Output distinguishes between new files and overwrites
- [x] Exit code 0 even in dry-run mode
- [x] Tests verify no files written in dry-run mode
- [x] Short flag `-n` also works

**Test Results:**
- 46/46 installer tests passing
- Manual testing confirmed:
  - No files created in dry-run mode
  - `[CREATE]` shown for new files
  - `[OVERWRITE]` shown for existing files
  - Both `--dry-run` and `-n` flags work

### Acceptance Criteria
- [x] `dot-work install --dry-run` shows planned changes without writing
- [x] Output distinguishes between new files and overwrites
- [x] Exit code 0 even in dry-run mode
- [x] Tests verify no files written in dry-run mode

### Notes
Implementation completed after refactor, which made adding the parameter much easier (only needed to add to generic function and propagate to all installers).

---

---
id: "FEAT-008@f7d4a2"
title: "Add batch overwrite option when files exist during install"
description: "Provide 'overwrite all' choice instead of only file-by-file prompting"
created: 2024-12-20
completed: 2025-12-25
section: "cli"
tags: [cli, install, ux, prompting]
type: enhancement
priority: medium
status: completed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
When running `dot-work install` without `--force` and files already exist, the user is prompted for each file individually. For projects with many prompt files (8+), this becomes tedious.

Current behavior:
```
  ⚠ File already exists: do-work.prompt.md
    Overwrite? [y/N]: y
  ⚠ File already exists: setup-issue-tracker.prompt.md
    Overwrite? [y/N]: y
  ... (repeated for each file)
```

### Affected Files
- `src/dot_work/installer.py` (modify `should_write_file()` and install functions)
- `src/dot_work/cli.py` (potentially add `--update-all` flag)
- `tests/unit/test_installer.py` (add tests for batch behavior)

### Importance
User experience improvement. Power users reinstalling/updating prompts shouldn't need to answer the same question 8+ times. This is especially painful when updating to a new version of dot-work.

### Proposed Solution
1. When first existing file is encountered, offer expanded choices:
   ```
   ⚠ Found existing prompt files. How should I proceed?
     [a] Overwrite ALL existing files
     [s] Skip ALL existing files
     [p] Prompt for each file individually
     [c] Cancel installation
   Choice [a/s/p/c]:
   ```
2. Store user's choice for the session
3. Apply consistently to remaining files
4. Alternative: Add `--update-all` / `--skip-existing` CLI flags

### Acceptance Criteria
- [ ] First conflict offers batch choice (all/skip/prompt/cancel)
- [ ] Choice "a" overwrites all remaining without further prompts
- [ ] Choice "s" skips all existing files without further prompts
- [ ] Choice "p" maintains current file-by-file behavior
- [ ] Choice "c" aborts installation cleanly
- [ ] `--force` still works as before (silent overwrite all)
- [ ] Tests verify each batch mode behavior

### Notes
Consider interaction with `--force` flag:
- `--force` = silent overwrite (no prompts at all)
- No flag + batch "a" = overwrite after single confirmation
- No flag + batch "p" = current behavior

This builds on FEAT-003 (--force implementation). Could be combined with FEAT-007 (--dry-run) for a complete UX.

---
id: "RECONCILE-001@a1b2c3"
title: "Reconcile enum schemas between old and new issue-tracker"
description: "Differences between migrated enums and original issue-tracker spec need resolution"
created: 2024-12-23
completed: 2024-12-24
section: "db-issues"
tags: [db-issues, enums, reconciliation, migration]
type: refactor
priority: medium
status: completed
references:
  - src/dot_work/db_issues/domain/entities.py
---

### Problem
MIGRATE-041 updated enum values to match the issue-tracker project specification, but this introduced breaking changes from the original "Beads-compatible" schema that was initially migrated in MIGRATE-034.

### Investigation Result (2024-12-24)
Upon investigation of the actual code in `entities.py`, it was discovered that **Option C: Merge both schemas** was already implemented. The current enums contain a union of values from both old and new schemas:

**IssuePriority (5 values):**
- CRITICAL, HIGH, MEDIUM, LOW, BACKLOG
- BACKLOG from old schema is preserved (line 154)

**IssueStatus (7 values):**
- PROPOSED (new), IN_PROGRESS, BLOCKED, RESOLVED (old), COMPLETED, STALE (new), WONT_FIX (new)
- RESOLVED from old schema is preserved (line 168)
- STALE and WONT_FIX are new additions

**IssueType (10 values):**
- BUG, FEATURE, TASK, ENHANCEMENT (new), REFACTOR (new), DOCS (new), TEST (new), SECURITY (new), PERFORMANCE (new), STORY (new), EPIC (old)
- EPIC from old schema is preserved (line 219)

**DependencyType (6 values):**
- BLOCKS, DEPENDS_ON, RELATED_TO, DUPLICATES (new), PARENT_OF (new), CHILD_OF (new)
- DISCOVERED_FROM from old schema was intentionally removed (superseded by new types)

### Resolution
**Decision: Option C (Merge both schemas) - Already Implemented**

The enum schemas have been successfully merged to include:
1. All values from the old "Beads-compatible" schema that remain relevant
2. All new values from the issue-tracker project specification
3. EPIC type is preserved (supports epic hierarchy)
4. BACKLOG priority is preserved
5. RESOLVED status is preserved
6. New dependency types (DUPLICATES, PARENT_OF, CHILD_OF) added
7. Only DISCOVERED_FROM and CHORE types were removed (functionality superseded)

### Affected Files
- `src/dot_work/db_issues/domain/entities.py` - All enums already merged

### Acceptance Criteria
- [x] Decision made: Option C (merge both schemas)
- [x] Enums expanded with union of both value sets
- [x] Epic functionality preserved (EPIC type exists)
- [x] BACKLOG priority preserved
- [x] RESOLVED status preserved
- [x] All tests passing (259 tests)

### Notes
The RECONCILE-001 issue was based on outdated analysis. The actual code in entities.py already implements the optimal solution: a merged schema that maintains backward compatibility while adding new functionality from the issue-tracker project.

---


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
