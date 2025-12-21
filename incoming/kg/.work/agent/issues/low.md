# Low Priority Issues (P3)

Minor improvements, cosmetic changes.

---

## FEAT-017@e7d1a4 — ANN Backend (hnswlib)

```yaml
id: "FEAT-017@e7d1a4"
title: "ANN Backend (hnswlib)"
description: "Implement optional approximate nearest neighbor search using hnswlib for large corpora."
created: 2024-12-19
section: "search"
tags: [ann, hnswlib, semantic-search, performance]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/ann/
  - chat.md#6-indexing
```

### Problem
Brute-force cosine similarity is too slow for >100k nodes. Need ANN for scale.

### Affected Files
- `src/kgshred/ann/__init__.py` (to create)
- `src/kgshred/ann/hnsw.py` (to create)
- `tests/unit/test_ann.py` (to create)
- `tests/integration/test_ann_integration.py` (to create)

### Importance
Performance optimization for large corpora. Optional dependency.

### Proposed Solution
From chat.md section 6:
- Add `hnswlib` as optional dependency (`kg[ann]`)
- Store HNSW index per (model, dims) on disk
- Map node_pk ↔ label for lookup
- Background index rebuild when embeddings change

### Acceptance Criteria
- [ ] Works without `hnswlib` installed (graceful fallback)
- [ ] Index persisted to disk
- [ ] Query time <10ms for 100k vectors
- [ ] Index rebuild command

### Unit Tests — `tests/unit/test_ann.py`

```python
# HNSW index creation
def test_create_index():
    """Should create HNSW index with correct dimensions."""

def test_create_index_with_parameters():
    """Should accept ef_construction and M parameters."""

def test_add_vectors_to_index():
    """Should add vectors with labels."""

def test_query_index_returns_k_neighbors():
    """Query should return k nearest neighbors."""

def test_query_result_includes_distance():
    """Results should include distance/similarity."""

def test_query_result_includes_label():
    """Results should include node_pk label."""

# Index persistence
def test_save_index_to_disk():
    """Index should be saved to disk."""

def test_load_index_from_disk():
    """Index should be loaded from disk."""

def test_load_nonexistent_index_error():
    """Loading missing index should raise error."""

# Fallback
def test_fallback_when_hnswlib_missing():
    """Should fallback to brute-force without hnswlib."""

def test_fallback_warning_logged():
    """Should log warning when using fallback."""

# Label mapping
def test_label_to_node_pk_mapping():
    """Should map label to node_pk correctly."""

def test_node_pk_to_label_mapping():
    """Should map node_pk to label correctly."""

# Index rebuild
def test_rebuild_index_from_embeddings():
    """Should rebuild index from stored embeddings."""

def test_incremental_add_to_index():
    """Should add new vectors without full rebuild."""

# Edge cases
def test_empty_index_query():
    """Query on empty index should return empty."""

def test_query_k_greater_than_index_size():
    """k > index size should return all items."""

def test_duplicate_labels_handled():
    """Duplicate labels should be handled gracefully."""
```

### Integration Tests — `tests/integration/test_ann_integration.py`

```python
@pytest.mark.integration
def test_ann_search_performance_100k():
    """Query on 100k vectors should complete in <10ms."""

@pytest.mark.integration
def test_ann_index_persists_across_sessions():
    """Index should be loadable after process restart."""

@pytest.mark.integration
def test_ann_with_real_embeddings():
    """Should work with real embedding vectors."""

@pytest.mark.integration
def test_ann_rebuild_command():
    """kg reindex --ann should rebuild HNSW index."""

@pytest.mark.integration
def test_ann_vs_brute_force_results():
    """ANN results should approximate brute-force results."""
```

---

## FEAT-018@f8e2b5 — List & Quote Block Parsing

```yaml
id: "FEAT-018@f8e2b5"
title: "List & Quote Block Parsing"
description: "Extend parser to recognize list_block and quote_block node types."
created: 2024-12-19
section: "parser"
tags: [parser, lists, blockquotes, markdown]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/parse_md.py
  - chat.md#5-parsing-pipeline
```

### Problem
v1 parser only handles headings, paragraphs, code fences. Lists and quotes are common in docs.

### Affected Files
- `src/kgshred/parse_md.py` (to extend)
- `tests/unit/test_parse_md.py` (to extend)
- `tests/unit/test_parse_lists_quotes.py` (to create)

