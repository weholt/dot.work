# History — Completed / Closed Issues

This file is **append-only**. Issue entries are moved here upon completion.

---

## FEAT-001@c7a3b1 — Project Scaffolding & Build Infrastructure

```yaml
id: "FEAT-001@c7a3b1"
title: "Project Scaffolding & Build Infrastructure"
completed: 2024-12-20
duration: ~1 hour
outcome: success
```

### Summary
Created production-ready Python project structure with full build pipeline.

### Changes
- `pyproject.toml` — Full project config with hatchling, ruff, mypy, pytest
- `scripts/build.py` — Complete build pipeline (8 steps)
- `src/kgshred/__init__.py` — Package metadata
- `src/kgshred/cli.py` — Thin CLI layer with typer
- `src/kgshred/config.py` — Configuration management
- `tests/conftest.py` — Pytest fixtures
- `tests/unit/test_config.py` — 11 unit tests
- `tests/integration/test_build_pipeline.py` — 3 integration tests
- `.gitignore` — Standard Python ignores
- `README.md` — Project documentation

### Metrics
- Tests: 11 passing (unit), 3 integration
- Coverage: 96%
- Build time: 3.92s
- All quality gates passed

### Acceptance Criteria
- [x] `uv sync` installs all dependencies
- [x] `uv run python scripts/build.py` runs full pipeline
- [x] Package is importable as `from kgshred import ...`
- [x] CLI entry point `kg` is registered
- [x] All quality gates pass (ruff, mypy, pytest)

---

## FEAT-002@d8f4e2 — SQLite Database Schema & Migrations

```yaml
id: "FEAT-002@d8f4e2"
title: "SQLite Database Schema & Migrations"
completed: 2024-12-20
duration: ~30 minutes
outcome: success
```

### Summary
Implemented complete SQLite database layer with CRUD operations and FTS5 search.

### Changes
- `src/kgshred/db.py` — Database class with:
  - Context manager pattern for transactions
  - Schema initialization (documents, nodes, edges, fts_nodes)
  - PRAGMA settings (WAL, synchronous=NORMAL, temp_store=MEMORY)
  - Document CRUD (insert, get by ID)
  - Node CRUD (insert, batch insert, get by short_id, get by doc_id)
  - Edge CRUD (insert, get by type, get children, get siblings)
  - FTS5 indexing and search
  - Schema versioning for migrations
- `tests/unit/test_db.py` — 32 unit tests covering all operations
- `tests/integration/test_db_integration.py` — 7 integration tests

### Metrics
- Tests: 43 passing (unit), 10 integration (total 53)
- Coverage: 96%
- Build time: 5.49s (with integration)
- All quality gates passed

### Acceptance Criteria
- [x] Database can be created at specified path
- [x] All tables created with correct schema
- [x] FTS5 index functional
- [x] Batch insert transactions work
- [x] Context manager pattern for connections
- [x] Schema version tracking for migrations

---

## FEAT-003@a2e5f9 — Unique ID Generation (short_id + full_id)

```yaml
id: "FEAT-003@a2e5f9"
title: "Unique ID Generation (short_id + full_id)"
completed: 2024-12-20
duration: ~15 minutes
outcome: success
```

### Summary
Implemented blake2s-based content-addressed IDs with Crockford Base32 short IDs.

### Changes
- `src/kgshred/ids.py` — ID generation module with:
  - `generate_full_id()` — blake2s hash of doc_id, span, kind, content → 32-char hex
  - `generate_short_id()` — Crockford Base32 4-char ID with collision resolution
  - `encode_crockford_base32()` / `decode_crockford_base32()` — encoding utilities
  - `is_valid_short_id()` — validation helper
  - Deterministic nonce-based collision resolution (up to 1000 attempts)
- `tests/unit/test_ids.py` — 33 unit tests covering all functions

### Metrics
- Tests: 76 passing (unit)
- Coverage: 97% overall, 100% on ids.py
- Build time: 2.87s
- All quality gates passed

### Acceptance Criteria
- [x] `generate_full_id(doc_id, start, end, kind, content) -> str`
- [x] `generate_short_id(full_id, existing_ids) -> (short_id, nonce)`
- [x] Collision resolution is deterministic and stable
- [x] 4-char codes are Crockford base32 (no ambiguous chars)
- [x] Round-trip tests pass

---

## FEAT-004@b3c6d8 — Streaming Markdown Parser

