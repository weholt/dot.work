# JavaScript/TypeScript Development Setup

You are a local devops agent on my machine. Install and configure JavaScript/TypeScript code review and quality tools.

## Tasks

1. Ensure Node.js (LTS) and Corepack are available. Enable Corepack.
2. In the current project, install devDependencies:
   - eslint, @eslint/js, @typescript-eslint/parser, @typescript-eslint/eslint-plugin
   - eslint-plugin-import, eslint-plugin-n, eslint-plugin-promise, eslint-plugin-unicorn
   - eslint-config-prettier, prettier
   - typescript, @types/node
   - vitest (tests)
3. Create/update `eslint.config.js` (flat config) with recommended + TypeScript rules.
4. Create/update `.prettierrc` with standard settings (printWidth 100, singleQuote true, trailingComma all).
5. Add npm scripts:
   - `"lint": "eslint ."`
   - `"format": "prettier -w ."`
   - `"typecheck": "tsc -p tsconfig.json --noEmit"`
   - `"test": "vitest run"`
6. Install SonarScanner CLI globally: `npm i -g @sonarsource/sonar-scanner-cli`
7. Install GitHub CLI and extensions:
   - `gh` + `gh extension install github/gh-copilot`
   - `gh extension install dlvhdr/gh-dash`

## Output

- `npm ls --depth=0` (devDependencies only) and the resolved TypeScript version.
- A one-line command to lint, format, and typecheck the repo.
