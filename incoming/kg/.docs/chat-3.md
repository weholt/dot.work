# Segmentation: central repository with cross-project reuse (recommended)

## 1) Use one central DB, segment by “collections”
Single SQLite DB works well for reuse. Treat “project” as a *collection*, not a separate database.

### Why
- shared content remains one canonical node set
- projects become saved views over the same nodes (no duplication)
- you can attach different tags/notes/derived summaries per project without mutating the source nodes

## 2) Add first-class concepts: project, topic, collection, and scope

### Entities
- **Document**: imported raw text
- **Node**: span-based block (heading/paragraph/etc.)
- **Project**: a named collection with rules + defaults (retrieval budgets, preferred docs, etc.)
- **Topic**: reusable label (can span projects)
- **Collection**: generic group type (project is a collection; you may also have “knowledgebase”, “customer-X”, “specs”, etc.)

### Relationships
- `collection_contains(collection -> node|doc)` (membership)
- `topic_applies(topic -> node|doc)` (tagging)
- `derived_from(derived_node -> node)` (provenance)
- `ref(node -> node)` (inline references)
- optional: `alias(topic -> topic)` (synonyms)

## 3) DB schema additions (minimal)

### Tables
- `collections(collection_id TEXT PK, kind TEXT, name TEXT UNIQUE, meta_json TEXT)`
- `collection_members(collection_id TEXT, member_type TEXT, member_pk INT, PRIMARY KEY(collection_id, member_type, member_pk))`
  - `member_type`: `doc|node`
- `topics(topic_id TEXT PK, name TEXT UNIQUE, meta_json TEXT)`
- `topic_links(topic_id TEXT, target_type TEXT, target_pk INT, weight REAL, meta_json TEXT, PRIMARY KEY(topic_id, target_type, target_pk))`
- `project_settings(collection_id TEXT PK, defaults_json TEXT)` (only if kind=project)

Keep `nodes` canonical; don’t clone per project.

## 4) How segmentation is created

### A) Explicit assignment (fast, deterministic)
CLI examples:
- `kg project create myproj`
- `kg project add myproj docs/**/*.md`
- `kg topic add "event-sourcing" --doc docs/backoffice.md`
- `kg topic add "cqrs" --id ABCD`

This is the most reliable for “high signal” organization.

### B) Rule-based auto-membership (good UX, still deterministic)
Allow collections to have rules:
- path prefixes (`docs/specs/**`)
- doc frontmatter fields (`project: backoffice`)
- heading prefixes (`# Backoffice:`)
- tags/keywords
- source repo name

Store rules in `collections.meta_json`. Provide:
- `kg project rules set myproj --json '<rules>'`
- `kg project sync myproj` (recompute membership)

### C) LLM-assisted labeling (optional, with provenance)
Use the LLM to suggest topics/collections:
- `kg classify --doc <id> --suggest-topics --suggest-projects`
- Tool proposes:
  - topics with confidence + supporting node IDs
  - project candidates (or just “tags”)
You choose to accept/apply:
- `kg apply --plan plan.json`

Never silently mutate segmentation.

## 5) Retrieval scoping: how searches respect projects/topics

### Scope model
All queries accept a scope filter:
- `--project myproj` (collection membership)
- `--topic event-sourcing`
- `--docs <glob|ids>`
- `--exclude-topic draft`
- `--include-shared` (include nodes tagged as shared/core)

Implementation:
- retrieval candidate set = intersection of:
  - (FTS / semantic hits)
  - membership constraints
  - topic constraints

### Practical defaults
- By default, `kg ask` searches “global” (all content).
- `kg ask --project myproj` narrows.
- `kg ask --project myproj --include-topics shared,core` pulls in reusable knowledge.

## 6) Reuse across projects: “shared topics” + “core collections”

### Approach
- Create collections like:
  - `core` (architecture, practices, templates)
  - `platform` (infra, CI/CD, deployment)
- Tag nodes with topics:
  - `shared`, `patterns`, `guidelines`, `event-sourcing`
Then projects reference those in their rules, e.g.:
- project includes:
  - its own docs by path
  - plus `collection=core`
  - plus `topic=event-sourcing`

This avoids duplication while keeping project views coherent.

## 7) Handling conflicts and evolution
- Canonical nodes never change unless the underlying document changes.
- Project/topic annotations are additive metadata, can be versioned:
  - `annotations(annotation_id, target, project_id, author, created_at, json)`
- Derived summaries are nodes of kind `derived`, always linked back with `derived_from`.

## 8) CLI surface (suggested)

### Projects / collections
- `kg project create <name>`
- `kg project add <name> <paths...>`
- `kg project rules set <name> --json '<rules>'`
- `kg project sync <name>`
- `kg project ls`
- `kg project rm <name>`

### Topics
- `kg topic create <name>`
- `kg topic tag <name> --id ABCD`
- `kg topic tag <name> --doc <doc_id>`
- `kg topic ls [--project <name>]`
- `kg topic untag <name> --id ABCD`

### Search / ask with scope
- `kg search --q "<fts>" [--project X] [--topic Y]`
- `kg ask --q "<nl>" [--project X] [--topic Y] [--include-topics shared]`

## 9) Recommendation
Use one central repository (single DB) with:
- projects as collections + rules,
- topics as reusable labels,
- scope-aware retrieval and rendering.

This matches “content has value across projects” while keeping the system fast and minimal.

## Note on the uploaded reference
The previously uploaded reference file is no longer available in this session. Re-upload if you want me to align this segmentation plan with the specific structures in that codebase.
