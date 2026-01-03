# Memory quota enforcement for pytest

## Problem
Some pytest test runs consume excessive memory, causing the entire system to freeze or become unresponsive. There is no built-in way in pytest to enforce a hard memory limit per test run.

## Proposed Solution
Implement a robust mechanism to enforce a memory quota for pytest runs, so that if memory usage exceeds a specified threshold, the process is killed or stopped.

### Options:
- Use `ulimit` to set a virtual memory limit for the pytest process (simple, shell-based, works per session).
- Use Linux cgroups (systemd-run or manual cgroup v2) to enforce a memory limit at the OS level, ensuring only the pytest process is killed if the limit is exceeded.
- Optionally, document or provide helper scripts for both methods.

## Acceptance Criteria
- Documentation or scripts for running pytest with a memory quota (e.g., 8GB, configurable).
- Solution works on Linux (desktop/server) and is suitable for both local and CI environments.
- (Optional) Integrate with test runner or CI pipeline for automated enforcement.

## References
- See AGENTS.md for workflow and standards.
- See user request for detailed Linux/systemd/cgroup usage examples.