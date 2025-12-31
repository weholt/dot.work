# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

---
id: "CR-060@c5d7e9"
title: "Console singleton in CLI modules makes testing difficult"
description: "Module-level console = Console() prevents output capture"
created: 2024-12-27
section: "cli"
tags: [testing, dependency-injection]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/cli.py
  - src/dot_work/version/cli.py
  - src/dot_work/db_issues/cli.py
---

### Problem
Multiple CLI modules create module-level `console = Console()` singletons. This makes testing output difficult without monkeypatching.

### Affected Files
- `src/dot_work/cli.py`
- `src/dot_work/version/cli.py`
- `src/dot_work/db_issues/cli.py`

### Importance
Testing CLI output requires workarounds.

### Proposed Solution
Consider dependency injection for console.

### Acceptance Criteria
- [ ] Testable CLI output

---

---
id: "CR-065@b0c2d4"
title: "Full page reload on comment submission loses scroll position"
description: "UX could be improved with partial updates"
created: 2024-12-27
section: "review"
tags: [ux, enhancement]
type: enhancement
priority: low
status: proposed
references:
  - src/dot_work/review/static/app.js
---

### Problem
`window.location.reload()` (line 43) after submitting a comment causes full page refresh, losing scroll position and potentially unsaved work.

### Affected Files
- `src/dot_work/review/static/app.js`

### Importance
UX improvement for review workflow.

### Proposed Solution
Dynamically update the DOM or use partial updates.

### Acceptance Criteria
- [ ] Scroll position preserved
- [ ] Better UX on comment submission

---

---
id: "CR-067@d2e4f6"
title: "Collector class in overview/code_parser.py has too many responsibilities"
description: "200 lines mixing AST visiting, docstrings, metrics, classification"
created: 2024-12-27
section: "overview"
tags: [refactor, srp]
type: refactor
priority: low
status: proposed
references:
  - src/dot_work/overview/code_parser.py
---

### Problem
`_Collector` class (lines 105-303) is 200 lines mixing AST visiting, docstring extraction, metric lookup, interface flag detection, and model classification.

### Affected Files
- `src/dot_work/overview/code_parser.py`

### Importance
Violates single responsibility, hard to test in isolation.

### Proposed Solution
Extract helper classes or functions for distinct concerns.

### Acceptance Criteria
- [ ] Responsibilities separated
- [ ] Improved testability

---

---
---

---
id: "DOGFOOD-014@foa1hu"
title: "Document version format conventions"
description: "dot-work version uses date-based format - why and how documented?"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, versioning, dogfooding]
type: docs
priority: low
status: proposed
references:
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/version/
---

### Problem
`dot-work version` uses date-based format. Why date-based instead of semantic?

**Unclear:**
- What is the version format exactly?
- Why date-based instead of semantic (SemVer)?
- How does version ordering work?

### Affected Files
- Documentation files
- `src/dot_work/version/` docs

### Importance
**LOW**: Nice to know but doesn't block usage:
- Version format is discoverable by use
- SemVer not strictly required for this tool
- Users can see format in action

### Proposed Solution
Add documentation section:
```markdown
## Version Format

dot-work uses date-based versioning: `YYYY.MM.PATCH`

Example: `2025.10.001`
- `2025` – Year
- `10` – Month (October)
- `001` – Patch/sequence

This format aligns with CalVer (Calendar Versioning).
```

### Acceptance Criteria
- [ ] Version format documented
- [ ] Rationale for date-based explained
- [ ] Examples provided
- [ ] Ordering rules clear

### Validation Plan
1. Add version format section to README or docs
2. Document CalVer format: `YYYY.MM.PATCH`
3. Explain rationale (date-based vs SemVer)
4. Provide ordering rules

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #11 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-015@foa1hu"
title: "Add integration testing guide for prompts"
description: "How to verify prompts work across AI tools - requires human validation"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, testing, prompts, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - docs/dogfood/baseline.md
---

### Problem
How to verify prompts work across different AI tools?

**Unclear:**
- How to test if prompts are installed correctly?
- How to test if AI tools use prompts correctly?
- What to check after installation?

User feedback: "Requires human validation"

### Affected Files
- Documentation files
- Testing guides

### Importance
**LOW**: Testing requires manual verification:
- No automated way to test AI prompts
- Each AI tool has different interface
- Human validation inherently required

### Proposed Solution
Add testing checklist:
```markdown
## Testing Installation

# Verify files exist
ls -la .github/prompts/  # Copilot
ls -la CLAUDE.md         # Claude

# Test with AI tool
# In GitHub Copilot: Type /agent-prompts-reference
# Should see list of available prompts
```

