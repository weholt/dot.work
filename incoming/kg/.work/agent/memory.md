# Memory — Persistent Cross-Session Knowledge

## Project Context

This workspace contains planning documents for **kgshred**, a CLI knowledge-graph "shredder" for plain text/Markdown with:
- Lossless reconstruction via span-based graph storage
- SQLite FTS5 keyword search (zero extra deps)
- Optional semantic search via pluggable embedders
- LLM-assisted UX for natural language queries
- Central repository with cross-project segmentation

## Key Design Documents

- [chat.md](../../chat.md) — Core architecture plan (span graph, SQLite, 4-char IDs, streaming parser)
- [chat-2.md](../../chat-2.md) — LLM-assisted UX (ask, pack, rerank commands)
- [chat-3.md](../../chat-3.md) — Segmentation model (projects, topics, collections)

## Reference Codebase

- `repomix-output-weholt-crampus.xml` — Packed snapshot of original kgtool repo (TF-IDF/KMeans approach to improve upon)

## Implementation Plan

- [Implementation Overview](issues/references/implementation-overview.md) — Phase breakdown, issue summary, module structure

## Issue Summary (2024-12-19)

| Priority | Count | Issues |
|----------|-------|--------|
| Critical (P0) | 2 | FEAT-001 (scaffolding), FEAT-002 (schema) |
| High (P1) | 6 | FEAT-003–008 (core features) |
| Medium (P2) | 8 | FEAT-009–016 (embeddings, projects, LLM) |
| Low (P3) | 8 | FEAT-017–023, PERF-001 (extensions) |

**Total: 24 issues**

## Decisions

### 2024-12-19: Architecture Decisions from Design Docs

1. **Storage**: Single SQLite DB with WAL mode, span-based nodes (no text duplication)
2. **IDs**: blake2s full_id + 4-char Crockford base32 short_id with collision resolution
3. **Parser**: Streaming line-by-line with byte offset tracking
4. **Search**: FTS5 always-on, semantic search optional via HTTP embedders
5. **CLI**: typer-based, thin layer delegating to core modules
6. **Dependencies**: Core uses stdlib only; extras for HTTP, ANN, advanced parsing
7. **Segmentation**: Projects as collections, topics as labels, scope-aware retrieval

### 2024-12-19: Implementation Phasing

1. **Phase 1 (MVP)**: Scaffolding → Schema → IDs → Parser → Graph → FTS → Render → CLI
2. **Phase 2**: Embedder interface → Semantic search
3. **Phase 3**: Collections schema → Scoped search → Project/Topic CLI
4. **Phase 4**: LLM planner → `kg ask` → `kg pack`
5. **Phase 5**: ANN, extended parsing, maintenance

## Learnings

### 2024-12-20: FEAT-001@c7a3b1 - Project Scaffolding

1. **Template-based scaffolding works**: Using `python-project-from-discussion.prompt.md` template provides consistent, production-ready structure
2. **Coverage threshold matters**: Initial 62% coverage failed; adding mock-based tests for error paths pushed to 96%
3. **Minimal config.py is sufficient**: For MVP, just need `get_db_path()`, `ensure_db_directory()`, `validate_path()`
4. **CLI thin layer pattern**: `cli.py` delegates to modules, no business logic

### 2024-12-20: FEAT-002@d8f4e2 - SQLite Database Schema

1. **FTS5 external content is simpler**: Using `content=''` (external content) avoids sync issues with content= tables
2. **Dataclasses work well for row mapping**: Document, Node, Edge dataclasses with `_row_to_*` helpers keep code clean
3. **Context manager for transactions**: `with db.transaction() as conn:` pattern handles commit/rollback cleanly
4. **PRAGMA configuration early**: Set WAL, synchronous, temp_store, foreign_keys on connection open
5. **Schema versioning from start**: `schema_version` table enables future migrations without breakage
6. **Import from collections.abc**: Use `from collections.abc import Iterator, Sequence` not `from typing import Iterator`

### 2024-12-20: FEAT-003@a2e5f9 - ID Generation

1. **Crockford Base32 is ideal for short IDs**: Excludes ambiguous chars (I, L, O, U), uppercase for readability
2. **Nonce-based collision resolution**: Deterministic — same inputs always produce same output with collision set
3. **blake2s is fast and sufficient**: 16-byte digest (32 hex chars) is plenty for content addressing
4. **NamedTuple for structured returns**: `ShortIDResult(short_id, nonce)` cleaner than raw tuples

### 2024-12-20: FEAT-004@b3c6d8 - Markdown Parser

1. **Byte offset tracking**: Must handle CRLF vs LF carefully - track end after newline
2. **Regex on bytes**: Use `rb"^..."` patterns for byte-based matching
3. **Code fence state machine**: Track open/close with fence_char to handle nested fences
4. **Blank lines skip cleanly**: Just increment index and continue
5. **Reconstruction excludes separators**: Blank lines are not stored as blocks, so reconstruction is of content only

