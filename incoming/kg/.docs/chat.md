# Plan: fast CLI knowledge-graph “shredder” for plain text/Markdown with reconstruction + semantic search

## 0) What the attached repo shows (baseline to improve)
The reference codebase (`kgtool`) builds a graph from chunks using TF-IDF/KMeans + cosine similarity, with dependencies like `networkx`, `scikit-learn`, `yake`, `rapidfuzz`. That approach is fine for demos, but it’s heavy, not streaming-first, and it doesn’t guarantee lossless reconstruction.

This plan designs a new tool that:
- parses text/Markdown into a *structural* graph (contains/next edges),
- keeps *lossless spans* back to the original document so you can reconstruct exactly,
- indexes for *keyword search* via SQLite FTS5 (fast, zero extra deps),
- optionally adds *semantic search* via a pluggable embedder + ANN backend,
- supports an output mode that returns full structure but only “fleshes out” matching parts (others become references).

---

## 1) Goals / constraints

### Goals
- Ingest unlimited-length content (streaming; not “load whole file and split”).
- Deterministic, lossless reconstruction of:
  - entire documents, or
  - partial documents with placeholders that can later be expanded.
- Every piece gets a **unique 4-char code** (human-friendly), while remaining collision-safe.
- Search:
  - keyword/phrase search (fast baseline),
  - semantic search (optional, pluggable).
- Minimal core dependencies; “fast as fuck” on large corpora.

### Non-goals (initially)
- Full Markdown AST fidelity (tables, nested lists, footnotes) in v1.
- Rich graph analytics (PageRank, clustering) in core.

---

## 2) Core design: “span graph” over raw documents

Key idea: store each imported document as a raw text blob; nodes reference **byte offsets** into that blob. This makes reconstruction exact and avoids duplicating text in the DB.

### Node types (v1)
- `doc` (one per source file)
- `block` (top-level blocks in markdown-ish parsing)
- `heading` (H1..H6)
- `paragraph`
- `codeblock`
- `list_block` (optional v1.1)
- `quote_block` (optional v1.1)

### Edge types (v1)
- `contains(parent -> child)` : structural hierarchy (doc → blocks; heading → its content blocks, etc.)
- `next(a -> b)` : total ordering for reconstruction at each level
- `ref(a -> b)` : explicit references (Wiki links, `[@ABCD]`, anchors, etc.)
- `tag(node -> tag)` : optional (store tags as nodes, or as a table)

This is enough to:
- reconstruct by walking `contains` + `next`,
- render a skeleton tree,
- expand only selected nodes.

---

## 3) Identifiers: unique 4-char codes without lying to yourself about collisions

A pure 4-char space is small. You can still make it **unique in your corpus** reliably by combining:
- a *long* content-addressed ID (stored internally), and
- a *short* 4-char presentation ID with collision resolution.

### Proposed scheme
- `full_id`: `blake2s(doc_id || start || end || kind || content_bytes)` as 16 bytes (or 32) stored as hex.
- `short_id`: base32 (Crockford) of the first 20 bits of `full_id` → exactly **4 chars**.

**Collision handling (DB-enforced):**
- `nodes.short_id` has a UNIQUE constraint.
- On collision:
  - re-derive `short_id` using `blake2s(full_id || nonce)` with nonce incremented until unique.
- Keep `short_id` stable by persisting the chosen nonce (`short_nonce`) with the node.

This keeps the UX requirement (“4 chars”) while guaranteeing uniqueness in the actual DB.

---

## 4) Storage: SQLite-first (fast, minimal deps, great ergonomics)

Single DB file, e.g. `~/.kgshred/db.sqlite`.

### Tables (minimal schema)
- `documents(doc_id TEXT PK, source_path TEXT, sha256 TEXT, created_at INT, raw BLOB)`
- `nodes(node_pk INTEGER PK, short_id TEXT UNIQUE, full_id TEXT UNIQUE, doc_id TEXT, kind TEXT, level INT, title TEXT, start INT, end INT, parent_node_pk INT, meta_json TEXT)`
- `edges(src_node_pk INT, dst_node_pk INT, type TEXT, weight REAL, meta_json TEXT, PRIMARY KEY (src_node_pk, dst_node_pk, type))`

### Search indexes
- `fts_nodes` (FTS5 virtual table)
  - columns: `title`, `text`, `short_id UNINDEXED`
  - use `bm25(fts_nodes)` for ranking
- Optional:
  - `embeddings(node_pk INT, model TEXT, dims INT, vec BLOB, PRIMARY KEY(node_pk, model))`

