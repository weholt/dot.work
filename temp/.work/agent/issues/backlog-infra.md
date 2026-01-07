# Backlog: Infrastructure & Refactoring

Infrastructure improvements and prompt system refactoring.

Issues: INFRA-001, REFACTOR-001, REFACTOR-002, REFACTOR-003, REFACTOR-004
Split from: backlog.md
Created: 2026-01-01

---
id: "INFRA-001@g3h9i5"
title: "Issue file size management and automatic splitting"
description: "Implement token limit enforcement and automatic splitting for issue files to maintain them below 25,000 tokens"
created: 2025-12-30
section: "infrastructure/issue-tracker"
tags: [infrastructure, issue-tracker, token-management, file-splitting, data-integrity]
type: maintenance
priority: high
status: proposed
references:
  - .work/agent/issues/backlog.md
  - .work/agent/issues/references/issue-file-format.md
---

### Problem
Issue tracker files (`backlog.md`, `doing.md`, `done.md`, etc.) grow indefinitely as issues are added. Problems:

1. **Token overflow**: Files exceed 25,000 tokens, causing context truncation
2. **Performance**: Reading large files slows down AI agents
3. **Memory**: Large files consume more memory and tokens
4. **Maintenance**: Hard to navigate and manage large files
5. **Risk**: Data loss if manual splitting fails

Current state: `backlog.md` has 2245+ lines and growing.

### Affected Files
- NEW: `src/dot_work/db_issues/token_counter.py` (token estimation utility)
- NEW: `src/dot_work/db_issues/issue_splitter.py` (file splitting tool)
- NEW: `src/dot_work/db_issues/issue_indexer.py` (index maintenance)
- MODIFIED: `src/dot_work/db_issues/parser.py` (handle split files)
- MODIFIED: `src/dot_work/db_issues/__init__.py` (add split commands)
- `src/dot_work/cli.py` (add issue file management commands)

### Importance
**HIGH**: File size management ensures:
- AI agents can read complete issue files without truncation
- Consistent performance regardless of file size
- Data integrity during splits (no lost issues)
- Automatic maintenance (no manual intervention)
- Scalability to hundreds/thousands of issues
- Reduced token usage and costs

### Proposed Solution

**Phase 1: Token Estimation (1 day)**
Create token counter utility:

1. Token estimation strategies:
   - Word-based: ~0.75 tokens per word (rough estimate)
   - Character-based: ~4 characters per token
   - Exact tokenization: Use tiktoken or similar library

2. `token_counter.py`:
   ```python
   def estimate_tokens(text: str, method: str = "word") -> int:
     """Estimate token count for text."""
     if method == "word":
       return len(text.split()) * 0.75
     elif method == "char":
       return len(text) / 4
     elif method == "exact":
       import tiktoken
       enc = tiktoken.encoding_for_model("gpt-4")
       return len(enc.encode(text))

   def count_file_tokens(path: Path) -> int:
     """Count tokens in issue file."""
     content = path.read_text()
     return estimate_tokens(content)

   def count_issue_tokens(issue_yaml: str) -> int:
     """Count tokens in single issue block."""
     return estimate_tokens(issue_yaml)
   ```

3. CLI command:
   ```bash
   # Check file token count
   dot-work db-issues tokens backlog.md

   # Check all issue files
   dot-work db-issues tokens --all

   # Show detailed breakdown
   dot-work db-issues tokens backlog.md --verbose
   ```

**Phase 2: Issue Parser Enhancement (2 days)**
Enhance parser to handle split files:

1. Multi-file parsing:
   ```python
   def parse_issues_dir(dir_path: Path) -> List[Issue]:
     """Parse all issue files in directory."""
     issues = []
     for file_path in dir_path.glob("*.md"):
       issues.extend(parse_issues_file(file_path))
     return sorted(issues, key=lambda i: i.created, reverse=True)
   ```

2. Issue file discovery:
   - Support patterns: `backlog-001.md`, `backlog-002.md`, etc.
   - Support dates: `backlog-2025-12-30.md`
   - Support alphabetical: `backlog-a.md`, `backlog-b.md`

3. Index file:
   ```yaml
   # .work/agent/issues/index.yaml
   files:
     - path: "backlog-001.md"
       issues: 50
       tokens: 23456
       date_range: ["2025-12-26", "2025-12-28"]
     - path: "backlog-002.md"
       issues: 30
       tokens: 18900
       date_range: ["2025-12-29", "2025-12-30"]
   total_issues: 80
   total_tokens: 42356
   ```