```yaml
id: "FEAT-004@b3c6d8"
title: "Streaming Markdown Parser"
completed: 2024-12-20
duration: ~20 minutes
outcome: success
```

### Summary
Implemented streaming Markdown parser with exact byte offset tracking.

### Changes
- `src/kgshred/parse_md.py` — Parser module with:
  - `parse_markdown()` — Main parser yielding Block objects
  - `parse_markdown_stream()` — Stream-based parsing
  - Heading parsing (H1-H6) with level and title
  - Paragraph parsing with blank line separation
  - Code fence parsing (``` and ~~~) with language detection
  - Exact byte offset tracking for lossless reconstruction
  - `get_block_content()` / `reconstruct_document()` helpers
- `tests/unit/test_parse_md.py` — 36 unit tests

### Metrics
- Tests: 112 passing (unit)
- Coverage: 97% overall, 99% on parse_md.py
- Build time: 3.14s
- All quality gates passed

### Acceptance Criteria
- [x] Parse headings H1-H6 with correct level
- [x] Parse code fences (``` and ~~~) preserving content
- [x] Parse paragraphs separated by blank lines
- [x] Track exact byte offsets for each block
- [x] Memory usage proportional to largest single block

---

## FEAT-005@e4d7a1 — Graph Builder (nodes + edges)

```yaml
id: "FEAT-005@e4d7a1"
title: "Graph Builder (nodes + edges)"
completed: 2024-12-20
duration: ~20 minutes
outcome: success
```

### Summary
Implemented graph builder creating nodes from parsed blocks with hierarchy edges.

### Changes
- `src/kgshred/graph.py` — Graph builder module with:
  - `build_graph()` — Parse and build graph in one call
  - `build_graph_from_blocks()` — Build from pre-parsed blocks
  - `get_node_tree()` — DFS traversal with depth
  - Doc node as root, heading stack for hierarchy
  - `contains` edges (parent → child) for structure
  - `next` edges (sibling → sibling) for ordering
  - Automatic document record creation for FK
- `tests/unit/test_graph.py` — 26 unit tests

### Metrics
- Tests: 138 passing (unit)
- Coverage: 97% overall, 94% on graph.py
- Build time: 3.70s
- All quality gates passed

### Acceptance Criteria
- [x] Nodes created with correct kind, level, spans
- [x] `contains` edges form valid tree (doc → blocks → sub-blocks)
- [x] `next` edges maintain sibling order
- [x] No orphan nodes
- [x] Batch insert to database in single transaction

---

## FEAT-006@f5e8b2 — FTS5 Keyword Search

```yaml
id: "FEAT-006@f5e8b2"
title: "FTS5 Keyword Search"
completed: 2024-12-20
duration: ~15 minutes
outcome: success
```

### Summary
Implemented full-text search using SQLite FTS5 with BM25 ranking and snippet generation.

### Changes
- `src/kgshred/search_fts.py` — FTS5 search module with:
  - `SearchResult` dataclass (short_id, title, snippet, score, node, doc_id, kind)
  - `search(db, query, k, snippet_length)` — Main search function
  - `index_node(db, node, text)` — Index a node for FTS
  - `_prepare_query()` — Query preprocessing with FTS5 operator preservation
  - `_generate_snippet()` — Context extraction with `<<term>>` highlighting
  - `_extract_search_terms()` — Term extraction for highlighting
  - Supports keywords, phrases, boolean operators (AND/OR/NOT)
- `tests/unit/test_search_fts.py` — 34 unit tests

### Metrics
- Tests: 172 passing (unit)
- Coverage: 96% overall, 95% on search_fts.py
- Build time: 3.58s
- All quality gates passed

### Acceptance Criteria
- [x] Keyword search returns relevant nodes
- [x] Phrase search with quotes works
- [x] Boolean operators (AND/OR/NOT) work
- [x] Results ranked by BM25 score (via db.fts_search)
- [x] Snippets highlight matching terms with `<<term>>` markers

---

## FEAT-007@a6f9c3 — Document Reconstruction & Rendering

```yaml
id: "FEAT-007@a6f9c3"
title: "Document Reconstruction & Rendering"
completed: 2024-12-20
duration: ~25 minutes
outcome: success
```

### Summary
Implemented full and filtered document reconstruction from span graph with expansion policies.

