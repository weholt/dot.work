#!/usr/bin/env bash
# Helper script to run tests in Docker with memory limits
# Usage: ./scripts/test-docker.sh [unit|integration|all] [test_file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="${1:-all}"
TEST_FILE="${2:-}"
COMPOSE_FILE="docker-compose.test.yml"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}dot-work Test Runner (Docker)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: docker-compose or docker compose is not installed${NC}"
    exit 1
fi

# Use docker compose or docker-compose based on availability
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# Clean up previous test log
if [ -f "test_logs/test_execution_log.txt" ]; then
    echo -e "${YELLOW}Cleaning up previous test log...${NC}"
    rm test_logs/test_execution_log.txt
fi

# Ensure test_logs directory exists
mkdir -p test_logs

case "$TEST_TYPE" in
    unit)
        echo -e "${GREEN}Running UNIT tests with 4GB memory limit...${NC}"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --profile unit run --rm test-unit
        ;;
    integration)
        echo -e "${GREEN}Running INTEGRATION tests with 4GB memory limit...${NC}"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --profile integration run --rm test-integration
        ;;
    single)
        if [ -z "$TEST_FILE" ]; then
            echo -e "${RED}Error: 'single' mode requires a test file as second argument${NC}"
            echo "Usage: $0 single <test_file>"
            exit 1
        fi
        echo -e "${GREEN}Running SINGLE test with 4GB memory limit: $TEST_FILE${NC}"
        TEST_FILE="$TEST_FILE" $DOCKER_COMPOSE -f "$COMPOSE_FILE" --profile single run --rm test-single
        ;;
    all|*)
        echo -e "${GREEN}Running ALL tests with 4GB memory limit...${NC}"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" run --rm test
        ;;
esac

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"

    # Show test execution log location
    if [ -f "test_logs/test_execution_log.txt" ]; then
        echo ""
        echo -e "${GREEN}Test execution log: test_logs/test_execution_log.txt${NC}"
        echo -e "${YELLOW}Last 10 lines:${NC}"
        tail -n 10 test_logs/test_execution_log.txt
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Tests failed!${NC}"
    echo -e "${RED}========================================${NC}"

    # Show test execution log location
    if [ -f "test_logs/test_execution_log.txt" ]; then
        echo ""
        echo -e "${RED}Test execution log: test_logs/test_execution_log.txt${NC}"
        echo -e "${YELLOW}Last 20 lines:${NC}"
        tail -n 20 test_logs/test_execution_log.txt
    fi

    exit 1
fi
