# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

---
id: "MIGRATE-021@c5d6e7"
title: "Create zip module structure in dot-work"
description: "Copy zipparu source files to src/dot_work/zip/ and refactor to dot-work patterns"
created: 2024-12-21
section: "zip"
tags: [migration, zip, zipparu, module-structure]
type: enhancement
priority: medium
status: proposed
references:
  - incoming/zipparu/zipparu/main.py
  - src/dot_work/zip/
---

### Problem
The zipparu utility exists as a standalone package in `incoming/zipparu/`. To integrate it as a dot-work command, we need to create the module structure and refactor to follow dot-work patterns.

### Source Analysis
From `incoming/zipparu/zipparu/main.py` (~60 lines):
- `load_api_url()` - Load upload URL from `~/.zipparu` config
- `should_include()` - Check if file matches gitignore patterns
- `zip_folder()` - Create zip respecting .gitignore
- `upload_zip()` - POST zip to API endpoint
- `main()` - CLI entry point

### Target Structure
```
src/dot_work/zip/
├── __init__.py          # Package exports
├── cli.py               # Typer CLI commands
├── config.py            # Configuration (env vars, .work/zip.conf)
├── zipper.py            # Core zip logic (zip_folder, should_include)
└── uploader.py          # Upload logic (optional feature)
```

### Proposed Solution
1. Create directory `src/dot_work/zip/`
2. Extract `zip_folder()` and `should_include()` into `zipper.py`
3. Extract `upload_zip()` into `uploader.py`
4. Create `config.py` following dot-work patterns (env vars, dataclass)
5. Create `cli.py` with Typer commands
6. Add `__init__.py` with exports

### Acceptance Criteria
- [ ] Directory `src/dot_work/zip/` created
- [ ] Core zip logic in `zipper.py` with type annotations
- [ ] Upload logic in `uploader.py` (optional dependency)
- [ ] Config using `DOT_WORK_ZIP_*` env vars
- [ ] All functions have Google-style docstrings
- [ ] No syntax errors in module files

### Notes
Keep the code simple - this is a ~60 line utility. Don't over-engineer.

---

---
id: "MIGRATE-022@d6e7f8"
title: "Update zip module imports and config to use dot-work patterns"
description: "Refactor zipparu to use dot-work conventions for imports, config, and error handling"
created: 2024-12-21
section: "zip"
tags: [migration, zip, config, refactor]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/zip/config.py
  - src/dot_work/zip/zipper.py
---

### Problem
After creating the zip module, we need to ensure it follows dot-work patterns:
- Config via environment variables and `.work/` files
- Proper error handling with rich console output
- Type annotations on all functions
- pathlib.Path for all file operations

### Current Config (zipparu)
```python
# Reads from ~/.zipparu file
config_path = Path.home() / ".zipparu"
config = dotenv_values(config_path)
url = config.get("API_URL")
```

### New Config (dot-work)
```python
@dataclass
class ZipConfig:
    upload_url: str | None = None
    
    @classmethod
    def from_env(cls) -> ZipConfig:
        return cls(
            upload_url=os.getenv("DOT_WORK_ZIP_UPLOAD_URL"),
        )
```

### Changes Required

