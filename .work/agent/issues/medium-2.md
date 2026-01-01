# Medium Priority Issues (P2) — Part 2

---
id: "PERF-013@r3s4t5"
title: "Redundant Scope Set Computations"
description: "Search scope sets recomputed for every search operation"
created: 2024-12-27
section: "knowledge_graph"
tags: [performance, caching, search, scope, knowledge-graph]
type: refactor
priority: medium
status: completed
completed: 2025-01-01
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
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

**Decision (2025-01-01):** Session-level cache with TTL (60 seconds). Scope rarely changes within session. TTL handles edge case of topic/collection modifications. 60 seconds balances freshness vs performance.

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py` (lines 100-109)
- `src/dot_work/knowledge_graph/search_semantic.py` (lines 128-137)
- `src/dot_work/knowledge_graph/scope.py` (cache implementation)

### Importance
**MEDIUM**: Affects search performance:
- Repeated searches slow down unnecessarily
- Database overhead for each search
- Poor user experience in search-heavy workflows
- Easy optimization with caching

### Solution Implemented
Cache scope sets with 60-second TTL in `src/dot_work/knowledge_graph/scope.py`:

- Added `_SCOPE_CACHE` and `_SCOPE_CACHE_TIMESTAMPS` dictionaries
- Modified `build_scope_sets()` to check cache before building
- Added `use_cache` parameter (default: True)
- Added `clear_scope_cache()` and `get_cache_stats()` helper functions
- Cache key includes: project, topics (sorted), exclude_topics (sorted), include_shared
- TTL of 60 seconds balances freshness vs performance

### Acceptance Criteria
- [x] Scope sets cached with 60-second TTL
- [x] Cache key based on scope parameters (project, topics, exclude_topics, include_shared)
- [x] Unit tests for cache hit, miss, TTL expiry, and stats
- [x] TTL-based cache invalidation implemented
- [x] Documentation of cache behavior in docstring

### Validation Plan
1. Run 100 searches with identical scope
2. Verify performance improvement
3. Verify cache respects TTL (invalidates after 60 seconds)
4. All tests passing: 7/7 tests in test_scope_caching.py

---
**COMPLETED 2025-01-01**: Caching implemented with session-level cache and 60-second TTL. All tests passing.
---

### Dependencies
None.

### Clarifications Needed
None. Decision documented: 60-second TTL cache.

### Notes
Search scope rarely changes within a session. Caching should provide 3-5x speedup for repeated searches with identical scope parameters. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

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
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
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

**Decision (2025-01-01):** Auto-detect based on commit count (>50 commits = parallel). Small comparisons (<50) don't benefit from parallelization overhead. Large comparisons (>50) see significant speedup. Auto-detection provides good UX without requiring flags.

### Affected Files
- `src/dot_work/git/services/git_service.py` (lines 94-102)

### Importance
**MEDIUM**: Visible in large comparisons:
- CPU underutilized on multi-core systems
- Large comparisons take unnecessarily long
- Easy optimization with large impact

### Proposed Solution
Parallelize commit analysis with auto-detection:

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    commits = self._get_commits_between_refs(from_ref, to_ref)

    # Auto-detect: parallel only for >50 commits
    if len(commits) > 50:
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
    else:
        # Sequential for small comparisons
        analyzed_commits = []
        for commit in tqdm(commits, desc="Analyzing commits"):
            try:
                analysis = self.analyze_commit(commit)
                analyzed_commits.append(analysis)
            except Exception as e:
                self.logger.error(f"Failed to analyze commit {commit.hexsha}: {e}")
                continue

    # ... rest of comparison
```

### Acceptance Criteria
- [ ] Commit analysis parallelized for >50 commits
- [ ] Sequential processing for ≤50 commits
- [ ] CPU utilization increased to 80%+ on multi-core for large comparisons
- [ ] Performance test: 100 commits on 8-core < 30 seconds vs current 200+ seconds
- [ ] Error handling preserves all successful analyses
- [ ] Results sorted by original commit order

### Validation Plan
1. Test with 25 commits - verify sequential processing used
2. Test with 100 commits - verify parallel processing used
3. Measure CPU utilization on multi-core system
4. Verify results maintain commit order

### Dependencies
None.

### Clarifications Needed
None. Decision documented: auto-detect based on commit count (>50 = parallel).

### Notes
This optimization should provide 4-8x speedup on multi-core machines (linear speedup with core count for CPU-bound analysis). Memory usage increases with worker count but is manageable. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

