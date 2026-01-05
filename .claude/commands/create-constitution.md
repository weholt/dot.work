---
meta:
  title: "Project Constitution Generator"
  description: "Create a platform-agnostic constitution.md that must exist before any autonomous work begins"
  version: "2.0.0"

environments:
  claude:
    target: ".claude/commands/"
    prefix: "constitution"
    
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

# Project Constitution Generator

Generate `.work/constitution.md` as the project's authoritative configuration for autonomous agent operation. The constitution provides platform-agnostic commands and rules that agents read before any work.

---

## Generation Process

### Step 1: Detect Project Environment

Scan the workspace to determine:

```yaml
detection_checks:
  language:
    python:
      - pyproject.toml exists
      - setup.py exists
      - requirements.txt exists
      - .py files in src/ or root
    javascript:
      - package.json exists
      - .js or .ts files
    rust:
      - Cargo.toml exists
    go:
      - go.mod exists
    
  package_manager:
    python:
      - pyproject.toml with [tool.uv] → uv
      - pyproject.toml with [tool.poetry] → poetry
      - requirements.txt → pip
    javascript:
      - pnpm-lock.yaml → pnpm
      - yarn.lock → yarn
      - package-lock.json → npm
      - bun.lockb → bun
      
  test_framework:
    python:
      - pytest in dependencies → pytest
      - unittest imports → unittest
    javascript:
      - jest in package.json → jest
      - vitest in package.json → vitest
      - mocha in package.json → mocha
      
  build_system:
    python:
      - pyproject.toml with [build-system] → detected build
      - setup.py → setuptools
    javascript:
      - scripts.build in package.json → npm run build
      - vite.config.* → vite
      - next.config.* → next
```

### Step 2: Detect Operating System Patterns

```yaml
os_detection:
  # Look for OS-specific patterns in existing config
  ci_files:
    - .github/workflows/*.yml → extract os matrix
    - .gitlab-ci.yml → extract os targets
    
  scripts:
    - scripts/*.sh → unix-style
    - scripts/*.ps1 → windows-style
    - scripts/*.bat → windows-style
    
  path_patterns:
    - Path() usage → cross-platform
    - os.path.join → cross-platform
    - hardcoded / → unix-specific
    - hardcoded \ → windows-specific
```

### Step 3: Generate Platform-Agnostic Commands

Create commands that work across platforms:

```yaml
command_generation:
  # Use package manager abstractions
  python_uv:
    install: "uv sync"
    run: "uv run"
    test: "uv run pytest"
    build: "uv run python -m build"
    
  python_poetry:
    install: "poetry install"
    run: "poetry run"
    test: "poetry run pytest"
    build: "poetry build"
    
  javascript_npm:
    install: "npm install"
    run: "npm run"
    test: "npm test"
    build: "npm run build"
    
  # Prefer cross-platform tools
  file_operations:
    - pathlib.Path (Python)
    - path module (Node.js)
    - std::path (Rust)
```

---

## Constitution Template

Generate `.work/constitution.md` with this structure:

