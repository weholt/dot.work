# Medium-Priority Issue Clarifications

**Date:** 2025-01-01
**Context:** Resolving clarifications for medium-priority issues per agent-loop.md requirement to not wait for user intervention.

---

## Research Summary

### TagGenerator (CR-030@c6d8e0)

**Finding:** Read full `tag_generator.py` (571 lines). Examined test file `tests/unit/git/test_tag_generator.py`.

**Evidence:**
- Extensive emoji-to-tag mappings (50+ emoji mappings, lines 449-496)
- Rich keyword patterns across 15+ categories (lines 15-210)
- Redundancy filtering with canonical mappings (lines 498-570)
- Priority-based limiting to 5 tags (lines 538-570)
- Complexity-based tags using complexity scores (lines 295-302)
- Test `test_limit_tags_to_five` explicitly expects multiple tags for complex commits
- Test `test_filter_tags_removes_duplicates` validates deduplication
- Test `test_generate_tags_from_emoji` validates emoji support

**Decision:** Keep current complexity - tag quality is worth the code size.

**Rationale:**
1. Tests explicitly validate rich functionality (emoji, deduplication, priority limiting)
2. Each feature has distinct purpose: keyword matching, emoji parsing, redundancy filtering, complexity scoring
3. Removing features would require test changes
4. 50-100 line simplification would lose emoji support, priority ordering, and deduplication

**Updated Acceptance Criteria:**
- [ ] Document TagGenerator complexity rationale in code comments
- [ ] No regression in existing test coverage
- [ ] Tag quality maintained (all existing tests pass)

---

### Test Coverage (TEST-001@cov001)

**Finding:** Tests are memory-intensive and take time to run full coverage report.

**Evidence:**
- Build script `scripts/build.py` runs pytest with coverage
- Issue mentions "coverage threshold of 15% is not being met"
- Baseline.md shows "Total test functions: 1,679"

**Decision:** Focus on adding module-specific tests rather than blanket coverage increase.

**Rationale:**
1. 15% threshold is low - suggests many modules lack any tests
2. Adding targeted tests to key modules is more effective than random additions
3. Priority: git/, review/, db_issues/ modules first

**Updated Acceptance Criteria:**
- [ ] Add 5 tests to `src/dot_work/git/services/` (tag_generator, file_analyzer, git_service)
- [ ] Add 5 tests to `src/dot_work/review/` (git, server modules)
- [ ] Add 3 tests to `src/dot_work/db_issues/` (cli, adapters)
- [ ] Coverage reaches 15% threshold
- [ ] All tests pass

---

### Error Handling (SEC-004@security-review-2026)

**Finding:** Examined error handling patterns in cli.py files. Verbose mode shows tracebacks.

**Evidence:**
- Pattern: `if verbose: console.print(traceback.format_exc())`
- Verbose mode is opt-in (requires user to pass --verbose flag)
- Standard developer tool practice

**Decision:** Verbose mode can show tracebacks (developer-facing). Base exception messages should be sanitized.

**Rationale:**
1. Verbose mode is explicitly opt-in for debugging
2. Developers need tracebacks to diagnose issues
3. Security risk is minimal since verbose is opt-in
4. Base exception messages (non-verbose) should be generic

**Updated Acceptance Criteria:**
- [ ] Non-verbose error messages are generic (no paths, internal details)
- [ ] Verbose mode keeps traceback display for debugging
- [ ] Sensitive data filtered from all exception messages
- [ ] Errors logged to file with full details

---

### Path Validation (SEC-005@security-review-2026)

**Finding:** Examined `installer.py` write operations.

**Evidence:**
- Line 348: `combined_path.write_text()` - combined_path = target / config.combined_path
- Line 430: `dest_path.write_text()` - dest_path = dest_dir / dest_name
- Line 450: `aux_full_path.write_text()` - auxiliary files
- `target` comes from user CLI argument
- `config.combined_path` and `config.dest_path` are hardcoded strings in INSTALLERS dict
- No validation against `../` in config paths

**Decision:** Add path validation utility to ensure all write paths stay within target directory.

**Rationale:**
1. While config paths are currently trusted, future modifications could introduce vulnerabilities
2. Path traversal is a critical security issue (OWASP A01:2021)
3. Validation utility is inexpensive insurance
4. Symlink resolution prevents edge case attacks

**Updated Acceptance Criteria:**
- [ ] Create `safe_path_join(target, path)` utility in src/dot_work/utils/path.py
- [ ] Utility resolves symlinks and validates result is within target directory
- [ ] All installer.py write operations use safe_path_join
- [ ] Tests verify path traversal attempts are blocked
- [ ] Documentation for safe file operations

---

### Jinja2 Autoescape (SEC-006@security-review-2026)

**Finding:** Examined Jinja2 setup in installer.py.

