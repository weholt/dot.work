# Medium Priority Issues (P2) — Part 2

---
id: "PERF-012@q2r3s4"
title: "No Memoization for Git Branch/Tag Lookups"
description: "Branch and tag lookups performed repeatedly for same commits"
created: 2024-12-27
section: "git"
tags: [performance, memoization, caching, git, branch-tag]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:615-639`, branch and tag lookups have no caching:

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    # No caching - performs full traversal every time
    for branch in self.repo.branches:
        if commit.hexsha in [c.hexsha for c in self.repo.iter_commits(branch.name)]:
            return branch.name
    return "unknown"

def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    # No caching - iterates all tags every time
    tags = []
    for tag in self.repo.tags:
        if tag.commit.hexsha == commit.hexsha:
            tags.append(tag.name)
    return tags
```

**Performance issue:**
- Same commit queried multiple times during analysis
- Branch lookup: Full branch traversal per commit
- Tag lookup: Full tag iteration per commit
- Called for EVERY commit in comparison (100-1000+ times)
- Redundant work across analyses

**Impact:**
- Git comparison becomes progressively slower
- Redundant work for same commits across analyses
- Analysis time scales quadratically with commit count
- 100 commits × full traversal each = massive waste

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 615-639)

### Importance
**MEDIUM**: Visible in multi-commit analyses:
- Repeated full traversals for same commits
- Wasted CPU cycles and I/O
- Makes repeated analyses slower
- Easy optimization with large impact

### Proposed Solution
Memoize branch/tag lookups once per comparison:

```python
def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    # Clear and build caches once per comparison
    self._commit_to_branch = {}
    self._commit_to_tags = {}

    commits = self._get_commits_between_refs(from_ref, to_ref)

    # Pre-build commit → branch mapping
    for branch in self.repo.branches:
        for commit in self.repo.iter_commits(branch.name):
            self._commit_to_branch[commit.hexsha] = branch.name

    # Pre-build commit → tags mapping
    for tag in self.repo.tags:
        commit_hash = tag.commit.hexsha
        if commit_hash not in self._commit_to_tags:
            self._commit_to_tags[commit_hash] = []
        self._commit_to_tags[commit_hash].append(tag.name)

    # Now O(1) lookups in analyze_commit()
    for commit in commits:
        analysis = self.analyze_commit(commit)  # Uses cached maps

def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    return self._commit_to_branch.get(commit.hexsha, "unknown")

def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
    return self._commit_to_tags.get(commit.hexsha, [])
```

### Acceptance Criteria
- [ ] Commit-to-branch mapping built once per comparison
- [ ] Commit-to-tags mapping built once per comparison
- [ ] O(1) lookups in `_get_commit_branch()` and `_get_commit_tags()`
- [ ] Performance test: 1000 commits < 5 seconds vs current 30+ seconds
- [ ] Caches cleared between comparisons

### Notes
This optimization should provide 10-100x speedup for multi-commit analyses. Memory overhead is minimal (dict with commit hash keys).

---
id: "PERF-013@r3s4t5"
title: "Redundant Scope Set Computations"
description: "Search scope sets recomputed for every search operation"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, caching, search, scope, knowledge-graph]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
---

### Problem
In `search_fts.py:100-109` and `search_semantic.py:128-137`, scope sets computed for EVERY search:

```python
# search_fts.py - Called for EVERY search
if scope:
    scope_members, scope_topics, exclude_topic_ids, shared_topic_id = _build_scope_sets(
        db, scope
    )

# _build_scope_sets() performs multiple queries:
def _build_scope_sets(db, scope):
    # Query 1: Get collection members
    # Query 2: Get topic links
    # Query 3: Build exclusion sets
    # Query 4: Get shared topic
```

**Performance issue:**
- Scope sets computed for EVERY search operation
- Scope doesn't change between searches in same session
- Multiple database queries for set building
- Called in both FTS and semantic search (high frequency)
- Repeated work for identical scope parameters