```markdown
# Project Constitution

> Generated: {ISO-8601 timestamp}
> Project: {project name from pyproject.toml/package.json}
> Version: {version if found}

---

## 1. Project Identity

**Name:** {project name}
**Type:** {library | application | service | cli}
**Primary Language:** {detected language}
**Package Manager:** {detected package manager}

---

## 2. Commands (Platform-Agnostic)

All commands must be run from the project root.

### Setup
\`\`\`bash
{install_command}
\`\`\`

### Build
\`\`\`bash
{build_command}
\`\`\`

### Test
\`\`\`bash
{test_command}
\`\`\`

### Test with Coverage
\`\`\`bash
{test_coverage_command}
\`\`\`

### Lint
\`\`\`bash
{lint_command}
\`\`\`

### Type Check
\`\`\`bash
{type_check_command}
\`\`\`

### Format
\`\`\`bash
{format_command}
\`\`\`

### Full Validation
\`\`\`bash
{full_validation_command}
\`\`\`

---

## 3. Memory Protection

{IF memory protection script exists:}
### Test Memory Limits

Tests MUST use memory-protected execution to prevent system freezes:

\`\`\`bash
{memory_protected_test_command}
\`\`\`

Default memory limit: {limit}GB
{ELSE:}
No memory protection configured. Consider adding for large test suites.
{ENDIF}

---

## 4. Code Standards

### Style
- {detected or default style rules}
- {formatting tool}: {config file if exists}
- {linter}: {config file if exists}

### Type Checking
- Tool: {mypy | pyright | typescript | none}
- Strictness: {strict | standard | disabled}

### Testing
- Framework: {pytest | jest | vitest | unittest}
- Minimum coverage: {percentage or TODO}
- Test naming: test_{function}_{scenario}_{expected}

---

## 5. File Structure

### Source Code
- Location: {src_dir}/
- Import style: from {package_name} import X

### Tests
- Location: {tests_dir}/
- Mirror source structure: {yes | no}

### Configuration
- Project config: {config_file}
- {additional config files}

---

## 6. Git Workflow

### Branch Strategy
- Main branch: {main | master}
- Feature prefix: {feat/ | feature/}
- Bugfix prefix: {fix/ | bugfix/}

### Commit Convention
- Style: {conventional | none detected}
- Format: {type}({scope}): {description}

---

## 7. Dependencies

### Adding Dependencies
\`\`\`bash
{add_dependency_command}
\`\`\`

### Adding Dev Dependencies
\`\`\`bash
{add_dev_dependency_command}
\`\`\`

### Updating Dependencies
\`\`\`bash
{update_dependencies_command}
\`\`\`

---

## 8. CI/CD

{IF ci_config exists:}
### Detected CI: {GitHub Actions | GitLab CI | etc}
- Config: {ci_config_path}
- Required checks: {list}
{ELSE:}
No CI configuration detected.
{ENDIF}

---

## 9. Platform Notes

### Cross-Platform Compatibility
- File paths: Use pathlib.Path (Python) or equivalent
- Line endings: {LF | CRLF | auto}
- Shell commands: Prefer cross-platform alternatives

### OS-Specific Considerations
{detected OS-specific notes or "None detected"}

---

## 10. Constraints

### Performance
- Max test duration: {limit or TODO}
- Max memory usage: {limit or TODO}

### Security
- No hardcoded secrets
- No credentials in config files
- Use environment variables for sensitive data

### Compatibility
- Minimum language version: {detected}
- Supported platforms: {detected or "all"}

---

## 11. Appendix: Raw Commands

For scripting or CI, here are the raw commands:

| Action | Command |
|--------|---------|
| Install | {install_command} |
| Build | {build_command} |
| Test | {test_command} |
| Lint | {lint_command} |
| Type Check | {type_check_command} |
| Format | {format_command} |

---

*This constitution was auto-generated. Review and adjust as needed.*
*Regenerate with: create-constitution*
```

---

## Placeholder Handling

For anything that cannot be detected:

```yaml
placeholder_format: "TODO: {description}"

examples:
  - "TODO: Add test command"
  - "TODO: Configure coverage threshold"
  - "TODO: Add lint configuration"
```

---

## Output Location

Write to: `.work/constitution.md`

```yaml
output:
  path: ".work/constitution.md"
  create_dir: true  # Create .work/ if it doesn't exist
  overwrite: true   # Replace existing constitution
```

---

## Validation

After generation, verify:

```yaml
validation:
  - All required sections present
  - No empty command sections (use TODO if unknown)
  - Commands are syntactically valid
  - Paths use forward slashes (cross-platform)
```

---

## Usage by Agents

Agents read the constitution to:

1. **Get correct commands** - No hardcoding in prompts
2. **Understand project structure** - Where to find/put code
3. **Follow style rules** - Consistent formatting
4. **Respect constraints** - Memory limits, timeouts

```yaml
agent_integration:
  pre_loop:
    - Verify constitution exists
    - Load commands into context
    
  implementation:
    - Use test_command from constitution
    - Use lint_command from constitution
    
  validation:
    - Use full_validation_command
```

---

## See Also

**Related Prompts:** `establish-baseline`, `agent-orchestrator-v2`, `do-work`

**Related Hooks:** `pre-loop`
