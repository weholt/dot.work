# Investigation: FEAT-002@d8f4e2 — SQLite Database Schema

Investigation started: 2024-12-20

## Schema from chat.md Section 4

### Tables

1. **documents**
   - `doc_id TEXT PRIMARY KEY` — Document identifier
   - `source_path TEXT` — Original file path
   - `sha256 TEXT` — Content hash
   - `created_at INT` — Unix timestamp
   - `raw BLOB` — Raw document bytes

2. **nodes**
   - `node_pk INTEGER PRIMARY KEY` — Auto-increment internal PK
   - `short_id TEXT UNIQUE` — 4-char human-friendly ID
   - `full_id TEXT UNIQUE` — Full blake2s hash
   - `doc_id TEXT` — FK to documents
   - `kind TEXT` — Node type (heading, paragraph, code_fence, etc.)
   - `level INT` — Heading level (1-6) or NULL
   - `title TEXT` — Heading text or NULL
   - `start INT` — Byte offset start
   - `end INT` — Byte offset end
   - `parent_node_pk INT` — FK to parent node
   - `meta_json TEXT` — Additional metadata as JSON

3. **edges**
   - `src_node_pk INT` — Source node
   - `dst_node_pk INT` — Destination node
   - `type TEXT` — Edge type (contains, next, ref)
   - `weight REAL` — Edge weight (default 1.0)
   - `meta_json TEXT` — Additional metadata
   - `PRIMARY KEY (src_node_pk, dst_node_pk, type)`

4. **fts_nodes** (FTS5 virtual table)
   - `title` — Indexed
   - `text` — Indexed (node content)
   - `short_id UNINDEXED` — For reference, not search

5. **schema_version** (for migrations)
   - `version INT PRIMARY KEY`
   - `applied_at INT`

### PRAGMAs
- `journal_mode=WAL`
- `synchronous=NORMAL`
- `temp_store=MEMORY`

### Optional (Phase 2)
- `embeddings(node_pk INT, model TEXT, dims INT, vec BLOB, PRIMARY KEY(node_pk, model))`

## Implementation Approach

1. **Database class** with context manager for transactions
2. **Schema initialization** on first connection
3. **CRUD operations** for documents, nodes, edges
4. **FTS5 triggers** to keep fts_nodes in sync
5. **Batch insert** support for performance

## Files to Create
- `src/kgshred/db.py` — Database module
- `tests/unit/test_db.py` — Unit tests
- `tests/integration/test_db_integration.py` — Integration tests

## Data Classes
- `Document` — Document record
- `Node` — Node record  
- `Edge` — Edge record