**Phase 3: Automatic Splitting Strategy (2-3 days)**
Create splitting tool:

1. Split triggers:
   - Token limit exceeded (default: 25,000 tokens)
   - Issue count threshold (default: 50 issues)
   - Manual split command
   - Time-based (e.g., monthly splits)

2. Split strategies:
   - **By issue count**: N issues per file
   - **By date**: All issues within time range
   - **By section**: Group by section/tags
   - **Balanced**: Equal token distribution

3. `issue_splitter.py`:
   ```python
   def split_file(
     source_path: Path,
     output_dir: Path,
     max_tokens: int = 25000,
     strategy: str = "balanced"
   ) -> List[Path]:
     """Split issue file into multiple files."""
     issues = parse_issues_file(source_path)

     if strategy == "balanced":
       return split_balanced(issues, output_dir, max_tokens)
     elif strategy == "date":
       return split_by_date(issues, output_dir, max_tokens)
     elif strategy == "count":
       return split_by_count(issues, output_dir, max_tokens)
     elif strategy == "section":
       return split_by_section(issues, output_dir, max_tokens)

   def split_balanced(issues, output_dir, max_tokens):
     """Split into files with balanced token counts."""
     files = []
     current_issues = []
     current_tokens = 0
     file_num = 1

     for issue in issues:
       issue_tokens = estimate_tokens(issue.content)

       if current_tokens + issue_tokens > max_tokens and current_issues:
         # Flush current file
         out_path = output_dir / f"{source_path.stem}-{file_num:03d}.md"
         write_issues_file(out_path, current_issues)
         files.append(out_path)
         current_issues = []
         current_tokens = 0
         file_num += 1

       current_issues.append(issue)
       current_tokens += issue_tokens

     # Write remaining issues
     if current_issues:
       out_path = output_dir / f"{source_path.stem}-{file_num:03d}.md"
       write_issues_file(out_path, current_issues)
       files.append(out_path)

     return files
   ```

4. Validation before split:
   - Verify all issues parsed successfully
   - Count total issues
   - Estimate tokens
   - Preview split plan
   - Require confirmation (unless `--force`)

**Phase 4: Split CLI Commands (2 days)**
Add splitting commands:

```bash
# Check if file needs splitting
dot-work db-issues check-split backlog.md

# Show split preview
dot-work db-issues split backlog.md --preview

# Perform split
dot-work db-issues split backlog.md \
  --max-tokens 25000 \
  --strategy balanced \
  --output-dir .work/agent/issues/

# Split with confirmation
dot-work db-issues split backlog.md --interactive

# Force split (no confirmation)
dot-work db-issues split backlog.md --force

# Split all files
dot-work db-issues split --all --max-tokens 25000

# Merge split files (reverse operation)
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog-merged.md
```

**Phase 5: Index Maintenance (1-2 days)**
Create index management:

1. Auto-update index:
   - Update on split/merge operations
   - Update on issue creation/closure
   - Validate index consistency

2. Index commands:
   ```bash
   # Build/update index
   dot-work db-issues index build

   # Validate index
   dot-work db-issues index validate

   # Show index
   dot-work db-issues index show

   # Rebuild from scratch
   dot-work db-issues index rebuild
   ```

3. Index format:
   ```yaml
   version: "1.0"
   updated: "2025-12-30T12:00:00Z"
   files:
     backlog:
       - path: "backlog-001.md"
         issues: 50
         tokens: 24500
         date_range: ["2025-12-26", "2025-12-28"]
         sections: ["skills", "docker", "context"]
       - path: "backlog-002.md"
         issues: 30
         tokens: 18900
         date_range: ["2025-12-29", "2025-12-30"]
         sections: ["file-transfer", "url-injection"]
     doing:
       - path: "doing.md"
         issues: 5
         tokens: 3200
     done:
       - path: "done.md"
         issues: 20
         tokens: 15000
   totals:
     issues: 105
     tokens: 61600
   ```

**Phase 6: Safe Splitting with Rollback (1-2 days)**
Ensure data integrity:

1. Atomic split operation:
   - Create temporary directory for split files
   - Write split files to temp location
   - Validate split files contain all issues
   - Rename original to backup
   - Move split files to final location
   - Delete backup on success

2. Rollback on failure:
   - If validation fails, restore backup
   - Log failure reason
   - Keep backup for manual recovery

