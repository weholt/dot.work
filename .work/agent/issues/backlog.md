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