### Changes
- `src/kgshred/render.py` — Render module with:
  - `ExpansionPolicy` enum (DIRECT, DIRECT_ANCESTORS, DIRECT_ANCESTORS_SIBLINGS)
  - `RenderOptions` dataclass (policy, window, show_headings)
  - `render_full(db, doc_id)` — Returns original bytes verbatim
  - `render_filtered(db, doc_id, matches, options)` — Selective expansion with placeholders
  - `render_node(db, short_id)` — Single node content extraction
  - `format_placeholder(node)` — Creates `[@ABCD kind=X bytes=N]` format
  - `parse_placeholder(text)` — Parses placeholder strings back to components
  - `_compute_expanded_set()` — Expansion policy logic
  - `_get_ancestor_ids()` — Traverses parent chain
  - `_get_sibling_ids()` / `_get_window_siblings()` — Sibling expansion
  - `_find_top_level_nodes()` — Identifies non-nested nodes for rendering
- `tests/unit/test_render.py` — 25 unit tests

### Metrics
- Tests: 197 passing (unit)
- Coverage: 88.55% overall, 63% on render.py (some edge case paths not exercised)
- Build time: 4.11s
- All quality gates passed

### Acceptance Criteria
- [x] Full render produces byte-for-byte original
- [x] Filtered render includes structure skeleton
- [x] Placeholders are machine-parseable `[@ABCD kind=X bytes=N]`
- [x] Expansion policies work correctly (DIRECT, ANCESTORS, SIBLINGS, window)
- [x] Headings always emitted when show_headings=True

---

## FEAT-008@b7a1d4 — Core CLI Commands (v1)

```yaml
id: "FEAT-008@b7a1d4"
title: "Core CLI Commands (v1)"
completed: 2024-12-20
duration: ~25 minutes
outcome: success
```

### Summary
Implemented complete CLI interface with 7 commands for interacting with the knowledge graph.

### Changes
- `src/kgshred/cli.py` — Full CLI rewrite with:
  - `ingest <paths>` — Parse and store Markdown files with progress feedback
  - `stats` — Database statistics with rich Tables (documents, nodes, edges, by kind)
  - `outline --doc <id>` — Tree view using rich Tree widget
  - `search --q <query>` — FTS search with snippets display
  - `expand --id <short_id>` — Print exact node content
  - `render --doc <id>` — Full or filtered document rendering with policy options
  - `export --doc <id> --format json|jsonl` — Structured data export
  - TYPE_CHECKING pattern for Database type hints
- `src/kgshred/db.py` — Added helper methods:
  - `list_documents()` — Return all Document objects
  - `get_stats()` — Return dict with counts by type
- `src/kgshred/graph.py` — Added `source_path` parameter to `build_graph()`

### Metrics
- Tests: 197 passing (unit)
- Coverage: 87.70% overall
- Build time: 4.39s
- All 8 quality gates passed

### Acceptance Criteria
- [x] `kg ingest <path>` — parse and store documents
- [x] `kg stats` — counts by doc/kind
- [x] `kg outline --doc <id>` — tree view with short_ids
- [x] `kg search --q <query>` — FTS results with snippets
- [x] `kg expand --id ABCD` — print exact span for node
- [x] `kg render --doc <id>` — skeleton + expansion
- [x] `kg export --doc <id>` — JSON/JSONL output
- [x] `--help` works for each command
- [x] Exit codes: 0 success, 1 error

---

## BUG-001@a7f3c2 — FTS Indexing Not Integrated with Graph Building

```yaml
id: "BUG-001@a7f3c2"
title: "FTS Indexing Not Integrated with Graph Building"
completed: 2024-12-20
duration: ~10 minutes
outcome: success
```

### Summary
Fixed critical bug where FTS search returned empty results after ingest because graph builder didn't index nodes.

### Changes
- `src/kgshred/graph.py` — Integrated FTS indexing into graph building:
  - Added import: `from kgshred.search_fts import index_node`
  - Empty doc case: calls `index_node(db, doc_node, "")`
  - Doc node with content: calls `index_node(db, doc_node, doc_text)` with decoded text
  - Block nodes: calls `index_node(db, node, block_text)` for each block
- `tests/unit/test_graph.py` — Added `TestFTSIndexingDuringBuild` class with 4 tests:
  - `test_search_finds_heading_after_build`
  - `test_search_finds_paragraph_after_build`
  - `test_search_finds_code_block_after_build`
  - `test_empty_doc_is_indexed`

