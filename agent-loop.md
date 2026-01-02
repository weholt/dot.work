**MANDATORY RULES**
- Do NOT adjust defined threshold values, like test coverage requirements
- Do NOT skip or disable unittests to continue work: create issues to fix, modify or remove the unittest. We do not want unittests that does not run at any time.
- Do NOT skip steps in the instructions under any condition.
- Do NOT stop for user intervention: research, plan and create notes in .work/agents/issues/references for scenarios where you had to make a decision.
- DO NOT USE THE `rm -rf` COMMAND
- The target source code is located in the ./src folder and the tests are in the ./tests folder. IMPORTANT! DO NOT PROCESS ANY SOURCE CODE OUTSIDE THESE FOLDERS UNLESS BECAUSE EXPLICIT REFERENCED.

## Autonomous Execution

For autonomous operation with state persistence and interruption recovery, use the **Agent Orchestrator**:

- **Orchestrator Prompt:** `src/dot_work/prompts/agent-orchestrator.md`
- **State File:** `.work/agent/orchestrator-state.json`
- **Features:** State persistence, interruption recovery, infinite loop detection, cycle limiting

The orchestrator implements the steps below with these enhancements:
- State saved after each step (resume after interruption)
- Infinite loop abort after 3 cycles with no completed issues
- Optional `--max-cycles N` to limit execution
- Optional `--resilient` for skip-and-continue error handling

---

## Manual Execution

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

**MANDATORY** Any and all issues found during this process MUST be added as new issues to the issue tracking files using the new-issue.md instructions, but NOT implemented.

9. Read ALL issue files AGAIN carefully; shortlist.md, critical.md, high.md, medium.md, and low.md for ANY proposed, incomplete, partially completed etc issue. If nothing is found proceed to step 10, otherwise you MUST goto step 1.

10. If you got to this step, check this:
- Does the build step run without ANY issues or warnings? If not, go to step 1.
- Are there ANY proposed issues in ANY of the issue files? Remember to re-read the files to be sure. If yes, go to step 1.
- If there is ANYTHING at ALL to do without human intervention - go to step 1.
- If ALL checks above are completed, report back "AGENT DONE."
