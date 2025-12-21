# Completed Enhancements

---
id: "ENHANCE-001"
title: "Scope interface detection to decorated symbols"
description: "Module-level decorator scan marks unrelated callables as user-facing"
created: 2025-10-15
section: src/birdseye/code_parser.py
tags: [interface-detection, accuracy]
type: enhancement
priority: medium
references: src/birdseye/code_parser.py
status: completed

---

`_detect_interfaces` flags the entire module as API/CLI/MCP/Web when any matching decorator string is present, so every collected feature inherits the same flags. That inflates reports (e.g., helper classes and inner decorators show up as API-facing) and dilutes downstream prompts. Rework the detection to inspect each callable’s decorator list and propagate flags only when a specific function or method is decorated, falling back to docstring heuristics as a secondary signal. This keeps exposure data precise and prevents false positives in generated walkthroughs.
Implemented targeted decorator scanning in `src/birdseye/code_parser.py` so interface flags now attach per callable and tests confirm accurate exposure signals.

---
id: "ENHANCE-002"
title: "Compute complexity metrics per callable"
description: "File averages hide hotspots for individual functions"
created: 2025-10-15
section: src/birdseye/code_parser.py
tags: [metrics, quality]
type: enhancement
priority: medium
references: src/birdseye/code_parser.py
status: completed

---

`_calc_metrics` runs radon over the whole file and the resulting averages are copied onto every feature entry. That makes the numbers meaningless for larger files and hides truly complex functions. Capture radon’s per-block metrics (it already returns CC results with line numbers) and map them back to each `Feature`, falling back to the file average only when no direct match exists. This yields actionable complexity data and aligns with the intent of highlighting hotspots for follow-up testing.
Per-callable cyclomatic complexity and maintainability indices now derive from Radon’s block data in `src/birdseye/code_parser.py`, with file-level figures used only as fallback.

---
id: "ENHANCE-003"
title: "Stabilize document section identifiers"
description: "Heading text collisions prevent reliable doc linking"
created: 2025-10-15
section: src/birdseye/markdown_parser.py
tags: [documentation-linking, architecture]
type: enhancement
priority: medium
references: src/birdseye/markdown_parser.py, src/birdseye/pipeline.py
status: completed

---

`extract_sections` stores only the raw heading text, and `_attach_document_references` matches features by lower-casing that text. Duplicate headings across files or sibling sections ("Overview") collide, and multi-level headings lose context, so references are often missing. Emit a normalized slug that includes the hierarchical path (e.g., `docs/guide.md#overview-data-loading`) and keep both slug and display text. Anchor lookups on the slug while still presenting the human-friendly heading. This reduces collisions and makes feature-to-doc links reliable across larger documentation sets.
Section slug generation in `src/birdseye/markdown_parser.py` plus anchor matching in `src/birdseye/pipeline.py` now link features to fully qualified `path#slug` anchors, eliminating heading collisions.

---
id: "ENHANCE-004"
title: "Derive CLI version from package metadata"
description: "Version callback hardcodes 0.1.0 instead of reading installed metadata"
created: 2025-10-15
section: src/birdseye/cli.py
tags: [cli, packaging]
type: enhancement
priority: medium
references: src/birdseye/cli.py, pyproject.toml
status: completed

---

`_version_callback` echoes a hard-coded `0.1.0`, so the CLI drifts from the package version once releases change. Switching to `importlib.metadata.version("birdseye")` (or Typer’s built-in `@app.callback` with `typer.version_option`) keeps the flag authoritative. This aligns the CLI with the version declared in `pyproject.toml` and prevents stale version strings in downstream automation.
`src/birdseye/cli.py` now resolves the installed version via `importlib.metadata.version`, with a graceful fallback when running from source.

---
id: "ENHANCE-005"
title: "Externalize scanner include/exclude rules"
description: "Hard-coded extension and directory filters limit project adaptability"
created: 2025-10-15
section: src/birdseye/scanner.py
tags: [configuration, flexibility]
type: enhancement
priority: medium
references: src/birdseye/scanner.py, src/birdseye/cli.py
status: completed

---

`iter_project_files` relies on fixed `DEFAULT_INCLUDE_EXT` and `DEFAULT_EXCLUDE_DIRS`, so scanning a repo with reStructuredText docs or custom build directories requires code edits. Pull these settings from CLI options or a `[tool.birdseye]` section in `pyproject.toml`, merge them with sensible defaults, and document the knobs. This makes the analyzer safer for large mono-repos where teams need tailored inclusion lists without patching library code.
Scanner configuration is now read from `[tool.birdseye.scanner]` in `pyproject.toml` (with normalized defaults) in `src/birdseye/scanner.py`, and the pipeline honors these settings.

---
id: "ENHANCE-006"
title: "Preserve markdown section formatting"
description: "Section extraction strips indentation and breaks code fences"
created: 2025-10-15
section: src/birdseye/markdown_parser.py
tags: [documentation, parsing]
type: enhancement
priority: medium
references: src/birdseye/markdown_parser.py
status: completed

---

`extract_sections` trims each captured block with `.strip()`, which collapses leading indentation and blank lines. Markdown code fences and indented lists lose their structure, so regenerated reports and downstream prompts omit critical formatting. Replace the blanket strip with a newline-only trim (e.g., `.strip("\n")`) or preserve indentation while normalizing trailing whitespace so code samples and lists round-trip correctly.
Heading extraction now preserves indentation by removing only leading/trailing newlines, so fenced blocks and lists keep their original layout in downstream outputs.

---
id: "ENHANCE-007"
title: "Capture markdown preamble text"
description: "Introductory content ahead of the first heading is dropped"
created: 2025-10-15
section: src/birdseye/markdown_parser.py
tags: [documentation, completeness]
type: enhancement
priority: medium
references: src/birdseye/markdown_parser.py
status: completed

---

`extract_sections` only emits sections for explicit headings, skipping any prose or tables that precede the first heading. Repository READMEs frequently include badges or summaries before the opener, so we lose that context entirely. Emit a synthetic level-0 section for the preamble and anchor it (e.g., `path#preamble`) so the pipeline keeps those paragraphs and badges available to the reporter and JSON consumers.
Preamble content is now captured as a synthetic section at `path#preamble`, ensuring introductory badges and summaries remain available for cross-reference.

---
id: "ENHANCE-008"
title: "Align reporter CLI instructions with Typer command"
description: "Generated overview suggests a command signature that does not exist"
created: 2025-10-15
section: src/birdseye/reporter.py
tags: [documentation, cli]
type: enhancement
priority: medium
references: src/birdseye/reporter.py, src/birdseye/cli.py
status: completed

---

`build_markdown_report` tells readers to run `birdseye <path-to-project> <path-to-output>`, but the Typer app requires the `analyze` subcommand (`birdseye analyze <input> <output>`). The inaccurate guidance causes scripted replays to fail. Update the walkthrough to mirror the actual CLI invocation (and include the optional flags) so the generated docs are runnable without guesswork.
The Quick Orientation section now references `birdseye analyze <input-path> <output-path>` and wraps text to stay within formatter limits, restoring accurate usage guidance.
