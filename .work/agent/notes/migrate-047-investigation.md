# MIGRATE-047 Investigation: Container Provision Module

**Started:** 2025-12-23T01:15:00Z
**Issue:** Create container provision module structure in dot-work

## Source Analysis: incoming/crampus/repo-agent/src/repo_agent/

Files found:
- `cli.py` (6705 bytes) - Typer CLI with commands: run, init, validate
- `core.py` (29101 bytes) - Core Docker/Git logic (largest file)
- `__init__.py` (525 bytes) - Package initialization
- `templates.py` (1573 bytes) - Instruction templates
- `validation.py` (2577 bytes) - Frontmatter validation

## Target Status: src/dot_work/container/
Directory does NOT exist - needs to be created

## Migration Plan
1. Create src/dot_work/container/ directory
2. Create src/dot_work/container/provision/ subdirectory
3. Copy all 5 files from repo_agent to container/provision/
4. Update file headers
5. Create package __init__.py files
6. Add module README.md

## Next Steps
- Create directory structure
- Copy source files
- Update focus.md progress