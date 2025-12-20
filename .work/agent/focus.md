# Agent Focus
Last updated: 2024-12-21

## Previous
- Issue: DOC-001@a7f3b2 – README documents 2 prompts but package contains 12 (P1)
- Completed: 2024-12-20
- Outcome: README now documents all 12 prompts in 4 categories

## Current
- Issue: None (ready for next issue)
- Status: idle

## Next
- Issue: MIGRATE-001@a1b2c3 – Create dot_work/review subpackage structure (P1)
- Source: migration-review.md
- Reason: First step in integrating agent-review as `dot-work review` command

## Migration Plan
Created `.work/agent/issues/migration-review.md` with 12 issues to integrate incoming/review:
| ID | Title | Priority | Dependencies |
|----|-------|----------|--------------|
| MIGRATE-001 | Create review subpackage structure | P1 | - |
| MIGRATE-002 | Update import paths | P1 | 001 |
| MIGRATE-003 | Copy static assets and templates | P1 | 001 |
| MIGRATE-004 | Add new dependencies | P1 | - |
| MIGRATE-005 | Integrate review CLI commands | P1 | 001-004 |
| MIGRATE-006 | Migrate unit tests | P1 | 002 |
| MIGRATE-007 | Add integration tests | P2 | 006 |
| MIGRATE-008 | Update Python version to 3.11+ | P1 | - |
| MIGRATE-009 | Update storage path to .work/reviews/ | P2 | 002 |
| MIGRATE-010 | Add README documentation | P2 | 005 |
| MIGRATE-011 | Add CLI tests for review command | P1 | 005 |
| MIGRATE-012 | Clean up incoming/review | P3 | all |
