#!/usr/bin/env bash
# Run pytest with a memory quota using ulimit.
#
# This script enforces a memory limit on pytest runs using the ulimit command.
# The limit applies to virtual memory (address space) and is enforced per-session.
#
# Usage:
#   ./scripts/pytest-with-ulimit.sh [memory_limit_gb] [pytest_args...]
#
# Examples:
#   ./scripts/pytest-with-ulimit.sh 8                          # 8GB limit, all tests
#   ./scripts/pytest-with-ulimit.sh 4 tests/unit/test_foo.py  # 4GB limit, specific test
#   ./scripts/pytest-with-ulimit.sh 12 -k "test_bar"          # 12GB limit, filtered tests
#
# Default memory limit: 8GB

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

# Convert GB to KB (ulimit uses KB)
MEMORY_KB=$((MEMORY_GB * 1024 * 1024))

echo "🧪 Running pytest with memory limit: ${MEMORY_GB}GB"
echo "   Using: ulimit -v ${MEMORY_KB} (virtual memory limit)"
echo "   Command: uv run pytest $*"
echo

# Set the virtual memory limit and run pytest
# -v: virtual memory (address space) limit
ulimit -v "$MEMORY_KB"
exec uv run pytest "$@"
