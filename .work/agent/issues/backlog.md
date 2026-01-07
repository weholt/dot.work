# Backlog

Untriaged ideas and future work.

---

id: "FEAT-099@d4e5f6"
title: "Skills and Subagents marketplace/registry"
description: "Create a community registry for sharing skills and subagents with search, install, and version management"
created: 2026-01-03
section: "ecosystem"
tags: [marketplace, registry, skills, subagents, community, future]
type: enhancement
priority: low
status: deferred
deferred: 2026-01-03
references:
  - src/dot_work/marketplace/ (potential new module)
---

### Problem
After implementing skills and subagents, users will want to share their creations with the community. Currently there's no central way to discover, install, and update community-contributed skills and subagents.

### Proposed Solution
**User decision:** Defer to future enhancement. Will revisit when skills/subagents are stable and in use.

### Notes
Estimated effort: 20-40 days depending on scope. Git-based approach recommended for simplicity.

---

---
id: "ARCH-100@langadapt"
title: "Language Adapter Pattern for multi-language build support"
description: "Refactor Python-specific build.py into abstract LanguageAdapter interface to enable TypeScript, .NET, and future language support"
created: 2026-01-07
section: "architecture"
tags: [architecture, refactoring, language-support, adapter-pattern, multi-language]
type: enhancement
priority: medium
status: proposed
references:
  - scripts/build.py (Python-specific implementation to refactor)
  - src/dot_work/languages/base.py (new adapter interface)
  - src/dot_work/languages/python.py (refactored Python adapter)
  - src/dot_work/languages/registry.py (language detection)
---

### Problem

dot-work currently has hardcoded Python-specific tooling in `scripts/build.py`:
- Hardcoded commands: `uv run ruff`, `uv run mypy`, `uv run pytest`
- Python-specific artifact cleanup: `__pycache__`, `.pytest_cache`, `.mypy_cache`
- No abstraction for supporting other languages

This makes it difficult to add support for TypeScript/JavaScript, .NET, or other languages without duplicating code or creating separate build scripts.

### Affected Files

**To create:**
- `src/dot_work/languages/base.py` - Abstract `LanguageAdapter` base class
- `src/dot_work/languages/python.py` - `PythonAdapter` implementation
- `src/dot_work/languages/registry.py` - Language detection and adapter instantiation

**To modify:**
- `scripts/build.py` - Refactor to use `LanguageAdapter` interface
- `src/dot_work/installer.py` - Update `detect_project_context()` to return adapter

### Importance

**Medium priority (architectural foundation)** - This refactoring is a prerequisite for adding TypeScript, .NET, and other language support. Without it, each language would require separate build scripts and duplicated code.

### Proposed Solution

#### Phase 1: Define LanguageAdapter Interface (1-2 days)

Create `src/dot_work/languages/base.py` with abstract `LanguageAdapter` base class containing:
- `detect()` - Check if project uses this language
- `get_name()` - Return human-readable name
- `get_package_manager()` - Detect package manager
- `format_code()` - Run formatter (ruff, prettier, dotnet format)
- `lint_code()` - Run linter (ruff check, eslint, Roslyn analyzers)
- `type_check()` - Run type checker (mypy, tsc, dotnet build)
- `run_tests()` - Run tests with coverage
- `build_project()` - Run build command
- `clean_artifacts()` - Remove build caches
- `install_dependencies()` - Install packages

#### Phase 2: Implement PythonAdapter (1-2 days)

Extract existing Python tooling from `scripts/build.py` into `PythonAdapter` class:
- Detect via pyproject.toml, setup.py, requirements.txt
- Detect package manager (uv, poetry, pip)
- Implement all adapter methods with current Python commands

#### Phase 3: Create Language Registry (1 day)

Create `src/dot_work/languages/registry.py`:
- `LANGUAGE_ADAPTERS` list of all available adapters
- `detect_language()` - Auto-detect project language
- `get_adapter_by_name()` - Explicit adapter selection

#### Phase 4: Update build.py (1 day)

Refactor `scripts/build.py` to use adapter pattern:
- Auto-detect language on startup
- Delegate all operations to adapter instance
- Maintain identical Python behavior

### Acceptance Criteria

