# Medium Priority Issues (P2)

Enhancements, technical debt.

---

## FEAT-001@7a3c2f

---
id: "FEAT-001@7a3c2f"
title: "Create JSON validation tool using Python stdlib only"
description: "Build a JSON schema validator and linter using only Python 3.11+ standard library"
created: 2024-12-20
section: "src/dot_work/tools"
tags: [validation, json, stdlib, zero-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/tools/
---

### Problem

The project needs JSON validation capabilities for validating configuration files, API responses, and data structures. Currently there's no built-in validation tool, and external dependencies like `jsonschema` add complexity.

### Affected Files
- `src/dot_work/tools/__init__.py`
- `src/dot_work/tools/json_validator.py` (new)
- `tests/unit/test_json_validator.py` (new)

### Importance
- Enables validation of JSON configs without external deps
- Python 3.11+ has improved `json` module performance
- Useful for validating issue tracker files, prompts, etc.

### Proposed Solution

Create a `json_validator.py` module with:

1. **JSON Syntax Validation**
   - Parse JSON and report syntax errors with line/column info
   - Use `json.JSONDecodeError` for detailed error reporting

2. **Schema Validation (subset)**
   - Type checking: `string`, `number`, `integer`, `boolean`, `array`, `object`, `null`
   - Required fields validation
   - Enum validation
   - Basic pattern matching (using `re` stdlib)
   - Nested object/array validation

3. **Linting Features**
   - Detect duplicate keys
   - Check for trailing commas (via raw text parsing)
   - Validate key naming conventions (optional)

4. **API Design**
   ```python
   @dataclass
   class ValidationResult:
       valid: bool
       errors: list[ValidationError]
       warnings: list[ValidationWarning]
   
   def validate_json(content: str) -> ValidationResult: ...
   def validate_json_file(path: Path) -> ValidationResult: ...
   def validate_against_schema(data: Any, schema: dict) -> ValidationResult: ...
   ```

### Acceptance Criteria
- [ ] Validates JSON syntax with detailed error messages (line, column, context)
- [ ] Supports subset of JSON Schema Draft 7 (type, required, enum, pattern)
- [ ] No external dependencies (Python 3.11+ stdlib only)
- [ ] Comprehensive unit tests with >90% coverage for the module
- [ ] Google-style docstrings on all public functions
- [ ] Type annotations throughout
- [ ] CLI integration via `dot-work validate json <file>`

### Notes
- Python 3.11+ required for `tomllib` (for comparison) and improved error messages
- Consider using `ast.literal_eval` as fallback for edge cases
- May extend to support JSON5 comments in future

---

## FEAT-002@b8d4e1

---
id: "FEAT-002@b8d4e1"
title: "Create YAML validation tool using Python stdlib only"
description: "Build a YAML syntax validator and linter using only Python 3.11+ standard library"
created: 2024-12-20
section: "src/dot_work/tools"
tags: [validation, yaml, stdlib, zero-deps]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/tools/
  - .work/agent/issues/ (YAML issue files)
---

### Problem

YAML files are used extensively (issue tracker, configs, CI/CD). The standard approach requires PyYAML, but we want zero external dependencies. Need a stdlib-only YAML validator.

### Affected Files
- `src/dot_work/tools/__init__.py`
- `src/dot_work/tools/yaml_validator.py` (new)
- `tests/unit/test_yaml_validator.py` (new)

### Importance
- Validates issue tracker YAML frontmatter
- Zero-dependency installation
- Useful for CI/CD validation without pip installs

### Proposed Solution

Create a `yaml_validator.py` module with:

1. **YAML 1.1/1.2 Subset Parser**
   - Support common constructs: scalars, sequences, mappings
   - Handle multi-line strings (literal `|`, folded `>`)
   - Basic anchor/alias detection (warn, not full support)
   - Indentation-based structure validation

2. **Syntax Validation**
   - Indentation errors with line numbers
   - Invalid character detection
   - Unclosed quotes/brackets
   - Tab vs space mixing detection

3. **Frontmatter Validation**
   - Detect `---` delimiters
   - Parse frontmatter as separate document
   - Validate against expected schema (for issue files)

4. **API Design**
   ```python
   @dataclass
   class YAMLValidationResult:
       valid: bool
       errors: list[YAMLError]
       warnings: list[YAMLWarning]
       parsed_data: dict | list | None  # If parseable
   
   def validate_yaml(content: str) -> YAMLValidationResult: ...
   def validate_yaml_file(path: Path) -> YAMLValidationResult: ...
   def validate_frontmatter(content: str) -> YAMLValidationResult: ...
   def parse_yaml_subset(content: str) -> dict | list: ...
   ```

5. **Supported YAML Subset**
   - Scalars: strings, numbers, booleans, null
   - Sequences: `- item` style
   - Mappings: `key: value` style
   - Comments: `# comment`
   - Multi-line: `|` and `>` block scalars
   - **Not supported**: anchors, aliases, tags, complex keys

### Acceptance Criteria
- [ ] Validates YAML syntax with line/column error reporting
- [ ] Parses common YAML subset (scalars, sequences, mappings)
- [ ] Detects indentation errors and tab/space mixing
- [ ] Validates markdown frontmatter (`---` delimited)
- [ ] No external dependencies (Python 3.11+ stdlib only)
- [ ] Comprehensive unit tests with >90% coverage for the module
- [ ] Google-style docstrings on all public functions
- [ ] Type annotations throughout
- [ ] CLI integration via `dot-work validate yaml <file>`

### Notes
- This is a **subset** parser, not full YAML spec compliance
- For full YAML, users should install PyYAML separately
- Consider regex-based tokenizer for simplicity
- May use recursive descent parser for nested structures

### Implementation Hints
```python
# Basic tokenizer approach
import re
from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    KEY = auto()
    VALUE = auto()
    SEQUENCE_ITEM = auto()
    INDENT = auto()
    NEWLINE = auto()
    COMMENT = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
```

---

---
id: "FEAT-006@e6c3f9"
title: "Add Cline and Cody environments"
description: "Popular AI coding tools not currently supported"
created: 2024-12-20
section: "environments"
tags: [environments, cline, cody]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/environments.py
  - src/dot_work/installer.py
---

### Problem
Cline (VS Code extension) and Cody (Sourcegraph) are popular AI coding assistants not currently supported by dot-work.

### Affected Files
- `src/dot_work/environments.py` (add environment configs)
- `src/dot_work/installer.py` (add installer functions)

### Importance
Users of these tools cannot use dot-work to install prompts, limiting adoption.

### Proposed Solution
1. Research Cline and Cody prompt/rules file conventions:
   - Cline: likely `.cline/` or similar
   - Cody: likely `.cody/` or `.sourcegraph/`
2. Add Environment entries with appropriate detection markers
3. Add `install_for_cline()` and `install_for_cody()` functions
4. Add to INSTALLERS dispatch table
5. Add tests for new environments

### Acceptance Criteria
- [ ] `dot-work list` shows cline and cody environments
- [ ] `dot-work install --env cline` creates correct structure
- [ ] `dot-work install --env cody` creates correct structure
- [ ] `dot-work detect` recognizes cline/cody markers
- [ ] Tests cover new installer functions

### Notes
May need to verify exact conventions by checking official documentation or popular repos using these tools.

---

---
id: "REFACTOR-001@f7d4a1"
title: "Extract common installer logic to reduce duplication"
description: "10 install_for_* functions share ~80% identical code"
created: 2024-12-20
section: "installer"
tags: [refactor, dry, maintainability]
type: refactor
priority: medium
status: proposed
references:
  - src/dot_work/installer.py
---

### Problem
The 10 `install_for_*` functions in installer.py contain ~200 lines of repetitive code. Each function:
1. Creates destination directory
2. Gets environment config
3. Iterates prompts, renders, writes
4. Prints status messages

Adding a new environment requires copying ~20 lines of near-duplicate code.

### Affected Files
- `src/dot_work/installer.py`

### Importance
Violates DRY principle. Bug fixes must be applied to 10 places. Adding new environments is error-prone. The `force` flag implementation will need to be duplicated 10 times without this refactor.

### Proposed Solution
1. Create generic `install_prompts_generic()` function
2. Define environment-specific behavior via configuration:
   - Destination path pattern
   - Whether to create auxiliary files (.cursorrules, etc.)
   - Auxiliary file content template
   - Console messaging
3. Keep simple dispatch: `INSTALLERS[env_key] = lambda: install_prompts_generic(config)`
4. Special cases (claude, aider combining into single file) handled via config flag

### Acceptance Criteria
- [ ] Single generic installer function handles all environments
- [ ] No more than 5 lines of environment-specific code per environment
- [ ] All existing tests pass
- [ ] Adding new environment requires only config, not code
- [ ] `force` flag implemented in one place

### Notes
Do this AFTER implementing the force flag to avoid conflicts. Consider config-as-data pattern using dataclass or dict.

---

---
id: "FEAT-007@a8e5b2"
title: "Add --dry-run flag to install command"
description: "Allow previewing changes before writing files"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
Users cannot preview what files will be created or modified before running `dot-work install`. This makes it difficult to understand the impact of installation, especially when files might be overwritten.

### Affected Files
- `src/dot_work/cli.py` (add --dry-run option)
- `src/dot_work/installer.py` (add dry_run parameter)

### Importance
Improves user confidence and reduces surprises. Useful for CI/CD integration where destructive changes should be previewed.

### Proposed Solution
1. Add `--dry-run` / `-n` flag to install command
2. Pass through to installer functions
3. When dry_run=True:
   - Print what would be created/modified
   - Show file paths and whether new/overwrite
   - Do not write any files
4. Output format: `[CREATE] .github/prompts/do-work.prompt.md` or `[OVERWRITE] .github/prompts/do-work.prompt.md`

### Acceptance Criteria
- [ ] `dot-work install --dry-run` shows planned changes without writing
- [ ] Output distinguishes between new files and overwrites
- [ ] Exit code 0 even in dry-run mode
- [ ] Tests verify no files written in dry-run mode

### Notes
Implement after force flag and ideally after refactor to avoid duplication.

---

---
id: "FEAT-008@f7d4a2"
title: "Add batch overwrite option when files exist during install"
description: "Provide 'overwrite all' choice instead of only file-by-file prompting"
created: 2024-12-20
section: "cli"
tags: [cli, install, ux, prompting]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/installer.py
---

### Problem
When running `dot-work install` without `--force` and files already exist, the user is prompted for each file individually. For projects with many prompt files (8+), this becomes tedious.

Current behavior:
```
  ⚠ File already exists: do-work.prompt.md
    Overwrite? [y/N]: y
  ⚠ File already exists: setup-issue-tracker.prompt.md
    Overwrite? [y/N]: y
  ... (repeated for each file)
```

### Affected Files
- `src/dot_work/installer.py` (modify `should_write_file()` and install functions)
- `src/dot_work/cli.py` (potentially add `--update-all` flag)
- `tests/unit/test_installer.py` (add tests for batch behavior)

### Importance
User experience improvement. Power users reinstalling/updating prompts shouldn't need to answer the same question 8+ times. This is especially painful when updating to a new version of dot-work.

### Proposed Solution
1. When first existing file is encountered, offer expanded choices:
   ```
   ⚠ Found existing prompt files. How should I proceed?
     [a] Overwrite ALL existing files
     [s] Skip ALL existing files  
     [p] Prompt for each file individually
     [c] Cancel installation
   Choice [a/s/p/c]: 
   ```
2. Store user's choice for the session
3. Apply consistently to remaining files
4. Alternative: Add `--update-all` / `--skip-existing` CLI flags

### Acceptance Criteria
- [ ] First conflict offers batch choice (all/skip/prompt/cancel)
- [ ] Choice "a" overwrites all remaining without further prompts
- [ ] Choice "s" skips all existing files without further prompts
- [ ] Choice "p" maintains current file-by-file behavior
- [ ] Choice "c" aborts installation cleanly
- [ ] `--force` still works as before (silent overwrite all)
- [ ] Tests verify each batch mode behavior

### Notes
Consider interaction with `--force` flag:
- `--force` = silent overwrite (no prompts at all)
- No flag + batch "a" = overwrite after single confirmation
- No flag + batch "p" = current behavior

This builds on FEAT-003 (--force implementation). Could be combined with FEAT-007 (--dry-run) for a complete UX.

---