------
id: "DOGFOOD-009@foa1hu"
title: "Add non-goals section to main documentation"
description: "dot-work documentation lacks explicit statement of what it does NOT do"
created: 2024-12-29
completed: 2025-01-01
section: "dogfooding"
tags: [documentation, clarity, dogfooding]
type: docs
priority: medium
status: completed
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
**COMPLETED 2025-01-01**: Non-goals section added to README.md with comprehensive "What to Use Instead" table. Commit: ce2a2e5
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
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
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

**Decision (2025-01-01):** Option C - Both: update tests AND add --json flag for future use. Tests should pass with current CLI (Option A). --json flag is useful for automation/scripting (Option B). Doing both provides immediate fix + future capability.

### Affected Files
- `tests/integration/db_issues/test_bulk_operations.py`
- `tests/integration/db_issues/test_team_collaboration.py`
- `tests/integration/db_issues/test_agent_workflows.py`
- `tests/integration/db_issues/test_dependency_model.py`
- `tests/integration/db_issues/test_advanced_filtering.py` (partially fixed)
- `src/dot_work/db_issues/cli.py`

### Importance
**MEDIUM**: Integration tests provide valuable coverage but are currently blocked:
- Tests can't run without fixes
- No integration test coverage for db-issues module
- Core bugs already fixed (SQLite URL format, session.commit()), but tests can't verify them

### Proposed Solution
**Step 1: Update tests to match current CLI**
1. Remove `--json` flag usage from existing tests
2. Parse wrapped output: `data = json.loads(result.stdout); issues = data["issues"]`
3. Use regex for issue ID parsing: `re.search(r"issue-[\w]+", result.stdout)`
4. Update all 4 affected test files

**Step 2: Add --json flag to CLI commands**
1. Add `--json` option to create, list, edit commands
2. Return issue objects directly in JSON format when flag is used
3. Add new tests for --json flag functionality
4. Document --json flag in help text

### Acceptance Criteria
- [ ] All 4 affected db_issues integration tests pass with current CLI
- [ ] Tests parse wrapped JSON output correctly
- [ ] Issue IDs extracted with regex instead of split()
- [ ] `--json` flag added to create/list/edit commands
- [ ] New tests verify --json flag functionality
- [ ] Documentation updated for --json flag

### Validation Plan
1. Run `./scripts/pytest-with-cgroup.sh 30 tests/integration/db_issues/ -v`
2. Verify all tests pass
3. Test --json flag manually with CLI commands
4. Verify JSON output is valid and useful

### Dependencies
None.

### Clarifications Needed
None. Decision documented: Option C - both update tests AND add --json flag.

### Notes
**Core bugs already fixed in commit a28f145:**
- SQLite URL format for absolute paths (config.py)
- Missing session.commit() in create command (cli.py)
- Integration test fixture database initialization (conftest.py)

**Already fixed:**
- `test_advanced_filtering.py::test_filter_by_date_range` - Updated with regex and correct JSON parsing

**Remaining work:** Update 4 more test files with same pattern, then add --json flag. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

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
---
id: "PERF-015@perf-review-2025"
title: "N+1 Query Problem in IssueRepository._model_to_entity"
description: "Labels, assignees, and references loaded individually for each issue"
created: 2025-01-01
section: "db_issues"
tags: [performance, database, n-plus-1, sqlite, optimization]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/db_issues/adapters/sqlite.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
In `sqlite.py:718-762`, `_model_to_entity()` performs 3 separate database queries for EVERY issue:

```python
def _model_to_entity(self, model: IssueModel) -> Issue:
    # Query 1: Load labels (N+1 problem)
    statement = select(IssueLabelModel).where(IssueLabelModel.issue_id == model.id)
    label_models = self.session.exec(statement).all()

    # Query 2: Load assignees (N+1 problem)
    assignee_statement = select(IssueAssigneeModel).where(
        IssueAssigneeModel.issue_id == model.id
    )
    assignee_models = self.session.exec(assignee_statement).all()

    # Query 3: Load references (N+1 problem)
    ref_statement = select(IssueReferenceModel).where(IssueReferenceModel.issue_id == model.id)
    ref_models = self.session.exec(ref_statement).all()
```

**Performance issue:**
- Called for EVERY issue returned from queries
- 100 issues = 300 additional database queries (3 per issue)
- Each query has round-trip overhead to SQLite
- List operations suffer from severe query amplification