### Importance
Parsing fidelity improvement. Phase 4 feature.

### Proposed Solution
From chat.md section 5:
- Detect lists: `^(\s*[-*+]|\s*\d+\.) `
- Detect blockquotes: `^> `
- Create `list_block` and `quote_block` nodes
- Handle nested structures

### Acceptance Criteria
- [ ] Unordered lists parsed correctly
- [ ] Ordered lists parsed correctly
- [ ] Blockquotes parsed correctly
- [ ] Nested lists/quotes handled
- [ ] Byte offsets accurate

### Unit Tests — `tests/unit/test_parse_lists_quotes.py`

```python
# Unordered lists
def test_parse_unordered_list_dash():
    """- item should be list_block."""

def test_parse_unordered_list_asterisk():
    """* item should be list_block."""

def test_parse_unordered_list_plus():
    """+ item should be list_block."""

def test_unordered_list_multiple_items():
    """Multiple items should be one list_block."""

def test_unordered_list_byte_offsets():
    """List block offsets should be accurate."""

# Ordered lists
def test_parse_ordered_list():
    """1. item should be list_block."""

def test_ordered_list_any_number():
    """42. item should be list_block."""

def test_ordered_list_multiple_items():
    """Multiple ordered items should be one block."""

# Nested lists
def test_nested_unordered_list():
    """Indented list items should nest correctly."""

def test_nested_ordered_list():
    """Nested ordered lists should work."""

def test_mixed_nested_lists():
    """Mixed ordered/unordered nesting should work."""

def test_deeply_nested_list():
    """3+ levels of nesting should work."""

# Blockquotes
def test_parse_blockquote():
    """> text should be quote_block."""

def test_blockquote_multiple_lines():
    """Multi-line quote should be one block."""

def test_blockquote_lazy_continuation():
    """Quote without > on continuation should work."""

def test_nested_blockquote():
    """>> nested should be nested quote."""

def test_blockquote_byte_offsets():
    """Quote block offsets should be accurate."""

# Blockquote content
def test_blockquote_with_heading():
    """Quote containing heading should work."""

def test_blockquote_with_code():
    """Quote containing code fence should work."""

def test_blockquote_with_list():
    """Quote containing list should work."""

# Edge cases
def test_list_after_paragraph():
    """List after paragraph should be separate block."""

def test_quote_after_paragraph():
    """Quote after paragraph should be separate block."""

def test_empty_list_item():
    """Empty list item should be handled."""

def test_list_interrupts_paragraph():
    """List should interrupt preceding paragraph."""
```

### Integration Tests — `tests/integration/test_parse_lists_quotes_integration.py`

```python
@pytest.mark.integration
def test_parse_real_markdown_with_lists():
    """Should parse real markdown files with lists."""

@pytest.mark.integration
def test_roundtrip_with_lists_quotes():
    """Parse → render should preserve lists and quotes."""
```

---

## FEAT-019@a9f3c6 — Link Extraction & Ref Edges

```yaml
id: "FEAT-019@a9f3c6"
title: "Link Extraction & Ref Edges"
description: "Extract inline links and wiki-style references to create ref edges."
created: 2024-12-19
section: "parser"
tags: [links, references, edges, wiki-links]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/parse_md.py
  - src/kgshred/graph.py
  - chat.md#2-core-design
```

### Problem
Documents contain cross-references that should become graph edges for navigation.

### Affected Files
- `src/kgshred/parse_md.py` (to extend)
- `src/kgshred/graph.py` (to extend)
- `tests/unit/test_ref_edges.py` (to create)
- `tests/integration/test_ref_edges_integration.py` (to create)

### Importance
Improves graph connectivity. Enables "related content" queries.

### Proposed Solution
From chat.md section 2:
- Extract: `[text](url)`, `[[wiki-link]]`, `[@ABCD]` placeholders
- Create `ref(a -> b)` edges for internal links
- Store external links in node metadata

### Acceptance Criteria
- [ ] Markdown links extracted
- [ ] Wiki-style links extracted
- [ ] Internal refs become edges
- [ ] External links stored as metadata
- [ ] Bidirectional navigation possible

### Unit Tests — `tests/unit/test_ref_edges.py`