**Phase 1 (Interface)**
- [ ] `LanguageAdapter` ABC with all abstract methods defined
- [ ] `BuildResult` and `TestResult` dataclasses

**Phase 2 (Python Adapter)**
- [ ] `PythonAdapter` implements all methods
- [ ] Python projects build identically to current implementation

**Phase 3 (Registry)**
- [ ] Auto-detection works for Python projects
- [ ] Explicit language selection via name

**Phase 4 (build.py)**
- [ ] BuildRunner uses adapter registry
- [ ] Error handling for unsupported languages

### Dependencies

- **Prerequisite**: None
- **Enables**: FEAT-102 (TypeScript/JavaScript), ARCH-101 (.NET support)

### Estimated Effort

**Total: 4-7 days**

- Interface: 1-2 days
- Python adapter: 1-2 days
- Registry: 1 day
- build.py refactor: 1 day
- Testing: 1 day

### Notes

**Design Decisions:**
- Adapter pattern for language encapsulation
- Detection by marker files (pyproject.toml, package.json, *.csproj)
- Package manager auto-detection

**Future Extensions:**
- Add `TypeScriptAdapter` (FEAT-102)
- Add `DotNetAdapter` (ARCH-101)
- Add `RustAdapter`, `GoAdapter`, `JavaAdapter`

---

---
id: "ARCH-101@dotnet"
title: ".NET/C# support for dot-work"
description: "Add .NET language adapter to dot-work for C#/F# projects with dotnet CLI tooling"
created: 2026-01-07
section: "ecosystem"
tags: [dotnet, csharp, fsharp, language-support, future]
type: enhancement
priority: low
status: proposed
references:
  - ARCH-100 (language adapter pattern - prerequisite)
  - src/dot_work/languages/dotnet.py (new module)
---

### Problem

