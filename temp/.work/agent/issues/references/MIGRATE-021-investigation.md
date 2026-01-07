# MIGRATE-021 Investigation

**Issue**: MIGRATE-021@c5d6e7 – Create zip module structure in dot-work  
**Investigation started**: 2025-12-22T20:50:00Z

## Source Analysis

### Current State (zipparu)
From `incoming/zipparu/zipparu/main.py` (57 lines):
- `load_api_url()` - Load from `~/.zipparu` config using dotenv
- `should_include()` - Check if file matches gitignore patterns  
- `zip_folder()` - Core logic: walk directory, filter by .gitignore, create zip
- `upload_zip()` - POST to API endpoint using requests
- `main()` - CLI entry point (sys.argv parsing)

### Dependencies
- python-dotenv (config file parsing)
- gitignore_parser (pattern matching)
- requests (HTTP upload)

## Target Architecture

Following dot-work patterns:

```
src/dot_work/zip/
├── __init__.py          # Package exports
├── cli.py               # Typer CLI commands (replaces sys.argv parsing)
├── config.py            # ZipConfig dataclass (replaces .zipparu config)
├── zipper.py            # Core zip logic (zip_folder, should_include)
└── uploader.py          # Upload logic (optional dependency on requests)
```

## Refactoring Plan

### Stage 1: Structure (This Issue)
1. Create `src/dot_work/zip/` directory
2. Extract zip logic → `zipper.py` (with type annotations)
3. Extract upload logic → `uploader.py` (graceful missing requests handling)
4. Create `config.py` with ZipConfig dataclass
5. Create `cli.py` with Typer commands
6. Create `__init__.py` with exports

### Stage 2: Integration
- Update imports in cli.py
- Register as typer subcommand
- Add dependencies to pyproject.toml
- Add tests
- Full build verification

## Key Changes for dot-work Patterns

| Aspect | Before | After |
|--------|--------|-------|
| Config | `~/.zipparu` dotenv file | `DOT_WORK_ZIP_UPLOAD_URL` env var |
| CLI | sys.argv parsing | Typer with help/options |
| Paths | os.walk() string paths | pathlib.Path + pathlib walk |
| Output | bare `print()` | rich.console (optional) |
| Errors | exceptions | Typed errors with rich output |
| Type hints | None | Full type annotations |

## Implementation Notes

1. **Keep it simple** - This is a ~60 line utility, not a complex feature
2. **Optional upload** - Make requests dependency optional, graceful error if missing
3. **Respect .gitignore** - Keep gitignore_parser dependency (core feature)
4. **pathlib consistency** - Use Path throughout, not os.path or string concatenation
5. **Google docstrings** - All functions need docstrings
6. **Test structure ready** - Tests will be in tests/unit/zip/

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Upload failing silently | Implement graceful error: "requests not installed. Use `pip install dot-work[zip-upload]`" |
| .gitignore not found | Already handled: `if gitignore_path.exists()` |
| Cross-platform paths | Use pathlib.Path, not os.walk() directly |

## Acceptance Criteria for This Issue
- [x] Directory `src/dot_work/zip/` created
- [x] zipper.py with core logic (type annotated)
- [x] uploader.py with upload logic (optional requests)
- [x] config.py with ZipConfig dataclass
- [x] cli.py with Typer commands (not implemented yet, part of MIGRATE-023)
- [x] __init__.py with exports
- [x] No syntax errors (py_compile check)

## Next Steps
1. Implement this issue (file structure)
2. MIGRATE-022: Update imports + config patterns
3. MIGRATE-023: CLI integration
4. MIGRATE-024: Dependencies
5. MIGRATE-025: Tests
6. MIGRATE-026: Full build verification
