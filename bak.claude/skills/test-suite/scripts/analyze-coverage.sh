#!/usr/bin/env bash
# Analyze test coverage gaps in a project.
# Usage: bash analyze-coverage.sh [directory]
#
# Detects the project type and produces a coverage gap summary.

set -euo pipefail

DIR="${1:-.}"
cd "$DIR"

echo "=== Test Coverage Gap Analysis ==="
echo "Directory: $(pwd)"
echo ""

# Detect project type
detect_project() {
  if [ -f "go.mod" ]; then echo "go"
  elif [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then echo "python"
  elif [ -f "package.json" ]; then echo "node"
  elif [ -f "Cargo.toml" ]; then echo "rust"
  else echo "unknown"
  fi
}

PROJECT_TYPE=$(detect_project)
echo "Project type: $PROJECT_TYPE"
echo ""

# Count source and test files
echo "=== File Counts ==="
case "$PROJECT_TYPE" in
  go)
    SRC_COUNT=$(find . -name "*.go" -not -name "*_test.go" -not -path "./vendor/*" | wc -l | tr -d ' ')
    TEST_COUNT=$(find . -name "*_test.go" -not -path "./vendor/*" | wc -l | tr -d ' ')
    echo "Source files: $SRC_COUNT"
    echo "Test files: $TEST_COUNT"
    ;;
  python)
    SRC_COUNT=$(find . -name "*.py" -not -name "test_*" -not -name "*_test.py" -not -path "./.venv/*" -not -path "./venv/*" | wc -l | tr -d ' ')
    TEST_COUNT=$(find . -name "test_*.py" -o -name "*_test.py" | grep -v -E '\.venv|venv' | wc -l | tr -d ' ')
    echo "Source files: $SRC_COUNT"
    echo "Test files: $TEST_COUNT"
    ;;
  node)
    SRC_COUNT=$(find . -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" | grep -v node_modules | grep -v -E '\.test\.|\.spec\.|__tests__' | wc -l | tr -d ' ')
    TEST_COUNT=$(find . -name "*.test.ts" -o -name "*.spec.ts" -o -name "*.test.js" -o -name "*.spec.js" -o -name "*.test.tsx" -o -name "*.spec.tsx" | grep -v node_modules | wc -l | tr -d ' ')
    echo "Source files: $SRC_COUNT"
    echo "Test files: $TEST_COUNT"
    ;;
  *)
    echo "Unknown project type — manual analysis required"
    ;;
esac

if [ "$SRC_COUNT" -gt 0 ] 2>/dev/null; then
  RATIO=$(echo "scale=1; $TEST_COUNT * 100 / $SRC_COUNT" | bc 2>/dev/null || echo "N/A")
  echo "Test/source ratio: ${RATIO}%"
fi
echo ""

# Find source files without corresponding test files
echo "=== Source Files Without Tests ==="
case "$PROJECT_TYPE" in
  go)
    for src in $(find . -name "*.go" -not -name "*_test.go" -not -path "./vendor/*"); do
      test_file="${src%.go}_test.go"
      if [ ! -f "$test_file" ]; then
        echo "  UNTESTED: $src"
      fi
    done
    ;;
  python)
    for src in $(find . -name "*.py" -not -name "test_*" -not -name "*_test.py" -not -name "conftest.py" -not -name "__init__.py" -not -path "./.venv/*" -not -path "./venv/*"); do
      dir=$(dirname "$src")
      base=$(basename "$src" .py)
      if [ ! -f "$dir/test_${base}.py" ] && [ ! -f "tests/test_${base}.py" ] && [ ! -f "tests/unit/test_${base}.py" ]; then
        echo "  UNTESTED: $src"
      fi
    done
    ;;
  node)
    for src in $(find . -name "*.ts" -o -name "*.js" | grep -v node_modules | grep -v -E '\.test\.|\.spec\.|__tests__|\.d\.ts'); do
      dir=$(dirname "$src")
      base=$(basename "$src" | sed 's/\.[^.]*$//')
      ext=$(echo "$src" | grep -o '\.[^.]*$')
      if [ ! -f "$dir/${base}.test${ext}" ] && [ ! -f "$dir/__tests__/${base}.test${ext}" ] && [ ! -f "$dir/${base}.spec${ext}" ]; then
        echo "  UNTESTED: $src"
      fi
    done
    ;;
esac
echo ""

# Check for test infrastructure
echo "=== Test Infrastructure ==="
case "$PROJECT_TYPE" in
  node)
    if grep -q '"test"' package.json 2>/dev/null; then
      echo "  [OK] test script defined in package.json"
    else
      echo "  [MISSING] No test script in package.json"
    fi
    for runner in vitest jest "bun:test" mocha; do
      if grep -rq "$runner" package.json 2>/dev/null; then
        echo "  [OK] Test runner: $runner"
      fi
    done
    ;;
  python)
    if [ -f "conftest.py" ] || find . -name "conftest.py" -not -path "./.venv/*" | grep -q .; then
      echo "  [OK] conftest.py fixtures found"
    else
      echo "  [MISSING] No conftest.py — consider adding shared fixtures"
    fi
    ;;
  go)
    if find . -name "testutil_test.go" -o -name "*_testutil.go" | grep -q .; then
      echo "  [OK] Test utility files found"
    else
      echo "  [INFO] No testutil files — consider adding shared helpers"
    fi
    ;;
esac
echo ""

echo "=== Test Categories ==="
UNIT=$(find . -path "*/unit/*" -name "*test*" 2>/dev/null | wc -l | tr -d ' ')
INTEGRATION=$(find . -path "*/integration/*" -name "*test*" 2>/dev/null | wc -l | tr -d ' ')
E2E=$(find . -path "*/e2e/*" -name "*test*" 2>/dev/null | wc -l | tr -d ' ')
echo "  Unit tests: $UNIT files"
echo "  Integration tests: $INTEGRATION files"
echo "  E2E tests: $E2E files"

if [ "$INTEGRATION" = "0" ]; then
  echo "  [GAP] No integration tests found"
fi
if [ "$E2E" = "0" ]; then
  echo "  [GAP] No E2E tests found"
fi
echo ""
echo "=== Analysis Complete ==="
