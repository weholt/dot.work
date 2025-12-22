# Investigation Notes: FEAT-010@b2c3d4

## Issue: FEAT-010@b2c3d4 – Implement multi-environment frontmatter parsing and selection
Investigation started: 2025-12-21

## Requirements Analysis

From shortlist.md, this issue requires:
- Parse environments block from canonical prompt file frontmatter
- Select correct environment based on install target
- Extract only selected environment's keys (excluding `target`)
- Pass correct frontmatter and prompt body to output file

## Current Implementation Status (from FEAT-009)

### Existing Canonical System
- `CanonicalPrompt` dataclass with `meta`, `environments`, `content`, `source_file`
- `EnvironmentConfig` dataclass with `target`, `filename`, `filename_suffix`
- `CanonicalPromptParser` - parses YAML frontmatter
- `CanonicalPromptValidator` - validates structure
- `generate_environment_prompt(prompt, env_name)` - generates environment-specific prompt
- `extract_environment_file()` - extracts to file
- `install_canonical_prompt()` - installs to environment
- `install_canonical_prompt_directory()` - batch install

### Current Behavior
The installer.py already implements environment selection:
```python
# From install_canonical_prompt()
env_config = prompt.get_environment(env_key)  # Raises KeyError if not found

# Determines output path based on target
if env_config.target.startswith("/"):
    output_dir = Path(env_config.target.lstrip("/"))
elif env_config.target.startswith("./"):
    output_dir = target / env_config.target[2:]
else:
    output_dir = target / env_config.target

# Strips .canon/.canonical suffix from base filename
base_name = prompt_file.stem
if base_name.endswith(".canon"):
    base_name = base_name[:-6]
elif base_name.endswith(".canonical"):
    base_name = base_name[:-10]
output_filename = base_name + env_config.filename_suffix
```

## Gap Analysis: What's Missing?

### 1. Environment Selection Logic
The current code gets environment by key but doesn't have explicit logic for:
- Multiple environment scenarios
- Fallback handling
- Clear error messages

### 2. Frontmatter Extraction
Current behavior includes ALL env_config fields:
```python
frontmatter = {
    "meta": prompt.meta,
    "filename": output_filename,
    **{k: v for k, v in vars(env_config).items() if k != "target" and v is not None},
}
```

This includes `filename` and `filename_suffix` - should we include these?

### 3. Acceptance Criteria Check
- [x] Installer parses environments block (CanonicalPromptParser does this)
- [?] Correct environment is selected at install time (Done, but need to verify behavior)
- [?] Only selected environment's keys are included in output frontmatter (Current implementation includes both filename/filename_suffix)
- [?] Hard error if environment is missing or ambiguous (Done, but can be improved)

## Key Questions to Resolve

1. **What should the output frontmatter contain?**
   - Just meta? Or meta + selected environment config?
   - Should we include filename/filename_suffix in output?
   - According to spec: "Only selected environment's keys"

2. **Error Handling:**
   - Current: `KeyError` if environment missing - good
   - Current: Already raises with environment list - good
   - Need: Better error messages per FEAT-012

3. **Frontmatter Structure in Output:**
   From spec: "Output file contains only selected environment's frontmatter and prompt body"
   Current output includes both filename and filename_suffix if present

## Investigation Findings

### Current Implementation Assessment
- ✅ Parsing environments block: COMPLETE
- ✅ Selecting environment by name: COMPLETE
- ⚠️ Frontmatter inclusion: PARTIAL (includes too much)
- ✅ Error on missing environment: COMPLETE

### What Needs Implementation

1. **Review current frontmatter generation** - should we exclude filename_suffix?
2. **Test frontmatter content** - verify what's actually written to files
3. **Consider edge cases**:
   - Environment with no filename/filename_suffix config?
   - Multiple environments in output file?
   - Filename conflicts?

## Implementation Plan

### Step 1: Review Current Behavior
- Check what `generate_environment_prompt()` does
- Check what `install_canonical_prompt()` outputs
- Run tests to verify current output

### Step 2: Clarify Requirements
- Should output frontmatter include filename/filename_suffix?
- Or should output be minimal (just meta)?
- Per spec: "only selected environment's frontmatter (excluding `target`)"

### Step 3: Implementation
- If needed, modify frontmatter generation to exclude filename/filename_suffix
- Or, add environment key to output for clarity
- Ensure output is deterministic

### Step 4: Testing
- Verify install_canonical_prompt outputs correct frontmatter
- Verify re-parsing output file gets correct environment
- Verify filename determinism

## Affected Code
- `src/dot_work/prompts/canonical.py:generate_environment_prompt()`
- `src/dot_work/installer.py:install_canonical_prompt()`
- Tests: `tests/unit/test_installer_canonical.py`

## Success Criteria
- [x] Installer parses environments block
- [x] Correct environment is selected at install time
- [ ] Only selected environment's keys are included in output frontmatter (verify)
- [ ] Hard error if environment is missing (done in FEAT-012)
- [ ] Tests verify environment selection behavior
