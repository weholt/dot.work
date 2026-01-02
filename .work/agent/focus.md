# Agent Focus
Last updated: 2026-01-02T17:00:00Z

## Previous
- Issue: FEAT-026@d0e6f2 - Context and file injection for Dockerized OpenCode containers
- Completed: 2026-01-02T14:30:00Z
- Outcome: Complete implementation (runtime context injection with auto-detection, 27 tests passing, documentation updated)

- Issue: FEAT-027@e1f7g3 - Runtime URL-based context injection for OpenCode containers
- Completed: 2026-01-02T14:50:00Z
- Outcome: Complete implementation (HTTPS URL fetching, ZIP extraction, caching, 30 tests passing)

- Issue: FEAT-029@j6k2l8 - Create agent-loop orchestrator prompt for infinite autonomous operation
- Completed: 2026-01-02T16:30:00Z
- Outcome: Complete implementation (agent-orchestrator.md prompt, state persistence, 26 tests passing)

- Issue: SPLIT-100@a1b2c3 - Plugin infrastructure foundation
- Completed: 2026-01-02T17:00:00Z
- Outcome: Complete implementation (plugins.py, discover/register functions, entry-points in pyproject.toml, 11 tests passing)

## Current
- Issue: SPLIT-101@b2c3d4 - Extract high-priority submodules (dot-issues, dot-kg, dot-review)
- Status: COMPLETED - All 3 plugins extracted to EXPORTED_PROJECTS/
- Issue: SPLIT-102@c3d4e5 - Extract medium-priority submodules (6 remaining modules)
- Status: COMPLETED - All 6 plugins extracted to EXPORTED_PROJECTS/
- Source: shortlist.md

## Next
- Commit extraction changes to git
- Work on SPLIT-103: Integration testing and core package updates

## Ralph Loop Status
**Iteration 11 Progress:**
- Completed: SPLIT-100 (plugin infrastructure), SPLIT-101 (high-priority extractions), SPLIT-102 (medium-priority extractions)
- Plugin infrastructure: src/dot_work/plugins.py with discover/register functions
- Entry points: [project.entry-points."dot_work.plugins"] added to pyproject.toml
- CLI refactoring: cli.py uses register_all_plugins(app) for dynamic command registration
- `dot-work plugins` command: Shows installed plugins (currently none, but infrastructure ready)
- Extraction script: scripts/extract_plugin.py automates extraction with validation
- All 9 plugins extracted:
  - High priority: dot-issues, dot-kg, dot-review
  - Medium priority: dot-container, dot-git, dot-harness, dot-overview, dot-python, dot-version
- Extraction location: EXPORTED_PROJECTS/ folder in project root
- Code quality: ruff ✓, mypy ✓

## Notes
- Plugin infrastructure complete with discover_plugins() and register_plugin_cli() functions
- Extraction script validated: SHA256 hashes calculated, file counts verified, imports rewritten
- Each extracted package has:
  - src/<package>/ with rewritten imports (dot_work.X → dot_X)
  - tests/unit/ and tests/integration/ with structure preserved
  - pyproject.toml with dependencies, entry-points, and build config
  - README.md with installation and usage instructions
  - .github/workflows/ci.yml for CI
  - CLI_GROUP = "<command>" in __init__.py for plugin registration
- Next steps: Integration testing (SPLIT-103) to verify plugins work correctly with dot-work core
