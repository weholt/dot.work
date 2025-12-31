# Agent Focus
Last updated: 2025-12-31T11:20:00Z

## Previous
- Issue: Commit shortlist issues and installer fixes
- Completed: 2025-12-30T22:05:00Z
- Outcome: Committed changes (857535c), generated baseline with pre-existing issues

- Issue: ENH-025@4a8f2c - Global YAML frontmatter configuration for prompts
- Completed: 2025-12-30T22:55:00Z
- Outcome: Created global.yml with default environment configs, added deep merge to canonical.py, added tests, fixed issue-readiness.prompt.md

- Issue: ENH-026@5b9g3d - Rename .prompt.md files to .md
- Completed: 2025-12-30T23:15:00Z
- Outcome: Renamed 60+ prompt files, updated global.yml, canonical.py, installer.py, wizard.py, environments.py; all 44 canonical tests pass

- Issue: REFACTOR-003@f4a8b2 - Remove duplicate environment frontmatter from prompts
- Completed: 2025-12-30T23:45:00Z
- Outcome: Removed 28-line duplicate environments section from all 22 prompt files, fixed copilot suffix in global.yml, updated wizard.py; all 44 tests pass

## Current
- Issue: DOGFOOD-001@foa1hu - Rename init-work to init-tracking
- Started: 2025-12-31T11:20:00Z
- Status: in-progress
- Phase: Implementation
- Progress:
  - [x] Investigation complete (findings in issue)
  - [ ] Rename command in cli.py
  - [ ] Update CLI help text
  - [ ] Update documentation
  - [ ] Run validation
- Source: critical.md (P0)

## Next
- Issue: TBD (select from high.md after DOGFOOD-001 completes)