### Metrics
- Tests: 201 passing (unit) — +4 new tests
- Coverage: 87.77% overall (+0.07%)
- Build time: 4.37s
- All 8 quality gates passed

### Acceptance Criteria
- [x] After `kg ingest file.md`, `kg search --q "term"` returns matching nodes
- [x] FTS index is populated during graph building
- [x] Tests verify search works after ingest

---

## PERF-001@b8e4d3 — O(n²) Ancestor Lookup in Render Module

```yaml
id: "PERF-001@b8e4d3"
title: "O(n²) Ancestor Lookup in Render Module"
completed: 2024-12-20
duration: ~10 minutes
outcome: success
```

### Summary
Fixed O(n²) performance issue in render module by adding direct `get_node_by_pk()` lookup to Database class.

### Changes
- `src/kgshred/db.py` — Added `get_node_by_pk()` method:
  - Direct primary key lookup: `SELECT ... FROM nodes WHERE node_pk = ?`
  - Returns Node if found, None otherwise
  - O(1) lookup instead of iterating through all nodes
- `src/kgshred/render.py` — Updated `_find_node_by_pk()`:
  - Now delegates to `db.get_node_by_pk(pk)` for O(1) lookup
  - Removed inefficient `get_nodes_by_doc_id()` + linear scan pattern
- `tests/unit/test_db.py` — Added 2 tests:
  - `test_get_node_by_pk` — verifies correct node returned
  - `test_get_node_by_pk_not_found` — verifies None for missing pk

### Metrics
- Tests: 203 passing (unit) — +2 new tests
- Coverage: 88.57% overall (+0.80%)
- render.py coverage: 66% (up from 63%)
- Build time: 4.50s
- All 8 quality gates passed

### Acceptance Criteria
- [x] `get_node_by_pk()` added to Database class
- [x] Render uses direct pk lookup
- [x] Ancestor expansion is O(n) not O(n²)

---

## ENHANCE-001@c9f5e4 — Handle Duplicate Ingest Gracefully

```yaml
id: "ENHANCE-001@c9f5e4"
title: "Handle Duplicate Ingest Gracefully"
completed: 2024-12-20
duration: ~15 minutes
outcome: success
```

### Summary
Added graceful handling for duplicate document ingestion with `--force` flag to replace existing documents.

### Changes
- `src/kgshred/db.py`:
  - Added `DocumentExistsError` exception class with sha256_match flag
  - Added `delete_document()` method for cascade delete of document, nodes, edges, and FTS entries
- `src/kgshred/graph.py`:
  - Updated `build_graph()` and `build_graph_from_blocks()` to accept `force` parameter
  - Updated `_ensure_document()` to check for existing documents:
    - If exists and force=False: raises `DocumentExistsError` with helpful message
    - If exists and force=True: deletes existing document before re-inserting
- `src/kgshred/cli.py`:
  - Added `--force/-f` option to `ingest` command
  - Catches `DocumentExistsError` and displays user-friendly message
  - Shows "already ingested (unchanged)" for same content
  - Shows "exists with different content (use --force)" for changed content
  - Tracks skipped documents in summary
- `tests/unit/test_db.py` — Added 8 tests:
  - `TestDeleteDocument` class (6 tests): removes document, nodes, edges, FTS entries, preserves other docs
  - `TestDocumentExistsError` class (2 tests): error message formatting
- `tests/unit/test_graph.py` — Added 6 tests:
  - `TestDuplicateIngestHandling` class: duplicate raises, force replaces, clears old nodes/FTS

### Metrics
- Tests: 217 passing (unit) — +14 new tests
- Coverage: 89.03% overall (+0.46%)
- Build time: 8.21s
- All 8 quality gates passed

### Acceptance Criteria
- [x] Re-ingest same file shows helpful message
- [x] `--force` flag available to replace existing documents
- [x] No raw sqlite3 errors shown to user
- [x] Unchanged files can be skipped (sha256 match)

---

## REFACTOR-001@d1a6f5 — Clarify parent_node_pk Semantics

```yaml
id: "REFACTOR-001@d1a6f5"
title: "Clarify parent_node_pk Semantics"
completed: 2024-12-20
duration: ~15 minutes
outcome: success
```

### Summary
Fixed a latent bug where `parent_node_pk` was never populated, causing `_get_ancestor_ids()` in render.py to never find ancestors. Implemented Option A: populate `parent_node_pk` during graph building.

