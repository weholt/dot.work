# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

---
id: "CR-058@a3b5c7"
title: "AnalysisProgress.estimated_remaining_seconds is hardcoded fiction"
description: "Progress tracking uses len(commits) * 2 without actual timing"
created: 2024-12-27
section: "git"
tags: [ux, accuracy]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/git/models.py
---

### Problem
`AnalysisProgress.estimated_remaining_seconds` (line 222-230) is hardcoded to `len(commits) * 2` in git_service.py:90 without any actual timing. This progress tracking is essentially fiction.

### Affected Files
- `src/dot_work/git/models.py`
- `src/dot_work/git/services/git_service.py`

### Importance
Users see misleading time estimates.

### Proposed Solution
Either make progress track real timing or remove the fictional estimate.

### Acceptance Criteria
- [ ] Accurate timing or removed

---

---
id: "CR-059@b4c6d8"
title: "Magic numbers in complexity.py weights lack documentation"
description: "No explanation for why deletions cost 0.015 vs additions at 0.01"
created: 2024-12-27
section: "git"
tags: [documentation, clarity]
type: docs
priority: low
status: proposed
references:
  - src/dot_work/git/services/complexity.py
---

### Problem
In `complexity.py:13-67`, the massive nested dict `self.weights` has magic numbers for complexity calculation. No documentation explains why deletions cost `0.015` per line vs additions at `0.01`, or why "breaking" is worth `25.0` points.

### Affected Files
- `src/dot_work/git/services/complexity.py`

### Importance
Opaque scoring makes it impossible to understand or calibrate.

### Proposed Solution
Add comments explaining the rationale for specific weights.

### Acceptance Criteria
- [ ] Weights documented
- [ ] Rationale explained

---

---
id: "CR-060@c5d7e9"
title: "Inconsistent naming: hash vs commit_hash in git models"
description: "CommitInfo.hash vs ChangeAnalysis.commit_hash"
created: 2024-12-27
section: "git"
tags: [naming, consistency]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/git/models.py
---

### Problem
`CommitInfo` contains `hash` and `short_hash`, while `ChangeAnalysis` contains `commit_hash`. The inconsistent naming creates confusion.

### Affected Files
- `src/dot_work/git/models.py`

### Importance
Consistent naming reduces cognitive load.

### Proposed Solution
Standardize on either `hash` or `commit_hash` throughout.

### Acceptance Criteria
- [ ] Consistent naming

---

---
id: "CR-061@d6e8f0"
title: "ConventionalCommitParser scope regex doesn't support common formats"
description: "Scope pattern doesn't allow api/v2 or @angular/core"
created: 2024-12-27
section: "version"
tags: [compatibility, parsing]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/version/commit_parser.py
---

### Problem
Regex `(?P<scope>[\w-]+)` in `commit_parser.py:28` only allows word characters and hyphens in scope. Some projects use scopes like `api/v2` or `@angular/core` which would fail to parse.

### Affected Files
- `src/dot_work/version/commit_parser.py`

### Importance
Limited compatibility with some project conventions.

### Proposed Solution
Expand regex to support more scope formats.

### Acceptance Criteria
- [ ] Common scope formats supported
- [ ] No regression on existing formats

---

---
id: "CR-062@e7f9a1"
title: "short_hash uses 12 chars instead of conventional 7"
description: "Non-standard short hash length may confuse users"
created: 2024-12-27
section: "version"
tags: [convention, clarity]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/version/commit_parser.py
---

### Problem
`short_hash` is set to `commit.hexsha[:12]` (line 79) which is 12 characters. The conventional "short hash" in git is 7 characters.

### Affected Files
- `src/dot_work/version/commit_parser.py`

### Importance
Non-standard may confuse users comparing to git output.

### Proposed Solution
Use 7 characters to match git convention, or document the choice.

### Acceptance Criteria
- [ ] Conventional or documented

---

---
id: "CR-063@f8a0b2"
title: "Console singleton in CLI modules makes testing difficult"
description: "Module-level console = Console() prevents output capture"
created: 2024-12-27
section: "cli"
tags: [testing, dependency-injection]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/version/cli.py
  - src/dot_work/db_issues/cli.py