**Evidence:**
- Line 106: `# noqa: S701 - autoescape disabled for markdown`
- Line 111: `autoescape=False`
- Comment: "Autoescape is disabled since we generate markdown, not HTML"
- Comment: "These templates are trusted internal files, not user input"
- Templates come from `dot_work/prompts/` directory (bundled with package)

**Decision:** No HTML output planned. Add documentation explaining the security rationale.

**Rationale:**
1. Templates are internal, not user-specified
2. Output is markdown, not HTML
3. XSS risk is low for markdown output
4. Documentation prevents future accidental HTML generation

**Updated Acceptance Criteria:**
- [ ] Add docstring explaining why autoescape is disabled
- [ ] Add comment warning if HTML output is ever added
- [ ] Tests verify template content is treated as trusted
- [ ] Security review note in documentation

---

### Secrets Management (SEC-007@security-review-2026)

**Finding:** Searched codebase for API key and token usage.

**Evidence:**
- `OPENAI_API_KEY`: used in `knowledge_graph/embed/openai.py` and `git/services/llm_summarizer.py`
- `ANTHROPIC_API_KEY`: used in `git/services/llm_summarizer.py`
- `GITHUB_TOKEN`: used in `container/provision/` modules
- SQLite uses file-based database (no credentials)

**Decision:** Scope secrets management to these three environment variables.

**Rationale:**
1. Only three actual secrets in use
2. SQLite is file-based (no credentials)
3. Focused scope allows targeted solution

**Updated Acceptance Criteria:**
- [ ] Create `secrets.py` utility with validation for OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN
- [ ] Secrets never appear in logs or error messages (use sanitize_log_message)
- [ ] .env.example file provided (without actual secrets)
- [ ] Documentation for secrets management
- [ ] Tests verify secrets aren't leaked in output

---

### Git Branch/Tag Memoization (PERF-012@q2r3s4)

**Finding:** Examined `git_service.py` lines 615-639.

**Evidence:**
- `_get_commit_branch()` and `_get_commit_tags()` called for every commit
- No caching between calls
- Same commit queried multiple times during comparison

**Decision:** Clear cache per comparison (as proposed in issue).

**Rationale:**
1. Comparison is self-contained operation
2. Between comparisons, repo state may have changed (new branches/tags)
3. Cache invalidation is simpler with per-comparison approach
4. Memory overhead is minimal (dict with commit hash keys)

**Updated Acceptance Criteria:**
- [ ] Commit-to-branch mapping built once per comparison
- [ ] Commit-to-tags mapping built once per comparison
- [ ] O(1) lookups in `_get_commit_branch()` and `_get_commit_tags()`
- [ ] Caches cleared between comparisons
- [ ] Performance test: 1000 commits < 5 seconds vs current 30+ seconds

---

### Scope Set Caching (PERF-013@r3s4t5)

**Finding:** Examined `search_fts.py` and `search_semantic.py`.

**Evidence:**
- Scope sets computed for EVERY search operation
- Scope doesn't typically change between searches in same session
- Multiple database queries per scope build

**Decision:** Session-level cache with TTL (60 seconds).

**Rationale:**
1. Scope rarely changes within session
2. TTL handles edge case of topic/collection modifications
3. 60 seconds balances freshness vs performance
4. Session-level cache is simpler than manual invalidation

**Updated Acceptance Criteria:**
- [ ] Scope sets cached with 60-second TTL
- [ ] Cache key based on scope parameters (project, topics, exclude_topics)
- [ ] Performance test: 100 searches with same scope < 2 seconds vs current 5+ seconds
- [ ] TTL-based cache invalidation implemented
- [ ] Documentation of cache behavior

---

### Sequential Commit Processing (PERF-014@s4t5u6)

**Finding:** Examined `git_service.py` commit processing loop.

**Evidence:**
- Commits analyzed sequentially (one at a time)
- Each commit requires file diff parsing, complexity calculation
- CPU-bound operations not parallelized

**Decision:** Auto-detect based on commit count (>50 commits = parallel).

**Rationale:**
1. Small comparisons (<50 commits) don't benefit from parallelization overhead
2. Large comparisons (>50 commits) see significant speedup
3. Auto-detection provides good UX without requiring flags
4. Fallback to sequential for single commits

**Updated Acceptance Criteria:**
- [ ] Commit analysis parallelized with ProcessPoolExecutor for >50 commits
- [ ] Sequential processing for ≤50 commits
- [ ] CPU utilization increased to 80%+ on multi-core for large comparisons
- [ ] Performance test: 100 commits on 8-core < 30 seconds vs current 200+ seconds
- [ ] Error handling preserves all successful analyses
- [ ] Results sorted by original commit order

---

### db-issues Integration Tests (TEST-040@7a277f)

**Finding:** Examined integration tests in `tests/integration/db_issues/`.