dot-work lacks support for .NET projects (C#, F#, VB.NET). .NET developers need equivalent tooling for:
1. **Build commands**: `dotnet build`, `dotnet publish`
2. **Testing**: `dotnet test` with coverage
3. **Formatting**: `dotnet format` (built-in)
4. **Linting**: Roslyn analyzers (compiler warnings)
5. **Package management**: NuGet via `dotnet add/remove`

### Affected Files

**To create (after ARCH-100):**
- `src/dot_work/languages/dotnet.py` - `DotNetAdapter` implementation

**To modify:**
- `src/dot_work/languages/registry.py` - Register DotNetAdapter
- `src/dot_work/installer.py` - Add .NET detection

### Importance

**Low priority (future enhancement)** - Adds .NET support after architecture foundation is in place.

### Proposed Solution

Create `DotNetAdapter` implementing `LanguageAdapter`:

**Detection:**
- Marker files: *.csproj, *.fsproj, *.vbproj, *.sln
- Package manager: `dotnet`

**Tool mappings:**
| Python | .NET |
|--------|------|
| ruff format | dotnet format |
| ruff check | dotnet build (Roslyn) |
| mypy | dotnet build (compiler) |
| pytest | dotnet test |
| uv sync | dotnet restore |
| __pycache__ | bin/, obj/ |

**Implementation methods:**
- `format_code()` - `dotnet format` (with --verify-no-changes for check mode)
- `lint_code()` - `dotnet build` (Roslyn analyzers)
- `type_check()` - `dotnet build` (compiler type-checking)
- `run_tests()` - `dotnet test --collect:"XPlat Code Coverage"`
- `build_project()` - `dotnet build` (solution or projects)
- `clean_artifacts()` - Remove bin/, obj/, TestResults/
- `install_dependencies()` - `dotnet restore`

**Test discovery:**
- Convention: *.Tests.csproj or *Test.csproj
- Fallback: tests/ directory

### Acceptance Criteria

- [ ] `DotNetAdapter` implements all `LanguageAdapter` methods
- [ ] Detects .NET projects via *.csproj, *.fsproj, *.vbproj, *.sln
- [ ] `dotnet build` builds solution or projects
- [ ] `dotnet test` runs tests with coverage
- [ ] `dotnet format` formats code
- [ ] `dotnet restore` installs NuGet packages
- [ ] `clean_artifacts()` removes bin/, obj/, TestResults/
- [ ] Registered in adapter registry
- [ ] Unit tests for adapter methods

### Dependencies

- **Prerequisite**: ARCH-100 (Language Adapter Pattern)
- **Optional**: `dotnet coverlet` for coverage

### Estimated Effort

**Total: 3-5 days**

- Adapter implementation: 2-3 days
- Testing: 1 day
- Documentation: 1 day

### Notes

**Framework-specific support:**
- ASP.NET: wwwroot/, Controllers/
- MAUI: Platforms/
- Blazor: WebAssembly projects

**Future enhancements:**
- Docker detection
- Azure Functions detection
- NuGet version management

---

---
id: "FEAT-102@360708"
title: "TypeScript/JavaScript support for dot-work"
description: "Extend dot-work to support TypeScript/JavaScript projects with language-specific tooling and conventions"
created: 2026-01-06
section: "ecosystem"
tags: [typescript, javascript, nodejs, language-support, future]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/ (new typescript/ module needed)
---

### Problem

dot-work currently has Python-specific features (build.py, mypy, ruff, pytest) but lacks equivalent functionality for TypeScript/JavaScript projects. As TypeScript adoption grows, many developers need similar tooling for:

1. **TypeScript-specific commands**: `tsc`, `eslint`, `prettier`, `vitest`
2. **Package managers**: npm, yarn, pnpm, bun
3. **Build tools**: vite, webpack, rollup, esbuild
4. **Node.js project patterns**: Different structure than Python projects

### Affected Files

- New module needed: `src/dot_work/typescript/` or `src/dot_work/nodejs/`
- `src/dot_work/cli.py` - May need new command groups
- `src/dot_work/installer.py` - May need TypeScript-specific environment support

### Importance

**Low priority (future enhancement)** - The current Python-focused implementation is stable and complete. TypeScript support would expand the user base but requires significant new development effort.

### Proposed Solution

#### Phase 1: Research & Design (2-3 days)

1. **Analyze TypeScript project patterns**:
   - Common project structures (monorepos, workspaces, standard apps)
   - Package manager ecosystems (npm, yarn, pnpm, bun)
   - Build tool configurations (vite.config.ts, tsconfig.json)
   - Testing frameworks (vitest, jest, playwright)

2. **Define TypeScript equivalents** for Python features:
   ```
   Python              →  TypeScript/JavaScript
   ──────────────────────────────────────────────
   build.py            →  build.ts (or package.json scripts)
   mypy                →  tsc --noEmit
   ruff                →  eslint --fix
   pytest              →  vitest / jest
   pyproject.toml      →  package.json / tsconfig.json
   .work/              →  .work/ (same structure)
   ```

3. **Design language-agnostic architecture**:
   - Extract common functionality from Python-specific code
   - Create abstract base classes for language adapters
   - Define plugin interface for language support

#### Phase 2: Core TypeScript Support (5-10 days)

1. **New module: `src/dot_work/typescript/`**

   ```python
   """TypeScript/JavaScript project support for dot-work."""

   from pathlib import Path
   from dataclasses import dataclass

   @dataclass
   class TypeScriptProjectConfig:
       """TypeScript project configuration."""

       package_manager: str  # "npm", "yarn", "pnpm", "bun"
       build_tool: str       # "vite", "webpack", "rollup", "esbuild"
       test_framework: str   # "vitest", "jest", "mocha"
       use_ts: bool = True

   def detect_typescript_project(target: Path) -> bool:
       """Detect if target is a TypeScript/JavaScript project."""

   def get_package_manager(target: Path) -> str:
       """Detect which package manager is in use."""

   def run_typescript_build(target: Path) -> None:
       """Run TypeScript build commands."""

   def run_typescript_tests(target: Path) -> None:
       """Run TypeScript test commands."""

   def run_typescript_lint(target: Path, fix: bool = False) -> None:
       """Run TypeScript lint commands."""
   ```

2. **CLI Commands**:

   ```bash
   dot-work ts build          # Run tsc + build tool
   dot-work ts test           # Run vitest/jest
   dot-work ts lint           # Run eslint
   dot-work ts format         # Run prettier
   dot-work ts type-check     # Run tsc --noEmit
   dot-work ts init           # Initialize TypeScript project
   ```

3. **Package Manager Detection**:

   - Check for lockfiles: `package-lock.json` (npm), `yarn.lock` (yarn), `pnpm-lock.yaml` (pnpm), `bun.lockb` (bun)
   - Provide CLI override: `--package-manager=pnpm`

#### Phase 3: Environment Support (3-5 days)

1. **Add TypeScript/JavaScript to ENVIRONMENTS** in `src/dot_work/environments.py`:

   ```python
   TYPESCRIPT = Environment(
       name="TypeScript",
       prompt_dir=".claude/prompts",
       detection=["package.json", "tsconfig.json"],
       notes="Support for TypeScript/JavaScript projects",
   )
   ```

2. **Create TypeScript-specific prompts**:
   - `.claude/prompts/typescript-conventions.md`
   - `.claude/prompts/react-patterns.md`
   - `.claude/prompts/nodejs-best-practices.md`

#### Phase 4: Testing & Documentation (2-3 days)

1. **Unit tests** for:
   - Package manager detection
   - Build command execution
   - Configuration parsing
   - Error handling

2. **Integration tests** using:
   - Temporary TypeScript projects
   - Mock package.json files
   - Fixture tsconfig.json files

3. **Documentation**:
   - README section on TypeScript support
   - Examples for common frameworks (React, Vue, Node.js APIs)
   - Migration guide from Python to TypeScript workflows

### Acceptance Criteria

#### Phase 1 (Research)
- [ ] Document TypeScript project patterns and common structures
- [ ] Define language adapter interface
- [ ] Design architecture for multi-language support

#### Phase 2 (Core Support)
- [ ] `dot-work ts build` runs `tsc` and build tool
- [ ] `dot-work ts test` runs test framework with coverage
- [ ] `dot-work ts lint` runs eslint with optional --fix
- [ ] `dot-work ts format` runs prettier
- [ ] Package manager auto-detection works (npm/yarn/pnpm/bun)
- [ ] Error handling for missing dependencies

#### Phase 3 (Environments)
- [ ] TypeScript environment defined in ENVIRONMENTS
- [ ] TypeScript-specific prompts installable
- [ ] React/Vue/Node.js variants available

#### Phase 4 (Testing & Docs)
- [ ] Unit tests for all TypeScript functions
- [ ] Integration tests with sample projects
- [ ] Documentation complete with examples
- [ ] CLI help text updated

### Dependencies

- **Prerequisite**: None (can be developed independently)
- **Related**: FEAT-101 (user profile) - could store preferred package manager
- **Related**: FEAT-099 (skills marketplace) - could share TypeScript-specific skills

### Estimated Effort

**Total: 12-21 days** (depending on scope)

- Phase 1: 2-3 days (research & design)
- Phase 2: 5-10 days (core implementation)
- Phase 3: 3-5 days (environment support)
- Phase 4: 2-3 days (testing & documentation)

### Notes

#### Design Considerations

1. **Language Adapter Pattern**:
   - Create abstract base class `LanguageAdapter`
   - Python adapter implements for current functionality
   - TypeScript adapter extends the pattern
   - Future: Rust, Go, Java adapters

2. **Package Manager Compatibility**:
   - Support all major package managers
   - Detect from lockfiles (fallback to npm)
   - Allow CLI override: `--package-manager=pnpm`

3. **Framework-Specific Support**:
   - React: Vite + Vitest + ESLint React
   - Vue: Vite + Vitest + ESLint Vue
   - Node.js: ts-node/esbuild + Jest
   - Next.js: Built-in build + testing

4. **Configuration File Locations**:
   - `package.json` - Scripts, dependencies
   - `tsconfig.json` - TypeScript compiler options
   - `vite.config.ts` - Vite build configuration
   - `.eslintrc.js` - ESLint rules
   - `.prettierrc` - Prettier formatting

#### Future Enhancements

- Monorepo support (nx, turborepo)
- Angular-specific support
- Svelte/SvelteKit support
- Bun/Node.js native patterns
- ESM vs CJS module handling

#### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fragmented ecosystem | High | Focus on most common tools (Vite, Vitest, ESLint) |
| Package manager divergence | Medium | Auto-detection + CLI override |
| Framework-specific differences | Medium | Start with vanilla TypeScript, add frameworks later |
| Maintenance burden | Low | Reuse existing patterns, modular design |

---