3. Validation checks:
   - Issue count: total after split == total before split
   - Issue IDs: all unique, no duplicates
   - Issue content: YAML frontmatter preserved
   - Token counts: within limits
   - File format: valid markdown

**Phase 7: Automatic Splitting (1-2 days)**
Automatic split on threshold:

1. Auto-split triggers:
   - On issue creation if file exceeds limit
   - Scheduled check (e.g., daily via cron)
   - CLI command: `dot-work db-issues check --auto-split`

2. Auto-split workflow:
   ```python
   def auto_split_if_needed(file_path: Path, max_tokens: int):
     """Check and auto-split if file exceeds limit."""
     tokens = count_file_tokens(file_path)

     if tokens > max_tokens:
       log.info(f"File {file_path} exceeds {max_tokens} tokens, splitting...")
       split_file(file_path, max_tokens=max_tokens, strategy="balanced")
       return True
     return False
   ```

3. Configuration:
   ```yaml
   # .work/agent/issues/config.yaml
   splitting:
     max_tokens: 25000
     max_issues: 50
     strategy: balanced
     auto_split: true
     backup_enabled: true
     backup_retention: 30d
   ```

**Phase 8: Merge and Consolidation (1 day)**
Reverse operation to merge split files:

```bash
# Merge split files back
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog-merged.md \
  --sort date  # or name, priority

# Merge specific files
dot-work db-issues merge \
  --files backlog-001.md,backlog-002.md \
  --output backlog.md

# Merge and sort by priority
dot-work db-issues merge \
  --pattern "backlog-*.md" \
  --output backlog.md \
  --sort priority
```

Merge features:
- Deduplicate issues (by ID)
- Preserve original order or re-sort
- Update index
- Validate merged file

**Phase 9: Documentation (1 day)**
Create documentation:

1. Splitting guide:
   - When to split (token limits, issue count)
   - How to split (preview, interactive, force)
   - Split strategies (balanced, date, count, section)
   - Troubleshooting common issues

2. Reference docs:
   - File naming conventions
   - Index format reference
   - Configuration options
   - Best practices

3. Examples in README:
   ```bash
   # Check file size
   dot-work db-issues tokens backlog.md
   # Output: File: backlog.md, Issues: 80, Tokens: 42356

   # Preview split
   dot-work db-issues split backlog.md --preview
   # Output:
   # Will split into 2 files:
   #   backlog-001.md: 50 issues, 23456 tokens
   #   backlog-002.md: 30 issues, 18900 tokens

   # Perform split
   dot-work db-issues split backlog.md --strategy balanced
   # Output: Created backlog-001.md, backlog-002.md

   # Auto-split all files
   dot-work db-issues split --all --auto-split

   # Merge files back
   dot-work db-issues merge --pattern "backlog-*.md" --output backlog.md
   ```

**Phase 10: Testing (2 days)**
Comprehensive testing:

1. Unit tests:
   - Token estimation accuracy
   - Issue parsing from split files
   - Split strategies (balanced, date, count, section)
   - Index building and validation

2. Integration tests:
   - End-to-end split operation
   - Rollback on validation failure
   - Merge operation
   - Auto-split triggers
   - Index updates

3. Edge case tests:
   - Single issue larger than token limit
   - Empty files
   - Invalid YAML frontmatter
   - Duplicate issue IDs
   - Concurrent splits (file locking)

### Acceptance Criteria
- [ ] `token_counter.py` with word/char/exact token estimation
- [ ] CLI command to check file tokens
- [ ] Parser handles multiple issue files
- [ ] `issue_splitter.py` with 4 split strategies
- [ ] Split CLI commands: check, preview, split, merge
- [ ] Atomic split with rollback
- [ ] Index file maintenance
- [ ] Auto-split on threshold exceedance
- [ ] Configuration via config.yaml
- [ ] Validation checks (issue count, IDs, content)
- [ ] Documentation with examples
- [ ] Unit tests for all components
- [ ] Integration tests for split/merge workflows

### Notes
- Token estimation doesn't need to be exact (±10% acceptable)
- Splitting should preserve issue order and metadata
- Consider adding file locking for concurrent access
- Future: Support splitting by status (backlog/doing/done)
- Future: Support splitting by priority (high/medium/low)
- Future: GUI tool for visual splitting
- Monitor split file sizes in production
- Keep backups for configurable retention period
- Consider compression for large issue files

