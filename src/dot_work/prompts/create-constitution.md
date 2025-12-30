---
meta:
  title: "Project Constitution Generator"
  description: "Create a single authoritative constitution.md that must exist before any other work begins"
  version: "0.1.1"
---

You are an expert software architect and technical writer. Your task is to generate **one Markdown file named `.work/constitution.md`** that becomes the **highest authority** for this project. It must be read and accepted **before any code changes, scaffolding, or planning**.

## Input you must incorporate

Use only the following project inputs. If an item is missing, keep the section but mark it with `TODO:` placeholders.

### Project identity
- Project title: {{PROJECT_TITLE}}
- One-line description: {{PROJECT_TAGLINE}}
- Primary users/personas: {{PRIMARY_USERS}}
- Non-goals (explicitly out of scope): {{NON_GOALS}}

### Why (problem + value)
- Problem statement: {{PROBLEM_STATEMENT}}
- Why now / motivation: {{MOTIVATION}}
- Success definition (measurable): {{SUCCESS_METRICS}}

### How (principles + approach)
- Architecture style constraints (e.g. monolith/microservices, DDD, CQRS): {{ARCH_STYLE}}
- Technology constraints (languages/frameworks/db/runtime): {{TECH_CONSTRAINTS}}
- Deployment/runtime context (local/cloud, containers, CI): {{RUNTIME_CONTEXT}}
- Security/privacy constraints: {{SECURITY_CONSTRAINTS}}
- Performance constraints: {{PERFORMANCE_CONSTRAINTS}}

### Repo boundaries
- Target folders and files that may be modified: {{ALLOWED_PATHS}}
- Protected folders and files that must never be modified: {{PROTECTED_PATHS}}
- Generated artifacts (where they go, how to regenerate): {{GENERATED_ARTIFACTS}}

### Build, test, and validation
- Build commands (single-line commands): {{BUILD_COMMANDS}}
- Test commands (single-line commands): {{TEST_COMMANDS}}
- Lint/format commands (single-line commands): {{QUALITY_COMMANDS}}
- Minimal CI expectations: {{CI_EXPECTATIONS}}
- Definition of Done: {{DOD}}

### Evidence and proof
- What constitutes proof that changes align with goals: {{PROOF_REQUIREMENTS}}
- Required validation artifacts (logs, screenshots, benchmarks, test outputs): {{VALIDATION_ARTIFACTS}}

---

## Output requirements (constitution.md)

The file must contain the sections below **in the same order**, with content that is specific, enforceable, and easy to audit.

### 1) Authority and Precedence
- Declare this document as the top-level authority.
- Define precedence order (e.g. constitution.md > README > ADRs > code comments).
- Define what happens if a conflict is found (stop, open issue, propose amendment).

### 2) Project Overview
- Title, tagline, primary users.
- One paragraph problem statement.
- Bullet list of non-goals.

### 3) Goals and Success Metrics
- 3–7 measurable goals.
- Each goal must include:
  - Metric
  - Measurement method
  - Target threshold
  - Where it is validated (tests, benchmark, manual checklist)

### 4) Principles and Invariants
- 8–15 rules/invariants.
- Each invariant must include:
  - Rationale (one sentence)
  - Enforcement method (test, static check, code review checklist, CI gate)
  - Where the enforcement lives (file path, folder, or process step)

### 5) Architecture and System Boundaries
- Declare architecture style constraints.
- Define major components (even if TBD) and boundaries.
- State allowed dependency directions (e.g. domain -> application -> infra).
- Define data ownership rules and integration points.

### 6) Repository Map and Change Policy
- Explicit allowlist of modifiable paths and what belongs there.
- Explicit blocklist of protected paths and why they’re protected.
- Rules for adding new top-level folders.
- Rules for generated files (never edit by hand, regeneration command).
- A “safe editing checklist” (short, actionable).

### 7) Build and Run Contract
- Canonical build command(s).
- Canonical run/dev command(s).
- Required environment variables (names + purpose, no secrets).
- Determinism rules (lockfiles, pinned versions, reproducible builds).

### 8) Test and Validation Contract
- Canonical test command(s).
- Testing layers required (unit/integration/e2e, as applicable).
- Test data rules (fixtures, snapshots, seeds).
- Minimum coverage expectations if relevant (or explicitly declare not used).
- Performance/regression testing rules if relevant.

### 9) Proof of Alignment
- A concrete procedure to prove a change aligns with goals:
  - “Claim” (what goal/invariant is affected)
  - “Evidence” (what output proves it)
  - “Verification” (how another person/agent can reproduce)
- A required “change log” format for PRs/commits that references goals/invariants.

### 10) Definition of Done and Release Criteria
- A strict Definition of Done checklist.
- Release criteria (what must be true to ship).

### 11) Governance and Amendments
- How constitution.md can be changed (who, when, how).
- Required review steps.
- Amendment template (short).
- Versioning strategy (date or semver) for the constitution itself.

### 12) Appendix: Commands (Single-line only)
- List all build/test/quality commands exactly as single-line commands.
- If unknown, include TODO stubs.

---

## Style constraints
- Markdown only.
- Use headings (##) and bullet lists.
- Avoid long prose; prefer enforceable checklists.
- No motivational language; only operational rules.
- Use explicit paths, filenames, and commands where available.
- Where input is missing: add `TODO:` lines, do not ask questions.

## Final instruction
Generate and output only the full contents of `.work/constitution.md`.
