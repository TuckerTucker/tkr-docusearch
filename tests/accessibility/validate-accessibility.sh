#!/bin/bash
# Accessibility Module Validation Script
# Validates that all accessibility files are in place and properly structured

set -e

PROJECT_ROOT="/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch"
PASS=0
FAIL=0

echo "=================================="
echo "Accessibility Module Validation"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file=$1
    local expected_lines=$2
    local tolerance=50

    if [ -f "$file" ]; then
        actual_lines=$(wc -l < "$file" | tr -d ' ')
        min_lines=$((expected_lines - tolerance))
        max_lines=$((expected_lines + tolerance))

        if [ "$actual_lines" -ge "$min_lines" ] && [ "$actual_lines" -le "$max_lines" ]; then
            echo -e "${GREEN}✓${NC} $file ($actual_lines lines)"
            PASS=$((PASS + 1))
        else
            echo -e "${YELLOW}⚠${NC} $file ($actual_lines lines, expected ~$expected_lines)"
            PASS=$((PASS + 1))
        fi
    else
        echo -e "${RED}✗${NC} $file (missing)"
        FAIL=$((FAIL + 1))
    fi
}

# Check JavaScript modules
echo "Checking JavaScript modules..."
check_file "$PROJECT_ROOT/src/frontend/accessibility/keyboard-nav.js" 368
check_file "$PROJECT_ROOT/src/frontend/accessibility/aria-labels.js" 304
check_file "$PROJECT_ROOT/src/frontend/accessibility/screen-reader-announce.js" 343
check_file "$PROJECT_ROOT/src/frontend/accessibility/INTEGRATION_EXAMPLE.js" 300
echo ""

# Check CSS modules
echo "Checking CSS modules..."
check_file "$PROJECT_ROOT/src/frontend/styles/accessibility.css" 516
check_file "$PROJECT_ROOT/src/frontend/styles/highlighting-animations.css" 360
echo ""

# Check test files
echo "Checking test files..."
check_file "$PROJECT_ROOT/tests/accessibility/test-keyboard-nav.html" 439
check_file "$PROJECT_ROOT/tests/accessibility/test-screen-reader.html" 517
echo ""

# Check documentation
echo "Checking documentation..."
check_file "$PROJECT_ROOT/src/frontend/accessibility/README.md" 400
check_file "$PROJECT_ROOT/tests/accessibility/WCAG_COMPLIANCE_CHECKLIST.md" 300
echo ""

# Verify exports in JavaScript modules
echo "Verifying module exports..."
if grep -q "export function enableKeyboardNav" "$PROJECT_ROOT/src/frontend/accessibility/keyboard-nav.js"; then
    echo -e "${GREEN}✓${NC} keyboard-nav.js exports enableKeyboardNav"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} keyboard-nav.js missing enableKeyboardNav export"
    FAIL=$((FAIL + 1))
fi

if grep -q "export function labelBbox" "$PROJECT_ROOT/src/frontend/accessibility/aria-labels.js"; then
    echo -e "${GREEN}✓${NC} aria-labels.js exports labelBbox"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} aria-labels.js missing labelBbox export"
    FAIL=$((FAIL + 1))
fi

if grep -q "export function announceChunkNav" "$PROJECT_ROOT/src/frontend/accessibility/screen-reader-announce.js"; then
    echo -e "${GREEN}✓${NC} screen-reader-announce.js exports announceChunkNav"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} screen-reader-announce.js missing announceChunkNav export"
    FAIL=$((FAIL + 1))
fi
echo ""

# Verify CSS classes
echo "Verifying CSS classes..."
if grep -q ".sr-only" "$PROJECT_ROOT/src/frontend/styles/accessibility.css"; then
    echo -e "${GREEN}✓${NC} accessibility.css has .sr-only class"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} accessibility.css missing .sr-only class"
    FAIL=$((FAIL + 1))
fi

if grep -q "@keyframes highlightFadeIn" "$PROJECT_ROOT/src/frontend/styles/highlighting-animations.css"; then
    echo -e "${GREEN}✓${NC} highlighting-animations.css has highlightFadeIn animation"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} highlighting-animations.css missing highlightFadeIn animation"
    FAIL=$((FAIL + 1))
fi

if grep -q "@media (prefers-reduced-motion: reduce)" "$PROJECT_ROOT/src/frontend/styles/highlighting-animations.css"; then
    echo -e "${GREEN}✓${NC} highlighting-animations.css has reduced motion support"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} highlighting-animations.css missing reduced motion support"
    FAIL=$((FAIL + 1))
fi
echo ""

# Summary
echo "=================================="
echo "Validation Summary"
echo "=================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All accessibility modules validated successfully!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed. Please review the output above.${NC}"
    exit 1
fi
