---
id: "SDA-002@d2e3f4"
title: "Document KG database location and schema"
description: "dot-work kg stores data in SQLite - location and schema undocumented"
created: 2025-12-31
section: "documentation"
tags: [documentation, knowledge-graph, storage, schema, spec-delivery-audit]
type: docs
priority: medium
status: proposed
references:
  - .work/agent/issues/references/SDA-001-spec-delivery-audit-report.md
  - src/dot_work/knowledge_graph/db.py
  - docs/db-issues/
---

### Problem
`dot-work kg` stores data in SQLite, but the location and schema are not documented.

**Undocumented:**
- Where is the database stored?
- What is the schema?
- How to migrate/copy knowledge graphs?
- How to backup/restore?

### Affected Files
- Documentation files (README.md, docs/)
- `src/dot_work/knowledge_graph/db.py` (implementation reference)

### Importance
**MEDIUM**: Users cannot manage knowledge graph data without documentation:
- Cannot backup knowledge graphs
- Cannot migrate between projects
- Cannot understand data structure

### Proposed Solution
Add documentation section to tooling-reference.md:
```markdown
## Knowledge Graph Storage

Database location: `.work/kg/graph.db`

### Schema

The database contains the following tables:
- `documents` - Ingested markdown documents
- `nodes` - Text fragments/chunks
- `edges` - Relationships between nodes
- `embeddings` - Vector embeddings for semantic search
- `collections` - Document groupings

### Backup

```bash
# Backup database
cp .work/kg/graph.db backup/kg-backup-$(date +%Y%m%d).db

# Restore database
cp backup/kg-backup-20251231.db .work/kg/graph.db
```

### Migration

```bash
# Export knowledge graph
dot-work kg export > backup.json

# Import knowledge graph (if supported)
dot-work kg ingest --import backup.json
```
```

### Acceptance Criteria
- [ ] Database location documented in tooling-reference.md
- [ ] Schema overview documented (tables and relationships)
- [ ] Backup procedure documented
- [ ] Migration procedure documented (if supported)

### Notes
Found during spec delivery audit SDA-001. Implementation is solid, only documentation is missing.
