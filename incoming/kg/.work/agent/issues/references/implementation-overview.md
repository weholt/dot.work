# kgshred Implementation Overview

**Version:** 0.1.0 (Planning)  
**Created:** 2024-12-19  
**Status:** Issues Created, Ready for Implementation

---

## 🎯 Project Vision

**kgshred** is a fast CLI knowledge-graph "shredder" for plain text/Markdown that:
- Parses documents into a structural span graph (lossless)
- Enables reconstruction of entire or partial documents
- Provides fast keyword search via SQLite FTS5
- Optionally supports semantic search via pluggable embedders
- Outputs LLM-ready context with selective expansion

**Key differentiator:** Unlike the reference `kgtool` (TF-IDF/KMeans), kgshred stores **byte offsets** into raw documents, enabling exact reconstruction without text duplication.

---

## 📊 Issue Summary

| Priority | Count | Description |
|----------|-------|-------------|
| **Critical (P0)** | 2 | Scaffolding, database schema |
| **High (P1)** | 6 | Core features (IDs, parser, graph, search, render, CLI) |
| **Medium (P2)** | 8 | Embeddings, semantic search, projects, LLM integration |
| **Low (P3)** | 8 | ANN, parsing extensions, maintenance, performance |

**Total Issues:** 24

---

## 🧪 Test Summary

All issues include comprehensive unit and integration test specifications.

### Test File Structure

```
tests/
├── unit/                          # Fast, isolated unit tests
│   ├── test_db.py                 # Database schema tests (~20 tests)
│   ├── test_ids.py                # ID generation tests (~20 tests)
│   ├── test_parse_md.py           # Parser tests (~25 tests)
│   ├── test_graph.py              # Graph builder tests (~18 tests)
│   ├── test_search_fts.py         # FTS5 search tests (~25 tests)
│   ├── test_search_semantic.py    # Semantic search tests (~15 tests)
│   ├── test_render.py             # Rendering tests (~20 tests)
│   ├── test_embed.py              # Embedder tests (~20 tests)
│   ├── test_collections.py        # Collections/topics tests (~25 tests)
│   ├── test_search_scope.py       # Scoped search tests (~15 tests)
│   ├── test_llm_planner.py        # LLM planner tests (~25 tests)
│   ├── test_ask.py                # Ask command tests (~15 tests)
│   ├── test_pack.py               # Pack command tests (~15 tests)
│   ├── test_ann.py                # ANN backend tests (~18 tests)
│   ├── test_parse_lists_quotes.py # List/quote parsing (~25 tests)
│   ├── test_ref_edges.py          # Link extraction tests (~18 tests)
│   ├── test_tags.py               # Tag extraction tests (~25 tests)
│   ├── test_chat.py               # Chat REPL tests (~18 tests)
│   ├── test_classify.py           # LLM classification tests (~18 tests)
│   ├── test_maintenance.py        # GC/reindex tests (~20 tests)
│   └── test_embed_batch.py        # Batch embedding tests (~18 tests)
│
└── integration/                   # End-to-end integration tests
    ├── test_cli.py                # Full CLI command tests (~35 tests)
    ├── test_ingest_render.py      # Ingest → render roundtrip
    ├── test_parse_md_integration.py
    ├── test_graph_integration.py
    ├── test_search_fts_integration.py
    ├── test_search_semantic_integration.py
    ├── test_render_integration.py
    ├── test_embed_integration.py
    ├── test_collections_integration.py
    ├── test_search_scope_integration.py
    ├── test_llm_planner_integration.py
    ├── test_ask.py
    ├── test_pack.py
    ├── test_project_topic.py
    ├── test_ann_integration.py
    ├── test_parse_lists_quotes_integration.py
    ├── test_ref_edges_integration.py
    ├── test_tags_integration.py
    ├── test_chat.py
    ├── test_classify_integration.py
    ├── test_maintenance.py
    └── test_embed_batch_integration.py
```

### Test Counts by Category

| Category | Unit Tests | Integration Tests | Total |
|----------|-----------|-------------------|-------|
| **Core Infrastructure** | ~40 | ~10 | ~50 |
| **Parser & Graph** | ~45 | ~10 | ~55 |
| **Search (FTS + Semantic)** | ~55 | ~15 | ~70 |
| **Rendering** | ~20 | ~8 | ~28 |
| **CLI Commands** | ~30 | ~45 | ~75 |
| **Embeddings** | ~38 | ~10 | ~48 |
| **Collections/Topics** | ~40 | ~10 | ~50 |
| **LLM Integration** | ~58 | ~15 | ~73 |
| **Extended Parsing** | ~68 | ~8 | ~76 |
| **Maintenance** | ~20 | ~5 | ~25 |

**Estimated Total: ~400 unit tests + ~135 integration tests = ~535 tests**

### Testing Guidelines

