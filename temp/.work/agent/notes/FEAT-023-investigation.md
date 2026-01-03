# FEAT-023 Investigation: Agent Skills Support

Issue: FEAT-023@a7b3c9
Started: 2026-01-01T15:30:00Z

## Problem Statement
dot-work needs to integrate Agent Skills specification for reusable agent capability packages. Currently there is no mechanism for discovering, validating, and injecting skills into agent contexts.

## Requirements (from skills_spec.md)
1. Create data models (SkillMetadata, Skill) with validation
2. Implement SKILL.md parser with YAML frontmatter extraction
3. Build validator with error collection (name format, description length)
4. Implement filesystem discovery (.skills/, ~/.config/dot-work/skills/, bundled)
5. Generate `<available_skills>` XML for agent prompts
6. Add CLI commands: dot-work skills list/validate/show/prompt/install
7. Integrate with harness for session injection

## Affected Files (per spec)
- Create: src/dot_work/skills/__init__.py, models.py, parser.py, validator.py, discovery.py, prompt_generator.py
- Modify: src/dot_work/harness/ (integration point)
- Create: tests/unit/skills/ (test suite)
- Create: tests/fixtures/skills/ (test fixtures)

## Implementation Plan (from spec)
1. models.py - Data classes with validation in __post_init__
2. parser.py - Frontmatter extraction and parsing
3. validator.py - Full validation with error collection
4. discovery.py - Filesystem scanning
5. prompt_generator.py - XML generation
6. CLI commands in cli.py
7. Integration with harness/

## Memory.md Context
Key patterns to follow:
- Google-style docstrings
- Type annotations on all functions
- pathlib.Path for file operations
- dataclass.replace() for immutable updates
- __post_init__ for dataclass field validation

## Existing Patterns to Mirror
- CanonicalPromptParser for parser pattern
- Existing prompts/ structure for reference
- Typer CLI patterns
- pytest fixtures for testing

## Validation Plan (from issue)
```bash
# Unit tests
uv run pytest tests/unit/skills/ -v --cov=src/dot_work/skills --cov-report=term-missing

# CLI smoke test
uv run dot-work skills list
uv run dot-work skills validate tests/fixtures/skills/valid
uv run dot-work skills show test-skill

# Integration test
uv run pytest tests/integration/skills/test_skill_injection.py -v
```

## Acceptance Criteria
- [ ] Skill discovery finds valid skills in search paths
- [ ] Parser extracts frontmatter and content with 100% coverage
- [ ] Validator rejects invalid names (format check) and empty descriptions
- [ ] CLI list command shows discovered skills with name/description
- [ ] CLI validate reports specific validation errors
- [ ] generate_skills_prompt() produces valid XML output
- [ ] Harness integration injects skills into agent sessions
- [ ] Unit tests for all modules (≥75% coverage)
- [ ] Integration test for end-to-end skill discovery and injection
