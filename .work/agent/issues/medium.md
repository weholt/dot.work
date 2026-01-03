# Medium Priority Issues (P2)

Enhancements, technical debt.

---
---
id: "FEAT-031@b2c3d4"
title: "Create bundled subagents content package"
description: "Create pre-defined canonical subagents that ship with dot-work (code-reviewer, test-runner, debugger, docs-writer, security-auditor, refactorer)"
created: 2026-01-03
section: "subagents"
tags: [subagents, content, bundled, canonical]
type: enhancement
priority: medium
status: proposed
references:
  - src/dot_work/bundled_subagents/ (new)
  - src/dot_work/subagents/discovery.py
---

### Problem
After implementing subagent infrastructure (FEAT-030), users will have empty bundled content directories. To provide immediate value and demonstrate best practices, we need to create useful pre-defined canonical subagents.

### Affected Files
- **New directory**: `src/dot_work/bundled_subagents/`
- **New files**: code-reviewer.md, test-runner.md, debugger.md, docs-writer.md, security-auditor.md, refactorer.md

### Importance
Bundled subagents provide:
- Immediate value upon installation
- Examples of canonical format best practices
- Core functionality most users need
- Reduced time-to-first-value
- Multi-environment deployment examples

### Proposed Solution
Create 6 canonical subagent definitions with `environments:` frontmatter for all supported platforms:

1. **code-reviewer.md**
   - Description: Expert code reviewer ensuring quality and security
   - Tools: Read, Grep, Glob, Bash
   - Claude: model=sonnet, skills=[code-review]
   - OpenCode: mode=subagent, temperature=0.1
   - Copilot: infer=true
   - Focus: Clarity, security vulnerabilities, performance, test coverage

2. **test-runner.md**
   - Description: Test execution and failure analysis specialist
   - Tools: Read, Bash, Grep
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Run tests, analyze failures, suggest fixes

3. **debugger.md**
   - Description: Root cause analysis for errors and unexpected behavior
   - Tools: Read, Grep, Bash, Glob
   - Claude: model=opus (for deep analysis)
   - OpenCode: mode=subagent, temperature=0.2
   - Focus: Systematic debugging, log analysis, reproduction steps

4. **docs-writer.md**
   - Description: Technical documentation specialist
   - Tools: Read, Write, Edit
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Clear, comprehensive documentation, API docs, guides

5. **security-auditor.md**
   - Description: Security vulnerability detection expert
   - Tools: Read, Grep, Bash
   - Claude: model=opus, permissionMode=bypassPermissions
   - OpenCode: mode=subagent, temperature=0.0
   - Focus: OWASP top 10, input validation, authentication, authorization

6. **refactorer.md**
   - Description: Code refactoring and improvement specialist
   - Tools: Read, Write, Edit, Grep, Glob
   - Claude: model=sonnet
   - OpenCode: mode=subagent
   - Focus: Code clarity, deduplication, patterns, maintainability

Each subagent should include:
- Proper `meta:` section with name and description
- `environments:` section for claude, opencode, copilot
- Common `tools:` list
- Markdown body with clear instructions
- Usage examples

### Acceptance Criteria
- [ ] 6 canonical subagent files created in `bundled_subagents/`
- [ ] Each has valid YAML frontmatter with `meta:` and `environments:`
- [ ] Each has clear markdown body with instructions
- [ ] Claude Code environment configured for all
- [ ] OpenCode environment configured for all
- [ ] Copilot environment configured for all
- [ ] Tool lists are appropriate for each subagent's purpose
- [ ] CI validation passes for all bundled subagents
- [ ] Tested via `dot-work subagents install` command

### Notes
- These are starter subagents - users can modify or create their own
- Canonical format enables single definition for all platforms
- Estimated effort: 4-6 hours
- Dependencies: FEAT-030 (subagent infrastructure is complete)

---
---
id: "DOCS-009@c3d4e5"
title: "Document Skills and Subagents integration and usage"
description: "Create comprehensive documentation for skills and subagents features including architecture, usage, and examples"
created: 2026-01-03
section: "documentation"
tags: [documentation, skills, subagents, guide]
type: docs
priority: medium
status: proposed
references:
  - skills_agents_guid.md (update)
  - README.md (update)
  - docs/ (potential new directory)
---

### Problem
After implementing skills and subagents (FEAT-023, FEAT-030, FEAT-031), there needs to be comprehensive documentation explaining:
- What skills and subagents are
- How they differ from each other and from prompts
- How to create and use them
- Multi-environment support
- Best practices and examples

### Affected Files
- `skills_agents_guid.md` (update with current implementation state)
- `README.md` (add skills/subagents sections)
- Potential new: `docs/skills.md`, `docs/subagents.md`

### Importance
Good documentation ensures:
- Users understand when to use skills vs subagents vs prompts
- Clear mental model for the three content types
- Successful adoption of features
- Reduced support burden
- Community contributions

### Proposed Solution

**1. Update skills_agents_guid.md**
- Remove "proposed" language, features are implemented
- Add current architecture documentation
- Document actual file paths and module structure
- Add examples from bundled content
- Document CLI commands with real output
- Add troubleshooting section

**2. Update README.md**
- Add "Skills" section explaining:
  - What skills are (capability packages)
  - How to use bundled skills
  - How to create custom skills
- Add "Subagents" section explaining:
  - What subagents are (AI personalities)
  - Multi-environment support
  - How to use bundled subagents
  - How to create custom subagents
- Add comparison table: Prompts vs Skills vs Subagents

**3. Create detailed guides (if needed)**
- `docs/skills.md` - Complete skills guide
- `docs/subagents.md` - Complete subagents guide
- `docs/multi-env.md` - Multi-environment deployment

**Content to cover:**
- Architecture diagrams (text-based)
- File structure examples
- YAML frontmatter reference
- CLI command reference
- Environment-specific behaviors
- Tool name mappings
- Best practices
- Common patterns

### Acceptance Criteria
- [ ] skills_agents_guid.md updated to reflect implementation
- [ ] README.md has skills and subagents sections
- [ ] Clear comparison of prompts/skills/subagents
- [ ] CLI commands documented with examples
- [ ] Multi-environment support explained
- [ ] Environment-specific behaviors documented
- [ ] Best practices and examples included
- [ ] Troubleshooting section added

### Notes
- Skills and subagents are complementary, not competing features
- Documentation should match actual implementation, not the spec
- Use real examples from bundled content
- Estimated effort: 4-6 hours
- Dependencies: FEAT-023, FEAT-030, FEAT-031 (features should be implemented first)

---
