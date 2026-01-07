#!/usr/bin/env bash
# Helper script to monitor test execution log in real-time
# Usage: ./scripts/monitor-tests.sh

LOG_FILE="test_logs/test_execution_log.txt"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Execution Log Monitor${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Monitoring: $LOG_FILE${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}Log file not found. Waiting for tests to start...${NC}"
fi

# Follow the log file with colored output
tail -f "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
    # Colorize based on content
    if [[ "$line" == *"[ERROR]"* ]] || [[ "$line" == *"FAILED"* ]]; then
        echo -e "\033[0;31m$line\033[0m"  # Red
    elif [[ "$line" == *"START:"* ]]; then
        echo -e "\033[0;36m$line\033[0m"  # Cyan
    elif [[ "$line" == *"FINISH:"* ]]; then
        echo -e "\033[0;32m$line\033[0m"  # Green
    elif [[ "$line" == *"EXECUTING:"* ]]; then
        echo -e "\033[0;33m$line\033[0m"  # Yellow
    elif [[ "$line" == *"==="* ]]; then
        echo -e "\033[1;37m$line\033[0m"  # Bold white
    else
        echo "$line"
    fi
done
