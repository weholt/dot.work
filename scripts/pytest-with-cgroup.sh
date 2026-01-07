#!/usr/bin/env bash
# Run pytest with a memory quota using cgroups v2 (systemd-run).
#
# This script enforces a memory limit on pytest runs using systemd-run with
# cgroup v2 memory controller. The OS will kill the process if it exceeds
# the limit, preventing system freezes.
#
# IMPORTANT: Uses --user mode by default for non-interactive/agent use.
# No sudo or password required.
#
# When the process is killed due to OOM, a log entry is written to
# pytest-oom-killed.log in the project root with timestamp and test arguments.
#
# This is the RECOMMENDED method for CI environments and systems with cgroup v2.
#
# Usage:
#   ./scripts/pytest-with-cgroup.sh [memory_limit_gb] [pytest_args...]
#
# Examples:
#   ./scripts/pytest-with-cgroup.sh 30                         # 30GB limit, all tests
#   ./scripts/pytest-with-cgroup.sh 16 tests/unit/test_foo.py  # 16GB limit, specific test
#   ./scripts/pytest-with-cgroup.sh 30 -k "test_bar"           # 30GB limit, filtered tests
#
# Default memory limit: 30GB
#
# Requirements:
#   - systemd (for systemd-run)
#   - cgroup v2 with memory controller enabled
#   - User-level cgroup delegation (standard on modern Linux)

set -euo pipefail

# Default memory limit: 30GB
DEFAULT_MEMORY_GB=30

# Log file for OOM kills (in project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OOM_LOG_FILE="$PROJECT_ROOT/pytest-oom-killed.log"

# Parse arguments
MEMORY_GB="${1:-$DEFAULT_MEMORY_GB}"
shift || true

# Validate memory limit
if ! [[ "$MEMORY_GB" =~ ^[0-9]+$ ]]; then
  echo "Error: Memory limit must be a positive integer (GB)" >&2
  echo "Usage: $0 [memory_limit_gb] [pytest_args...]" >&2
  exit 1
fi

# Check for systemd-run
if ! command -v systemd-run &> /dev/null; then
  echo "Error: systemd-run not found. This script requires systemd." >&2
  echo "For systems without systemd, use pytest-with-ulimit.sh instead." >&2
  exit 1
fi

# Store test arguments for logging
TEST_ARGS="$*"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

echo "Running pytest with memory limit: ${MEMORY_GB}GB"
echo "   Using: systemd-run --user (no sudo required)"
echo "   Command: uv run pytest $TEST_ARGS"
echo "   OOM log: $OOM_LOG_FILE"
echo

# Run pytest under a transient user scope with memory limit
# --user: Use user session (NO SUDO/PASSWORD REQUIRED)
# --scope: Create a transient scope unit
# --property=MemoryMax: Set the maximum memory for the scope
# --quiet: Don't print the scope unit name
# --same-dir: Run in the current working directory
# --setenv=PYTHONUNBUFFERED=1: Ensure Python output is not buffered
systemd-run \
  --user \
  --scope \
  --quiet \
  --same-dir \
  --property="MemoryMax=${MEMORY_GB}G" \
  --property="MemorySwapMax=0" \
  --setenv=PYTHONUNBUFFERED=1 \
  uv run pytest "$@"

EXIT_CODE=$?

# Check if process was killed by OOM (exit code 137 = 128 + SIGKILL)
if [[ $EXIT_CODE -eq 137 ]]; then
  echo ""
  echo "ERROR: Tests were killed due to exceeding ${MEMORY_GB}GB memory limit"
  echo "See $OOM_LOG_FILE for details"
  
  # Log the OOM event
  {
    echo "================================================================================"
    echo "PYTEST OOM KILLED"
    echo "================================================================================"
    echo "Timestamp:    $TIMESTAMP"
    echo "Memory Limit: ${MEMORY_GB}GB"
    echo "Exit Code:    $EXIT_CODE (SIGKILL - OOM)"
    echo "Working Dir:  $(pwd)"
    echo "Test Args:    $TEST_ARGS"
    echo ""
    echo "The pytest process was terminated by the kernel OOM killer because it"
    echo "exceeded the ${MEMORY_GB}GB memory limit enforced by cgroup."
    echo ""
    echo "To investigate:"
    echo "  1. Run tests in smaller batches to identify the memory-hungry test"
    echo "  2. Check test_logs/test_execution_log.txt for the last running test"
    echo "  3. Use: ./scripts/pytest-with-cgroup.sh $MEMORY_GB tests/unit/<specific_module> -v"
    echo ""
    echo "================================================================================"
    echo ""
  } >> "$OOM_LOG_FILE"
fi

exit $EXIT_CODE
