---
meta:
  title: "Housekeeping"
  description: "Cleans up issue files and basic workflow debris"
  version: "0.1.1"
---


# Housekeeping

## All completed tasks goes to history.md

- Scan all issues files in `.work/agent/issues` for issues with status `completed:
  - `focus.md`
  - `shortlist.md`
  - `critical.md`
  - `high.md`
  - `medium.md`
  - `low.md`
- Move all completed tasks to `history.md`
- If `history.md` is larger than 150kb, rename the file to `history-N.md` where N is a positive integer value. Avoid overwriting existing files by increasing the N value.

## Compress memory.md

- Remove duplicated entries in `.work/agent/memory.md`
- Compress entries related to same topic into one consice section with a clear header

## Issue quality check

- Follow instructions in the `task-assessment.md` prompt to analyze the remaining issues.

## End Condition

* No issue with completed in any issue file