### Acceptance Criteria
- [ ] Installation verification checklist
- [ ] File existence checks for each environment
- [ ] Manual testing steps
- [ ] Expected results documented

### Validation Plan
1. Add "Testing Installation" section to docs
2. Provide checklist for file existence verification
3. Document manual testing steps for each AI tool
4. List expected results for verification

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #12 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-016@foa1hu"
title: "Document changelog format and customization"
description: "dot-work version freeze generates changelog - format and customization undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, versioning, changelog, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/version/
---

### Problem
`dot-work version freeze` generates changelog. What is the format? Where is it stored? How to customize?

**Unclear:**
- What is the changelog format?
- Where is it stored?
- How to customize the format?

### Affected Files
- Documentation files
- `src/dot_work/version/changelog.py`

### Importance
**LOW**: Default behavior works for most users:
- Format follows common conventions
- Storage location is predictable
- Customization is edge case

### Proposed Solution
Add documentation section:
```markdown
## Changelog Format

The changelog is generated in Keep a Changelog format:

# Changelog

## [2025.10.001] - 2025-10-15
### Added
- New feature X

### Fixed
- Bug Y
```

### Acceptance Criteria
- [ ] Changelog format documented
- [ ] Storage location documented
- [ ] Keep a Changelog reference provided
- [ ] Customization options (if any) documented

### Validation Plan
1. Add "Changelog Format" section to docs
2. Document Keep a Changelog format
3. Specify storage location (CHANGELOG.md in project root)
4. Reference external Keep a Changelog guide

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #13 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-017@foa1hu"
title: "Document environment detection signals and logic"
description: "dot-work detect identifies AI tool - signals and logic undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, cli, detection, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/installer.py
---

### Problem
`dot-work detect` identifies AI tool. What files/signals are checked? What if multiple detected?

**Unclear:**
- What files/signals are checked?
- What if multiple environments detected?
- What if none detected?

### Affected Files
- Documentation files
- Tooling reference

### Importance
**LOW**: Detection usually works correctly:
- Interactive fallback handles ambiguity
- Signals are tool-specific conventions
- Users can override with --env flag

### Proposed Solution
Add documentation section:
```markdown
## Detection Logic

dot-work detect checks for:

| Environment | Detection Signal |
|-------------|------------------|
| copilot | `.github/prompts/` or `.github/copilot-instructions.md` |
| claude | `CLAUDE.md` or `.claude/` |
| cursor | `.cursor/rules/` or `.cursorrules` |
| windsurf | `.windsurf/rules/` or `.windsurfrules` |

If multiple detected, uses first match.
If none detected, prompts user to select.
```

### Acceptance Criteria
- [ ] Detection signals table added
- [ ] Multiple detection behavior documented
- [ ] No detection fallback documented
- [ ] Override options explained

### Validation Plan
1. Add "Detection Logic" section to docs
2. Create table of environment detection signals
3. Document multiple detection behavior (first match)
4. Document no-detection fallback (user prompt)
5. Document --env override option

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #14 in gaps-and-questions.md (Low Priority).

---

---

id: "DOGFOOD-018@foa1hu"
title: "Document prompt uninstallation process"
description: "How to remove installed prompts - undocumented"
created: 2024-12-29
section: "dogfooding"
tags: [documentation, prompts, uninstall, dogfooding]
type: docs
priority: low
status: proposed
references:
  - docs/dogfood/gaps-and-questions.md
  - src/dot_work/installer.py
---

### Problem
How to remove installed prompts? Is there an uninstall command?

**Unclear:**
- Is there an uninstall command?
- How to remove specific prompts?
- How to remove all prompts?

### Affected Files
- Documentation files
- Tooling reference

### Importance
**LOW**: Manual removal works for most cases:
- Users can delete prompt files directly
- Uninstall is not common operation
- Clean install usually sufficient

### Proposed Solution
Add documentation section:
```markdown
## Uninstalling Prompts

# Remove specific environment
rm .github/prompts/*.prompt.md  # Copilot
rm CLAUDE.md                    # Claude

# Or use uninstall command (if exists)
dot-work uninstall --env copilot
dot-work uninstall --all
```

### Acceptance Criteria
- [ ] Manual removal documented
- [ ] Uninstall command documented (if exists)
- [ ] All environments covered
- [ ] Warning about data loss

### Validation Plan
1. Add "Uninstalling Prompts" section to docs
2. Document manual file removal for each environment
3. Check if uninstall command exists and document it
4. Add warning about data loss (custom prompts, local changes)

### Dependencies
None.

### Clarifications Needed
None. Decision received: Add basic documentation.

### Notes
This is gap #15 in gaps-and-questions.md (Low Priority).

---