---
id: "REFACTOR-001@h4i0j6"
title: "Merge redundant code review prompts into unified review framework"
description: "Consolidate code-review.md, critical-code-review.md, and review-related sections into a single configurable review prompt with severity modes"
created: 2025-12-30
section: "prompts/reviews"
tags: [refactor, prompts, code-review, consolidation, token-efficiency]
type: refactor
priority: high
status: proposed
references:
  - src/dot_work/prompts/code-review.md
  - src/dot_work/prompts/critical-code-review.md
  - src/dot_work/prompts/security-review.md
  - src/dot_work/prompts/performance-review.md
---

### Problem
There are **4 separate review prompts** with significant overlap:
1. `code-review.md` (76 lines) - Generic checklist-style review
2. `critical-code-review.md` (368 lines) - Detailed 12-axis review with issue output
3. `security-review.md` (109 lines) - OWASP-focused security checklist
4. `performance-review.md` (119 lines) - Performance-focused checklist

**Issues:**
- `code-review.md` is 80% redundant with `critical-code-review.md`
- Security and performance axes exist in both `critical-code-review.md` AND separate files
- Agents must load multiple prompts for comprehensive review
- Token waste: ~672 lines across 4 files when ~400 lines could cover all cases
- No clear guidance on when to use which prompt
- `agent-loop.md` step 8 calls all 4 separately, wasting tokens

### Affected Files
- `src/dot_work/prompts/code-review.md` (to be deprecated/merged)
- `src/dot_work/prompts/critical-code-review.md` (becomes base)
- `src/dot_work/prompts/security-review.md` (merged in)
- `src/dot_work/prompts/performance-review.md` (merged in)
- NEW: `src/dot_work/prompts/unified-review.md`

### Importance
**HIGH**: This consolidation:
- Reduces total review prompt tokens by ~40%
- Eliminates confusion about which prompt to use
- Enables single invocation for comprehensive reviews
- Simplifies agent-loop.md step 8 from 4 calls to 1
- Improves agent autonomy (no decision about which review to run)

### Proposed Solution
Create `unified-review.md` with configurable modes:

```yaml
# Usage modes
mode: quick | standard | critical | security | performance | full
default: standard
```

**Architecture:**
1. Core review engine (from critical-code-review.md)
2. Mode-specific axis activation:
   - `quick`: Problem Fit, Error Handling, Test Strategy only
   - `standard`: All 12 axes from critical-code-review
   - `security`: Standard + expanded OWASP (from security-review.md)
   - `performance`: Standard + expanded perf (from performance-review.md)
   - `full`: All axes from all prompts
3. Single output format supporting all modes
4. Deprecate the 3 redundant files

**Migration:**
- `code-review.md` → deprecated, reference `unified-review.md mode:quick`
- `security-review.md` → deprecated, reference `unified-review.md mode:security`
- `performance-review.md` → deprecated, reference `unified-review.md mode:performance`

### Acceptance Criteria
- [ ] `unified-review.md` supports all 5 modes
- [ ] All axes from all 4 prompts preserved in appropriate modes
- [ ] Output format compatible with issue tracker
- [ ] Token count reduced by >30% for equivalent functionality
- [ ] Documentation explains mode selection
- [ ] agent-loop.md updated to use single unified prompt
- [ ] Old prompts marked deprecated with redirect

### Notes
- Consider making mode selection automatic based on changed file types
- Keep security-review.md for standalone security audits (rare)
- The 12 axes in critical-code-review are already comprehensive

---
id: "REFACTOR-002@i5j1k7"
title: "Merge establish-baseline.md and compare-baseline.md into unified baseline system"
description: "Consolidate baseline prompts into single prompt with establish/compare modes and shared schema"
created: 2025-12-30
section: "prompts/baseline"
tags: [refactor, prompts, baseline, consolidation, workflow]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/establish-baseline.md
  - src/dot_work/prompts/compare-baseline.md
  - src/dot_work/prompts/do-work.md
---

### Problem
Baseline functionality is split across 2 prompts:
1. `establish-baseline.md` (331 lines) - Captures project snapshot
2. `compare-baseline.md` (464 lines) - Detects regressions

**Issues:**
- Baseline schema defined twice (drift risk)
- 795 total lines when ~500 could suffice
- `do-work.md` references both but duplicates schema examples
- No shared constants for baseline sections
- Comparison axes in compare-baseline must match establish-baseline sections

### Affected Files
- `src/dot_work/prompts/establish-baseline.md`
- `src/dot_work/prompts/compare-baseline.md`
- NEW: `src/dot_work/prompts/baseline.md` (unified)

