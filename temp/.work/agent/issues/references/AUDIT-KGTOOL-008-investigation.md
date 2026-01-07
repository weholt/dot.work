# AUDIT-KGTOOL-008 Investigation: KGTool Module Migration Gap Analysis

**Issue Reference:** AUDIT-KGTOOL-008
**Investigation started:** 2025-12-26T03:00:00Z
**Source:** `incoming/crampus/kgtool/`
**Destination:** NOT FOUND (potentially lost functionality)
**Priority:** CRITICAL

---

## Context

The kgtool module provides knowledge graph extraction and topic discovery functionality from markdown documentation. This is a **gap analysis** - the source was NOT migrated to the destination.

---

## Investigation Progress

### Phase 1: Source Structure Verification

**✅ Source exists at:** `incoming/crampus/kgtool/`
**❌ Destination:** NOT FOUND - kgtool was NOT migrated to dot-work

**Source files (Python):**
- `__init__.py`: Module exports
- `cli.py`: 2.4K - CLI interface with 3 commands
- `pipeline.py`: 11K - Core functionality (330 lines)

**Source Size:** ~13K total Python code

**Destination Status:** kgtool functionality does NOT exist in dot-work

---

### Phase 2: Functionality Analysis

**kgtool provides:**

1. **discover_topics** - Unsupervised topic discovery from markdown
   - KMeans clustering on TF-IDF vectors
   - Outputs topic_terms.json with discovered topics
   - CLI: `kgtool discover-topics --input INPUT --output OUTPUT --num-topics 5`

2. **build_graph** - Build knowledge graph from markdown document
   - TF-IDF vectorization (max_features=500)
   - YAKE keyphrase extraction
   - Topic classification with cosine similarity
   - NetworkX graph with nodes (headings) and edges (similarity)
   - Saves graph.json and individual node markdown files
   - CLI: `kgtool build --input INPUT --output OUTPUT --min-sim 0.3`

3. **extract_topic_context** - Extract context for a specific topic
   - Reads graph.json
   - Finds nodes matching topic (including neighbors optionally)
   - Writes topic context markdown file
   - CLI: `kgtool extract --topic TOPIC --graph GRAPH --output OUTPUT`

**Dependencies:**
- networkx (nx)
- yake (keyphrase extraction)
- rapidfuzz (fuzzy matching)
- sklearn (KMeans, TfidfVectorizer, cosine_similarity)

---

### Phase 3: Comparison with Existing knowledge_graph Module

**Existing knowledge_graph module (src/dot_work/knowledge_graph/):**
- cli.py: 23K - CLI interface
- config.py: 2K - Configuration
- db.py: 56K - Database operations (SQL with sqlite-vec)
- graph.py: 11K - Graph operations
- parse_md.py: 7K - Markdown parsing
- render.py: 9K - Rendering
- search_fts.py: 12K - Full-text search
- search_semantic.py: 14K - Semantic search (embeddings)
- embed/ directory - Embeddings

**kgtool vs knowledge_graph:**
- **kgtool**: Topic discovery using unsupervised learning (KMeans clustering, TF-IDF, YAKE)
- **knowledge_graph**: Full-featured knowledge graph with semantic search, embeddings, database, FTS

**Conclusion:** These are **different tools** with different purposes. kgtool provides unique topic discovery functionality that is NOT present in knowledge_graph.

---

### Phase 4: Test Coverage

**Source tests:**
- tests directory exists in source

---

## Investigation Conclusion

### Finding: kgtool NOT MIGRATED - Unique Functionality Lost

**`incoming/crampus/kgtool/`** was **NOT migrated** to dot-work.

### Assessment: ⚠️ FUNCTIONALITY GAP

**What was lost:**
1. **Topic discovery** - KMeans clustering for unsupervised topic discovery from markdown
2. **Knowledge graph building** - TF-IDF + YAKE + NetworkX for document graphs
3. **Context extraction** - Topic-based context extraction from graphs

**Unique capabilities not in knowledge_graph:**
- Unsupervised topic discovery (KMeans clustering)
- TF-IDF vectorization for topics
- YAKE keyphrase extraction
- NetworkX graph building from markdown
- Topic-based context extraction

### Integration Assessment

**Should kgtool be migrated?**

**Option 1: Migrate kgtool to dot-work**
- Add to src/dot_work/kgtool/ or integrate into knowledge_graph/
- Useful for topic discovery and context extraction
- ~13K Python code
- Dependencies: networkx, yake, rapidfuzz, sklearn

**Option 2: Document intentional exclusion**
- kgtool may have been superseded by knowledge_graph's semantic search
- Topic discovery via KMeans may not be needed with embeddings
- Document as intentionally excluded

**Recommendation:** This should be reviewed by the project maintainers to determine if topic discovery functionality is needed in dot-work.

### Gap Issues Created
1. **AUDIT-GAP-010 (HIGH)**: kgtool NOT migrated - unique topic discovery functionality lost
  - Decision needed: migrate or document intentional exclusion

---

## Recommendation

This is a **significant gap** in functionality. kgtool provides unique topic discovery capabilities that are NOT present in the existing knowledge_graph module.

**Suggested Action:** Create AUDIT-GAP-010 issue to track this gap and require a decision on whether to migrate kgtool or document intentional exclusion.