**Impact:**
- `list_all()`, `list_by_status()`, `list_by_project()` all affected
- Loading 100 issues: 1 main query + 300 sub-queries = 301 total queries
- Noticeable latency on issue list operations
- Database connection overhead multiplied

**Decision (2025-01-01):** Option A - Use existing `_models_to_entities()` for single-entity loads. Correct pattern already exists in codebase (lines 764-844). Single-row loads can call batch method with single-item list. Minimal code change required. Proven pattern (already tested).

### Affected Files
- `src/dot_work/db_issues/adapters/sqlite.py` (lines 718-762)

### Importance
**MEDIUM**: Visible in list operations:
- Issue list pages load slowly
- API endpoints for listing issues have high latency
- Wasted database round-trips
- Easy optimization with large impact

**Note:** The codebase already has `_models_to_entities()` (lines 764-844) that implements batch loading correctly! The single-entity method should reuse the batch logic or call it directly.

### Proposed Solution
Use existing batch-loading pattern for single-entity loads:

```python
def _model_to_entity(self, model: IssueModel) -> Issue:
    """Convert single model to entity, reusing batch-loading logic."""
    # Delegate to batch method with single-item list
    entities = self._models_to_entities([model])
    return entities[0] if entities else None
```

### Acceptance Criteria
- [ ] `_model_to_entity()` delegates to `_models_to_entities()` with single-item list
- [ ] Loading 100 issues uses ≤10 queries total (vs 301)
- [ ] Performance test: 100 issues < 1 second (vs 3-5 seconds)
- [ ] No regression in functionality
- [ ] Existing batch-loading tests pass

### Validation Plan
1. Test loading 100 issues and measure query count
2. Verify performance improvement
3. Run all repository tests to ensure no regression

### Dependencies
None.

### Clarifications Needed
None. Decision documented: Option A - use existing _models_to_entities().

### Notes
Good news: The codebase already has the correct pattern in `_models_to_entities()` (lines 764-844). This batch method loads all labels/assignees/references for N issues in 3 queries total. The fix is to apply the same pattern to single-entity loads. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "PERF-016@perf-review-2025"
title: "Inefficient O(N²) String Concatenation in Search Snippets"
description: "Multiple string concatenations in search result processing"
created: 2025-01-01
section: "knowledge_graph"
tags: [performance, algorithm, string-operations, search]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
---

### Problem
In `search_fts.py:271-324` and `search_semantic.py`, snippet generation performs multiple string concatenations:

```python
def _generate_snippet(text: str, query: str, max_length: int = 150) -> str:
    # Multiple string concatenations
    if context_start > 0:
        snippet = "..." + snippet  # Creates new string object
    if context_end < len(text):
        snippet = snippet + "..."  # Creates another new string object

    # Highlight terms with more concatenations
    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(lambda m: f"<<{m.group(0)}>>", result)
```

**Performance issue:**
- String concatenation in Python creates new objects (immutable strings)
- Each "+" operation allocates a new string
- Pattern compilation inside loop
- Multiple passes over same text

**Impact:**
- For 100 search results × 5 terms = 500+ string allocations
- O(n × m) where n = text length, m = number of terms
- Unnecessary GC pressure
- Search latency increases with result count

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py` (lines 271-324)
- `src/dot_work/knowledge_graph/search_semantic.py` (uses similar patterns)

### Importance
**MEDIUM**: Visible in search operations:
- FTS search snippet generation is slow
- Multiple results compound the overhead
- Easy optimization with string builder pattern or list joins

### Proposed Solution
**Optimize snippet generation:**
```python
def _generate_snippet(text: str, query: str, max_length: int = 150) -> str:
    if not text:
        return ""

    # Use list for efficient building
    parts = []

    if context_start > 0:
        parts.append("...")
    parts.append(text[context_start:context_end])
    if context_end < len(text):
        parts.append("...")

    # Single join instead of multiple concatenations
    snippet = "".join(parts)

    # Pre-compile pattern once, reuse for all terms
    # Use single pass with alternation pattern
    if terms:
        pattern = re.compile("|".join(map(re.escape, terms)), re.IGNORECASE)
        snippet = pattern.sub(lambda m: f"<<{m.group(0)}>>", snippet)

    return snippet
