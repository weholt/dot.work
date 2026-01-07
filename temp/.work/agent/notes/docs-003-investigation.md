# DOCS-003 Investigation: Document unified prompt authoring and migration

Investigation started: 2025-12-21

## Issue Summary
Create comprehensive documentation for the new canonical prompt file structure and migration guide for prompt authors transitioning from legacy formats.

## Requirements Analysis

### From DOCS-003 Acceptance Criteria:
1. ✓ Documentation published and accessible
2. ✓ Migration steps are clear and actionable
3. ✓ Examples for all supported environments
4. ✓ FAQ addresses common issues

### From DOCS-003 References:
- `docs/Unified Multi-Environment Prompt Specification.md` - Already exists in shortlist reference
- `docs/prompt-authoring.md` - To be created

## Current State

### Existing Implementation Knowledge
From FEAT-009, FEAT-010, FEAT-011, FEAT-012 implementation:
- Canonical prompt format with YAML frontmatter
- `meta` section: title, description, version
- `environments` section: per-environment configuration
- Environment config has: `target` (required), `filename` OR `filename_suffix`
- Installation via `install_canonical_prompt()` and `install_canonical_prompt_directory()`
- Error handling for missing/invalid environments
- Deterministic output generation

### Existing Code
- `src/dot_work/prompts/canonical.py` - Parser, validator, generator
- `src/dot_work/installer.py` - Installation functions
- `tests/unit/test_canonical.py` - Comprehensive test examples
- `tests/unit/test_installer_canonical.py` - Integration test examples

### Supported Environments
From `src/dot_work/environments.py`:
- Copilot (VS Code, `.github/prompts/`)
- Claude
- OpenCode
- Generic/other

## Documentation Plan

### File Structure to Create
```
docs/
├── Unified Multi-Environment Prompt Specification.md
│   - Formal specification (already referenced in shortlist)
│   - YAML schema
│   - Examples
│   - Operational guarantees
│
├── prompt-authoring.md (NEW)
│   - Quick start guide
│   - File format overview
│   - Migration guide
│   - Examples for each environment
│   - FAQ and troubleshooting
│
└── prompt-examples/ (NEW - optional subdirectory)
    ├── canonical-example.md
    └── migration-examples/
```

## Documentation Content Plan

### 1. prompt-authoring.md Structure
- **Quick Start** (5 min guide)
  - Single canonical file approach
  - Basic YAML structure
  - Installation command
  
- **Canonical Prompt Format**
  - Frontmatter section
  - Body section
  - Detailed schema with required/optional fields

- **Environment Configuration**
  - target: path configuration (absolute/relative)
  - filename: exact filename for environment
  - filename_suffix: dynamic naming based on title

- **Supported Environments**
  - GitHub Copilot
  - Claude (Anthropic)
  - OpenCode
  - Custom environments

- **Migration from Legacy**
  - Before: Multiple files per environment
  - After: Single canonical file
  - Step-by-step migration
  - Common pitfalls

- **Examples**
  - Complete working example
  - Multi-environment example
  - With all optional fields

- **FAQ & Troubleshooting**
  - "Environment not found" error
  - "Invalid target path" error
  - Best practices
  - Maintenance tips

### 2. Integration with existing docs
- Reference the specification
- Link to code examples
- Maintain consistency with implementation

## Key Insights from Implementation

### Error Handling
- Missing environment → Clear message with available options
- Empty target → Validation fails with explanation
- Both filename/filename_suffix missing → Clear error
- Empty filename/suffix → Rejected with validation

### Determinism
- Same canonical file + same target = identical output
- YAML ordering is stable (yaml.safe_dump)
- No non-deterministic factors
- Output includes only selected environment's config (not target path)

### File Patterns
- Canonical source files: `*.canon.md` or `*.canonical.md`
- Generated output files: per environment spec in `target`
- Generated files are disposable (never edit manually)

## Implementation Steps

1. Create `docs/` directory
2. Create `docs/prompt-authoring.md` with full guide
3. Ensure examples match real code
4. Test all code blocks are correct
5. Add internal links between docs
6. Validate no references to non-existent features

## Files to Create/Modify

### Create:
- `docs/prompt-authoring.md` (NEW - main documentation)
- `docs/Unified Multi-Environment Prompt Specification.md` (IF needed - may be implied)

### Potentially Update:
- `README.md` (add link to documentation)
- `docs/` index or similar

## Success Criteria Validation

- [ ] `docs/prompt-authoring.md` exists and is comprehensive
- [ ] Quick start section is under 5 minutes reading
- [ ] All supported environments documented with examples
- [ ] Migration guide covers before/after comparison
- [ ] FAQ has at least 5 Q&A pairs
- [ ] All code examples are correct and tested
- [ ] No broken links
- [ ] Documentation matches implementation (FEAT-009 through FEAT-012)

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Documentation gets outdated | Keep examples synced with actual code |
| Missing environment coverage | Test with all 4 supported environments |
| Unclear migration steps | Provide side-by-side before/after |
| Code examples don't work | Validate against actual functions |
| Incomplete specification | Cross-check with implementation tests |

## Notes

- Focus on practical guidance for prompt authors
- Assume audience has basic YAML knowledge
- Provide copy-paste examples
- Include common mistakes section
- Keep specification formal, authoring guide conversational
