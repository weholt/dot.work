# Tasks

Example task file for the dot-work harness.

## Core Tasks
- [ ] T-001: Create a python module `src/app.py` that exposes `add(a,b)` and `mul(a,b)` with type hints.
- [ ] T-002: Add unit tests for `add` and `mul` using pytest.
- [ ] T-003: Add `pyproject.toml` with minimal config to run `pytest -q`.

## Documentation
- [ ] D-001: Write README.md with usage examples.
- [ ] D-002: Add docstrings to all public functions.

## Notes
- Tasks are processed in order (first unchecked task is selected)
- When a task is complete, change `[ ]` to `[x]`
- Add evidence as indented sub-bullet: `  - Evidence: pytest -q passed`
- If blocked, add: `  - BLOCKED: reason` (don't mark as done)