```

### Acceptance Criteria
- [ ] Snippet generation uses list join instead of concatenation
- [ ] Regex pattern pre-compiled outside loop
- [ ] Single-pass term replacement with alternation pattern
- [ ] Performance test: 1000 snippets < 100ms (vs 500ms+)
- [ ] No functional change in output

---
---
id: "PERF-017@perf-review-2025"
title: "Missing Database Index on Common Query Patterns"
description: "No indexes on frequently queried columns in knowledge graph"
created: 2025-01-01
section: "knowledge_graph"
tags: [performance, database, indexing, sqlite]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
The knowledge graph database lacks indexes on frequently queried columns:

**Missing indexes:**
1. `nodes(doc_id)` - queried in `get_nodes_by_doc_id()` (line 823-841)
2. `nodes(kind)` - used in scope filtering
3. `embeddings(full_id, model)` - has UNIQUE constraint but no index on full_id alone
4. `collection_members(collection_id)` - queried in list operations
5. `topic_links(topic_id)` - queried in topic operations

**Performance issue:**
- Full table scans on common queries
- O(n) lookups instead of O(log n)
- Compound queries slower than necessary
- Scaling poorly with document/node count

**Impact:**
- Document loading slows linearly with node count
- Topic operations scan entire topic_links table
- Embedding lookups require full table scan
- Noticeable latency with 1000+ nodes

**Decision (2025-01-01):** Add migration script (version 5). Migration script is standard practice. Allows smooth upgrade for existing databases. Indexes are read-optimized (minimal write impact). Version 5 indicates next schema version.

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (schema creation, lines 255-303)

### Importance
**MEDIUM**: Visible at scale:
- Single document with 1000 nodes: full scan every time
- Topic operations degrade with graph size
- Embedding lookups don't scale
- Indexes are low-cost, high-benefit

**Note:** Some indexes exist (edges, nodes.primary keys), but coverage is incomplete.

### Proposed Solution
Add missing indexes in schema migration:

```python
# Add to migration (version 5)
conn.executescript("""
    -- Index on nodes.doc_id for document loading
    CREATE INDEX IF NOT EXISTS idx_nodes_doc_id ON nodes(doc_id);

    -- Index on nodes.kind for type filtering
    CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);

    -- Covering index for embedding lookups
    CREATE INDEX IF NOT EXISTS idx_embeddings_full_id_model
        ON embeddings(full_id, model);

    -- Index on collection members
    CREATE INDEX IF NOT EXISTS idx_collection_members_collection
        ON collection_members(collection_id);

    -- Index on topic links
    CREATE INDEX IF NOT EXISTS idx_topic_links_topic
        ON topic_links(topic_id);
""")
```

### Acceptance Criteria
- [ ] Schema migration created (version 5)
- [ ] Indexes added for doc_id, kind, full_id, collection_id, topic_id
- [ ] Migration applies indexes on startup if not present
- [ ] Performance test: 1000 nodes loaded < 100ms (vs 500ms+)
- [ ] No regression in write performance

### Validation Plan
1. Run migration on test database
2. Verify indexes created with `PRAGMA index_list`
3. Test performance with 1000 nodes
4. Verify write performance not degraded

### Dependencies
None.

### Clarifications Needed
None. Decision documented: migration script (version 5).

### Notes
Indexes are read-optimized. Write impact is minimal since indexes are created once and updated incrementally. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "PERF-018@perf-review-2025"
title: "Unbounded Memory Usage in get_all_embeddings_for_model"
description: "Function can load unlimited embeddings into memory"
created: 2025-01-01
section: "knowledge_graph"
tags: [performance, memory, database, safety]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/knowledge_graph/db.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
In `db.py:1098-1143`, `get_all_embeddings_for_model()` has dangerous default behavior:

```python
def get_all_embeddings_for_model(
    self, model: str, limit: int = 10000  # Default allows loading 10k vectors
) -> list[Embedding]:
    # Loads ALL embeddings if limit=0
    if limit > 0:
        cur = conn.execute("SELECT ... LIMIT ?", (model, limit))
    else:
        # WARNING: Loads unlimited embeddings
        logger.warning("Loading unlimited embeddings - may cause OOM")
        cur = conn.execute("SELECT ... WHERE model = ?", (model,))
