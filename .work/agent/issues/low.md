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
