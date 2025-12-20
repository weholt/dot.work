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