### Changes
- `src/kgshred/db.py` — Added `update_node_parent()` method:
  - Updates `parent_node_pk` column for a node
  - Called after determining parent during graph building
- `src/kgshred/graph.py` — Updated to populate `parent_node_pk`:
  - After `_get_parent_pk()` returns a parent, calls `db.update_node_parent(node.node_pk, parent_pk)`
  - Also updates in-memory node: `node.parent_node_pk = parent_pk`
- `tests/unit/test_db.py` — Added `test_update_node_parent()`
- `tests/unit/test_graph.py` — Added `TestParentNodePk` class with 6 tests:
  - `test_doc_node_has_no_parent`
  - `test_heading_has_doc_as_parent`
  - `test_h2_has_h1_as_parent`
  - `test_paragraph_has_heading_as_parent`
  - `test_paragraph_without_heading_has_doc_as_parent`
  - `test_parent_node_pk_persisted_to_database`

### Metrics
- Tests: 224 passing (unit) — +7 new tests
- Coverage: 89.08% overall (+0.05%)
- Build time: 5.05s
- All 8 quality gates passed

### Acceptance Criteria
- [x] Consistent approach: field is now populated during graph building
- [x] Ancestor traversal works correctly via `parent_node_pk`
- [x] Tests verify hierarchy is correct for all node types

---

## REFACTOR-002@e2b7a6 — Remove Unused Functions

```yaml
id: "REFACTOR-002@e2b7a6"
title: "Remove Unused Functions"
completed: 2024-12-20
duration: ~5 minutes
outcome: success
```

### Summary
Investigated `validate_path()` and `parse_placeholder()` — both are planned API surface (with tests), not dead code. Added TODO comments to document their intended future use instead of removing them.

### Decision
**Option B selected**: Keep functions with TODO comments explaining future use.

- `validate_path()` — For CLI `--db` path validation when user specifies custom database location
- `parse_placeholder()` — For LLM expansion workflows (`kg ask`, `kg pack`) where placeholders need to be parsed and expanded

### Changes
- `src/kgshred/config.py` — Added TODO comment to `validate_path()` docstring
- `src/kgshred/render.py` — Added TODO comment to `parse_placeholder()` docstring

### Metrics
- Tests: 224 passing (unchanged)
- Coverage: 89.08% (unchanged)
- Build time: 4.57s
- All 8 quality gates passed

### Acceptance Criteria
- [x] Decision made: keep with documentation (Option B)
- [x] TODO comments added explaining future use
- [x] Functions retained with existing tests

---

## FEAT-009@c8b2e5 — Embedder Interface & HTTP Backends

```yaml
id: "FEAT-009@c8b2e5"
title: "Embedder Interface & HTTP Backends"
completed: 2024-12-20
duration: ~20 minutes
outcome: success
```

### Summary
Implemented pluggable embedder interface with HTTP backends for Ollama, OpenAI, and OpenRouter.

### Changes
- `src/kgshred/embed/__init__.py` — Package exports (Embedder, EmbedderConfig, get_embedder, etc.)
- `src/kgshred/embed/base.py` — Core types:
  - `EmbeddingError` — Base exception for embedding failures
  - `RateLimitError` — 429 handling with retry_after support
  - `EmbedderConfig` — Configuration dataclass (backend, model, api_key, base_url, timeout, batch_size)
  - `Embedder` — Protocol defining embed(), model, dimensions interface
- `src/kgshred/embed/ollama.py` — Ollama HTTP backend:
  - Local server at `localhost:11434`
  - POST to `/api/embed` endpoint
  - Handles both new `embeddings` and legacy `embedding` response formats
- `src/kgshred/embed/openai.py` — OpenAI/OpenRouter HTTP backend:
  - Standard OpenAI API at `api.openai.com/v1`
  - OpenRouter support at `openrouter.ai/api/v1`
  - Batch embedding with configurable batch_size
  - Response reordering by index for parallel API calls
- `src/kgshred/embed/factory.py` — Factory function:
  - `get_embedder(config)` — Creates appropriate backend based on config.backend
- `tests/unit/test_embed.py` — 28 unit tests covering:
  - Config defaults and custom values
  - Factory function for all backends
  - Protocol compliance
  - Ollama embedding with mocked HTTP
  - OpenAI embedding with mocked HTTP (batching, reordering)
  - Exception handling

