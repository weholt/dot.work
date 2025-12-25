# Kill processes exceeding memory quota

## Problem
Long-running or misbehaving processes (such as pytest or its children) can consume excessive memory, leading to system instability or freezes. There is a need for a mechanism to automatically kill any process that exceeds a specified memory usage threshold.

## Proposed Solution
Implement a monitoring or enforcement mechanism that kills processes (e.g., pytest) if they exceed a configurable memory quota.

### Options:
- Use Linux cgroups (systemd-run or manual cgroup v2) to enforce memory limits at the OS level, so the OS kills the process if it exceeds the quota.
- Use `ulimit` to set a per-process memory limit before launching the process.
- (Optional) Provide a script or tool to monitor and kill processes exceeding a memory threshold (e.g., using `ps`, `awk`, and `kill`).

## Acceptance Criteria
- Solution reliably kills processes that exceed the specified memory quota.
- Works on Linux (desktop/server) and is suitable for both local and CI environments.
- Documentation or scripts provided for setup and usage.

## References
- See AGENTS.md for workflow and standards.
- See user request for cgroup, ulimit, and monitoring script examples.