### Importance
**MEDIUM**: Consolidation:
- Single source of truth for baseline schema
- Reduces tokens by ~35%
- Eliminates schema drift risk
- Simplifies do-work.md references

### Proposed Solution
Create `baseline.md` with modes:

```yaml
mode: establish | compare
default: establish
```

**Architecture:**
1. Shared baseline schema definition (single source)
2. Mode: establish
   - All 8 axes from establish-baseline.md
   - Output to .work/baseline.md
3. Mode: compare
   - All 8 comparison axes
   - Reference baseline.md file
   - Output regression report + issues

### Acceptance Criteria
- [ ] Single baseline schema definition
- [ ] Both establish and compare modes work
- [ ] Output formats preserved
- [ ] do-work.md updated to reference single prompt
- [ ] Token reduction >30%

### Notes
- Consider adding `baseline mode:diff` for side-by-side comparison

---
id: "REFACTOR-003@l8m4n0"
title: "Consolidate API-related prompts into unified API prompt"
description: "Merge api-export.md and production-ready-apis.md into single comprehensive API prompt with modes"
created: 2025-12-30
section: "prompts/api"
tags: [refactor, prompts, api, consolidation, token-efficiency]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/api-export.md
  - src/dot_work/prompts/production-ready-apis.md
---

### Problem
Two API prompts with significant overlap:
1. `api-export.md` (362 lines) - API audit with OpenAPI alignment
2. `production-ready-apis.md` (281 lines) - Production checklist

**Issues:**
- Overlapping sections: security, validation, error handling, testing
- ~643 total lines when ~400 could suffice
- api-export has 10 detailed axes already covering production concerns
- production-ready-apis is a checklist format, not audit format
- No clear guidance on when to use which

### Affected Files
- `src/dot_work/prompts/api-export.md`
- `src/dot_work/prompts/production-ready-apis.md`
- NEW: `src/dot_work/prompts/api-review.md` (unified)

### Importance
**MEDIUM**: Consolidation:
- Reduces tokens by ~35%
- Single comprehensive API review
- Consistent output format

### Proposed Solution
Create `api-review.md` with modes:

```yaml
mode: audit | checklist | full
default: audit
```

- `audit`: Deep 10-axis analysis (from api-export.md)
- `checklist`: Quick pass/fail (from production-ready-apis.md)
- `full`: Both

### Acceptance Criteria
- [ ] Single unified API prompt
- [ ] All axes preserved
- [ ] Both output formats supported
- [ ] Token reduction >30%

### Notes
- api-export.md name is confusing (it's audit, not export)

---
id: "REFACTOR-004@n0o6p2"
title: "Deprecate and archive redundant prompts"
description: "Remove or archive prompts that are fully superseded by unified prompts or no longer needed"
created: 2025-12-30
section: "prompts/cleanup"
tags: [refactor, prompts, deprecation, cleanup, maintenance]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/prompts/
---

### Problem
After consolidation efforts (REFACTOR-001, 002, 003), several prompts will be redundant:

**Candidates for deprecation:**
1. `code-review.md` - Superseded by unified-review.md
2. `security-review.md` - Merged into unified-review.md
3. `performance-review.md` - Merged into unified-review.md
4. `production-ready-apis.md` - Merged into api-review.md

**Candidates for archive:**
1. `pythonic-code.md` - Niche use, not part of agent-loop
2. `python-project-from-discussion.md` - Project creation, not iteration
3. `agent-prompts-reference.md` - Documentation, not operational

### Affected Files
- Multiple prompts in src/dot_work/prompts/

### Importance
**MEDIUM**: Cleanup:
- Reduces maintenance burden
- Clears confusion about which prompt to use
- Reduces token waste from loading deprecated prompts

### Proposed Solution
1. **Deprecate**: Add deprecation notice pointing to replacement
2. **Archive**: Move to `src/dot_work/prompts/archive/` 
3. **Update references**: Find all references and update

**Deprecation notice format:**
```markdown
---
meta:
  deprecated: true
  superseded_by: unified-review.md
  deprecation_date: 2025-12-30
---

> ⚠️ **DEPRECATED**: This prompt has been superseded by `unified-review.md`.
> Use `unified-review.md mode:quick` for equivalent functionality.
```

### Acceptance Criteria
- [ ] All redundant prompts identified
- [ ] Deprecation notices added
- [ ] Archive folder created
- [ ] References updated
- [ ] Documentation updated

### Notes
- Keep deprecated prompts for 2 releases before removal
- Archive should be clearly marked as not maintained

---
