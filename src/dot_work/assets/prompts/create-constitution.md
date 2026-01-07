---
meta:
  name: create-constitution
  title: "Project Constitution Generator"
  description: "Create a platform-specific constitution.md that must exist before any autonomous work begins"
  version: "2.1.0"

environments:
  claude:
    target: ".claude/commands/"
    prefix: "constitution"
    
  copilot:
    target: ".github/prompts/"
    filename_suffix: ".prompt.md"
---

# Project Constitution Generator

Generate `.work/constitution.md` as the project's **single source of truth** for all agent operations. Every subagent MUST read this file before doing ANY work to ensure they all operate on the same codebase.

---

## Critical: Workspace Anchoring

The constitution MUST define the **absolute workspace root** and all paths relative to it. This prevents subagents from operating on imaginary or different versions of files.

```yaml
purpose:
  - Define THE authoritative workspace location
  - All subagents read this FIRST
  - No code operations without constitution loaded
  - Prevents agents from hallucinating file paths
```

---

## Generation Process

### Step 0: Anchor Workspace Root

**CRITICAL:** Determine and record the absolute workspace path FIRST:

```yaml
workspace_anchoring:
  detection:
    1. Find .git directory (repository root)
    2. Or find pyproject.toml/package.json (project root)
    3. Or use current working directory
    
  record:
    - Absolute path to workspace root
    - Source code location relative to root
    - Tests location relative to root
```

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

**⚠️ ALL AGENTS MUST READ THIS FILE BEFORE ANY CODE OPERATIONS ⚠️**

---

## 0. Workspace (CRITICAL - READ FIRST)

This section defines THE authoritative workspace. All agents MUST use these paths.
Do NOT operate on files outside these locations.

### Workspace Root
**Absolute Path:** `{absolute_path_to_workspace}`

### Source Code Location
**Path:** `{src_dir}/` (e.g., `src/` or `lib/`)
**Package Name:** `{package_name}` (e.g., `dot_work`)
**Import Style:** `from {package_name} import X`

### Test Location
**Path:** `{tests_dir}/` (e.g., `tests/`)
**Test Framework:** {pytest | jest | vitest | unittest}
**Test Pattern:** `test_*.py` or `*.test.ts`

### Configuration Files
- Project config: `{config_file}` (e.g., `pyproject.toml`)
- Lint config: `{lint_config}` (e.g., `pyproject.toml` or `.eslintrc`)
- Type config: `{type_config}` (e.g., `pyproject.toml` or `tsconfig.json`)

### State Files
All agent state lives in `.work/`:
```
.work/
├── constitution.md     ← YOU ARE HERE
├── baseline.md         ← Quality metrics
└── agent/
    ├── focus.md        ← Current issue
    ├── memory.md       ← Accumulated learnings
    └── issues/         ← Issue tracker
```

### Off-Limits Paths
These paths should NOT be modified by agents:
- `node_modules/`, `.venv/`, `__pycache__/`
- `.git/` (except via git commands)
- Files in `.gitignore`

---

## 1. Project Identity

**Name:** {project name}
**Type:** {library | application | service | cli}
**Primary Language:** {detected language}
**Package Manager:** {detected package manager}

---

## 2. Code Standards

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

## 3. Git Workflow

### Branch Strategy
- Main branch: {main | master}
- Feature prefix: {feat/ | feature/}
- Bugfix prefix: {fix/ | bugfix/}

### Commit Convention
- Style: {conventional | none detected}
- Format: {type}({scope}): {description}

---

## 4. Constraints

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
