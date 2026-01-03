# FEAT-002 Investigation Notes

Issue: FEAT-002@b8d4e1 - Create YAML validation tool using Python stdlib only
Investigation started: 2025-12-23

### Problem Summary
YAML files are used extensively (issue tracker, configs, CI/CD). The standard approach requires PyYAML, but we want zero external dependencies. Need a stdlib-only YAML validator.

### Current State
- yaml_validator.py EXISTS but uses PyYAML (external dependency)
- Need to create stdlib-only version
- CLI integration exists: `dot-work validate yaml <file>`
- Tests exist but depend on PyYAML

### Requirements
- Use only Python 3.11+ standard library
- YAML syntax validation
- Report errors with line/column info
- Support for common YAML features used in dot-work

### Investigation Checklist
- [ ] Research YAML spec complexity for stdlib implementation
- [ ] Analyze what YAML features are actually needed
- [ ] Determine if full YAML parser is feasible with stdlib only
- [ ] Consider implementing a subset parser for dot-work needs

### Challenges
- YAML is a complex specification (much more complex than JSON)
- Full spec implementation without external libraries is extremely difficult
- Need to balance completeness vs. practicality

### Possible Approaches
1. **Limited YAML Parser**: Implement subset needed for dot-work
   - Simple key-value pairs
   - Lists (arrays)
   - Basic types (string, number, boolean)
   - Comments

2. **Validation Only**: Check syntax without full parsing
   - Basic indentation checking
   - Quote matching
   - Bracket/brace matching

### Decision Needed
Should we:
A. Implement a limited YAML parser for common cases?
B. Create a syntax validator that doesn't fully parse?
C. Reconsider the stdlib-only requirement for YAML?

### Files to Consider
- Replace: src/dot_work/tools/yaml_validator.py (currently uses PyYAML)
- Keep CLI integration (already exists)
- Update tests to work with new implementation