**Impact:**
- Repeated searches incur same overhead
- 100 searches = 400 redundant database queries
- Noticeable latency on search-heavy workflows
- Wasted database round-trips

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py` (lines 100-109)
- `src/dot_work/knowledge_graph/search_semantic.py` (lines 128-137)

### Importance
**MEDIUM**: Affects search performance:
- Repeated searches slow down unnecessarily
- Database overhead for each search
- Poor user experience in search-heavy workflows
- Easy optimization with caching

### Proposed Solution
Cache scope sets with TTL or session-level caching:

```python
from functools import lru_cache
import hashlib
import time

@lru_cache(maxsize=32)
def _build_scope_sets_cached(db_id: int, scope_hash: str, time_bucket: int):
    """Cached version of _build_scope_sets."""
    # This still needs to build real sets - just cached by parameters
    # Need to pass actual db reference somehow
    pass

# Better: Scope object-level caching
class SearchSession:
    def __init__(self, db):
        self.db = db
        self._scope_cache = {}

    def search(self, query, scope):
        if scope is None:
            return self._search_unscoped(query)

        scope_key = (scope.project, tuple(scope.topics), tuple(scope.exclude_topics))
        if scope_key not in self._scope_cache:
            self._scope_cache[scope_key] = _build_scope_sets(self.db, scope)

        # Use cached sets
        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = self._scope_cache[scope_key]

        # ... rest of search
```

### Acceptance Criteria
- [ ] Scope sets cached across searches
- [ ] Cache invalidation when data changes
- [ ] Performance test: 100 searches with same scope < 2 seconds vs current 5+ seconds
- [ ] TTL or manual invalidation implemented

### Notes
Search scope rarely changes within a session. Caching should provide 3-5x speedup for repeated searches with identical scope parameters.

---
id: "PERF-014@s4t5u6"
title: "Sequential Commit Processing"
description: "Git commits analyzed sequentially without parallelization"
created: 2024-12-27
section: "git"
tags: [performance, parallelism, git, commit-analysis, cpu]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/git_service.py
---

### Problem
In `git_service.py:94-102`, commits analyzed sequentially:

```python
# compare_refs() - Process commits sequentially
analyzed_commits = []
for commit in tqdm(commits, desc="Analyzing commits"):
    try:
        analysis = self.analyze_commit(commit)  # Blocking per commit
        analyzed_commits.append(analysis)
    except Exception as e:
        self.logger.error(f"Failed to analyze commit {commit.hexsha}: {e}")
        continue
```

**Performance issue:**
- Commits analyzed sequentially (one at a time)
- Each commit requires file diff parsing, complexity calculation
- CPU-bound operations not parallelized
- Analysis time scales linearly with commit count
- With LLM summarization: each commit = 1-2 seconds

**Impact:**
- Large comparisons (100+ commits) take minutes
- CPU underutilized (single core at 100%, others idle)
- Analysis time scales linearly with commit count
- 8-core machine using only 12.5% of capacity

### Proposed Solution
Parallelize commit analysis with ProcessPoolExecutor:

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    commits = self._get_commits_between_refs(from_ref, to_ref)

    # Parallelize CPU-bound commit analysis
    analyzed_commits = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(_analyze_commit_impl, commit.hexsha, self.config.repo_path)
            for commit in commits
        }

        for future in tqdm(as_completed(futures), total=len(commits), desc="Analyzing"):
            try:
                analysis = future.result()
                analyzed_commits.append(analysis)
            except Exception as e:
                self.logger.error(f"Failed to analyze commit: {e}")

    # Sort by original commit order
    commit_order = {c.hexsha: i for i, c in enumerate(commits)}
    analyzed_commits.sort(key=lambda a: commit_order.get(a.commit_hash, float('inf')))

    # ... rest of comparison
```

### Acceptance Criteria
- [ ] Commit analysis parallelized with ProcessPoolExecutor
- [ ] CPU utilization increased to 80%+ on multi-core
- [ ] Performance test: 100 commits on 8-core < 30 seconds vs current 200+ seconds
- [ ] Error handling preserves all successful analyses
- [ ] Results sorted by original commit order

