# MIGRATE-019 Investigation

**Issue**: MIGRATE-019@a3b9c8 - Migrate kg tests to dot-work test suite
**Investigation started**: 2025-12-21T22:05:00Z

### Current State
- **Source**: `incoming/kg/tests/` - Contains full test suite for kgshred
- **Target**: `tests/unit/knowledge_graph/` and `tests/integration/knowledge_graph/`
- **Partially migrated**: test_config.py, test_db.py, test_ids.py already present
- **Issue**: test_config.py.bak is disabled due to import errors

### Source Test Analysis
From `incoming/kg/tests/`:

**Unit tests (12 files):**
- test_cli_project_topic.py - CLI commands for project/topic management
- test_collections.py - Collection utilities
- test_config.py - Configuration module tests
- test_db.py - Database operations 
- test_embed.py - Embedding functionality
- test_graph.py - Graph building from Markdown
- test_ids.py - ID generation (already migrated)
- test_parse_md.py - Markdown parsing
- test_render.py - Document rendering
- test_search_fts.py - Full-text search
- test_search_scope.py - Search scoping
- test_search_semantic.py - Semantic search

**Integration tests (2 files):**
- test_build_pipeline.py - End-to-end pipeline
- test_db_integration.py - Database integration

**Fixtures/Support:**
- conftest.py - Shared test fixtures
- Test data and mock setup

### Import Issues Found
**test_config.py.bak** has import errors:
```python
from dot_work.knowledge_graph.config import ConfigError, ensure_db_directory, get_db_path, validate_path
```

But current config.py only exports:
```python
from dot_work.knowledge_graph.config import get_db_path
```

**Missing functions in config.py:**
- ConfigError (exception class)
- ensure_db_directory() (directory creation) 
- validate_path() (path validation)

### Required Work Plan
1. **Fix config.py**: Add missing functions that tests expect
2. **Migrate remaining unit tests**: 9 files still need migration
3. **Update all imports**: Change `from kgshred.*` to `from dot_work.knowledge_graph.*`
4. **Migrate integration tests**: 2 files for end-to-end testing
5. **Fix conftest.py**: Merge/import fixtures appropriately
6. **Verify all tests pass**: `uv run pytest tests/unit/knowledge_graph/ -v`

### Acceptance Criteria Review
- [ ] All kg unit tests in `tests/unit/knowledge_graph/`
- [ ] All kg integration tests in `tests/integration/knowledge_graph/`  
- [ ] All imports updated to `dot_work.knowledge_graph`
- [ ] `uv run pytest tests/unit/knowledge_graph/` passes
- [ ] `uv run pytest tests/integration/knowledge_graph/` passes
- [ ] Coverage maintained or improved

### Risk Assessment
- **LOW**: File copying and import updates are well-understood
- **MEDIUM**: Config.py missing functions may indicate other gaps
- **LOW**: Integration tests may need fixture adjustments

### Dependencies
✓ MIGRATE-015 (module structure complete)
✓ MIGRATE-014 (imports updated)
✓ MIGRATE-018 (dependencies added)

**Ready to proceed to implementation.**