```python
# Markdown link extraction
def test_extract_markdown_link():
    """Should extract [text](url) links."""

def test_extract_multiple_links():
    """Should extract all links in paragraph."""

def test_extract_link_text():
    """Should capture link text."""

def test_extract_link_url():
    """Should capture link URL."""

def test_ignore_malformed_link():
    """Should ignore malformed [text(url)."""

# Wiki-style links
def test_extract_wiki_link():
    """Should extract [[page]] links."""

def test_extract_wiki_link_with_alias():
    """Should extract [[page|alias]] links."""

def test_wiki_link_target():
    """Should capture wiki link target."""

# Placeholder links
def test_extract_placeholder_ref():
    """Should extract [@ABCD] references."""

def test_placeholder_short_id():
    """Should capture short_id from placeholder."""

# Internal vs external
def test_internal_link_creates_edge():
    """Internal link should create ref edge."""

def test_external_link_stored_metadata():
    """External link should be stored in metadata."""

def test_classify_internal_link():
    """Should correctly classify internal links."""

def test_classify_external_link():
    """Should correctly classify external links."""

# Ref edges
def test_ref_edge_source_node():
    """Ref edge should have correct source."""

def test_ref_edge_target_node():
    """Ref edge should have correct target."""

def test_ref_edge_type():
    """Edge type should be 'ref'."""

# Edge cases
def test_link_in_code_block_ignored():
    """Links in code blocks should be ignored."""

def test_broken_internal_link():
    """Link to nonexistent target should warn."""

def test_circular_reference():
    """Circular refs should not cause infinite loop."""

def test_duplicate_links_deduped():
    """Same link twice should create one edge."""
```

### Integration Tests — `tests/integration/test_ref_edges_integration.py`

```python
@pytest.mark.integration
def test_cross_document_links():
    """Links between documents should create edges."""

@pytest.mark.integration
def test_navigate_via_ref_edges():
    """Should navigate graph via ref edges."""

@pytest.mark.integration
def test_find_backlinks():
    """Should find all nodes linking to target."""
```

---

## FEAT-020@b1a4d7 — Tag Extraction (Frontmatter & Hashtags)

```yaml
id: "FEAT-020@b1a4d7"
title: "Tag Extraction (Frontmatter & Hashtags)"
description: "Extract tags from YAML frontmatter and inline hashtags."
created: 2024-12-19
section: "parser"
tags: [tags, frontmatter, hashtags, metadata]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/parse_md.py
  - chat.md#5-parsing-pipeline
```

### Problem
Documents often have explicit tags in frontmatter or inline that should be searchable.

### Affected Files
- `src/kgshred/parse_md.py` (to extend)
- `tests/unit/test_tags.py` (to create)
- `tests/integration/test_tags_integration.py` (to create)

### Importance
Improves organization and filtering. Phase 4 feature.

### Proposed Solution
- Parse YAML frontmatter at document start
- Extract `tags:` field as list
- Detect inline `#hashtag` patterns
- Store as topic links or node metadata

### Acceptance Criteria
- [ ] YAML frontmatter parsed
- [ ] Tags field extracted
- [ ] Inline hashtags detected
- [ ] Tags searchable/filterable
- [ ] Frontmatter not duplicated in content

### Unit Tests — `tests/unit/test_tags.py`

```python
# YAML frontmatter
def test_parse_yaml_frontmatter():
    """Should parse --- delimited YAML."""

def test_frontmatter_must_start_at_line_one():
    """YAML must start at first line."""

def test_frontmatter_closing_delimiter():
    """--- or ... should close frontmatter."""

def test_extract_tags_field():
    """Should extract tags: field."""

def test_tags_as_list():
    """tags: [a, b, c] should be list."""

def test_tags_as_yaml_list():
    """tags:\\n  - a\\n  - b should be list."""

def test_extract_title_from_frontmatter():
    """Should extract title field."""

def test_frontmatter_not_in_content():
    """Frontmatter should not appear in paragraph content."""

# Inline hashtags
def test_extract_inline_hashtag():
    """#tag should be extracted."""

def test_hashtag_word_boundary():
    """word#tag should not match (no word boundary)."""

def test_hashtag_at_start_of_line():
    """#tag at start should match."""

def test_hashtag_after_space():
    """space #tag should match."""

def test_hashtag_alphanumeric():
    """#tag123 should match."""

def test_hashtag_with_underscore():
    """#tag_name should match."""

def test_hashtag_with_hyphen():
    """#tag-name should match."""

def test_hashtag_in_code_ignored():
    """#tag in code block should be ignored."""

def test_heading_not_hashtag():
    """# Heading should not be a hashtag."""

# Tag storage
def test_tags_stored_as_metadata():
    """Tags should be in node metadata."""

def test_tags_linked_to_topics():
    """Tags should create topic links."""

def test_duplicate_tags_deduped():
    """Same tag twice should be one entry."""

# Edge cases
def test_empty_frontmatter():
    """Empty frontmatter should not crash."""

def test_invalid_yaml_error():
    """Invalid YAML should warn, not crash."""

def test_no_frontmatter():
    """Document without frontmatter should work."""
```