```

**Performance issue:**
- Default limit of 10,000 embeddings
- Each embedding is 384-1536 floats × 4 bytes = 1.5-6 KB
- 10k embeddings = 15-60 MB of memory just for vectors
- No enforcement of memory limits
- Can cause OOM crashes on memory-constrained systems

**Impact:**
- Large knowledge bases (10k+ nodes) consume massive memory
- No safety limit by default
- OOM risk on systems with <4GB RAM
- Memory spikes during semantic search

**Decision (2025-01-01):** Option A - Change default limit from 10000 to 1000 + document streaming for larger datasets. 1000 embeddings = 1.5-6 MB (reasonable default). Streaming API already exists for large datasets. Breaking API change (deprecation) not justified. Documentation guides users to streaming for large use cases.

### Affected Files
- `src/dot_work/knowledge_graph/db.py` (lines 1098-1143)

### Importance
**MEDIUM**: Risk at scale:
- Production systems can crash from OOM
- No safety railings on memory usage
- Defaults should be safe, not dangerous
- Easy fix with lower default limit

**Good news:** The codebase has `stream_embeddings_for_model()` (lines 1175-1200) that implements bounded streaming correctly! The issue is that `get_all_embeddings_for_model()` is still used as the primary API.

### Proposed Solution
Change default limit and add documentation:

```python
def get_all_embeddings_for_model(
    self, model: str, limit: int = 1000  # Reduced from 10000
) -> list[Embedding]:
    """
    Get all embeddings for a model.

    Memory usage: ~1.5-6 KB per embedding (384-1536 floats × 4 bytes).
    Default limit of 1000 = ~1.5-6 MB memory.

    For datasets >1000 embeddings, use stream_embeddings_for_model()
    to avoid OOM errors.
    """
    if limit > 1000:
        logger.warning(f"Loading {limit} embeddings - may use {limit * 6 / 1024:.1f}+ MB")
    # ... rest of implementation
```

### Acceptance Criteria
- [ ] Default limit changed from 10000 to 1000
- [ ] Memory usage documented in docstring (~1.5-6 KB per embedding)
- [ ] Warning logged when loading >1000 embeddings
- [ ] Documentation recommends streaming for datasets >1000 embeddings
- [ ] Tests verify OOM protection with default limit

### Validation Plan
1. Verify default limit is 1000
2. Test with 1001 embeddings - verify warning logged
3. Verify stream_embeddings_for_model() still works
4. Document in docstring and README

### Dependencies
None.

### Clarifications Needed
None. Decision documented: Option A - lower default to 1000 + document streaming.

### Notes
Streaming API already exists (lines 1175-1200). Use it for large datasets. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

---
---
id: "PERF-019@perf-review-2025"
title: "Inefficient File Scanning Without Incremental Cache"
description: "Python scanner reads all files on every scan, no incremental mode"
created: 2025-01-01
section: "python_scan"
tags: [performance, caching, incremental, file-io]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/python/scan/scanner.py
  - src/dot_work/python/scan/cache.py
  - src/dot_work/python/scan/service.py
---

### Problem
The Python AST scanner has incremental scanning infrastructure but doesn't use it effectively:

**In `scanner.py:42-57`:**
```python
def scan(self, incremental: bool = False) -> CodeIndex:
    index = CodeIndex(root_path=self.root_path)

    for file_path in self._find_python_files():  # Scans ALL files
        file_entity = self._scan_file(file_path)  # Reads EVERY file
        index.add_file(file_entity)

    return index
```

**In `cache.py` (lines 1-139):**
- Cache exists but is never used in scan logic
- `is_cached()` method available but not called
- Cache has mtime/size/hash for change detection

**Performance issue:**
- Every scan reads all Python files
- File I/O is dominant cost (not AST parsing)
- Large codebases (1000+ files) scan slowly
- Incremental flag accepted but ignored
- Cache infrastructure exists but unused

**Impact:**
- Scanning 1000-file codebase: 5-10 seconds every time
- Unchanged files re-parsed unnecessarily
- No benefit from cache infrastructure
- Repeated scans waste CPU and I/O

### Affected Files
- `src/dot_work/python/scan/scanner.py` (lines 42-57)
- `src/dot_work/python/scan/cache.py` (not used)
- `src/dot_work/python/scan/service.py` (accepts incremental but doesn't implement)

### Importance
**MEDIUM**: Visible in large codebases:
- Development workflows re-scan constantly
- CI/CD runs full scan every time
- Cache infrastructure exists but unused
- Easy win with existing cache

### Proposed Solution
Implement incremental scanning:

```python
def scan(self, incremental: bool = False) -> CodeIndex:
    index = CodeIndex(root_path=self.root_path)

    # Load cache for incremental mode
    if incremental:
        self.cache.load()

    for file_path in self._find_python_files():
        # Check cache if incremental
        if incremental and self.cache.is_cached(file_path):
            continue  # Skip unchanged files

        file_entity = self._scan_file(file_path)
        index.add_file(file_entity)

        # Update cache after scanning
        if incremental:
            self.cache.update(file_path)

    # Save cache after scan
    if incremental:
        self.cache.save()

    return index