| Current | New |
|---------|-----|
| `~/.zipparu` config file | `DOT_WORK_ZIP_UPLOAD_URL` env var |
| `print()` for output | `rich.console` for styled output |
| `sys.argv` parsing | Typer CLI with proper arguments |
| No type hints | Full type annotations |
| `os.walk()` | Continue using (pathlib doesn't have walk equivalent) |

### Proposed Solution
1. Create `ZipConfig` dataclass in `config.py`
2. Use `rich.console` for all output
3. Replace `print()` with styled console messages
4. Add type annotations to all functions
5. Use `pathlib.Path` consistently

### Acceptance Criteria
- [ ] Config uses `DOT_WORK_ZIP_UPLOAD_URL` env var
- [ ] All functions have type annotations
- [ ] Rich console used for output
- [ ] No bare `print()` statements
- [ ] `uv run python -c "from dot_work.zip import zipper"` works

### Notes
Depends on MIGRATE-021 (files must exist first).

---

---
id: "MIGRATE-023@e7f8a9"
title: "Register zip as subcommand in dot-work CLI"
description: "Add zip commands as 'dot-work zip <folder>' with optional upload flag"
created: 2024-12-21
section: "cli"
tags: [migration, zip, cli, integration]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/zip/cli.py
---

### Problem
After the zip module exists in dot-work, it needs to be registered in the main CLI so users can run `dot-work zip <folder>`.

### CLI Design

```bash
# Basic zip (creates <folder>.zip in current directory)
dot-work zip <folder>

# Zip with custom output path
dot-work zip <folder> --output my-archive.zip

# Zip and upload to configured endpoint
dot-work zip <folder> --upload

# Just upload an existing zip
dot-work zip upload <file.zip>
```

### CLI Structure
```python
zip_app = typer.Typer(help="Zip folders respecting .gitignore.")

@zip_app.command("create")
def zip_create(
    folder: Path,
    output: Path | None = None,
    upload: bool = False,
) -> None:
    """Create a zip archive of a folder, respecting .gitignore."""
    ...

@zip_app.command("upload")
def zip_upload(
    file: Path,
) -> None:
    """Upload a zip file to the configured endpoint."""
    ...

# Also make create the default command
@zip_app.callback(invoke_without_command=True)
def zip_default(ctx: typer.Context, folder: Path | None = None) -> None:
    if folder and ctx.invoked_subcommand is None:
        zip_create(folder)
```

### Proposed Solution
1. Create `zip_app = typer.Typer()` in `src/dot_work/zip/cli.py`
2. Add `create` and `upload` subcommands
3. Import and register: `from dot_work.zip.cli import zip_app`
4. Register with main app: `app.add_typer(zip_app, name="zip")`

### Acceptance Criteria
- [ ] `dot-work zip --help` shows zip commands
- [ ] `dot-work zip <folder>` creates zip file
- [ ] `dot-work zip <folder> --upload` creates and uploads
- [ ] `dot-work zip upload <file>` uploads existing zip
- [ ] `--output` flag allows custom output path

### Notes
Depends on MIGRATE-022 (module must work first).

---

---
id: "MIGRATE-024@f8a9b0"
title: "Add zip dependencies to pyproject.toml"
description: "Add gitignore_parser as core dependency, requests as optional for upload"
created: 2024-12-21
section: "dependencies"
tags: [migration, zip, dependencies, pyproject]
type: enhancement
priority: medium
status: proposed
references:
  - pyproject.toml
---

### Problem
The zip module requires `gitignore_parser` for parsing .gitignore files and optionally `requests` for upload functionality.

### Dependencies to Add

```toml
[project]
dependencies = [
    # Existing...
    "gitignore-parser>=0.1.0",  # For zip command
]

[project.optional-dependencies]
# Existing...
zip-upload = ["requests>=2.28.0"]
```

### Installation Options
- `pip install dot-work` - Basic zip (no upload)
- `pip install dot-work[zip-upload]` - Adds upload capability

### Proposed Solution
1. Add `gitignore-parser>=0.1.0` to core dependencies
2. Add `zip-upload` optional dependency group with `requests`
3. Ensure zip module gracefully handles missing `requests`
4. Run `uv sync` to verify dependency resolution

### Acceptance Criteria
- [ ] `gitignore-parser` in core dependencies
- [ ] `requests` in optional `zip-upload` group
- [ ] `dot-work zip <folder>` works without requests installed
- [ ] `dot-work zip <folder> --upload` shows helpful error if requests missing
- [ ] `uv sync` succeeds

### Notes
Consider: `requests` might already be a transitive dependency. Check before adding.
Alternative: Could use `httpx` instead of `requests` for consistency with kg module.

---

---
id: "MIGRATE-025@a9b0c1"
title: "Add tests for zip module"
description: "Create unit tests for zip functionality"
created: 2024-12-21
section: "tests"
tags: [migration, zip, tests]
type: test
priority: medium
status: proposed
references:
  - tests/unit/zip/
  - src/dot_work/zip/
---

### Problem
The zip module needs tests to ensure correct behavior, especially for .gitignore handling.

### Test Structure
```
tests/unit/zip/
├── __init__.py
├── conftest.py          # Fixtures (temp folders, mock gitignore)
├── test_zipper.py       # Core zip logic tests
├── test_config.py       # Config loading tests
└── test_cli.py          # CLI command tests
```

### Key Test Cases

**test_zipper.py:**
- `test_zip_folder_creates_archive` - Basic zip creation
- `test_zip_folder_excludes_gitignore_patterns` - .gitignore respected
- `test_zip_folder_without_gitignore` - Works when no .gitignore
- `test_zip_folder_empty_directory` - Handles empty folders
- `test_zip_folder_nested_gitignore` - Nested .gitignore files (if supported)
- `test_should_include_matches_pattern` - Pattern matching

**test_config.py:**
- `test_config_from_env_with_url` - Loads URL from env
- `test_config_from_env_without_url` - Handles missing URL gracefully

**test_cli.py:**
- `test_zip_create_command` - CLI creates zip
- `test_zip_create_with_output` - Custom output path
- `test_zip_upload_without_config` - Error when no upload URL

### Proposed Solution
1. Create `tests/unit/zip/` directory
2. Add conftest.py with temp directory fixtures
3. Write tests for each module
4. Mock `requests.post` for upload tests
5. Run: `uv run pytest tests/unit/zip/ -v`

### Acceptance Criteria
- [ ] Tests in `tests/unit/zip/`
- [ ] Coverage ≥ 80% for zip module
- [ ] All tests pass: `uv run pytest tests/unit/zip/`
- [ ] Upload tests use mocked requests

### Notes
Depends on MIGRATE-022 (module must be functional).

---

---
id: "MIGRATE-026@b0c1d2"
title: "Verify zip migration with full build"
description: "Run complete build pipeline and verify all zip functionality"
created: 2024-12-21
section: "zip"
tags: [migration, zip, verification, qa]
type: test
priority: medium
status: proposed
references:
  - scripts/build.py
---

### Problem
After completing all migration steps, verify the zip migration works correctly.

### Verification Checklist

**Build Pipeline:**
```bash
uv run python scripts/build.py
```
- [ ] Formatting passes
- [ ] Linting passes
- [ ] Type checking passes
- [ ] All tests pass
- [ ] Coverage ≥75%

**CLI Verification:**
```bash
# Create test folder with files
mkdir test_folder
echo "hello" > test_folder/file.txt
echo "*.log" > test_folder/.gitignore
echo "ignored" > test_folder/debug.log

# Test zip creation
dot-work zip test_folder
# Should create test_folder.zip without debug.log

# Verify contents
unzip -l test_folder.zip
# Should show file.txt, .gitignore but NOT debug.log

# Test custom output
dot-work zip test_folder --output custom.zip

# Cleanup
rm -rf test_folder test_folder.zip custom.zip
```

**Upload Test (if configured):**
```bash
export DOT_WORK_ZIP_UPLOAD_URL="https://httpbin.org/post"
dot-work zip test_folder --upload
# Should create zip and POST to endpoint
```

### Acceptance Criteria
- [ ] `uv run python scripts/build.py` passes
- [ ] `dot-work zip <folder>` works correctly
- [ ] .gitignore patterns respected
- [ ] Upload works with configured endpoint
- [ ] No regressions in existing dot-work functionality

### Notes
Final verification step. Only mark migration complete when all checks pass.

Depends on: MIGRATE-021 through MIGRATE-025.

---


id: "FEAT-009@a1b2c3"
title: "Enforce canonical prompt file structure with multi-environment frontmatter"
description: "Require all prompt files to use a single canonical file with meta and environments blocks"
created: 2025-12-21
section: "prompts"
tags: [prompts, frontmatter, environments, specification]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
	- docs/Unified Multi-Environment Prompt Specification.md
---

### Problem
Prompt files are currently duplicated or hand-edited for each environment (Copilot, Claude, OpenCode, etc.), leading to drift and maintenance burden. There is no enforced structure for canonical prompt files.

### Affected Files
- `src/dot_work/installer.py` (prompt parsing logic)
- `docs/Unified Multi-Environment Prompt Specification.md` (specification)

### Importance
A single canonical prompt file per agent, with environment-specific frontmatter, will eliminate drift and ensure deterministic prompt installation across all supported tools.

### Proposed Solution
1. Define and document the canonical prompt file structure:
	 - YAML frontmatter with `meta` and `environments` blocks
	 - Immutable prompt body
2. Update prompt authoring guidelines and validation logic to require this structure
3. Add validation to the installer to reject non-conforming prompt files

### Acceptance Criteria
- [ ] All prompt files use the canonical structure
- [ ] Validation rejects non-conforming files
- [ ] Documentation updated for prompt authors
- [ ] No prompt drift across environments

### Notes
See the Unified Multi-Environment Prompt Specification for details.

---
id: "FEAT-010@b2c3d4"
title: "Implement multi-environment frontmatter parsing and selection"
description: "Parse environments block and select correct environment at install time"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, environments, parsing]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
The installer currently does not support selecting environment-specific frontmatter from a canonical prompt file. It cannot parse or extract the correct environment block.

