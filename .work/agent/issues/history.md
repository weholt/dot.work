# Issue History (Append-Only)

Completed and closed issues are archived here.

---

## 2024-12-21: agent-review Migration Complete

Successfully migrated the standalone `agent-review` project into `dot_work.review` subpackage.

| ID | Title | Completed |
|----|-------|-----------|
| MIGRATE-001@a1b2c3 | Create review subpackage structure | 2024-12-21 |
| MIGRATE-002@b2c3d4 | Update import paths | 2024-12-21 |
| MIGRATE-003@c3d4e5 | Copy static assets and templates | 2024-12-21 |
| MIGRATE-004@d4e5f6 | Add new dependencies | 2024-12-21 |
| MIGRATE-005@e5f6a7 | Integrate review CLI commands | 2024-12-21 |
| MIGRATE-006@f6a7b8 | Migrate unit tests (56 tests) | 2024-12-21 |
| MIGRATE-007@a7b8c9 | Add integration tests (10 tests) | 2024-12-21 |
| MIGRATE-008@b8c9d0 | Update Python version to 3.11+ | 2024-12-21 |
| MIGRATE-009@c9d0e1 | Update storage path to .work/reviews/ | 2024-12-21 |
| MIGRATE-010@d0e1f2 | Add README documentation | 2024-12-21 |
| MIGRATE-011@e1f2a3 | Add CLI tests for review command | 2024-12-21 |
| MIGRATE-012@f2a3b4 | Clean up incoming/review | 2024-12-21 |

### Summary
- **Source**: `incoming/review/` (standalone agent-review project)
- **Target**: `src/dot_work/review/` subpackage
- **Tests Added**: 66 (56 unit + 10 integration)
- **Final Coverage**: 68%
- **Python Version**: Upgraded from 3.10+ to 3.11+
- **Key Commits**: 9189f2a, de4b01c, df67cdc, d092826

### Features Added
- `dot-work review start` - Web-based code review UI
- `dot-work review export` - Export comments to markdown
- `dot-work review clear` - Clear review data

---
