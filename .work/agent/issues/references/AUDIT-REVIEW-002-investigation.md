# AUDIT-REVIEW-002 Investigation: Review Module Migration Validation

**Issue Reference:** AUDIT-REVIEW-002
**Investigation started:** 2025-12-26T00:25:00Z
**Source:** `incoming/crampus/repo-agent/`
**Destination:** `src/dot_work/review/`
**Migration Range:** MIGRATE-001 through MIGRATE-012 (12 issues)

---

## Context

The repo-agent module is a code review system with Docker integration, template support, and Git operations.

---

## Investigation Progress

### Phase 1: Source Structure Verification

**✅ Source exists at:** `incoming/crampus/repo-agent/`
**✅ Destination exists at:** `src/dot_work/review/`

**Source files (Python only):**
- `__init__.py`: 525 bytes
- `cli.py`: 6.6K - Typer CLI with run/init/validate commands
- `core.py`: 29K - Main Docker agent execution logic
- `templates.py`: 1.6K - Default instruction templates
- `validation.py`: 2.6K - Frontmatter validation

**Destination files (Python only):**
- `__init__.py`: 270 bytes
- `config.py`: 974 bytes - Configuration management
- `exporter.py`: 2.5K - Export review comments to markdown
- `git.py`: 8.0K - Git operations and diff parsing
- `models.py`: 1.3K - Pydantic data models
- `server.py`: 5.6K - FastAPI web server
- `storage.py`: 2.8K - Comment storage (JSONL)

---

### 🔴 CRITICAL FINDING: Different Codebases

**Source (`repo-agent`) is a CLI Docker-based LLM agent runner:**
- Commands: `repo-agent run`, `repo-agent init`, `repo-agent validate`
- Reads markdown instruction files with YAML frontmatter
- Builds and runs Docker containers
- Runs code tools (OpenCode, Claude, etc.) in containers
- Auto-commits and creates PRs
- Template system for instruction files
- Validation logic for frontmatter

**Destination (`review`) is a code review comment management system:**
- FastAPI web server for review UI
- JSONL-based comment storage
- Git diff parsing
- Export to markdown for agents
- NO CLI interface at all
- NO Docker functionality
- NO agent runner

**VERDICT: These are NOT the same codebase migrated. They are completely different tools that happen to both relate to "code review" but serve entirely different purposes.**

---

### Phase 2: Feature Parity Analysis

| Feature | Source (repo-agent) | Destination (review) | Status |
|---------|---------------------|---------------------|--------|
| CLI interface | ✅ Typer-based (run/init/validate) | ❌ None | **NOT MIGRATED** |
| Docker integration | ✅ Full Docker build/run | ❌ None | **NOT MIGRATED** |
| Agent execution | ✅ Container-based runner | ❌ None | **NOT MIGRATED** |
| Template system | ✅ DEFAULT_INSTRUCTIONS_TEMPLATE | ❌ None | **NOT MIGRATED** |
| Validation logic | ✅ validate_instructions() | ❌ None | **NOT MIGRATED** |
| Git operations | ✅ PR creation, branch management | ✅ Diff parsing | Different purpose |
| Storage | ❌ N/A | ✅ JSONL comment storage | Different purpose |
| Web server | ❌ N/A | ✅ FastAPI UI | Different purpose |

---

### Phase 3: Test Coverage

**Source tests (7 files):**
- `test_cli.py` - CLI command tests
- `test_coderabbit_config.py` - OpenCode config tests
- `test_core.py` - Core functionality tests
- `test_integration.py` - Integration tests
- `test_templates.py` - Template tests
- `test_validation.py` - Validation tests
- `conftest.py` - Test fixtures

**Destination tests (5 files, 56 tests, ALL PASSING):**
- `test_review_config.py` - Config tests
- `test_review_exporter.py` - Exporter tests
- `test_review_git.py` - Git operations tests
- `test_review_models.py` - Model tests
- `test_review_storage.py` - Storage tests

**VERDICT: Zero tests from source migrated. The destination has its own test suite for its different functionality.**

---

### Phase 4: Quality Metrics (Destination)