### Affected Files
- `src/dot_work/installer.py` (prompt parsing and install logic)

### Importance
Correct parsing and selection of the environment block is required for deterministic, environment-specific prompt installation.

### Proposed Solution
1. Parse the `environments` block from the prompt file frontmatter
2. Select the correct environment based on the install target
3. Extract only the selected environment's keys (excluding `target`)
4. Pass the correct frontmatter and prompt body to the output file

### Acceptance Criteria
- [ ] Installer parses environments block
- [ ] Correct environment is selected at install time
- [ ] Only selected environment's keys are included in output frontmatter
- [ ] Hard error if environment is missing or ambiguous

### Notes
See the Minimal Installer Logic in the specification for reference.

---
id: "FEAT-011@c3d4e5"
title: "Generate deterministic environment-specific prompt files"
description: "Emit prompt files with only the selected environment's frontmatter and the canonical prompt body"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, deterministic, output]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
Generated prompt files must be deterministic: same input + same target = identical output. Current logic may not guarantee this.

### Affected Files
- `src/dot_work/installer.py` (prompt file generation)

### Importance
Deterministic output is required for reproducibility, safe cleanup, and reliable prompt installation.

### Proposed Solution
1. Ensure output file contains only the selected environment's frontmatter (excluding `target`)
2. Write the prompt body verbatim
3. Output path and filename must match the selected environment's `target`
4. Add tests to verify determinism

