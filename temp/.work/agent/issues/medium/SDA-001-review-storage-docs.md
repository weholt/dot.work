---
id: "SDA-001@c1d2e3"
title: "Document review storage location and format"
description: "dot-work review stores data in .work/reviews/ - location and format undocumented"
created: 2025-12-31
section: "documentation"
tags: [documentation, review, storage, spec-delivery-audit]
type: docs
priority: medium
status: proposed
references:
  - .work/agent/issues/references/SDA-001-spec-delivery-audit-report.md
  - src/dot_work/review/storage.py
  - src/dot_work/review/cli.py
---

### Problem
`dot-work review` stores data somewhere, but the location and format are not documented.

**Undocumented:**
- Where are reviews stored?
- What is the review ID format?
- How to list all reviews?
- How to delete old reviews?

### Affected Files
- Documentation files (README.md, docs/)
- `src/dot_work/review/storage.py` (implementation reference)

### Importance
**MEDIUM**: Users cannot manage review data without knowing storage location:
- Cannot clean up old reviews
- Cannot backup review data
- Cannot understand review lifecycle

### Proposed Solution
Add documentation section to tooling-reference.md:
```markdown
## Review Storage

Reviews are stored in: `.work/reviews/`

Review ID format: `YYYYMMDD-HHMMSS` (timestamp)

## Managing reviews

# List all reviews
dot-work review list

# Export a review
dot-work review export <review-id>

# Delete old reviews
rm .work/reviews/<review-id>.json
```

### Acceptance Criteria
- [ ] Review storage location documented in tooling-reference.md
- [ ] Review ID format documented
- [ ] Listing/retrieving reviews documented
- [ ] Example commands provided

### Notes
Found during spec delivery audit SDA-001. This is a documentation-only gap with no implementation work needed.