1. **Unit tests**: Mark with no special decorator, run fast (<1s each)
2. **Integration tests**: Mark with `@pytest.mark.integration`
3. **Coverage requirement**: ≥75% for all modules
4. **Test naming**: `test_<function>_<scenario>_<expected>`

### Running Tests

```bash
# All unit tests
uv run pytest tests/unit -v

# All tests including integration
uv run python scripts/build.py --integration all

# Specific test file
uv run pytest tests/unit/test_ids.py -v

# With coverage
uv run pytest tests/ --cov=src/kgshred --cov-report=term-missing
```

---

## 🏗️ Implementation Phases

### Phase 1: MVP Foundation (P0 + P1)

**Goal:** Functional CLI with ingest, search, and render capabilities.

| Issue | Title | Dependencies |
|-------|-------|--------------|
| [FEAT-001@c7a3b1](.work/agent/issues/critical.md#feat-001c7a3b1--project-scaffolding--build-infrastructure) | Project Scaffolding | None |
| [FEAT-002@d8f4e2](.work/agent/issues/critical.md#feat-002d8f4e2--sqlite-database-schema--migrations) | SQLite Schema | FEAT-001 |
| [FEAT-003@a2e5f9](.work/agent/issues/high.md#feat-003a2e5f9--unique-id-generation-short_id--full_id) | ID Generation | FEAT-001 |
| [FEAT-004@b3c6d8](.work/agent/issues/high.md#feat-004b3c6d8--streaming-markdown-parser) | Markdown Parser | FEAT-001 |
| [FEAT-005@e4d7a1](.work/agent/issues/high.md#feat-005e4d7a1--graph-builder-nodes--edges) | Graph Builder | FEAT-002, FEAT-003, FEAT-004 |
| [FEAT-006@f5e8b2](.work/agent/issues/high.md#feat-006f5e8b2--fts5-keyword-search) | FTS5 Search | FEAT-002, FEAT-005 |
| [FEAT-007@a6f9c3](.work/agent/issues/high.md#feat-007a6f9c3--document-reconstruction--rendering) | Reconstruction | FEAT-002, FEAT-005 |
| [FEAT-008@b7a1d4](.work/agent/issues/high.md#feat-008b7a1d4--core-cli-commands-v1) | Core CLI | All above |

**Deliverable:** `kg ingest`, `kg search`, `kg render`, `kg expand` working end-to-end.

---

### Phase 2: Semantic Search (P2 Subset)

**Goal:** Add embedding-based search with pluggable backends.

| Issue | Title | Dependencies |
|-------|-------|--------------|
| [FEAT-009@c8b2e5](.work/agent/issues/medium.md#feat-009c8b2e5--embedder-interface--http-backends) | Embedder Interface | Phase 1 |
| [FEAT-010@d9c3f6](.work/agent/issues/medium.md#feat-010d9c3f6--semantic-search-brute-force) | Semantic Search | FEAT-009 |

**Deliverable:** `kg embed`, `kg semsearch` commands.

---

### Phase 3: Multi-Project Support (P2 Subset)

**Goal:** Enable segmentation by projects and topics.

| Issue | Title | Dependencies |
|-------|-------|--------------|
| [FEAT-011@e1d4a7](.work/agent/issues/medium.md#feat-011e1d4a7--collections--projects-schema) | Collections Schema | Phase 1 |
| [FEAT-012@f2e5b8](.work/agent/issues/medium.md#feat-012f2e5b8--scope-aware-retrieval) | Scope-Aware Search | FEAT-011 |
| [FEAT-016@d6c9f3](.work/agent/issues/medium.md#feat-016d6c9f3--project--topic-cli-commands) | Project/Topic CLI | FEAT-011 |

**Deliverable:** `kg project`, `kg topic` commands with scoped search.

---

### Phase 4: LLM Integration (P2 Subset)

**Goal:** Natural language queries and LLM-assisted workflows.

| Issue | Title | Dependencies |
|-------|-------|--------------|
| [FEAT-013@a3f6c9](.work/agent/issues/medium.md#feat-013a3f6c9--llm-query-planner-interface) | LLM Planner | Phase 1 |
| [FEAT-014@b4a7d1](.work/agent/issues/medium.md#feat-014b4a7d1--kg-ask-command-natural-language-query) | `kg ask` Command | FEAT-013, Phase 2 |
| [FEAT-015@c5b8e2](.work/agent/issues/medium.md#feat-015c5b8e2--kg-pack-command-structured-output) | `kg pack` Command | FEAT-014 |

**Deliverable:** `kg ask`, `kg pack` for LLM-ready context.

---

### Phase 5: Polish & Scale (P3)

**Goal:** Extended parsing, ANN performance, maintenance tools.

| Issue | Title | Category |
|-------|-------|----------|
| [FEAT-017@e7d1a4](.work/agent/issues/low.md#feat-017e7d1a4--ann-backend-hnswlib) | ANN Backend | Performance |
| [FEAT-018@f8e2b5](.work/agent/issues/low.md#feat-018f8e2b5--list--quote-block-parsing) | List/Quote Parsing | Parser |
| [FEAT-019@a9f3c6](.work/agent/issues/low.md#feat-019a9f3c6--link-extraction--ref-edges) | Link Extraction | Parser |
| [FEAT-020@b1a4d7](.work/agent/issues/low.md#feat-020b1a4d7--tag-extraction-frontmatter--hashtags) | Tag Extraction | Parser |
| [FEAT-021@c2b5e8](.work/agent/issues/low.md#feat-021c2b5e8--kg-chat-interactive-repl) | `kg chat` REPL | CLI |
| [FEAT-022@d3c6f9](.work/agent/issues/low.md#feat-022d3c6f9--llm-assisted-classification) | LLM Classification | LLM |
| [FEAT-023@e4d7a1](.work/agent/issues/low.md#feat-023e4d7a1--maintenance-commands-gc-reindex) | Maintenance | CLI |
| [PERF-001@f5e8b2](.work/agent/issues/low.md#perf-001f5e8b2--parallel-embedding-jobs) | Parallel Embedding | Performance |

---

## 🗂️ Module Structure

```
src/kgshred/
├── __init__.py          # Package exports
├── cli.py               # Thin CLI layer (typer)
├── config.py            # Configuration management
├── db.py                # SQLite schema, queries, migrations
├── ids.py               # blake2s hashing, short_id generation
├── parse_md.py          # Streaming Markdown parser
├── graph.py             # Node/edge creation
├── search_fts.py        # FTS5 keyword search
├── search_semantic.py   # Semantic search (brute-force)
├── render.py            # Full + filtered reconstruction
├── collections.py       # Projects, topics, scopes
├── commands/            # CLI command implementations
│   ├── ingest.py
│   ├── search.py
│   ├── render.py
│   ├── ask.py
│   ├── pack.py
│   ├── project.py
│   ├── topic.py
│   └── maintenance.py
├── embed/               # Optional embeddings
│   ├── __init__.py
│   ├── client.py        # Abstract embedder
│   ├── ollama.py
│   ├── openai.py
│   └── batch.py
├── llm/                 # Optional LLM integration
│   ├── __init__.py
│   ├── client.py        # HTTP adapters
│   ├── planner.py       # Query plan generation
│   └── classify.py      # Topic/project suggestions
└── ann/                 # Optional ANN backends
    ├── __init__.py
    └── hnsw.py
```

---

## 📦 Dependencies

### Core (stdlib only)
```
sqlite3, hashlib, json, re, pathlib, argparse, time
```

### Required (minimal)
```
typer>=0.12.3
rich>=13.9.0
```

### Development
```
pytest>=8.0.0
pytest-cov>=4.1.0
ruff>=0.6.0
mypy>=1.11.0
```

### Optional Extras
```
kg[http]   → httpx
kg[ann]    → hnswlib
kg[mdx]    → advanced markdown parsing
```

---

## ✅ Acceptance Criteria (MVP)

From [chat.md](chat.md) section 14:

1. ✅ Ingest large markdown without memory explosion (streaming)
2. ✅ `kg render --doc X` outputs byte-for-byte original
3. ✅ Every node has unique 4-char code with collision resolution
4. ✅ `kg render --filter ...` returns skeleton + expanded matches
5. ✅ Keyword search returns correct nodes via FTS5
6. ✅ Semantic search works when configured, not required

---

## 🚀 Getting Started

Once Phase 1 is complete:

```bash
# Install
uv sync

# Ingest documents
kg ingest docs/**/*.md

# Search
kg search --q "event sourcing"

# Render with filter
kg render --doc docs/architecture.md --filter "projections" --policy direct+ancestors

# Expand specific node
kg expand --id ABCD
```

---

## 📚 Reference Documents

- [chat.md](chat.md) — Core architecture (span graph, SQLite, IDs, CLI)
- [chat-2.md](chat-2.md) — LLM integration (ask, pack, planner)
- [chat-3.md](chat-3.md) — Multi-project segmentation (collections, topics)
- [AGENTS.md](AGENTS.md) — AI agent guidelines
- [.github/prompts/project-from-discussion.prompt.md](.github/prompts/project-from-discussion.prompt.md) — Project scaffolding template
- [.github/prompts/issue-tracker-setup.prompt.md](.github/prompts/issue-tracker-setup.prompt.md) — Issue workflow specification

---

## 🔄 Next Steps

1. **Start with FEAT-001@c7a3b1** — Project scaffolding
2. Build incrementally through Phase 1
3. Validate with `uv run python scripts/build.py` at each step
4. Mark issues complete and move to history when done
