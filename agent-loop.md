**MANDATORY RULES**
- Do NOT adjust defined threshold values, like test coverage requirements
- Do NOT skip or disable unittests to continue work: create issues to fix, modify or remove the unittest. We do not want unittests that does not run at any time.
- Do NOT skip steps in the instructions under any condition.
- Do NOT stop for user intervention: research, plan and create notes in .work/agents/issues/references for scenarios where you had to make a decision.
- DO NOT USE THE `rm -rf` COMMAND

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

8. Scan ALL issue files; shortlist.md, critical.md, high.md, medium.md, and low.md for ANY proposed issue, if nothing is found proceed to step 9, otherwise you MUST goto step 1.
9. When there are no issue in any of the issue files with status proposed and ALL validation steps are running without findings of any kind, report back "AGENT DONE."
