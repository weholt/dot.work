---
meta:
  title: "Project Constitution Generator"
  description: "Create a single authoritative constitution.md that must exist before any other work begins"
  version: "0.1.1"
---


Generate a concise `.work/constitution.md` as the project's top authority, to be read before any work. Use only the provided project inputs; if missing, add `TODO:` placeholders. Follow this exact section order:

1. Authority and Precedence
2. Project Overview (title, tagline, users, problem, non-goals)
3. Goals and Success Metrics (3–7, each with metric, method, target, validation)
4. Principles and Invariants (8–15, each with rationale, enforcement, location)
5. Architecture and System Boundaries (style, components, dependencies, data)
6. Repository Map and Change Policy (allowlist, blocklist, folder rules, generated files, safe editing checklist)
7. Build and Run Contract (build/run commands, env vars, determinism)
8. Test and Validation Contract (test commands, layers, data, coverage, perf)
9. Proof of Alignment (claim, evidence, verification, changelog format)
10. Definition of Done and Release Criteria
11. Governance and Amendments (change process, review, amendment template, versioning)
12. Appendix: Commands (all build/test/quality commands, TODO if unknown)

Style: Markdown only, use headings and bullet lists, no motivational language, only operational rules. Where input is missing, add `TODO:` lines. Output only the full `.work/constitution.md` contents.
