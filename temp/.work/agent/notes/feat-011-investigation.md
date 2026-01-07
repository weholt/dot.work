# Investigation Notes: FEAT-011@c3d4e5

## Issue: FEAT-011@c3d4e5 – Generate deterministic environment-specific prompt files
Investigation started: 2025-12-21

## Requirements Analysis

From shortlist.md, FEAT-011 requires:
- Output is deterministic for same input/target
- Output file contains only selected environment's frontmatter and prompt body
- Output path and filename must match the selected environment's `target`
- Tests verify reproducibility

## What is Determinism?

For prompt installation: `Same canonical file + Same environment target = Identical output file`

This is critical for:
- Reproducible builds
- Safe cleanup (know what to delete)
- Version control
- Distribution consistency

## Current Implementation Analysis

### Determinism Factors

**Input factors:**
- Canonical prompt file path
- Environment key (e.g., "copilot")
- Target directory

**Output factors:**
- Filename (from filename or filename_suffix)
- Frontmatter (meta + environment config)
- Content body

### Current `generate_environment_prompt()` Implementation

```python
def generate_environment_prompt(prompt: CanonicalPrompt, env_name: str) -> tuple[str, str]:
    env_config = prompt.get_environment(env_name)
    
    # Generate filename
    if env_config.filename:
        filename = env_config.filename
    elif env_config.filename_suffix:
        # Use meta title or fallback to environment name
        base_name = prompt.meta.get("title", env_name).lower()
        base_name = re.sub(r"[^a-z0-9_-]", "-", base_name)
        filename = base_name + env_config.filename_suffix
    else:
        filename = f"{env_name}.prompt.md"
    
    # Generate frontmatter
    env_frontmatter = {
        "meta": prompt.meta,
    }
    
    env_config_dict = {
        k: v
        for k, v in {
            "filename": env_config.filename,
            "filename_suffix": env_config.filename_suffix,
        }.items()
        if v is not None
    }
    
    if env_config_dict:
        env_frontmatter["environment"] = env_config_dict
    
    # Output
    output = io.StringIO()
    output.write("---\n")
    yaml.dump(env_frontmatter, output, default_flow_style=False)
    output.write("---\n")
    output.write(prompt.content)
    
    return filename, output.getvalue()
```

### Determinism Assessment

**Deterministic aspects:**
- ✅ Filename always same for same input
- ✅ Meta copied as-is (stable)
- ✅ Environment config included (stable)
- ✅ Content body included as-is (stable)
- ✅ YAML serialization (safe_dump is deterministic)

**Potential non-deterministic aspects:**
- ⚠️ `meta.get("title", env_name).lower()` - case conversion
- ⚠️ Regex substitution `[^a-z0-9_-]` - consistent but depends on title
- ⚠️ YAML dict ordering - depends on Python dict order (3.7+ preserves insertion order)

## Testing Requirements for Determinism

### Test 1: Deterministic Output (same input → same output)
```python
def test_generate_deterministic_output():
    # Generate same prompt twice
    filename1, content1 = generate_environment_prompt(prompt, "copilot")
    filename2, content2 = generate_environment_prompt(prompt, "copilot")
    
    assert filename1 == filename2
    assert content1 == content2
```

### Test 2: Filename Matches Config
```python
def test_filename_matches_environment_config():
    # Test with explicit filename
    filename, content = generate_environment_prompt(prompt, "claude")
    assert filename == prompt.get_environment("claude").filename
    
    # Test with suffix
    filename, content = generate_environment_prompt(prompt, "copilot")
    assert filename.endswith(prompt.get_environment("copilot").filename_suffix)
```

### Test 3: Output Contains Only Selected Environment
```python
def test_output_contains_only_selected_environment():
    filename, content = generate_environment_prompt(prompt, "copilot")
    
    # Parse output frontmatter
    parsed = yaml.safe_load(content.split("---")[1])
    
    # Should have meta and environment, not other environments
    assert "meta" in parsed
    assert "environment" in parsed
    assert "copilot" not in parsed  # Should not duplicate env name
```

### Test 4: Install Creates Deterministic File
```python
def test_install_creates_deterministic_file():
    # Install same file twice
    install_canonical_prompt(file1, "copilot", target1, console)
    content1 = output_file1.read_text()
    
    install_canonical_prompt(file2, "copilot", target2, console)
    content2 = output_file2.read_text()
    
    # Excluding path/timestamp, content should be identical
    assert extract_frontmatter_and_body(content1) == extract_frontmatter_and_body(content2)
```

## Gap Analysis: What's Missing?

### 1. Tests for Determinism
- No tests explicitly verify deterministic output
- Need to add tests to test_installer_canonical.py

### 2. Documentation
- Need to document determinism guarantee
- Should be in README or specification

### 3. Verification
- Current tests pass for functionality
- But don't explicitly test determinism

## Implementation Plan

### Step 1: Add Determinism Tests
- Test same input produces same output
- Test filename determinism
- Test frontmatter stability

### Step 2: Run Tests
- Verify all tests pass
- Verify no regressions

### Step 3: Add Test for Re-parsing
- Install canonical prompt
- Parse the output file back
- Verify it can be re-installed

## Affected Code
- `src/dot_work/prompts/canonical.py:generate_environment_prompt()`
- `src/dot_work/installer.py:install_canonical_prompt()`
- `tests/unit/test_installer_canonical.py` - add determinism tests
- Possibly: `tests/unit/test_canonical.py` - add parsing tests

## Success Criteria
- [x] Output is deterministic for same input/target
- [x] Output file contains only selected environment's frontmatter
- [x] Output path and filename match selected environment's target (via install_canonical_prompt)
- [ ] Tests verify reproducibility (NEW)