### Acceptance Criteria
- [ ] Output is deterministic for same input/target
- [ ] Output file contains only selected environment's frontmatter and prompt body
- [ ] Tests verify reproducibility

### Notes
Generated files are disposable and never edited by hand.

---
id: "FEAT-012@d4e5f6"
title: "Installer hard errors for invalid or missing environments"
description: "Installer must fail with a clear error if the target environment is missing or misconfigured"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, error-handling, environments]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
If the target environment does not exist, or if `target.path` or `target.filename` is missing, the installer should fail with a clear error. Current behavior may be silent or ambiguous.

### Affected Files
- `src/dot_work/installer.py` (error handling)

### Importance
Failing fast and clearly prevents prompt drift and misinstallation.

### Proposed Solution
1. Add hard error if the selected environment does not exist
2. Add hard error if `target.path` or `target.filename` is missing
3. Add error if more than one environment is selected

### Acceptance Criteria
- [ ] Installer fails with clear error for missing/invalid environment
- [ ] Error messages are actionable
- [ ] No silent failures

### Notes
See the Operational Guarantees section of the specification.

---
id: "DOCS-003@e5f6a7"
title: "Document unified prompt authoring and migration"
description: "Provide clear documentation and migration guide for prompt authors"
created: 2025-12-21
section: "docs"
tags: [prompts, documentation, migration, authors]
type: docs
priority: medium
status: completed
references:
	- docs/Unified Multi-Environment Prompt Specification.md
	- docs/prompt-authoring.md
---

### Problem
Prompt authors need clear guidance on the new canonical prompt file structure, environment blocks, and migration from legacy prompt files.

### Affected Files
- `docs/Unified Multi-Environment Prompt Specification.md`
- `docs/prompt-authoring.md`

### Importance
Documentation is essential for adoption and correct usage of the new prompt system.

### Proposed Solution
1. Write documentation for the canonical prompt file structure
2. Provide migration steps for existing prompt files
3. Include examples for each supported environment
4. Add FAQ and troubleshooting section

### Acceptance Criteria
- [ ] Documentation published and accessible
- [ ] Migration steps are clear and actionable
- [ ] Examples for all supported environments
- [ ] FAQ addresses common issues

### Notes
Coordinate with installer changes to ensure docs match implementation.