### Integration Tests — `tests/integration/test_tags_integration.py`

```python
@pytest.mark.integration
def test_search_by_tag():
    """Should find nodes by tag."""

@pytest.mark.integration
def test_filter_by_frontmatter_tag():
    """Should filter search by frontmatter tag."""

@pytest.mark.integration
def test_tag_aggregation():
    """Should list all tags across corpus."""
```

---

## FEAT-021@c2b5e8 — `kg chat` Interactive REPL

```yaml
id: "FEAT-021@c2b5e8"
title: "`kg chat` Interactive REPL"
description: "Implement interactive chat mode for iterative query refinement."
created: 2024-12-19
section: "cli"
tags: [cli, chat, repl, interactive]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/cli.py
  - chat-2.md#2-new-capabilities
```

### Problem
Users may want to iteratively refine queries without restarting the tool.

### Affected Files
- `src/kgshred/cli.py` (to extend)
- `src/kgshred/commands/chat.py` (to create)
- `tests/unit/test_chat.py` (to create)
- `tests/integration/test_chat.py` (to create)

### Importance
Nice UX for exploration. Low priority for v1.

### Proposed Solution
From chat-2.md section 2D:

**Command:**
```
kg chat --doc <id>
```

**Features:**
- REPL loop for queries
- Show skeleton + expanded results
- Suggest "expand these refs" commands
- Support focus/filter directives

### Acceptance Criteria
- [ ] REPL loop works
- [ ] Results displayed incrementally
- [ ] Expansion suggestions offered
- [ ] Exit cleanly with Ctrl+C

### Unit Tests — `tests/unit/test_chat.py`

```python
# REPL handling
def test_chat_starts_repl():
    """Chat should start interactive loop."""

def test_chat_reads_input():
    """Should read user input."""

def test_chat_processes_query():
    """Should process query and show results."""

def test_chat_exit_command():
    """'exit' or 'quit' should exit REPL."""

def test_chat_ctrl_c_handling():
    """Ctrl+C should exit cleanly."""

# Query processing
def test_chat_query_to_search():
    """Query should trigger search."""

def test_chat_shows_skeleton():
    """Results should show document skeleton."""

def test_chat_shows_expanded():
    """Results should show expanded content."""

# Suggestions
def test_chat_suggests_expand():
    """Should suggest expand commands for refs."""

def test_chat_suggestion_format():
    """Suggestions should be copy-pasteable."""

# Focus directives
def test_chat_focus_directive():
    """'focus on X' should filter context."""

def test_chat_filter_directive():
    """'filter by X' should filter results."""

# History
def test_chat_maintains_context():
    """Should maintain context across queries."""

def test_chat_clear_command():
    """'clear' should reset context."""

# Edge cases
def test_chat_empty_input():
    """Empty input should prompt again."""

def test_chat_unknown_command():
    """Unknown command should show help."""
```

### Integration Tests — `tests/integration/test_chat.py`

```python
@pytest.mark.integration
def test_chat_session_end_to_end():
    """Full chat session with queries."""

@pytest.mark.integration
def test_chat_with_doc_filter():
    """kg chat --doc X should scope to document."""

@pytest.mark.integration
def test_chat_iterative_refinement():
    """Multiple queries should refine results."""
```

---

## FEAT-022@d3c6f9 — LLM-Assisted Classification

```yaml
id: "FEAT-022@d3c6f9"
title: "LLM-Assisted Classification"
description: "Use LLM to suggest topics and project assignments for content."
created: 2024-12-19
section: "llm"
tags: [llm, classification, topics, projects]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/llm/classify.py
  - chat-3.md#4-segmentation
```

