# Baseline Report
Generated: 2024-12-21
Commit: d11175e (post-FEAT-012)
Branch: iteration-2

## Build Status
- Status: PASSING (7/8 gates)
- Failed: Security Check (bandit not installed)
- Execution time: 5.99s

## Linting
- Total errors: 0
- Total warnings: 0

## Formatting
- Status: compliant

## Type Checking
- Total errors: 0
- Total warnings: 0

## Tests
- Unit tests: 341 passed, 0 failed
- Integration tests: 10 (deselected)
- Execution time: 3.51s

## Coverage
- Overall: 84.98%

### Coverage by File
| File | Coverage | Uncovered Lines |
|------|----------|-----------------|
| `src/kgshred/__init__.py` | 100% | — |
| `src/kgshred/config.py` | 96% | 91 |
| `src/kgshred/db.py` | 95% | 175, 185, 207, 496-500, 517-527, 681 |
| `src/kgshred/embed/__init__.py` | 100% | — |
| `src/kgshred/embed/base.py` | 91% | 72, 77, 82 |
| `src/kgshred/embed/factory.py` | 100% | — |
| `src/kgshred/embed/ollama.py` | 88% | 95-98, 116 |
| `src/kgshred/embed/openai.py` | 64% | 92-98, 121-128, 132-146, 152, 161 |
| `src/kgshred/graph.py` | 95% | 252, 335 |
| `src/kgshred/ids.py` | 100% | — |
| `src/kgshred/parse_md.py` | 99% | 128 |
| `src/kgshred/render.py` | 66% | 80, 108, 164-178, 199-211, 216-226, etc. |
| `src/kgshred/search_fts.py` | 95% | 75, 189, 194-195, 338, 395 |
| `src/kgshred/search_semantic.py` | 56% | 103, 115, 130-132, 146, 157, 196, 251-252, 273-308, 333-365 |

## Security
- Critical: 0
- High: 0
- Medium: 0

## Files Summary
- Total Python files: 14 (src/kgshred/)
- Total test files: 13 (tests/unit/) — +1 test_search_scope.py
- Clean files (100% lint/type): All

## Test Warnings
- 88 ResourceWarnings about unclosed database connections (test cleanup issue, not source bug)

## Issue Tracker State
| Priority | Count | Notes |
|----------|-------|-------|
| Critical (P0) | 0 | — |
| High (P1) | 0 | — |
| Medium (P2) | 4 | FEAT-013–016 remaining |
| Low (P3) | 1 | FEAT-017 |
| **Total** | **5** |

## Completed This Iteration
- FEAT-009@c8b2e5: Embedder Interface & HTTP Backends
- FEAT-010@d1e5f2: Semantic Search with Brute-Force Cosine Similarity
- FEAT-011@e1d4a7: Collections & Projects Schema
- FEAT-012@f2e5b8: Scope-Aware Retrieval

---

*Baseline updated after FEAT-012 completion.*