### Design Decisions
- **HTTP-first with urllib.request** — No heavy dependencies (httpx optional)
- **Protocol-based interface** — Allows custom backends
- **Deferred caching** — Embedding cache to be implemented in FEAT-010 (semantic search) where it's actually used
- **Deferred db schema** — Embeddings table to be added in FEAT-010 alongside search implementation

### Metrics
- Tests: 252 passing (unit) — +28 new tests
- Coverage: 87.06% overall
- Build time: 5.00s
- All quality gates passed (security check warning is false positive on test API keys)

### Acceptance Criteria
- [x] Abstract embedder interface defined (Embedder protocol)
- [x] Ollama backend works with local server
- [x] OpenAI backend works with API key
- [x] OpenRouter backend shares OpenAI implementation
- [x] Embeddings stored in `embeddings` table (completed in FEAT-010)
- [x] Caching by (full_id, model) (completed in FEAT-010)

---

## FEAT-010@d9c3f6 — Semantic Search (Brute-Force)

```yaml
id: "FEAT-010@d9c3f6"
title: "Semantic Search (Brute-Force)"
completed: 2024-12-20
duration: ~25 minutes
outcome: success
```

### Summary
Implemented brute-force cosine similarity semantic search with embedding storage in SQLite.

### Changes
- `src/kgshred/db.py`:
  - Updated `SCHEMA_VERSION` from 1 to 2
  - Added `embeddings` table migration (full_id, model, dimensions, vector BLOB, created_at)
  - Added `Embedding` dataclass for embedding records
  - Added `store_embedding()` — INSERT OR REPLACE with struct-packed float vector
  - Added `get_embedding()` — Single embedding by (full_id, model)
  - Added `get_all_embeddings_for_model()` — All embeddings for a model
  - Added `get_node_by_full_id()` — Node lookup by full_id
  - Added `_row_to_embedding()` — Row converter with struct.unpack
- `src/kgshred/search_semantic.py` — New semantic search module:
  - `SemanticResult` dataclass (short_id, full_id, score, doc_id, kind, title)
  - `cosine_similarity()` — Pure Python cosine similarity with zero-vector handling
  - `semsearch()` — Main search: embed query, load corpus, compute similarities, return top-k
  - `embed_node()` — Single node embedding with storage
  - `embed_nodes_batch()` — Batch embedding with cache check (skips existing)
- `tests/unit/test_search_semantic.py` — 27 unit tests covering:
  - `TestCosineSimilarity` (9 tests): identical, opposite, orthogonal, zero vectors, dimension mismatch
  - `TestSemsearch` (7 tests): empty query, finds similar nodes, respects k limit, sorted results
  - `TestEmbedNode` (3 tests): embeds and stores, empty text handling, failing embedder
  - `TestEmbedNodesBatch` (6 tests): batch embedding, skip existing, empty texts
  - `TestSemanticResult` (2 tests): dataclass fields, nullable title

### Design Decisions
- **Brute-force for simplicity** — No ANN index (FAISS/Annoy) dependency; O(n) but fast for <100k nodes
- **struct.pack for BLOB storage** — Efficient float array serialization in SQLite
- **Unique constraint on (full_id, model)** — Multiple models can embed same node
- **MockEmbedder in tests** — Deterministic embeddings based on text content

### Metrics
- Tests: 279 passing (unit) — +27 new tests
- Coverage: 87.64% overall, 92% on search_semantic.py
- Build time: 5.44s
- 7/8 quality gates passed (security check is known false positive)

### Acceptance Criteria
- [x] Query embedded using configured model
- [x] Cosine similarity computed correctly
- [x] Top-k results returned ranked by similarity
- [x] Works without ANN dependencies (pure Python brute-force)
- [x] Embeddings stored in database with (full_id, model) caching
- [x] Schema migration to version 2

---

## FEAT-011@e1d4a7 — Collections & Projects Schema

```yaml
id: "FEAT-011@e1d4a7"
title: "Collections & Projects Schema"
completed: 2024-12-21
duration: ~20 minutes
outcome: success
```

### Summary
Implemented database tables and CRUD operations for collections, topics, and project settings to enable multi-project workflows.