### Notes
This optimization should provide 4-8x speedup on multi-core machines (linear speedup with core count for CPU-bound analysis). Memory usage increases with worker count but is manageable.

------
id: "DOGFOOD-009@foa1hu"
title: "Add non-goals section to main documentation"
description: "dot-work documentation lacks explicit statement of what it does NOT do"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, clarity, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - README.md
  - docs/dogfood/baseline.md
---

### Problem
Documentation has no section on non-goals. Users may have incorrect expectations about what dot-work can do.

**Missing:**
- What problems are out of scope?
- What won't dot-work help with?
- What tools should be used instead for those problems?

### Affected Files
- `README.md`
- `docs/dogfood/baseline.md`

### Importance
**MEDIUM**: Clear non-goals prevent user disappointment:
- Sets proper expectations
- Avoids feature requests outside scope
- Helps users choose right tool

### Proposed Solution
Add non-goals section to README documenting that dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation:
```markdown
## Non-Goals

dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation. It does NOT:

- Replace full project management tools (Jira, Linear, etc.)
- Provide autonomous agents without human direction
- Host prompts or provide cloud services
- Manage dependencies or build systems
- Replace git workflow tools
- Provide CI/CD integration

It is a local development tool for AI-assisted coding workflows with human oversight.
```

**User decision:** dot-work is a human-directed AI agent framework for issue management and autonomous agent implementation

### Acceptance Criteria
- [ ] Non-goals section added to README
- [ ] Defines dot-work as human-directed AI agent framework
- [ ] Clear scope boundaries defined
- [ ] Alternative tools suggested where appropriate

### Validation Plan
1. Add "Non-Goals" section to README.md
2. Explicitly state "human-directed AI agent framework"
3. List out-of-scope features
4. Verify with user that definition is accurate

### Dependencies
None.

### Clarifications Needed
None. Definition provided by user.

### Notes
This is gap #3 in gaps-and-questions.md (Medium Priority).

---

---
id: "DOGFOOD-010@foa1hu"
title: "Document issue editing workflow (AI-only)"
description: "Clarify that AI tools should edit issue files, not humans"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, workflow, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - .work/agent/issues/
  - .github/prompts/
---

### Problem
How do users/edit-AI tools edit issues? User feedback: "The tools and AI should edit the issue files, not humans"

**Unclear:**
- Are there CLI commands to add/edit/move issues?
- Should humans ever edit `.work/agent/issues/*.md` directly?
- How to move issues between priority files?
- How to update issue status without AI?

### Affected Files
- Documentation files
- `.work/agent/issues/` (readme or guide)

### Importance
**MEDIUM**: Users need to understand proper workflow:
- Prevents manual file editing mistakes
- Ensures issues are managed correctly
- Maintains issue file format consistency

### Proposed Solution
Add documentation section:
```markdown
## Editing Issues

Issues are edited by AI agents via prompts:

- `/new-issue` – Create issue with generated ID
- `/do-work` – Move issue through workflow states
- `/focus on <topic>` – Create issues in shortlist.md

Direct file editing is NOT recommended. The AI manages issue state.
```

### Acceptance Criteria
- [ ] Issue editing workflow documented
- [ ] AI-only policy clearly stated
- [ ] Prompt commands listed for issue management
- [ ] Warning about manual editing

### Notes
This is gap #4 in gaps-and-questions.md (Medium Priority). User explicitly provided feedback on this.

---

---
id: "DOGFOOD-011@foa1hu"
title: "Document prompt trigger format by environment"
description: "How to use installed prompts varies by AI environment - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - README.md
  - src/dot_work/prompts/
---

### Problem
How to use prompts after install? Are all prompts slash commands? How does Claude Code use prompts (no slash commands)?

**Unclear:**
- Are all prompts slash commands?
- How does Claude Code use prompts (no slash commands)?
- What about Cursor, Windsurf, Aider, etc.?