| Metric | Result |
|--------|--------|
| Type checking (mypy) | ✅ **0 errors** |
| Linting (ruff) | ✅ **0 errors** |
| Unit tests | ✅ **56/56 passing** |
| Documentation | ❓ README not checked yet |

---

### Phase 5: Source Analysis Details

**Source CLI commands:**
```python
# repo-agent run - Execute agent with instruction file
@app.command()
def run(instructions, repo_url, branch, docker_image, ...)

# repo-agent init - Generate instruction template
@app.command()
def init(output, force)

# repo-agent validate - Validate instruction file
@app.command()
def validate(instructions)
```

**Source core functionality (core.py - 29K):**
- `RunConfig` dataclass with 20+ configuration fields
- `run_from_markdown()` - Main entry point
- `_resolve_config()` - Merge frontmatter + CLI overrides
- `_docker_build_if_needed()` - Build Docker image
- `_build_docker_run_cmd()` - Construct Docker command
- `_generate_inner_script()` - Bash script for container
- Supports SSH auth, GitHub API, OpenCode integration

**Source templates.py:**
- `DEFAULT_INSTRUCTIONS_TEMPLATE` - Full markdown template with frontmatter

**Source validation.py:**
- `validate_instructions()` - Validate frontmatter fields
- `REQUIRED_FIELDS` - repo_url, model
- `TOOL_REQUIRED_FIELDS` - name, entrypoint
- Checks strategy, Dockerfile existence, auth config

---

### Phase 6: Destination Analysis Details

**Destination modules (different purpose):**
- `config.py` - Environment-based configuration for review server
- `models.py` - Pydantic models (DiffLine, DiffHunk, FileDiff, ReviewComment)
- `git.py` - Git diff parsing and file operations
- `storage.py` - JSONL-based comment storage
- `exporter.py` - Export comments to agent-friendly markdown
- `server.py` - FastAPI web server with review UI

**Destination provides:**
- Web-based code review interface
- Comment management on diff lines
- Context-aware comment display
- Export for downstream agent processing

---

## Investigation Conclusion

### Finding: NOT A MIGRATION - Different Codebases

**`incoming/crampus/repo-agent/`** was **NOT migrated** to `src/dot_work/review/`.

These are two completely different tools:
1. **repo-agent** - CLI Docker-based LLM agent runner
2. **review** - Web-based code review comment management system

### Implications

1. **MIGRATE-001 through MIGRATE-012 issues** claim to migrate repo-agent → review, but this is **INCORRECT**

2. **repo-agent functionality is MISSING from dot-work:**
   - No CLI Docker agent runner
   - No instruction template system
   - No frontmatter validation
   - No agent execution in containers

3. **The review module appears to be original development** for dot-work, not a migration

4. **Decision needed:**
   - Should repo-agent be migrated to dot-work?
   - Or was it intentionally excluded?
   - Does dot-work need this functionality elsewhere?

### Quality Assessment of Destination (review)

**Positive:**
- ✅ Zero type errors
- ✅ Zero lint errors
- ✅ 56 unit tests passing
- ✅ Clean code structure

**Unrelated to source:**
- Completely different architecture
- Different purpose
- No shared functionality

---

## Recommendations

### Gap Issues to Create

1. **AUDIT-GAP-006 (CRITICAL): repo-agent NOT migrated**
   - The repo-agent CLI tool was NOT migrated to review
   - These are different codebases with different purposes
   - Decision needed: migrate or document intentional exclusion

2. **AUDIT-GAP-007 (HIGH): Missing repo-agent functionality in dot-work**
   - No CLI Docker agent runner
   - No instruction template system
   - No frontmatter validation
   - If this was intentional, document why

### Files Not Migrated (from source)

- `cli.py` - Entire CLI interface
- `core.py` - All Docker agent execution logic
- `templates.py` - Template system
- `validation.py` - Validation logic
- `tests/test_cli.py` - CLI tests
- `tests/test_core.py` - Core tests
- `tests/test_templates.py` - Template tests
- `tests/test_validation.py` - Validation tests
- `tests/test_integration.py` - Integration tests
- `Dockerfile` - Container definition
- `Dockerfile.smart-alpine` - Alternative container
- `README.md` - Documentation