### 2024-12-20: FEAT-005@e4d7a1 - Graph Builder

1. **Foreign key constraint**: Must insert Document record before Node insertion (nodes.doc_id references documents)
2. **Heading stack pattern**: Track parent hierarchy with stack of (node_pk, level) entries
3. **Sibling tracking by parent**: Use dict[parent_pk, prev_sibling_pk] for next edges
4. **DFS for tree traversal**: get_node_tree uses DFS with depth counter
5. **Edge types minimal**: `contains` + `next` sufficient for v1 reconstruction and navigation

## Workflow Process Notes

### 2024-12-20: Issue Tracker Hygiene

**⚠️ IMPORTANT: Move completed issues to history.md IMMEDIATELY when completing an issue — not during later housekeeping.**

The correct workflow during the COMPLETE phase is:
1. Update issue status to "completed" in source file
2. Move the complete issue entry to `history.md` (append)
3. **Remove** the issue from the source file (high.md, medium.md, etc.)
4. Update `focus.md` with Previous/Current/Next

This prevents:
- Duplicate issue tracking (completed issues sitting in both source and history)
- Stale "completed" issues cluttering priority files
- Need for manual housekeeping to clean up

The source issue files (high.md, medium.md, low.md) should ONLY contain open issues with status: proposed or in-progress.

### 2024-12-20: BUG-001@a7f3c2 - FTS Indexing Integration

1. **Graph building and FTS indexing must be coupled**: The `build_graph()` function creates nodes but originally didn't index them for search. This caused search to return empty results after ingest — a critical usability bug.
2. **Decode bytes for FTS**: Use `content[block.start:block.end].decode('utf-8', errors='replace')` to convert spans to searchable text.
3. **Index empty docs too**: Even empty documents should be indexed (with empty text) for consistency.
4. **Test search after build, not separately**: Integration-style tests that verify search works immediately after `build_graph()` catch integration gaps that unit tests miss.
5. **Code review catches integration bugs**: This bug was found during code review — the `index_node()` function existed but was never called from the main pipeline. Code reviews should check that all helper functions are actually used.

### 2024-12-20: ENHANCE-001@c9f5e4 - Duplicate Ingest Handling

1. **Custom exceptions for user-facing errors**: `DocumentExistsError` with `sha256_match` flag lets CLI show appropriate message without exposing raw sqlite3 errors.
2. **Cascade delete requires explicit order**: Delete FTS entries → edges → nodes → document, respecting foreign key dependencies.
3. **Force flag pattern**: Check-and-skip by default, delete-and-replace with `--force`. Common CLI UX for idempotent operations.
4. **sha256 comparison for unchanged content**: Calculate hash before insertion to detect unchanged files — skip silently or with message.
5. **Track skipped items separately**: Count skipped docs separately from ingested docs for accurate summary messages.

### 2024-12-20: REFACTOR-001@d1a6f5 - parent_node_pk Semantics (Actually a Bug)

1. **Dead code reveals bugs**: The `parent_node_pk` field existed but was never populated — `_get_ancestor_ids()` relied on it but always got None. Code that references fields that are never set is a bug waiting to be found.
2. **Denormalization after normalization**: Created `contains` edges for hierarchy first, then added `parent_node_pk` as denormalized shortcut. Order matters — ensure the edge-based hierarchy is authoritative.
3. **Update after insert pattern**: Call `update_node_parent()` after node insertion when parent is known. The parent is computed from context (heading stack), not from input data.
4. **In-memory + DB consistency**: When updating DB, also update in-memory object (`node.parent_node_pk = parent_pk`) so callers get consistent data without re-querying.
5. **Test hierarchy thoroughly**: 6 specific tests for different parent relationships (doc→heading, heading→subheading, heading→paragraph, doc→paragraph) catch subtle bugs in hierarchy logic.

### 2024-12-20: FEAT-009@c8b2e5 - Embedder Interface & HTTP Backends

1. **Protocol-based interfaces work well**: Using `@runtime_checkable class Embedder(Protocol)` allows custom backends while providing type safety. No ABC inheritance required.
2. **HTTP-first with stdlib avoids heavy deps**: Using `urllib.request` instead of httpx keeps core lightweight. HTTP clients are well-suited to stdlib.
3. **Dataclass for config is clean**: `EmbedderConfig` with typed fields (backend, model, api_key, base_url, timeout, batch_size) is simpler than dicts.
4. **Factory function pattern**: `get_embedder(config)` checks `config.backend` and returns appropriate class instance. Lazy imports inside factory avoid loading unused backends.
5. **Handle legacy API formats**: Ollama changed response format from `{"embedding": [...]}` to `{"embeddings": [[...]]}`. Check for both to support old servers.
6. **Mock urllib.request for tests**: Use `@patch("kgshred.embed.ollama.urllib.request.urlopen")` with mock response context manager for clean HTTP mocking.
7. **Defer caching to usage point**: Embedding cache makes more sense in search_semantic.py where embeddings are actually stored and retrieved, not in the embedder client itself.