### Affected Files
- `README.md`
- Documentation files

### Importance
**MEDIUM**: Users can't use installed prompts without knowing how:
- Prompts installed but unusable
- Environment-specific differences confusing
- Poor first-time user experience

### Proposed Solution
Add documentation section:
```markdown
## Using Installed Prompts

| Environment | How to Use |
|-------------|------------|
| GitHub Copilot | Type `/prompt-name` in chat |
| Claude Code | Automatically reads CLAUDE.md |
| Cursor | Select from `@` menu |
| Windsurf | Automatically reads .windsurf/rules/ |
| Aider | Automatically reads CONVENTIONS.md |
| Continue.dev | Type `/prompt-name` |
| Amazon Q | Automatically reads .amazonq/rules.md |
| Zed AI | Select from prompts menu |
| OpenCode | Automatically reads AGENTS.md |
| Generic | Manually reference prompt files |
```

### Acceptance Criteria
- [ ] Prompt usage table added
- [ ] All 10+ environments documented
- [ ] Clear examples for each environment
- [ ] Slash command vs automatic read distinction clear

### Notes
This is gap #9 in gaps-and-questions.md (Medium Priority).

---

---
id: "DOGFOOD-012@foa1hu"
title: "Document all undocumented CLI commands"
description: "Some commands in --help have no documentation: canonical, zip, container, python, git, harness"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, cli, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/dogfood/tooling-reference.md
  - src/dot_work/cli.py
---

### Problem
Some commands in `--help` have no documentation. From tooling-reference.md:

**Commands needing docs:**
| Command | Description | Priority |
|---------|-------------|----------|
| `canonical` | Validate/install canonical prompts | HIGH |
| `zip` | Zip folders respecting .gitignore | LOW |
| `container` | Container operations | MEDIUM |
| `python` | Python utilities | MEDIUM |
| `git` | Git analysis tools | MEDIUM |
| `harness` | Claude Agent SDK harness | LOW |

---

id: "DOGFOOD-013@foa1hu"
title: "Add canonical prompt validation documentation"
description: "How to validate .canon.md without installing - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, validation, dogfooding]
type: docs
priority: medium
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/prompt-authoring.md
  - src/dot_work/prompts/canonical.py
---

### Problem
How to validate .canon.md without installing? What validation is performed?

**Unclear:**
- Is there a `validate` command for canonical prompts?
- What validation is performed?
- How to test before installing?

### Affected Files
- `docs/prompt-authoring.md`
- Tooling reference

### Importance
**MEDIUM**: Prompt authors need to validate before distributing:
- Invalid prompts cause installation failures
- No way to test prompts locally
- Poor prompt authoring experience

### Proposed Solution
Add documentation section:
```markdown
## Validating Canonical Prompts

# Validate without installing
dot-work canonical validate my-prompt.canon.md

# Or check during install
dot-work prompts install my-prompt.canon.md --target copilot --dry-run
```

### Acceptance Criteria
- [ ] Validation command documented (if exists)
- [ ] Validation rules documented
- [ ] Dry-run mode documented
- [ ] Error examples with fixes

### Notes
This is gap #8 in gaps-and-questions.md (Medium Priority).

---
id: "TEST-040@7a277f"
title: "db-issues integration tests need CLI interface updates"
description: "Integration tests use non-existent --json flag and wrong output format"
created: 2025-12-29
section: "db_issues"
tags: [tests, integration, cli-compatibility]
type: test
priority: medium
status: proposed
references:
  - tests/integration/db_issues/test_bulk_operations.py
  - tests/integration/db_issues/test_team_collaboration.py
  - tests/integration/db_issues/test_agent_workflows.py
  - tests/integration/db_issues/test_dependency_model.py
  - tests/integration/db_issues/test_advanced_filtering.py
  - src/dot_work/db_issues/cli.py
---

### Problem
Integration tests in `tests/integration/db_issues/` were migrated from another project and don't match the current CLI interface:

1. **Non-existent `--json` flag**: Tests use `--json` on commands that don't support it (e.g., `create --json`)
2. **Wrong output format**: Tests expect `json.loads(result.stdout)` to return arrays directly, but the CLI returns wrapped objects like `{"command": "list", "issues": [...], "total": N}`
3. **Issue ID parsing**: Tests use `split()[0]` to parse issue IDs, but Rich-formatted output breaks this

**Affected tests:**
- `test_bulk_operations.py` - Uses `--json` flag on create command (doesn't exist)
- `test_team_collaboration.py` - Uses `--json` flag, expects direct array output
- `test_agent_workflows.py` - Uses `--json` flag, expects direct array output
- `test_dependency_model.py` - Uses `--json` flag, expects direct array output
- `test_advanced_filtering.py` - PARTIALLY FIXED: One test updated, others still need fixes

### Affected Files
- `tests/integration/db_issues/test_bulk_operations.py`
- `tests/integration/db_issues/test_team_collaboration.py`
- `tests/integration/db_issues/test_agent_workflows.py`
- `tests/integration/db_issues/test_dependency_model.py`
- `tests/integration/db_issues/test_advanced_filtering.py` (partially fixed)
- `src/dot_work/db_issues/cli.py` (may need --json flag added)

### Importance
**MEDIUM**: Integration tests provide valuable coverage but are currently blocked:
- Tests can't run without fixes
- No integration test coverage for db-issues module
- Core bugs already fixed (SQLite URL format, session.commit()), but tests can't verify them

### Proposed Solution
**Option A: Update tests to match current CLI**
1. Remove `--json` flag usage (doesn't exist)
2. Parse wrapped output: `data = json.loads(result.stdout); issues = data["issues"]`
3. Use regex for issue ID parsing: `re.search(r"issue-[\w]+", result.stdout)`
4. Update all affected test files

**Option B: Add --json flag to CLI commands**
1. Add `--json` option to create, edit, and other commands
2. Return issue objects directly in JSON format
3. Update tests to use new flag

**Recommendation**: Option A (update tests) is faster and matches current CLI design.

### Acceptance Criteria
- [ ] All db_issues integration tests pass
- [ ] Tests parse CLI output correctly
- [ ] Issue IDs extracted with regex instead of split()
- [ ] JSON output wrapper handled correctly
- [ ] No reliance on non-existent --json flag

### Notes
**Core bugs already fixed in commit a28f145:**
- SQLite URL format for absolute paths (config.py)
- Missing session.commit() in create command (cli.py)
- Integration test fixture database initialization (conftest.py)

**Already fixed:**
- `test_advanced_filtering.py::test_filter_by_date_range` - Updated with regex and correct JSON parsing

**Remaining work:** Update 4 more test files with same pattern.

---
id: "CR-085@e3f1g2"
title: "Missing Type Annotation for FileAnalyzer config Parameter"
description: "Parameter named 'config' but type is AnalysisConfig without annotation"
created: 2024-12-31
section: "git"
tags: [type-hints, naming, clarity]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/git/services/file_analyzer.py
---

### Problem
In `file_analyzer.py:24-25`, `FileAnalyzer.__init__` parameter is named `config` but the actual type is `AnalysisConfig`. No type annotation exists, making it unclear what configuration is expected.

### Affected Files
- `src/dot_work/git/services/file_analyzer.py` (lines 24-25)

### Importance
**MEDIUM**: Missing type annotations reduce IDE support and make refactoring harder:
- No autocomplete for config properties
- mypy cannot catch type mismatches
- Unclear what configuration object is required

### Proposed Solution
Add proper type annotation:
```python
from dot_work.git.models import AnalysisConfig

class FileAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
```

### Acceptance Criteria
- [ ] Type annotation added to `__init__` parameter
- [ ] Import of `AnalysisConfig` added
- [ ] mypy passes without new errors
- [ ] Documentation reflects typed parameter

---
