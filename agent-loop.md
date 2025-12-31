**MANDATORY RULES**
- Do NOT adjust defined threshold values, like test coverage requirements
- Do NOT skip or disable unittests to continue work: create issues to fix, modify or remove the unittest. We do not want unittests that does not run at any time.
- Do NOT skip steps in the instructions under any condition.
- Do NOT stop for user intervention: research, plan and create notes in .work/agents/issues/references for scenarios where you had to make a decision.
- DO NOT USE THE `rm -rf` COMMAND
- The target source code is located in the ./src folder and the tests are in the ./tests folder. IMPORTANT! DO NOT PROCESS ANY SOURCE CODE OUTSIDE THESE FOLDERS UNLESS BECAUSE EXPLICIT REFERENCED.

1. Follow the following prompts in src/dot_work/prompts in this sequence:

2. Scan ALL issue files in ./work/agent/issues/; shortlist.md, critical.md, high.md, medium.md, and low.md for ANY completed issues and MOVE these to ./work/agent/issues/history.md before doing anything else.

3. Establish a baseline following the establish-baseline.md instructions. Note! There should be NO build issues or failing unittests before creating the new baseline - NONE! ALL current issues should be added as issues to the correct issue files in ./work/agent/issues and then fixed.

4. When the baseline can be established, commit all changes.

5. Follow the do-work.md instructions to find isssues to update focus.md. All issues should require no human input or clarification.

6. Read through memory.md and follow the do-work.md instructions to work on issues.

7. Any issue discovered while implementing should be added using the new-issue.md prompt.

8. After implementing and completing issues, run validation steps:
    - critical-code-review.md
    - spec-delivery-auditor.md
    - performance-review.md
    - security-review.md

**MANDATORY** Any and all issues found during this process MUST be added as new issues to the issue tracking files using the new-issue.md instructions.

9. Scan ALL issue files; shortlist.md, critical.md, high.md, medium.md, and low.md for ANY proposed, incomplete, partially completed etc issue. If nothing is found proceed to step 10, otherwise you MUST goto step 1.

10. When there are no issue in any of the issue files with status proposed and ALL validation steps are running without findings of any kind, report back "AGENT DONE."
