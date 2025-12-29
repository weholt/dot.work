1. Follow the following prompts in src/dot_work/prompts in this sequence:
2. Establish a baseline following the establish-baseline.prompt.md Note! There should be NO build issues or failing unittests before creating the new baseline. ALL current issues should be added as issues to the correct issue files in ./work/agent/issues and then fixed.
3. When the baseline can be established, commit all changes.
4. Follow the do-work.prompt.md to find isssues to update focus.md. All issues should require no human input or clarification.
5. Read through memory.md and follow the do-work.prompt.md to work on issues.
6. Any issue discovered while implementing should be added using the new-issue.prompt.md
7. After implementing and completing issues, run validation steps like:
    - critical-code-review.prompt.md
    - spec-delivery-auditor.prompt.md
    - performance-review.prompt.md
    - security-review.prompt.md
**MANDATORY** Any and all issues found during this process MUST be added as new issues to the issue tracking files using the new-issue.prompt.md
8. When all issues are completed and ALL validation steps are running without findings, report back "AGENT DONE."