### Problem
Manual tagging is tedious. LLM can suggest topics with confidence scores.

### Affected Files
- `src/kgshred/llm/classify.py` (to create)
- `tests/unit/test_classify.py` (to create)
- `tests/integration/test_classify_integration.py` (to create)

### Importance
UX improvement for organization. Must be opt-in with provenance.

### Proposed Solution
From chat-3.md section 4C:

**Command:**
```
kg classify --doc <id> --suggest-topics --suggest-projects
```

**Output:**
- Topics with confidence + supporting node IDs
- Project candidates
- Plan JSON for `kg apply`

**Rules:**
- Never silently mutate
- Require explicit `kg apply --plan plan.json`

### Acceptance Criteria
- [ ] Suggestions returned with confidence
- [ ] Supporting evidence (node IDs) included
- [ ] Plan JSON format for review
- [ ] Apply command accepts plan
- [ ] No silent mutations

### Unit Tests — `tests/unit/test_classify.py`

```python
# Classification request
def test_classify_calls_llm():
    """Should call LLM for classification."""

def test_classify_includes_content():
    """LLM prompt should include document content."""

def test_classify_includes_existing_topics():
    """Prompt should include existing topics."""

# Topic suggestions
def test_classify_returns_topic_suggestions():
    """Should return list of suggested topics."""

def test_topic_suggestion_has_confidence():
    """Each suggestion should have confidence score."""

def test_topic_suggestion_has_evidence():
    """Each suggestion should list supporting node IDs."""

def test_confidence_between_0_and_1():
    """Confidence should be 0-1 range."""

# Project suggestions
def test_classify_returns_project_suggestions():
    """Should return project suggestions."""

def test_project_suggestion_has_confidence():
    """Project suggestions should have confidence."""

# Plan generation
def test_classify_generates_plan_json():
    """Should generate plan JSON for review."""

def test_plan_json_valid():
    """Plan JSON should be valid JSON."""

def test_plan_includes_actions():
    """Plan should list actions to perform."""

# Apply command
def test_apply_reads_plan():
    """Apply should read plan JSON."""

def test_apply_executes_actions():
    """Apply should execute plan actions."""

def test_apply_dry_run():
    """Apply --dry-run should not mutate."""

# Safety
def test_classify_no_silent_mutation():
    """Classify should not mutate database."""

def test_apply_requires_explicit_confirm():
    """Apply should require confirmation."""

# Edge cases
def test_classify_no_suggestions():
    """No good matches should return empty list."""

def test_classify_llm_error_handled():
    """LLM error should return graceful error."""
```

### Integration Tests — `tests/integration/test_classify_integration.py`

```python
@pytest.mark.integration
def test_classify_end_to_end(llm_available):
    """Full classify → review → apply pipeline."""

@pytest.mark.integration
def test_classify_with_existing_topics():
    """Should suggest from existing topic list."""

@pytest.mark.integration
def test_apply_creates_topic_links():
    """Apply should create topic links in DB."""

@pytest.mark.integration
def test_apply_rollback_on_error():
    """Error during apply should rollback."""
```

---

## FEAT-023@e4d7a1 — Maintenance Commands (gc, reindex)

```yaml
id: "FEAT-023@e4d7a1"
title: "Maintenance Commands (gc, reindex)"
description: "Implement database maintenance commands for cleanup and index rebuilding."
created: 2024-12-19
section: "cli"
tags: [cli, maintenance, gc, reindex]
type: enhancement
priority: low
status: proposed
references:
  - src/kgshred/cli.py
  - chat.md#8-cli-design
```

### Problem
Over time, orphan nodes and stale indexes accumulate. Need cleanup tools.

### Affected Files
- `src/kgshred/cli.py` (to extend)
- `src/kgshred/commands/maintenance.py` (to create)
- `tests/unit/test_maintenance.py` (to create)
- `tests/integration/test_maintenance.py` (to create)

### Importance
Operational hygiene. v1.1 feature.

### Proposed Solution
From chat.md section 8:

**Commands:**
- `kg gc` — remove orphan nodes/docs, rebuild indexes
- `kg reindex` — FTS rebuild, ANN rebuild

