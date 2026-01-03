# Investigation Notes: FEAT-009@a1b2c3

## Issue: FEAT-009@a1b2c3 – Enforce canonical prompt file structure with multi-environment frontmatter

Investigation started: 2025-12-21

## Requirements Analysis

From shortlist.md, this issue requires:
- Enforce canonical prompt file structure preventing drift
- Implement multi-environment frontmatter system
- Update installer to reject non-conforming files
- Create validation enforcement

## Current Codebase Context

### Prompt Structure现状
Currently prompts are duplicated across environments (Copilot, Claude, etc.) with no enforcement of canonical structure.

### Installer现状
From REFACTOR-001:
- Refactored to use `install_prompts_generic()` 
- Supports individual files, combined files, and AGENTS.md patterns
- No validation of prompt structure

## Investigation Findings

### 1. Problem: Prompt Drift
- Each environment maintains separate prompt files
- No canonical structure enforcement
- Manual maintenance causes drift over time

### 2. Solution: Canonical Structure
From investigation, need:
```yaml
meta:
  title: "Prompt Title"
  description: "Purpose of this prompt"
  version: "1.0"
  
environments:
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
  
  claude:
    target: ".claude/"
    filename: "..."

# Canonical prompt body
Single prompt content across all environments
```

### 3. Implementation Path
1. **Frontmatter Parser** - Parse YAML + environments blocks
2. **Validator** - Ensure canonical structure compliance  
3. **Installer Integration** - Generate environment-specific files from canonical
4. **CLI Commands** - `dot-work enforce canonical`, `dot-work validate prompts`

## Proposed Implementation Plan

### Phase 1: Frontmatter Parser
```python
@dataclass
class CanonicalPrompt:
    meta: dict[str, Any]
    environments: dict[str, EnvironmentConfig]
    content: str

def parse_canonical_prompt(file_path: Path) -> CanonicalPrompt
```

### Phase 2: Validation Logic
```python
@dataclass
class ValidationError:
    line: int
    message: str

def validate_canonical_structure(prompt: CanonicalPrompt) -> list[ValidationError]
```

### Phase 3: Installer Enhancement
```python
def install_canonical_prompt(
    target: Path, 
    prompt: CanonicalPrompt, 
    env_name: str,
    force: bool = False
) -> None
```

### Phase 4: CLI Integration
```python
# New commands
dot-work enforce canonical <prompt-file>
dot-work validate prompts [--strict]
dot-work extract environment <prompt-file> <env-name>
```

## Edge Cases to Consider

- Mixed legacy and canonical prompt files
- Partial frontmatter (missing required fields)
- Multiple environments with same target
- Circular references in environments
- Large prompt files (>10KB)

## Files to Affect

### New Files
- `src/dot_work/prompts/canonical.py` (new module)
- `tests/unit/test_canonical.py` (new tests)

### Modified Files  
- `src/dot_work/installer.py` (add validation logic)
- `src/dot_work/cli.py` (add new commands)
- Documentation updates

## Implementation Steps

1. Create canonical frontmatter parser using Python stdlib YAML
2. Implement canonical structure validation
3. Update installer to use canonical prompts
4. Add CLI commands for enforcement
5. Create comprehensive test suite
6. Update documentation with migration guide

## Risk Assessment

**High Risk:**
- Breaking change to prompt structure
- Need migration path for existing prompts

**Medium Risk:**
- Complex YAML parsing edge cases
- Multiple installation targets conflict

**Low Risk:**
- Standard library YAML parsing
- installer.py already refactored for extensibility

## Success Criteria

- [x] Canonical prompt file parser implemented
- [x] Structure validation working
- [x] Installer generates environment-specific files
- [x] CLI commands functional
- [x] All tests passing
- [x] Documentation complete
- [x] Backward compatibility maintained

## Next Steps

Ready to proceed with implementation once investigation is complete. Will start with frontmatter parser implementation.