---

### Problem
Multiple CLI modules create module-level `console = Console()` singletons. This makes testing output difficult without monkeypatching.

### Affected Files
- `src/dot_work/cli.py`
- `src/dot_work/version/cli.py`
- `src/dot_work/db_issues/cli.py`

### Importance
Testing CLI output requires workarounds.

### Proposed Solution
Consider dependency injection for console.

### Acceptance Criteria
- [ ] Testable CLI output

---

---
id: "CR-064@a9b1c3"
title: "time-based review ID has 1-second collision risk"
description: "Rapid successive calls could produce identical IDs"
created: 2024-12-27
section: "review"
tags: [reliability, uniqueness]
type: bug
priority: low
status: proposed
references:
  - src/dot_work/review/storage.py
---

### Problem
`new_review_id()` (lines 30-36) uses `%Y%m%d-%H%M%S` format which has 1-second granularity. Rapid successive calls within the same second would produce identical IDs.

### Affected Files
- `src/dot_work/review/storage.py`

### Importance
Unlikely in practice but possible in automated scenarios.

### Proposed Solution
Add milliseconds or a random suffix.

### Acceptance Criteria
- [ ] Unique IDs even within same second

---

---
id: "CR-065@b0c2d4"
title: "Full page reload on comment submission loses scroll position"
description: "UX could be improved with partial updates"
created: 2024-12-27
section: "review"
tags: [ux, enhancement]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/review/static/app.js
---

### Problem
`window.location.reload()` (line 43) after submitting a comment causes full page refresh, losing scroll position and potentially unsaved work.

### Affected Files
- `src/dot_work/review/static/app.js`

### Importance
UX improvement for review workflow.

### Proposed Solution
Dynamically update the DOM or use partial updates.

### Acceptance Criteria
- [ ] Scroll position preserved
- [ ] Better UX on comment submission

---

---
id: "CR-066@c1d3e5"
title: "__all__ exports module names instead of symbols in overview/__init__.py"
description: "Unusual export pattern doesn't match typical usage"
created: 2024-12-27
section: "overview"
tags: [api, clarity]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/overview/__init__.py
---

### Problem
`__all__` (lines 3-6) exports `"pipeline"` and `"cli"` as strings, but these are module names, not the actual functions/classes users would import. Consumers likely want `from dot_work.overview import analyze_project` directly.

### Affected Files
- `src/dot_work/overview/__init__.py`

### Importance
API doesn't match typical usage patterns.

### Proposed Solution
Export the commonly used functions directly.

### Acceptance Criteria
- [ ] Convenient import API

---

---
id: "CR-067@d2e4f6"
title: "Collector class in overview/code_parser.py has too many responsibilities"
description: "200 lines mixing AST visiting, docstrings, metrics, classification"
created: 2024-12-27
section: "overview"
tags: [refactor, srp]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
`_Collector` class (lines 105-303) is 200 lines mixing AST visiting, docstring extraction, metric lookup, interface flag detection, and model classification.

### Affected Files
- `src/dot_work/overview/code_parser.py`

### Importance
Violates single responsibility, hard to test in isolation.

### Proposed Solution
Extract helper classes or functions for distinct concerns.

### Acceptance Criteria
- [ ] Responsibilities separated
- [ ] Improved testability

---

---
id: "CR-068@e3f5a7"
title: "datetime.now() without timezone in version/manager.py"
description: "Timezone-naive datetime could cause version collisions"
created: 2024-12-27
section: "version"
tags: [reliability, datetime]
type: bug
priority: low
status: proposed
references:
  - src/dot_work/version/manager.py
---

### Problem
`datetime.now()` (line 71) is called without timezone awareness. In CI or distributed systems, this could cause version collisions or ordering issues.

### Affected Files
- `src/dot_work/version/manager.py`

### Importance
Reliability in distributed environments.

### Proposed Solution
Use UTC or make timezone explicit.

### Acceptance Criteria
- [ ] Timezone-aware or documented assumption

---