### Performance PRAGMAs (defaults)
- `PRAGMA journal_mode=WAL;`
- `PRAGMA synchronous=NORMAL;`
- `PRAGMA temp_store=MEMORY;`
- batch inserts in transactions (critical)

---

## 5) Parsing pipeline (streaming-friendly)

### Markdown-ish parser strategy (v1)
Implement a lightweight block parser (no heavy markdown libs) that recognizes:
- headings: `^#{1,6} `
- code fences: ``` / ~~~ (track fence type; capture exactly)
- blank-line separated paragraphs
- optionally: blockquotes `^> `
- optionally: lists `^(\s*[-*+]|\s*\d+\.) `

**Output:** a sequence of blocks with `(kind, start_offset, end_offset, title?, level?)`.

Then build hierarchy:
- `doc` contains all blocks.
- For headings: use a stack by heading level; subsequent blocks belong to the nearest preceding heading of lower level until next heading of same/upper level.

**Ordering:** create `next` edges among siblings in ingestion order.

### Unlimited-length handling
- Read input file as bytes, stream line-by-line while tracking byte offsets.
- For code fences and paragraphs, buffer only the current block; flush block nodes as soon as block ends.
- Store full raw doc bytes once in `documents.raw` (or store path + mmap; but BLOB is simplest and portable).

---

## 6) Indexing: keyword search always; semantic search optional

### Baseline search (always on; no extra deps)
- Insert each node’s searchable text into FTS5:
  - headings: `title`
  - paragraphs/codeblocks: exact span text (or a capped size + fallback to span retrieval for display)
- Queries:
  - keywords: `kg search "event sourcing projection"`
  - phrase: `kg search '"domain driven design"'`
  - boolean: `kg search 'cqrs AND marten NOT legacy'`

### Semantic search (optional, pluggable)
You need 2 plug points:
1) **Embedder**: turns text → vector
2) **Vector index backend**: finds nearest neighbors fast

#### Embedder interface (HTTP-first to avoid heavy deps)
- `embed(texts: list[str], model: str) -> list[float32[]]`
Backends:
- `ollama` (local, HTTP)
- `openai` / `openrouter` (HTTP)
- `local` (optional extra: `sentence-transformers`, heavy; not core)

#### Vector index backends
- Core fallback: brute-force cosine over DB-stored vectors (only acceptable for small corpora).
- Fast path (recommended extras):
  - `hnswlib` as an optional dependency (`kg[ann]`)
  - Store an HNSW index per `(model,dims)` on disk; map node_pk ↔ label.

The tool should function fully without embeddings; embeddings are an “accelerator” feature.

---

## 7) Reconstruction and “skeleton with selective expansion”

### Full reconstruction
Given `doc_id`:
- start at doc node, DFS by `contains`, but emit siblings by `next` ordering
- for leaf nodes, read bytes from `documents.raw[start:end]` and write verbatim

This yields byte-for-byte reconstruction (assuming you preserve original newlines and encoding).

### Filtered reconstruction (“structure returned, only matches fleshed out”)
Input:
- filter criteria: keyword query, semantic query, tags, node kinds, heading paths
- expansion policy: `direct`, `direct+ancestors`, `direct+ancestors+siblings`, `window=N next/prev`

Algorithm:
1) Evaluate filter → a set `M` of matching node_pks.
2) Compute `E` (nodes to expand):
   - always include ancestors up to doc so structure remains navigable
   - optionally include context windows (prev/next siblings)
3) Render:
   - For nodes in `E`: emit full span text (verbatim)
   - For nodes not in `E` but structurally needed: emit a placeholder reference, e.g.
     - `<!-- @ABCD kind=paragraph start=1234 end=1567 -->`
     - or `[@ABCD] (collapsed: paragraph, 333 bytes)`
4) Ensure the skeleton is still a valid, readable Markdown outline:
   - headings always emitted (title)
   - collapsed content under headings becomes references

The placeholder format must be machine-parseable so “expand later” is trivial.

---

## 8) CLI design (subcommands)

Binary name example: `kg` (or `kgshred`).

### Core commands (v1)
- `kg ingest --db ~/.kg/db.sqlite <path|glob|stdin>`
- `kg stats --db ...` (counts by doc/kind, index health)
- `kg outline --db ... --doc <doc_id|path> [--max-depth N]` (tree view with short_ids)
- `kg search --db ... --q <fts query> [--k 20]` (FTS results with short_ids + snippets)
- `kg expand --db ... --id ABCD` (print the exact span for a node)
- `kg render --db ... --doc <doc_id|path> [--filter <fts query>] [--semantic "<text>"] [--policy direct+ancestors] [--window 1]` (skeleton + selective expansion)
- `kg export --db ... --doc ... --format jsonl|json` (for external pipelines)

### Embeddings commands (v1.1)
- `kg embed --db ... --model <name> [--kinds paragraph,heading] [--changed-only]`
- `kg semsearch --db ... --model <name> --q "<text>" --k 20`

### Maintenance (v1.1)
- `kg gc --db ...` (remove orphan nodes/docs, rebuild indexes)
- `kg reindex --db ...` (FTS rebuild; ANN rebuild)

All command outputs should include short_ids prominently so users can “drill down”.

---

## 9) Output formats that work for LLM context assembly

### “LLM-ready pack” output (render mode)
Produce a single Markdown document with:
- a stable outline (headings and node refs),
- expanded content only where relevant,
- compact references elsewhere.

Example placeholder (recommended):
- `[@ABCD kind=paragraph bytes=412]`
This makes follow-up retrieval deterministic.

### Optional “bundle” format (for tooling)
- JSONL records: `{short_id, kind, title, doc_id, start, end, parent, tags, text_preview}`

---

## 10) Performance plan (“fast as fuck” without heavy deps in core)

### Must-do optimizations
- Streaming parse; avoid holding whole corpus in memory.
- SQLite batch inserts in one transaction per document (or per N nodes).
- FTS inserts batched too.
- Store raw doc once; nodes store spans only (no duplicate text).
- Use `blake2s` from stdlib for hashing (fast enough; zero deps).
- Use `sqlite3` from stdlib; keep schema tight; add indexes only where needed:
  - `nodes(doc_id)`, `nodes(parent_node_pk)`, `edges(src_node_pk,type)`

### Optional fast path
- `hnswlib` for ANN if semantic search must be truly fast at scale.
- parallel embedding jobs (process pool) since embedding is usually IO-bound (HTTP) or CPU-heavy (local model).

---

## 11) Implementation phases

### Phase 1 (MVP, minimal deps)
- SQLite schema + migrations
- streaming markdown-ish parser → nodes + edges
- short_id uniqueness with collision resolution
- FTS5 indexing + keyword search
- outline + full render + filtered render with placeholders
- expand by short_id

### Phase 2 (semantic search plumbing)
- embedder interface + HTTP backends (ollama/openai/openrouter)
- embeddings table + caching keyed by (full_id, model)
- brute-force semsearch for small corpora

### Phase 3 (scale semantics)
- optional ANN backend (`hnswlib`) with persistent index files
- background batch embedding (still invoked by explicit CLI command)

### Phase 4 (parsing fidelity)
- lists/quotes/tables as node kinds
- link extraction → `ref` edges
- tag extraction (frontmatter, hashtags, etc.)

---

## 12) Dependency policy

### Core (recommended)
- Python stdlib only: `argparse`, `sqlite3`, `hashlib`, `json`, `re`, `pathlib`, `time`
- Zero heavy libs; works everywhere.

### Optional extras
- `kg[emb]`: HTTP client convenience (or just use stdlib `urllib.request`)
- `kg[ann]`: `hnswlib`
- `kg[mdx]`: richer markdown parsing (only if you later accept heavier deps)

---

## 13) Repo layout (suggested)
- `kgshred/`
  - `kgshred/cli.py`
  - `kgshred/db.py` (schema, pragmas, queries)
  - `kgshred/ids.py` (hashing + short_id collision handling)
  - `kgshred/parse_md.py` (streaming block parser)
  - `kgshred/graph.py` (node/edge creation helpers)
  - `kgshred/search_fts.py`
  - `kgshred/render.py` (full + filtered skeleton renderer)
  - `kgshred/embed/` (optional)
  - `kgshred/ann/` (optional)
- `tests/` (golden tests: ingest → render equals original)

---

## 14) Acceptance criteria (what “done” means)
- Ingest a large markdown file without exceeding memory proportional to file size (streaming).
- `kg render --doc X` outputs exactly the original content (byte-for-byte) when no filters are used.
- Every node has a unique 4-char code; collisions are resolved deterministically and persistently.
- `kg render --filter ...` returns full structure; only matching nodes are expanded; others are references that can be expanded later via `kg expand --id ABCD`.
- Keyword search returns correct node references quickly using FTS5.
- Semantic search works when configured, without being required for the tool to function.