**Evidence:**
- Tests use `--json` flag that doesn't exist on current CLI
- Tests expect direct array output, but CLI returns wrapped objects
- Issue proposes Option A (update tests) vs Option B (add --json flag)

**Decision:** Option C - Both: update tests AND add --json for future use.

**Rationale:**
1. Tests should pass with current CLI (Option A)
2. --json flag is useful for automation/scripting (Option B)
3. Doing both provides immediate fix + future capability
4. Low additional effort to add --json flag

**Updated Acceptance Criteria:**
- [ ] Add `--json` flag to db-issues CLI create/list/edit commands
- [ ] Update all 4 affected test files to parse wrapped output
- [ ] Use regex for issue ID parsing instead of split()
- [ ] All db_issues integration tests pass
- [ ] JSON output format documented

---

### N+1 Query Problem (PERF-015@perf-review-2025)

**Finding:** Examined `sqlite.py` lines 718-762.

**Evidence:**
- `_model_to_entity()` performs 3 queries per issue (labels, assignees, references)
- Called for EVERY issue in list operations
- `_models_to_entities()` (lines 764-844) already implements batch loading correctly

**Decision:** Option A - Use existing `_models_to_entities()` for single-entity loads.

**Rationale:**
1. Correct pattern already exists in codebase
2. Single-row loads can call batch method with single-item list
3. Minimal code change required
4. Proven pattern (already tested)

**Updated Acceptance Criteria:**
- [ ] `_model_to_entity()` delegates to `_models_to_entities()` with single-item list
- [ ] Loading 100 issues uses ≤10 queries total (vs 301)
- [ ] Performance test: 100 issues < 1 second (vs 3-5 seconds)
- [ ] No regression in functionality
- [ ] Existing batch-loading tests pass

---

### Embedding Memory Usage (PERF-018@perf-review-2025)

**Finding:** Examined `db.py` lines 1098-1143.

**Evidence:**
- Default limit of 10,000 embeddings
- Each embedding is 384-1536 floats × 4 bytes = 1.5-6 KB
- 10k embeddings = 15-60 MB memory
- `stream_embeddings_for_model()` (lines 1175-1200) already exists

**Decision:** Option A - Change default limit from 10000 to 1000 + document streaming for larger sets.

**Rationale:**
1. 1000 embeddings = 1.5-6 MB (reasonable default)
2. Streaming API already exists for large datasets
3. Breaking API change (deprecation) not justified
4. Documentation guides users to streaming for large use cases

**Updated Acceptance Criteria:**
- [ ] Default limit changed from 10000 to 1000
- [ ] Memory usage documented in docstring (~1.5-6 KB per embedding)
- [ ] Warning logged when loading >1000 embeddings
- [ ] Documentation recommends streaming for datasets >1000 embeddings
- [ ] Tests verify OOM protection with default limit

---

### Query Result Caching (PERF-020@perf-review-2025)

**Finding:** Examined search operations in `search_fts.py` and `search_semantic.py`.

**Evidence:**
- No caching for search results
- Issue is marked LOW priority
- Notes "Only implement if usage patterns show high repetition"

**Decision:** Defer until actual usage patterns are measured.

**Rationale:**
1. Most searches are unique in typical workflows
2. Cache invalidation complexity may outweigh benefits
3. No evidence of high repetition in current usage
4. LOW priority indicates this is not urgent

**Updated Acceptance Criteria:**
- [ ] Issue marked as deferred pending usage analysis
- [ ] Note added: "Revisit if cache hit ratio would be >30%"
- [ ] No implementation at this time

---

### Database Indexes (PERF-017@perf-review-2025)

**Finding:** Examined `db.py` schema creation.

**Evidence:**
- Missing indexes on: nodes(doc_id), nodes(kind), embeddings(full_id, model), collection_members(collection_id), topic_links(topic_id)
- Some indexes exist (edges, nodes.primary keys)

**Decision:** Add migration script (version 5) with indexes.

**Rationale:**
1. Migration script is standard practice
2. Allows smooth upgrade for existing databases
3. Indexes are read-optimized (minimal write impact)
4. Version 5 indicates next schema version

**Updated Acceptance Criteria:**
- [ ] Schema migration created (version 5)
- [ ] Indexes added for doc_id, kind, full_id, collection_id, topic_id
- [ ] Migration applies indexes on startup if not present
- [ ] Performance test: 1000 nodes loaded < 100ms (vs 500ms+)
- [ ] No regression in write performance

---

## Updated Issue Status

After applying these decisions, all medium-priority issues should have:
- No open clarifications
- Explicit validation plans
- Deterministic acceptance criteria
- Technical choices documented

Next steps:
1. Update each issue with resolved decisions
2. Remove `needs-clarification` and `decision-required` tags
3. Add `has-deps` where dependencies identified
4. Move to implementation phase
