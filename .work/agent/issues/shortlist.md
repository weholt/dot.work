# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---


---
id: "FEAT-009@a1b2c3"
title: "Enforce canonical prompt file structure with multi-environment frontmatter"
description: "Require all prompt files to use a single canonical file with meta and environments blocks"
created: 2025-12-21
section: "prompts"
tags: [prompts, frontmatter, environments, specification]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
	- docs/Unified Multi-Environment Prompt Specification.md
---

### Problem
Prompt files are currently duplicated or hand-edited for each environment (Copilot, Claude, OpenCode, etc.), leading to drift and maintenance burden. There is no enforced structure for canonical prompt files.

### Affected Files
- `src/dot_work/installer.py` (prompt parsing logic)
- `docs/Unified Multi-Environment Prompt Specification.md` (specification)

### Importance
A single canonical prompt file per agent, with environment-specific frontmatter, will eliminate drift and ensure deterministic prompt installation across all supported tools.

### Proposed Solution
1. Define and document the canonical prompt file structure:
	 - YAML frontmatter with `meta` and `environments` blocks
	 - Immutable prompt body
2. Update prompt authoring guidelines and validation logic to require this structure
3. Add validation to the installer to reject non-conforming prompt files

### Acceptance Criteria
- [ ] All prompt files use the canonical structure
- [ ] Validation rejects non-conforming files
- [ ] Documentation updated for prompt authors
- [ ] No prompt drift across environments

### Notes
See the Unified Multi-Environment Prompt Specification for details.

---
id: "FEAT-010@b2c3d4"
title: "Implement multi-environment frontmatter parsing and selection"
description: "Parse environments block and select correct environment at install time"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, environments, parsing]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
The installer currently does not support selecting environment-specific frontmatter from a canonical prompt file. It cannot parse or extract the correct environment block.

### Affected Files
- `src/dot_work/installer.py` (prompt parsing and install logic)

### Importance
Correct parsing and selection of the environment block is required for deterministic, environment-specific prompt installation.

### Proposed Solution
1. Parse the `environments` block from the prompt file frontmatter
2. Select the correct environment based on the install target
3. Extract only the selected environment's keys (excluding `target`)
4. Pass the correct frontmatter and prompt body to the output file

### Acceptance Criteria
- [ ] Installer parses environments block
- [ ] Correct environment is selected at install time
- [ ] Only selected environment's keys are included in output frontmatter
- [ ] Hard error if environment is missing or ambiguous

### Notes
See the Minimal Installer Logic in the specification for reference.

---
id: "FEAT-011@c3d4e5"
title: "Generate deterministic environment-specific prompt files"
description: "Emit prompt files with only the selected environment's frontmatter and the canonical prompt body"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, deterministic, output]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
Generated prompt files must be deterministic: same input + same target = identical output. Current logic may not guarantee this.

### Affected Files
- `src/dot_work/installer.py` (prompt file generation)

### Importance
Deterministic output is required for reproducibility, safe cleanup, and reliable prompt installation.

### Proposed Solution
1. Ensure output file contains only the selected environment's frontmatter (excluding `target`)
2. Write the prompt body verbatim
3. Output path and filename must match the selected environment's `target`
4. Add tests to verify determinism

### Acceptance Criteria
- [ ] Output is deterministic for same input/target
- [ ] Output file contains only selected environment's frontmatter and prompt body
- [ ] Tests verify reproducibility

### Notes
Generated files are disposable and never edited by hand.

---
id: "FEAT-012@d4e5f6"
title: "Installer hard errors for invalid or missing environments"
description: "Installer must fail with a clear error if the target environment is missing or misconfigured"
created: 2025-12-21
section: "installer"
tags: [prompts, installer, error-handling, environments]
type: enhancement
priority: medium
status: completed
references:
	- src/dot_work/installer.py
---

### Problem
If the target environment does not exist, or if `target.path` or `target.filename` is missing, the installer should fail with a clear error. Current behavior may be silent or ambiguous.

### Affected Files
- `src/dot_work/installer.py` (error handling)

### Importance
Failing fast and clearly prevents prompt drift and misinstallation.

### Proposed Solution
1. Add hard error if the selected environment does not exist
2. Add hard error if `target.path` or `target.filename` is missing
3. Add error if more than one environment is selected

### Acceptance Criteria
- [ ] Installer fails with clear error for missing/invalid environment
- [ ] Error messages are actionable
- [ ] No silent failures

### Notes
See the Operational Guarantees section of the specification.

---
id: "DOCS-003@e5f6a7"
title: "Document unified prompt authoring and migration"
description: "Provide clear documentation and migration guide for prompt authors"
created: 2025-12-21
section: "docs"
tags: [prompts, documentation, migration, authors]
type: docs
priority: medium
status: completed
references:
	- docs/Unified Multi-Environment Prompt Specification.md
	- docs/prompt-authoring.md
---

### Problem
Prompt authors need clear guidance on the new canonical prompt file structure, environment blocks, and migration from legacy prompt files.

### Affected Files
- `docs/Unified Multi-Environment Prompt Specification.md`
- `docs/prompt-authoring.md`

### Importance
Documentation is essential for adoption and correct usage of the new prompt system.

### Proposed Solution
1. Write documentation for the canonical prompt file structure
2. Provide migration steps for existing prompt files
3. Include examples for each supported environment
4. Add FAQ and troubleshooting section

### Acceptance Criteria
- [ ] Documentation published and accessible
- [ ] Migration steps are clear and actionable
- [ ] Examples for all supported environments
- [ ] FAQ addresses common issues

### Notes
Coordinate with installer changes to ensure docs match implementation.