---
id: "CR-069@f4a6b8"
title: "generate_entry creates dataclass only to destructure it"
description: "Unnecessary overhead in changelog.py"
created: 2024-12-27
section: "version"
tags: [performance, simplification]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/version/changelog.py
---

### Problem
`generate_entry()` (lines 109-162) creates a `ChangelogEntry` dataclass only to immediately destructure it for template rendering. The dataclass creation is unnecessary overhead.

### Affected Files
- `src/dot_work/version/changelog.py`

### Importance
Minor performance improvement opportunity.

### Proposed Solution
Pass values directly to render without dataclass.

### Acceptance Criteria
- [ ] Simplified code path

---

---
id: "CR-070@a5b7c9"
title: "use_llm branch in generate_summary does same thing as else"
description: "Parameter is effectively dead code"
created: 2024-12-27
section: "version"
tags: [dead-code, cleanup]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/version/changelog.py
---

### Problem
The `use_llm` branch in `generate_summary()` (lines 193-197) does the same thing as the else branch (both call `_generate_conventional_summary`). The parameter is effectively dead code.

### Affected Files
- `src/dot_work/version/changelog.py`

### Importance
Dead code increases maintenance burden.

### Proposed Solution
Remove dead parameter or implement LLM summary.

### Acceptance Criteria
- [ ] Dead code removed or feature implemented

---

---
id: "CR-071@b6c8d0"
title: "AuditLog callback on_entry is never used"
description: "Unused callback mechanism in issue_service.py"
created: 2024-12-27
section: "db_issues"
tags: [dead-code, cleanup]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/db_issues/services/issue_service.py
---

### Problem
`AuditLog` class (lines 36-92) has an `on_entry` callback mechanism that appears unused in production code.

### Affected Files
- `src/dot_work/db_issues/services/issue_service.py`

### Importance
Unused complexity increases maintenance burden.

### Proposed Solution
Remove unused callback or document intended use.

### Acceptance Criteria
- [ ] Dead code removed or utilized

---

---
id: "CR-072@c7d9e1"
title: "DuplicateService.clock injected but never used"
description: "Uses datetime.now() directly instead of injected clock"
created: 2024-12-27
section: "db_issues"
tags: [dead-code, testability]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/db_issues/services/duplicate_service.py
---

### Problem
`DuplicateService.clock` (line 220-221) is injected but never used. The service uses `datetime.now(UTC).timestamp()` directly, breaking the dependency injection pattern.

### Affected Files
- `src/dot_work/db_issues/services/duplicate_service.py`

### Importance
Breaks testability - can't mock time in tests.

### Proposed Solution
Use the injected clock or remove the parameter.

### Acceptance Criteria
- [ ] Consistent use of clock injection

---
id: "PERF-015@t5u6v7"
title: "Potential Race Condition in Cache File Access"
description: "Concurrent cache writes may corrupt files without atomic operations"
created: 2024-12-27
section: "git"
tags: [performance, concurrency, race-condition, cache, file-atomic]
type: bug
priority: low
status: proposed
references:
  - src/dot_work/git/services/cache.py
---

### Problem
In `cache.py:143-164`, cache file writes have no atomicity or locking:

```python
def set(self, key: str, data: Any, ttl_hours: int = 24) -> bool:
    try:
        cache_path = self._get_cache_path(key)
        serialized_data = self._serialize_data(data)

        # No file locking - potential race condition
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
```

**Performance issue:**
- Multiple processes/threads can write same cache file simultaneously
- No atomic write or file locking
- Corrupted cache files from concurrent writes
- Cache invalidation race conditions
- Last writer wins, potentially overwriting valid cache

**Impact:**
- Cache corruption under parallel operations
- Lost cache writes
- Increased cache miss rate
- Re-computation of expensive operations
- Requires manual cache cleanup

### Affected Files
- `src/dot_work/git/services/cache.py` (lines 143-164)

### Importance
**LOW**: Only affects parallel scenarios (rare in typical use):
- Typical single-user development: unlikely to hit
- CI/CD or multi-user environments: may see corruption
- Affects reliability but not performance directly
- Low priority due to rare occurrence

