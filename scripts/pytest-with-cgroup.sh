#!/usr/bin/env bash
# Run pytest with a memory quota using cgroups v2 (systemd-run).
#
# This script enforces a memory limit on pytest runs using systemd-run with
# cgroup v2 memory controller. The OS will kill the process if it exceeds
# the limit, preventing system freezes.
#
# This is the RECOMMENDED method for CI environments and systems with cgroup v2.
#
# Usage:
#   ./scripts/pytest-with-cgroup.sh [memory_limit_gb] [pytest_args...]
#
# Examples:
#   ./scripts/pytest-with-cgroup.sh 8                          # 8GB limit, all tests
#   ./scripts/pytest-with-cgroup.sh 4 tests/unit/test_foo.py  # 4GB limit, specific test
#   ./scripts/pytest-with-cgroup.sh 12 -k "test_bar"          # 12GB limit, filtered tests
#
# Default memory limit: 8GB
#
# Requirements:
#   - systemd (for systemd-run)
#   - cgroup v2 with memory controller enabled

set -euo pipefail

# Default memory limit: 8GB
DEFAULT_MEMORY_GB=8

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

echo "🧪 Running pytest with memory limit: ${MEMORY_GB}GB"
echo "   Using: systemd-run with cgroup v2 memory controller"
echo "   Command: uv run pytest $*"
echo

# Run pytest under a transient scope with memory limit
# --scope: Create a transient scope unit
# --property=MemoryMax: Set the maximum memory for the scope
# --quiet: Don't print the scope unit name
# --same-dir: Run in the current working directory
# --setenv=PYTHONUNBUFFERED=1: Ensure Python output is not buffered
exec systemd-run \
  --scope \
  --quiet \
  --same-dir \
  --property="MemoryMax=${MEMORY_GB}G" \
  --property="MemorySwapMax=0" \
  --setenv=PYTHONUNBUFFERED=1 \
  uv run pytest "$@"
