#!/bin/bash
# Test suite for tool wrapper stubs
#
# Usage: bash tests/unit/test_tool_stubs.sh
# Returns: 0 if all tests pass, 1 otherwise

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TOOLS_DIR="$PROJECT_ROOT/tools"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_test() {
    echo "TEST: $1"
}

pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}  PASS${NC}"
}

fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}  FAIL: $1${NC}"
}

# Test: test.sh exists
test_test_sh_exists() {
    log_test "test.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$TOOLS_DIR/test.sh" ]]; then
        pass
    else
        fail "File not found: $TOOLS_DIR/test.sh"
    fi
}

# Test: test.sh is executable
test_test_sh_executable() {
    log_test "test.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$TOOLS_DIR/test.sh" ]]; then
        pass
    else
        fail "File not executable: $TOOLS_DIR/test.sh"
    fi
}

# Test: test.sh returns valid JSON
test_test_sh_valid_json() {
    log_test "test.sh returns valid JSON"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    # Run test.sh with the project root as target (which exists)
    result=$("$TOOLS_DIR/test.sh" "$PROJECT_ROOT/tests" 2>/dev/null)
    if echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Invalid JSON: $result"
    fi
}

# Test: test.sh JSON has required fields
test_test_sh_json_fields() {
    log_test "test.sh JSON has success and results fields"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$("$TOOLS_DIR/test.sh" "$PROJECT_ROOT/tests" 2>/dev/null)
    local has_success
    local has_results
    has_success=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print('success' in d)")
    has_results=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print('results' in d)")
    if [[ "$has_success" == "True" && "$has_results" == "True" ]]; then
        pass
    else
        fail "Missing fields in JSON"
    fi
}

# Test: lint.sh exists
test_lint_sh_exists() {
    log_test "lint.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$TOOLS_DIR/lint.sh" ]]; then
        pass
    else
        fail "File not found: $TOOLS_DIR/lint.sh"
    fi
}

# Test: lint.sh is executable
test_lint_sh_executable() {
    log_test "lint.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$TOOLS_DIR/lint.sh" ]]; then
        pass
    else
        fail "File not executable: $TOOLS_DIR/lint.sh"
    fi
}

# Test: lint.sh returns valid JSON
test_lint_sh_valid_json() {
    log_test "lint.sh returns valid JSON"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$("$TOOLS_DIR/lint.sh" "$PROJECT_ROOT/src" 2>/dev/null)
    if echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Invalid JSON: $result"
    fi
}

# Test: lint.sh JSON has required fields
test_lint_sh_json_fields() {
    log_test "lint.sh JSON has success and results fields"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$("$TOOLS_DIR/lint.sh" "$PROJECT_ROOT/src" 2>/dev/null)
    local has_success
    local has_results
    has_success=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print('success' in d)")
    has_results=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print('results' in d)")
    if [[ "$has_success" == "True" && "$has_results" == "True" ]]; then
        pass
    else
        fail "Missing fields in JSON"
    fi
}

# Test: e2e.sh exists
test_e2e_sh_exists() {
    log_test "e2e.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$TOOLS_DIR/e2e.sh" ]]; then
        pass
    else
        fail "File not found: $TOOLS_DIR/e2e.sh"
    fi
}

# Test: e2e.sh is executable
test_e2e_sh_executable() {
    log_test "e2e.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$TOOLS_DIR/e2e.sh" ]]; then
        pass
    else
        fail "File not executable: $TOOLS_DIR/e2e.sh"
    fi
}

# Test: e2e.sh returns valid JSON
test_e2e_sh_valid_json() {
    log_test "e2e.sh returns valid JSON"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$("$TOOLS_DIR/e2e.sh" 2>/dev/null)
    if echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Invalid JSON: $result"
    fi
}

# Test: all tools source common.sh
test_tools_source_common() {
    log_test "all tool scripts source common.sh"
    TESTS_RUN=$((TESTS_RUN + 1))
    local all_source=true
    for tool in test.sh lint.sh e2e.sh; do
        if [[ -f "$TOOLS_DIR/$tool" ]]; then
            if ! grep -q "source.*common.sh" "$TOOLS_DIR/$tool"; then
                fail "Tool $tool doesn't source common.sh"
                all_source=false
            fi
        fi
    done
    if [[ "$all_source" == "true" ]]; then
        pass
    fi
}

# Test: tools use strict mode
test_tools_strict_mode() {
    log_test "all tool scripts use strict mode"
    TESTS_RUN=$((TESTS_RUN + 1))
    local all_strict=true
    for tool in test.sh lint.sh e2e.sh; do
        if [[ -f "$TOOLS_DIR/$tool" ]]; then
            if ! grep -q "set -euo pipefail" "$TOOLS_DIR/$tool"; then
                fail "Tool $tool missing strict mode"
                all_strict=false
            fi
        fi
    done
    if [[ "$all_strict" == "true" ]]; then
        pass
    fi
}

# Test: lib/common.sh exists
test_lib_common_exists() {
    log_test "lib/common.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$TOOLS_DIR/lib/common.sh" ]]; then
        pass
    else
        fail "File not found: $TOOLS_DIR/lib/common.sh"
    fi
}

# Run all tests
main() {
    echo "=========================================="
    echo "Testing: tools/*.sh stubs"
    echo "=========================================="
    echo ""

    test_test_sh_exists
    test_test_sh_executable
    test_test_sh_valid_json
    test_test_sh_json_fields
    test_lint_sh_exists
    test_lint_sh_executable
    test_lint_sh_valid_json
    test_lint_sh_json_fields
    test_e2e_sh_exists
    test_e2e_sh_executable
    test_e2e_sh_valid_json
    test_tools_source_common
    test_tools_strict_mode
    test_lib_common_exists

    echo ""
    echo "=========================================="
    echo "Results: $TESTS_PASSED/$TESTS_RUN passed, $TESTS_FAILED failed"
    echo "=========================================="

    if [[ $TESTS_FAILED -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