### Proposed Solution
Use atomic write with temporary file:

```python
import tempfile
import os

def set(self, key: str, data: Any, ttl_hours: int = 24) -> bool:
    try:
        cache_path = self._get_cache_path(key)
        serialized_data = self._serialize_data(data)

        # Write to temp file first
        temp_path = cache_path.with_suffix('.tmp')
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        # Atomic rename (atomic on POSIX, near-atomic on Windows)
        os.replace(temp_path, cache_path)

        self.logger.debug(f"Cached data for key: {key}")
        return True
    except Exception as e:
        self.logger.error(f"Failed to cache data for key {key}: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink(silent_fail=True)
        return False
```

Or use file locking:

```python
import fcntl

def set(self, key: str, data: Any, ttl_hours: int = 24) -> bool:
    try:
        cache_path = self._get_cache_path(key)
        serialized_data = self._serialize_data(data)

        with open(cache_path, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock
            try:
                json.dump(cache_data, f, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        self.logger.debug(f"Cached data for key: {key}")
        return True
    except Exception as e:
        self.logger.error(f"Failed to cache data for key {key}: {e}")
        return False
```

### Acceptance Criteria
- [ ] Atomic write with temporary file and rename
- [ ] Or file locking with proper release
- [ ] Temporary files cleaned up on failure
- [ ] Works on Linux, macOS, Windows
- [ ] Tests for concurrent write scenarios

### Notes
Atomic write with temporary file is preferred over file locking for:
- Simpler implementation
- Better cross-platform compatibility
- No deadlock risks
- POSIX guarantees atomicity of rename()

File locking should be used if atomic rename is not sufficient (e.g., Windows < Vista).

---

---

---

id: "DOGFOOD-014@foa1hu"
title: "Document version format conventions"
description: "dot-work version uses date-based format - why and how documented?"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, versioning, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/version/
---

### Problem
`dot-work version` uses date-based format. Why date-based instead of semantic?

**Unclear:**
- What is the version format exactly?
- Why date-based instead of semantic (SemVer)?
- How does version ordering work?

### Affected Files
- Documentation files
- `src/dot_work/version/` docs

### Importance
**LOW**: Nice to know but doesn't block usage:
- Version format is discoverable by use
- SemVer not strictly required for this tool
- Users can see format in action

### Proposed Solution
Add documentation section:
```markdown
## Version Format

dot-work uses date-based versioning: `YYYY.MM.PATCH`

Example: `2025.10.001`
- `2025` – Year
- `10` – Month (October)
- `001` – Patch/sequence

This format aligns with CalVer (Calendar Versioning).
```

### Acceptance Criteria
- [ ] Version format documented
- [ ] Rationale for date-based explained
- [ ] Examples provided
- [ ] Ordering rules clear

### Validation Plan
1. Add version format section to README or docs
2. Document CalVer format: `YYYY.MM.PATCH`
3. Explain rationale (date-based vs SemVer)
4. Provide ordering rules

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #11 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-015@foa1hu"
title: "Add integration testing guide for prompts"
description: "How to verify prompts work across AI tools - requires human validation"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, testing, prompts, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/dogfood/baseline.md
---

### Problem
How to verify prompts work across different AI tools?

**Unclear:**
- How to test if prompts are installed correctly?
- How to test if AI tools use prompts correctly?
- What to check after installation?

User feedback: "Requires human validation"

### Affected Files
- Documentation files
- Testing guides

### Importance
**LOW**: Testing requires manual verification:
- No automated way to test AI prompts
- Each AI tool has different interface
- Human validation inherently required

### Proposed Solution
Add testing checklist:
```markdown
## Testing Installation

# Verify files exist
ls -la .github/prompts/  # Copilot
ls -la CLAUDE.md         # Claude

# Test with AI tool
# In GitHub Copilot: Type /agent-prompts-reference
# Should see list of available prompts
```

### Acceptance Criteria
- [ ] Installation verification checklist
- [ ] File existence checks for each environment
- [ ] Manual testing steps
- [ ] Expected results documented