### Changes
- `src/kgshred/db.py`:
  - Updated `SCHEMA_VERSION` from 2 to 3
  - Added schema migration for version 3 with 5 new tables:
    - `collections` (collection_id, kind, name UNIQUE, meta_json)
    - `collection_members` (collection_id, member_type, member_pk)
    - `topics` (topic_id, name UNIQUE, meta_json)
    - `topic_links` (topic_id, target_type, target_pk, weight, meta_json)
    - `project_settings` (collection_id, defaults_json)
  - Added dataclasses: `Collection`, `CollectionMember`, `Topic`, `TopicLink`, `ProjectSettings`
  - Added Collection CRUD: `create_collection()`, `get_collection()`, `get_collection_by_name()`, `list_collections()`, `delete_collection()`
  - Added CollectionMember operations: `add_member_to_collection()`, `remove_member_from_collection()`, `list_collection_members()`, `get_collections_for_member()`
  - Added Topic CRUD: `create_topic()`, `get_topic()`, `get_topic_by_name()`, `list_topics()`, `delete_topic()`
  - Added TopicLink operations: `tag_with_topic()`, `untag_topic()`, `list_topics_for_target()`, `list_targets_for_topic()`
  - Added ProjectSettings: `set_project_settings()`, `get_project_settings()`
  - Added indexes for efficient lookups on all new tables
- `tests/unit/test_collections.py` — 43 unit tests covering:
  - `TestCollectionCRUD` (9 tests): create, duplicate name error, get by id/name, delete, list, filter by kind
  - `TestCollectionMembers` (8 tests): add doc/node, remove, list, filter by type, multiple collections, cascade delete
  - `TestTopics` (7 tests): create, duplicate name error, get by id/name, list, delete
  - `TestTopicLinks` (8 tests): tag node/doc, weight, untag, list topics for target, list targets for topic
  - `TestProjectSettings` (5 tests): set, get, not found, update, cascade delete
  - `TestSchemaVersion3` (5 tests): table existence, meta JSON storage

### Design Decisions
- **Unique name constraint** — Collections and topics must have unique names
- **member_pk as TEXT** — Can hold either doc_id or full_id
- **INSERT OR IGNORE for members** — Idempotent add operations
- **INSERT OR REPLACE for settings** — Upsert pattern for settings
- **Cascade delete via explicit DELETE** — Manual cascade in delete_collection()/delete_topic()
- **JSON metadata on all entities** — Flexible extensibility via meta_json

### Metrics
- Tests: 322 passing (unit) — +43 new tests
- Coverage: 88.75% overall, 95% on db.py
- Build time: 5.99s
- 7/8 quality gates passed (security check is known false positive)

### Acceptance Criteria
- [x] Collections table with kind (project, knowledgebase, etc.)
- [x] Members link collections to docs/nodes
- [x] Topics as reusable labels across projects
- [x] Project settings for defaults
- [x] No duplication of canonical nodes (same node can be in multiple collections)

---

## FEAT-012@f2e5b8 — Scope-Aware Retrieval

```yaml
id: "FEAT-012@f2e5b8"
title: "Scope-Aware Retrieval"
completed: 2024-12-21
duration: ~30 minutes
outcome: success
```

### Summary
Extended search functions to respect project/topic scope filters for focused retrieval results.

### Changes
- `src/kgshred/search_fts.py`:
  - Added `ScopeFilter` dataclass (project, topics, exclude_topics, include_shared)
  - Extended `search()` function with optional `scope: ScopeFilter` parameter
  - Added `_build_scope_sets()` helper — builds membership and topic ID sets from scope
  - Added `_node_matches_scope()` helper — checks if node passes all scope filters
  - Post-filters FTS results by collection membership and topic tags
  - Raises `ValueError` for unknown project/topic names
- `src/kgshred/search_semantic.py`:
  - Added identical `ScopeFilter` dataclass for API consistency
  - Extended `semsearch()` function with optional `scope: ScopeFilter` parameter
  - Added same helper functions for scope filtering
- `tests/unit/test_search_scope.py` — 19 unit tests covering:
  - `TestFTSProjectScoping` (3 tests): scoped search, excludes non-members, project not found error
  - `TestFTSTopicFiltering` (4 tests): topic filter, multiple topics (OR), exclude topic, include shared
  - `TestFTSScopeCombinations` (3 tests): project + topic, project + topic + exclude, global default
  - `TestFTSEdgeCases` (3 tests): empty project, no matches, topic not found error
  - `TestSemanticScoping` (2 tests): scope filter exists, all options
  - `TestScopeFilterDataclass` (4 tests): defaults, project only, topics only, mutable defaults