### Acceptance Criteria
- [ ] gc removes orphan nodes
- [ ] gc removes deleted documents
- [ ] reindex rebuilds FTS5
- [ ] reindex rebuilds ANN (if configured)
- [ ] Dry-run option

### Unit Tests — `tests/unit/test_maintenance.py`

```python
# Garbage collection
def test_gc_finds_orphan_nodes():
    """Should identify nodes without parent edges."""

def test_gc_finds_orphan_docs():
    """Should identify docs marked deleted."""

def test_gc_removes_orphan_nodes():
    """Should delete orphan nodes."""

def test_gc_removes_orphan_docs():
    """Should delete orphan documents."""

def test_gc_preserves_valid_nodes():
    """Should not delete valid nodes."""

def test_gc_cascades_to_edges():
    """Deleting node should delete edges."""

def test_gc_cascades_to_embeddings():
    """Deleting node should delete embeddings."""

# Dry run
def test_gc_dry_run():
    """Dry run should not delete anything."""

def test_gc_dry_run_shows_count():
    """Dry run should show what would be deleted."""

# FTS reindex
def test_reindex_fts_rebuilds():
    """Should rebuild FTS5 index."""

def test_reindex_fts_all_nodes():
    """FTS should include all nodes after rebuild."""

def test_reindex_fts_handles_empty():
    """Empty DB should not crash reindex."""

# ANN reindex
def test_reindex_ann_rebuilds():
    """Should rebuild ANN index."""

def test_reindex_ann_skipped_if_not_configured():
    """Should skip ANN if not configured."""

def test_reindex_ann_with_hnswlib():
    """Should rebuild HNSW index if available."""

# Stats reporting
def test_gc_reports_counts():
    """GC should report deleted counts."""

def test_reindex_reports_counts():
    """Reindex should report indexed counts."""

# Edge cases
def test_gc_empty_db():
    """Empty DB should complete without error."""

def test_reindex_empty_db():
    """Empty DB should complete without error."""

def test_gc_during_ingest():
    """GC should wait for active transactions."""
```

### Integration Tests — `tests/integration/test_maintenance.py`

```python
@pytest.mark.integration
def test_gc_end_to_end():
    """Full gc after creating and deleting content."""

@pytest.mark.integration
def test_reindex_fts_end_to_end():
    """Full FTS reindex with verification."""

@pytest.mark.integration
def test_gc_cli_invocation():
    """kg gc should work from CLI."""

@pytest.mark.integration
def test_reindex_cli_invocation():
    """kg reindex should work from CLI."""

@pytest.mark.integration
def test_gc_dry_run_cli():
    """kg gc --dry-run should show preview."""
```

---

## DOCS-001@g6f9c3 — Issue Tracker Workflow Documentation

```yaml
id: "DOCS-001@g6f9c3"
title: "Issue Tracker Workflow Documentation"
description: "Document the file-based issue tracker workflow commands and iteration loop for AI agents."
created: 2024-12-19
section: "documentation"
tags: [docs, workflow, issue-tracker, agents]
type: documentation
priority: low
status: proposed
references:
  - AGENTS.md
  - .github/prompts/do-work.prompt.md
```

### Problem
AI agents need clear documentation on how to use the file-based issue tracker, including trigger commands, iteration workflow, and state management.

### Affected Files
- `AGENTS.md` (documentation added)
- `.work/agent/issues/references/workflow-guide.md` (to create)

### Importance
Essential for consistent AI agent behavior across sessions.

### Documentation Content

#### Trigger Commands Reference
| Command | Action |
|---------|--------|
| `init work` | Initialize `.work/` structure |
| `create issue` | Create issue with generated hash |
| `focus on <topic>` | Create issue(s) in shortlist |
| `add to shortlist X` | Add canonical issue entry |
| `remove from shortlist X` | Remove exact identifier |
| `continue` | Resume work deterministically |
| `status` | Report focus + issue counts |
| `what's next` | Recommend next issue (no state change) |
| `validate` | Run baseline-relative validation |
| `generate-baseline` | Full repo audit → `.work/baseline.md` |
| `housekeeping` | Cleanup (excluding shortlist) |