### Validation Plan
1. Add "Testing Installation" section to docs
2. Provide checklist for file existence verification
3. Document manual testing steps for each AI tool
4. List expected results for verification

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #12 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-016@foa1hu"
title: "Document changelog format and customization"
description: "dot-work version freeze generates changelog - format and customization undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, versioning, changelog, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/version/
---

### Problem
`dot-work version freeze` generates changelog. What is the format? Where is it stored? How to customize?

**Unclear:**
- What is the changelog format?
- Where is it stored?
- How to customize the format?

### Affected Files
- Documentation files
- `src/dot_work/version/changelog.py`

### Importance
**LOW**: Default behavior works for most users:
- Format follows common conventions
- Storage location is predictable
- Customization is edge case

### Proposed Solution
Add documentation section:
```markdown
## Changelog Format

The changelog is generated in Keep a Changelog format:

# Changelog

## [2025.10.001] - 2025-10-15
### Added
- New feature X

### Fixed
- Bug Y
```

### Acceptance Criteria
- [ ] Changelog format documented
- [ ] Storage location documented
- [ ] Keep a Changelog reference provided
- [ ] Customization options (if any) documented

### Validation Plan
1. Add "Changelog Format" section to docs
2. Document Keep a Changelog format
3. Specify storage location (CHANGELOG.md in project root)
4. Reference external Keep a Changelog guide

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #13 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-017@foa1hu"
title: "Document environment detection signals and logic"
description: "dot-work detect identifies AI tool - signals and logic undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, cli, detection, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/installer.py
---

### Problem
`dot-work detect` identifies AI tool. What files/signals are checked? What if multiple detected?

**Unclear:**
- What files/signals are checked?
- What if multiple environments detected?
- What if none detected?

### Affected Files
- Documentation files
- Tooling reference

### Importance
**LOW**: Detection usually works correctly:
- Interactive fallback handles ambiguity
- Signals are tool-specific conventions
- Users can override with --env flag

### Proposed Solution
Add documentation section:
```markdown
## Detection Logic

dot-work detect checks for:

| Environment | Detection Signal |
|-------------|------------------|
| copilot | `.github/prompts/` or `.github/copilot-instructions.md` |
| claude | `CLAUDE.md` or `.claude/` |
| cursor | `.cursor/rules/` or `.cursorrules` |
| windsurf | `.windsurf/rules/` or `.windsurfrules` |

If multiple detected, uses first match.
If none detected, prompts user to select.
```

### Acceptance Criteria
- [ ] Detection signals table added
- [ ] Multiple detection behavior documented
- [ ] No detection fallback documented
- [ ] Override options explained

### Validation Plan
1. Add "Detection Logic" section to docs
2. Create table of environment detection signals
3. Document multiple detection behavior (first match)
4. Document no-detection fallback (user prompt)
5. Document --env override option

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #14 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-018@foa1hu"
title: "Document prompt uninstallation process"
description: "How to remove installed prompts - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, uninstall, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/installer.py
---

### Problem
How to remove installed prompts? Is there an uninstall command?

**Unclear:**
- Is there an uninstall command?
- How to remove specific prompts?
- How to remove all prompts?

### Affected Files
- Documentation files
- Tooling reference

### Importance
**LOW**: Manual removal works for most cases:
- Users can delete prompt files directly
- Uninstall is not common operation
- Clean install usually sufficient

### Proposed Solution
Add documentation section:
```markdown
## Uninstalling Prompts

# Remove specific environment
rm .github/prompts/*.prompt.md  # Copilot
rm CLAUDE.md                    # Claude

# Or use uninstall command (if exists)
dot-work uninstall --env copilot
dot-work uninstall --all
```

### Acceptance Criteria
- [ ] Manual removal documented
- [ ] Uninstall command documented (if exists)
- [ ] All environments covered
- [ ] Warning about data loss

### Validation Plan
1. Add "Uninstalling Prompts" section to docs
2. Document manual file removal for each environment
3. Check if uninstall command exists and document it
4. Add warning about data loss (custom prompts, local changes)

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #15 in gaps-and-questions.md (Low Priority).

---