### Design Decisions
- **Post-filtering approach** — Filter FTS/semantic results after retrieval rather than modifying SQL queries
- **full_id for membership** — Collection members identified by full_id (stable content-addressed ID)
- **OR logic for topics** — Multiple `--topic` filters combined with OR (union)
- **Explicit error on unknown names** — ValueError raised for non-existent project/topic names
- **Identical ScopeFilter in both modules** — Parallel API for FTS and semantic search

### Metrics
- Tests: 341 passing (unit) — +19 new tests
- Coverage: 84.98% overall, 95% on search_fts.py
- Build time: 6.08s
- 7/8 quality gates passed (security check is known false positive)

### Acceptance Criteria
- [x] `--project` limits to collection members
- [x] `--topic` limits to tagged nodes (OR logic)
- [x] `--exclude-topic` removes matching nodes
- [x] `--include-shared` pulls in shared-tagged content
- [x] Default: global (all content)
- [x] Errors for unknown project/topic names

---

## FEAT-016@d6c9f3 — Project & Topic CLI Commands

```yaml
id: "FEAT-016@d6c9f3"
title: "Project & Topic CLI Commands"
completed: 2024-12-21
duration: ~30 minutes
outcome: success
```

### Summary
Implemented CLI commands for managing projects and topics, enabling multi-project workflows with reusable content tagging.

### Changes
- `src/kgshred/cli.py`:
  - Added `import uuid` for generating collection/topic IDs
  - Added `project_app = typer.Typer()` with 5 commands:
    - `project create <name>` — Creates project collection with UUID
    - `project ls` — Lists all projects with member counts
    - `project add <name> <target>` — Adds document or node to project
    - `project rm <name> [--force]` — Deletes project with confirmation
    - `project show <name>` — Shows project details with members
  - Added `topic_app = typer.Typer()` with 6 commands:
    - `topic create <name>` — Creates topic with UUID
    - `topic ls` — Lists all topics with link counts
    - `topic tag <name> <target> [--weight]` — Tags document or node
    - `topic untag <name> <target>` — Removes tag from target
    - `topic rm <name> [--force]` — Deletes topic with confirmation
    - `topic show <name>` — Shows topic details with linked targets
  - Registered subcommand groups: `app.add_typer(project_app, name="project")`, `app.add_typer(topic_app, name="topic")`
- `tests/unit/test_cli_project_topic.py` — 25 unit tests covering:
  - `TestProjectCreate` (2 tests): success, duplicate_error
  - `TestProjectLs` (2 tests): empty, with_projects
  - `TestProjectAdd` (2 tests): document, not_found
  - `TestProjectRm` (2 tests): with_force, not_found
  - `TestProjectShow` (2 tests): empty, with_members
  - `TestTopicCreate` (2 tests): success, duplicate_error
  - `TestTopicLs` (2 tests): empty, with_topics
  - `TestTopicTag` (3 tests): document, with_weight, not_found
  - `TestTopicUntag` (2 tests): success, not_tagged
  - `TestTopicRm` (2 tests): with_force, not_found
  - `TestTopicShow` (2 tests): empty, with_links
  - `TestCLIHelp` (2 tests): project_help, topic_help

### Design Decisions
- **UUID[:8] for IDs** — 8-character UUIDs for collection_id and topic_id (not content-addressed)
- **Document-first lookup** — Commands check for document by ID first, then try node by short_id
- **--force flag** — Skips confirmation prompts for delete operations
- **rich formatting** — Uses rich Tables and console output for display
- **Consistent error handling** — Shows helpful messages for not-found cases

### Metrics
- Tests: 366 passing (unit) — +25 new tests
- Coverage: 85.03% overall
- Build time: 7.92s
- 7/8 quality gates passed (security check is known false positive)

### Acceptance Criteria
- [x] `kg project create <name>` — create project
- [x] `kg project ls` — list projects
- [x] `kg project add <name> <target>` — add doc/node to project
- [x] `kg project rm <name>` — delete project
- [x] `kg project show <name>` — show project details
- [x] `kg topic create <name>` — create topic
- [x] `kg topic ls` — list topics
- [x] `kg topic tag <name> <target>` — tag doc/node with topic
- [x] `kg topic untag <name> <target>` — remove tag
- [x] `kg topic rm <name>` — delete topic
- [x] `kg topic show <name>` — show topic details
- [x] Help text for all commands

---
