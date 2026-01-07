# MIGRATE-023 Investigation

**Issue**: MIGRATE-023@e7f8a9 – Register zip as subcommand in dot-work CLI  
**Investigation started**: 2025-12-22T21:30:00Z

## CLI Design

### Target Commands
From the issue spec:

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

### Current CLI Structure
From inspection of src/dot_work/cli.py:

1. Main app: `typer.Typer(name="dot-work", no_args_is_help=True)`
2. Subcommands registered via `@app.command()` for simple commands
3. Subcommand groups registered via `app.add_typer(subapp, name="...")`
4. Pattern already established:
   - validate_app (json, yaml subcommands)
   - review_app (start, export, clear subcommands)
   - canonical_app (validate, install, extract subcommands)
   - kg_app (18 commands from knowledge_graph.cli)

### Implementation Plan

1. **Create zip/cli.py** with:
   - `zip_app = typer.Typer(help="Zip folders respecting .gitignore.")`
   - `@zip_app.command("create")` - Main create command
   - `@zip_app.command("upload")` - Upload existing zip
   - `@zip_app.callback(invoke_without_command=True)` - Default to create

2. **Register in main cli.py**:
   - `from dot_work.zip.cli import app as zip_app`
   - `app.add_typer(zip_app, name="zip")`

3. **Key Features**:
   - Rich console output for user feedback
   - Proper error handling with helpful messages
   - Type annotations throughout
   - Google-style docstrings

### ZipConfig Integration

Already available:
- `ZipConfig.from_env()` reads `DOT_WORK_ZIP_UPLOAD_URL`
- Upload logic in `uploader.py` with graceful error handling
- Core logic in `zipper.py`

### Command Signatures

```python
@zip_app.command("create")
def zip_create(
    folder: Path,
    output: Path | None = None,
    upload: bool = False,
) -> None:
    """Create a zip archive of a folder, respecting .gitignore."""
    # Implementation

@zip_app.command("upload")
def zip_upload(file: Path) -> None:
    """Upload a zip file to the configured endpoint."""
    # Implementation

@zip_app.callback(invoke_without_command=True)
def zip_callback(ctx: typer.Context, folder: Path | None = None) -> None:
    """Default behavior: if no subcommand, treat as create."""
    if folder and ctx.invoked_subcommand is None:
        zip_create(folder)
```

### Error Messages

Should provide helpful errors for:
1. Missing folder: "Folder not found: {path}"
2. Missing gitignore_parser: "Install with: pip install 'dot-work[zip]'"
3. Missing requests (for upload): "Install with: pip install 'dot-work[zip-upload]'"
4. Upload URL missing: "Set DOT_WORK_ZIP_UPLOAD_URL environment variable"

### Testing Strategy

CLI will be tested in MIGRATE-025 with:
- Basic zip creation
- Custom output paths
- Upload functionality
- Error conditions

---

## Implementation Notes

1. **Lazy Loading**: zip/cli.py will import from __init__.py which uses lazy loading
2. **Dependencies**: requests is optional, will show helpful error if missing
3. **Integration**: Follows same pattern as kg_app for consistency
4. **Build**: Must pass 8/8 checks after implementation
