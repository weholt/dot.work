#!/usr/bin/env bash
# Monitor and kill processes exceeding a memory quota.
#
# This script monitors processes matching a pattern and kills any that exceed
# a specified memory threshold. Useful for preventing runaway processes from
# causing system instability.
#
# Usage:
#   ./scripts/monitor-memory.sh [memory_limit_mb] [process_pattern] [--kill]
#
# Examples:
#   ./scripts/monitor-memory.sh 8192 pytest              # Monitor pytest, warn at 8GB
#   ./scripts/monitor-memory.sh 4096 "python.*test" --kill # Kill tests exceeding 4GB
#   ./scripts/monitor-memory.sh 16384 uv                 # Monitor uv processes
#
# Default memory limit: 8192 MB (8GB)
# Default action: warn only (use --kill to terminate processes)

set -euo pipefail

# Defaults
DEFAULT_MEMORY_MB=8192  # 8GB
DEFAULT_PATTERN="pytest"
KILL_MODE=false

# Parse arguments
MEMORY_MB="${1:-$DEFAULT_MEMORY_MB}"
PROCESS_PATTERN="${2:-$DEFAULT_PATTERN}"
if [[ "${3:-}" == "--kill" ]]; then
  KILL_MODE=true
fi

# Validate memory limit
if ! [[ "$MEMORY_MB" =~ ^[0-9]+$ ]]; then
  echo "Error: Memory limit must be a positive integer (MB)" >&2
  echo "Usage: $0 [memory_limit_mb] [process_pattern] [--kill]" >&2
  exit 1
fi

echo "🔍 Monitoring processes matching: $PROCESS_PATTERN"
echo "   Memory threshold: ${MEMORY_MB}MB"
echo "   Action: $([ "$KILL_MODE" = true ] && echo "KILL exceeding processes" || echo "WARN only (no killing)")"
echo

# Find processes matching the pattern and check their memory usage
ps aux | grep -E "$PROCESS_PATTERN" | grep -v grep | grep -v "$0" | while read -r user pid cpu mem vsz rss tty stat start time command; do
  # Extract RSS memory in MB (column 6 is RSS in KB, convert to MB)
  rss_kb=$(echo "$rss" | awk '{print $1}')
  rss_mb=$((rss_kb / 1024))

  if [[ $rss_mb -gt $MEMORY_MB ]]; then
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ⚠️  Process exceeds memory limit:"
    echo "   PID: $pid"
    echo "   Memory: ${rss_mb}MB (limit: ${MEMORY_MB}MB)"
    echo "   Command: $command"

    if [[ "$KILL_MODE" = true ]]; then
      echo "   Action: KILLING process $pid"
      kill -9 "$pid" 2>/dev/null || echo "   Warning: Failed to kill process (may require sudo)"
      echo "   ✓ Process $pid terminated"
    else
      echo "   Action: WARNING only (use --kill to terminate)"
    fi
    echo
  fi
done

# Summary
echo "✓ Monitoring complete"
echo "  To automatically kill exceeding processes, add --kill flag"
echo "  To run continuously, use: watch -n 5 '$0 $MEMORY_MB $PROCESS_PATTERN'"