```

### Acceptance Criteria
- [ ] Incremental mode implemented using existing cache
- [ ] Unchanged files skipped in incremental scans
- [ ] Cache saved after each scan
- [ ] Performance test: 1000 files, 10 changed = 10x faster (1s vs 10s)
- [ ] No functional change in scan results

---
---
id: "PERF-020@perf-review-2025"
title: "No Query Result Caching for Repeated Searches"
description: "Search results not cached despite high repetition probability"
created: 2025-01-01
section: "knowledge_graph"
tags: [performance, caching, search, database]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/knowledge_graph/search_fts.py
  - src/dot_work/knowledge_graph/search_semantic.py
  - .work/agent/issues/references/medium-issue-clarifications-2025-01-01.md
---

### Problem
Search operations in knowledge graph have no caching:

**In `search_fts.py:48-131`:**
```python
def search(db: Database, query: str, k: int = 20, ...) -> list[SearchResult]:
    # Performs FTS search every time
    results = db.fts_search(safe_query, limit=fetch_limit)

    # For each result, fetches document text again
    for node, score in results:
        text = _get_node_text(db, node)  # Additional database query per result
```

**In `search_semantic.py:77-244`:**
- Embedding lookup every search (no cache)
- Vector similarity computed every time
- Node lookups for each result

**Performance issue:**
- Same query repeated = redundant work
- Document text fetched per result (N+1)
- No memoization of embeddings
- Common queries (e.g., "test", "config") repeated constantly

**Impact:**
- Repeated searches have same latency
- No benefit from search repetition
- Database queries repeated unnecessarily
- User experience suffers from repeated searches

**Decision (2025-01-01):** Defer until actual usage patterns are measured. Most searches are unique in typical workflows. Cache invalidation complexity may outweigh benefits. No evidence of high repetition in current usage. LOW priority indicates this is not urgent.

### Affected Files
- `src/dot_work/knowledge_graph/search_fts.py`
- `src/dot_work/knowledge_graph/search_semantic.py`

### Importance
**LOW**: Nice-to-have optimization:
- Most searches are unique
- Cache invalidation complexity
- Memory overhead for cache
- Benefit depends on usage patterns

**Recommendation:** Revisit if cache hit ratio would be >30%.

### Proposed Solution
**Option A: LRU cache for search results**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search(db: Database, query: str, k: int = 20, ...):
```

**Option B: Application-level cache**
- Cache results in memory with TTL
- Manual invalidation on data changes

**DEFERRED:** Measure usage patterns first. If high repetition found, implement caching.

### Acceptance Criteria
- [ ] Issue marked as deferred pending usage analysis
- [ ] Note added: "Revisit if cache hit ratio would be >30%"
- [ ] No implementation at this time

### Validation Plan
1. Add logging to track search query repetition
2. Analyze logs after 1 week of usage
3. If >30% repetition rate, revisit this issue

### Dependencies
None.

### Clarifications Needed
None. Decision documented: defer until usage patterns measured.

### Notes
Issue marked LOW priority. Most searches are unique, so caching may not provide significant benefit. Cache invalidation complexity (data changes, schema updates) must be weighed against actual performance gains. See `.work/agent/issues/references/medium-issue-clarifications-2025-01-01.md` for full analysis.

**Revisit trigger:** Cache hit ratio >30% OR user complaints about search latency.
    # Cache based on query string
    # Invalidate on document changes
```

**Option B: Application-level cache**
- Cache in memory with TTL
- Invalidate on database writes
- Manual cache clearing

**Option C: Database query cache**
- Cache FTS results in database
- Reuse across sessions
- Persistent cache

### Acceptance Criteria
- [ ] Search results cached with LRU or TTL policy
- [ ] Cache invalidation on document changes
- [ ] Cache hit ratio >30% for typical workflows
- [ ] Memory usage bounded (LRU size limit)
- [ ] Performance test: cached searches <10ms (vs 100ms+)

---
