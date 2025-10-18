#!/bin/bash
#
# E2E Test Runner for Enhanced Mode Bidirectional Highlighting
#
# This script:
# 1. Checks if required services are running
# 2. Optionally starts services if not running
# 3. Runs E2E test suite with coverage
# 4. Generates test reports
# 5. Optionally stops services after tests
#
# Usage:
#   ./scripts/run_e2e_tests.sh [options]
#
# Options:
#   --start-services      Start services before tests
#   --stop-services       Stop services after tests
#   --skip-slow           Skip slow-running tests
#   --coverage            Generate coverage report (default)
#   --no-coverage         Skip coverage report
#   --verbose             Verbose test output
#   --html-report         Generate HTML test report
#   --marker MARKER       Run only tests with marker (e.g., integration)
#   --help                Show this help message

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
START_SERVICES=false
STOP_SERVICES=false
SKIP_SLOW=false
COVERAGE=true
VERBOSE=false
HTML_REPORT=false
MARKER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-services)
            START_SERVICES=true
            shift
            ;;
        --stop-services)
            STOP_SERVICES=true
            shift
            ;;
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --html-report)
            HTML_REPORT=true
            shift
            ;;
        --marker)
            MARKER="$2"
            shift 2
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}E2E Test Suite for Bidirectional Highlighting${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if services are running
check_services() {
    local chromadb_ok=false
    local worker_ok=false

    # Check ChromaDB (port 8001)
    if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        chromadb_ok=true
        echo -e "${GREEN}✓${NC} ChromaDB is running (port 8001)"
    else
        echo -e "${RED}✗${NC} ChromaDB is not running (port 8001)"
    fi

    # Check Worker API (port 8002)
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        worker_ok=true
        echo -e "${GREEN}✓${NC} Worker API is running (port 8002)"
    else
        echo -e "${RED}✗${NC} Worker API is not running (port 8002)"
    fi

    if $chromadb_ok && $worker_ok; then
        return 0
    else
        return 1
    fi
}

# Check Python virtual environment
if [ -z "$VIRTUAL_ENV" ] && [ ! -d ".venv-native" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating virtual environment first:"
    echo "  source .venv-native/bin/activate"
    echo ""
fi

# Step 1: Check/start services
echo -e "${BLUE}Step 1: Checking required services...${NC}"
if check_services; then
    echo -e "${GREEN}All required services are running${NC}"
else
    if $START_SERVICES; then
        echo -e "${YELLOW}Starting services...${NC}"
        ./scripts/start-all.sh
        sleep 5  # Wait for services to stabilize

        # Verify services started
        if check_services; then
            echo -e "${GREEN}Services started successfully${NC}"
        else
            echo -e "${RED}Failed to start services${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Required services are not running${NC}"
        echo "Start services manually or use --start-services flag"
        echo "  ./scripts/start-all.sh"
        echo "  or"
        echo "  ./scripts/run_e2e_tests.sh --start-services"
        exit 1
    fi
fi
echo ""

# Step 2: Build pytest command
echo -e "${BLUE}Step 2: Building test command...${NC}"

PYTEST_ARGS="tests/e2e/"

# Verbose output
if $VERBOSE; then
    PYTEST_ARGS="$PYTEST_ARGS -v -s"
else
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

# Coverage
if $COVERAGE; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term --cov-report=html:htmlcov/e2e"
    echo "Coverage reports will be generated in htmlcov/e2e/"
fi

# HTML report
if $HTML_REPORT; then
    PYTEST_ARGS="$PYTEST_ARGS --html=htmlcov/e2e/report.html --self-contained-html"
    echo "HTML report will be generated in htmlcov/e2e/report.html"
fi

# Skip slow tests
if $SKIP_SLOW; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
    echo "Skipping slow tests"
fi

# Marker filter
if [ -n "$MARKER" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m '$MARKER'"
    echo "Running only tests with marker: $MARKER"
fi

echo "Test command: pytest $PYTEST_ARGS"
echo ""

# Step 3: Run tests
echo -e "${BLUE}Step 3: Running E2E tests...${NC}"
echo ""

START_TIME=$(date +%s)

# Run pytest
if pytest $PYTEST_ARGS; then
    TEST_RESULT=0
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All tests passed${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    TEST_RESULT=1
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}========================================${NC}"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BLUE}Test execution time: ${DURATION}s${NC}"

# Step 4: Generate reports summary
if $COVERAGE; then
    echo ""
    echo -e "${BLUE}Step 4: Coverage summary${NC}"
    echo "Full coverage report: htmlcov/e2e/index.html"
    echo "Open with: open htmlcov/e2e/index.html"
fi

if $HTML_REPORT; then
    echo ""
    echo "HTML test report: htmlcov/e2e/report.html"
    echo "Open with: open htmlcov/e2e/report.html"
fi

# Step 5: Stop services if requested
if $STOP_SERVICES; then
    echo ""
    echo -e "${BLUE}Step 5: Stopping services...${NC}"
    ./scripts/stop-all.sh
    echo -e "${GREEN}Services stopped${NC}"
fi

# Final status
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}E2E test suite completed successfully${NC}"
    exit 0
else
    echo -e "${RED}E2E test suite completed with failures${NC}"
    echo "Review test output above for details"
    exit 1
fi