#### Iteration Loop Phases
1. **BASELINE** — Generate quality baseline before any code changes
2. **SELECT** — Choose issue from shortlist → critical → high → medium → low
3. **INVESTIGATE** — Understand problem, create notes
4. **IMPLEMENT** — Make code changes with tests
5. **VALIDATE** — Compare against baseline at file level
6. **COMPLETE** — Move to history, update focus
7. **FIX** — Create issues for regressions first, then fix
8. **LEARN** — Update memory.md after validation passes

#### Focus State Management
`focus.md` must always contain three sections:
- **Previous**: Last completed issue
- **Current**: Issue being worked on
- **Next**: Anticipated next issue

### Acceptance Criteria
- [ ] AGENTS.md updated with workflow instructions ✅
- [ ] Trigger commands documented with examples
- [ ] Iteration loop clearly explained
- [ ] Anti-patterns documented
- [ ] Quick reference for common flows

### Tasks
- [x] Add iteration workflow to AGENTS.md
- [ ] Create workflow-guide.md with detailed examples
- [ ] Add common flow examples (continue, complete, validation failure)
- [ ] Document focus.md state management

---

## PERF-001@f5e8b2 — Parallel Embedding Jobs

```yaml
id: "PERF-001@f5e8b2"
title: "Parallel Embedding Jobs"
description: "Implement parallel embedding using process pool for batch operations."
created: 2024-12-19
section: "embeddings"
tags: [performance, embeddings, parallel, batch]
type: performance
priority: low
status: proposed
references:
  - src/kgshred/embed/
  - chat.md#10-performance-plan
```

### Problem
Embedding large corpora is slow when done sequentially.

### Affected Files
- `src/kgshred/embed/batch.py` (to create)
- `tests/unit/test_embed_batch.py` (to create)
- `tests/integration/test_embed_batch_integration.py` (to create)

### Importance
Performance optimization for large ingestion jobs.

### Proposed Solution
From chat.md section 10:
- Use process pool for parallel HTTP requests
- Batch nodes for embedding API calls
- Progress reporting during batch jobs

### Acceptance Criteria
- [ ] Configurable parallelism level
- [ ] Progress bar during batch embedding
- [ ] Graceful error handling per batch
- [ ] Resume capability for failed jobs

### Unit Tests — `tests/unit/test_embed_batch.py`

```python
# Batch creation
def test_batch_nodes_for_embedding():
    """Should split nodes into batches."""

def test_batch_size_respected():
    """Each batch should respect max size."""

def test_batch_by_token_count():
    """Should batch by token count, not just count."""

# Parallel execution
def test_parallel_embed_uses_pool():
    """Should use process pool for parallelism."""

def test_parallel_level_configurable():
    """Parallelism should be configurable."""

def test_parallel_default_level():
    """Default parallelism should be reasonable."""

# Progress reporting
def test_progress_callback():
    """Should call progress callback."""

def test_progress_includes_count():
    """Progress should include completed/total."""

def test_progress_includes_rate():
    """Progress should include items/sec."""

# Error handling
def test_batch_error_isolated():
    """Error in one batch should not stop others."""

def test_batch_error_logged():
    """Batch errors should be logged."""

def test_batch_error_collected():
    """Failed batches should be collected for retry."""

# Resume capability
def test_resume_from_checkpoint():
    """Should resume from last checkpoint."""

def test_checkpoint_saved_periodically():
    """Checkpoints should be saved during batch."""

def test_resume_skips_completed():
    """Resume should skip already-embedded nodes."""

# Rate limiting
def test_rate_limit_respected():
    """Should respect API rate limits."""

def test_rate_limit_per_backend():
    """Rate limits should be per backend."""

# Edge cases
def test_empty_batch():
    """Empty input should complete immediately."""

def test_single_item_batch():
    """Single item should work without pool."""

def test_all_batches_fail():
    """All failures should return error summary."""
```

### Integration Tests — `tests/integration/test_embed_batch_integration.py`

```python
@pytest.mark.integration
def test_batch_embed_1k_nodes():
    """Should batch embed 1000 nodes."""

@pytest.mark.integration
def test_batch_embed_with_progress():
    """Should show progress during batch."""

@pytest.mark.integration
def test_batch_embed_resume():
    """Should resume after interruption."""

@pytest.mark.integration
def test_batch_embed_with_errors():
    """Should handle partial failures."""

@pytest.mark.integration
def test_batch_embed_performance():
    """Parallel should be faster than sequential."""
```
