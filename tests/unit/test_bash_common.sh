#!/bin/bash
# Test suite for tools/lib/common.sh
#
# Usage: bash tests/unit/test_bash_common.sh
# Returns: 0 if all tests pass, 1 otherwise

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
COMMON_SH="$PROJECT_ROOT/tools/lib/common.sh"

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

# Test: common.sh exists
test_common_sh_exists() {
    log_test "common.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$COMMON_SH" ]]; then
        pass
    else
        fail "File not found: $COMMON_SH"
    fi
}

# Test: common.sh is sourceable
test_common_sh_sourceable() {
    log_test "common.sh is sourceable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH'" 2>/dev/null; then
        pass
    else
        fail "Failed to source common.sh"
    fi
}

# Test: json_escape function exists
test_json_escape_exists() {
    log_test "json_escape function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type json_escape" >/dev/null 2>&1; then
        pass
    else
        fail "json_escape function not found"
    fi
}

# Test: json_escape handles quotes
test_json_escape_quotes() {
    log_test "json_escape escapes quotes"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$(bash -c "source '$COMMON_SH' && json_escape 'test\"quote'")
    if [[ "$result" == 'test\"quote' ]]; then
        pass
    else
        fail "Expected 'test\\\"quote', got '$result'"
    fi
}

# Test: emit_result function exists
test_emit_result_exists() {
    log_test "emit_result function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type emit_result" >/dev/null 2>&1; then
        pass
    else
        fail "emit_result function not found"
    fi
}

# Test: emit_result returns valid JSON
test_emit_result_valid_json() {
    log_test "emit_result returns valid JSON"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$(bash -c "source '$COMMON_SH' && emit_result '[]'")
    if echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Invalid JSON: $result"
    fi
}

# Test: emit_result has success field
test_emit_result_has_success() {
    log_test "emit_result has success: true"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$(bash -c "source '$COMMON_SH' && emit_result '[]'")
    local success
    success=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['success'])")
    if [[ "$success" == "True" ]]; then
        pass
    else
        fail "Expected success: true, got: $success"
    fi
}

# Test: emit_error function exists
test_emit_error_exists() {
    log_test "emit_error function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type emit_error" >/dev/null 2>&1; then
        pass
    else
        fail "emit_error function not found"
    fi
}

# Test: emit_error returns valid JSON
test_emit_error_valid_json() {
    log_test "emit_error returns valid JSON (non-exit mode)"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    # Use exit code 0 to prevent script exit
    result=$(bash -c "source '$COMMON_SH' && emit_error 'test error' 0")
    if echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Invalid JSON: $result"
    fi
}

# Test: emit_error has success false
test_emit_error_has_success_false() {
    log_test "emit_error has success: false"
    TESTS_RUN=$((TESTS_RUN + 1))
    local result
    result=$(bash -c "source '$COMMON_SH' && emit_error 'test error' 0")
    local success
    success=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['success'])")
    if [[ "$success" == "False" ]]; then
        pass
    else
        fail "Expected success: false, got: $success"
    fi
}

# Test: emit_partial function exists
test_emit_partial_exists() {
    log_test "emit_partial function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type emit_partial" >/dev/null 2>&1; then
        pass
    else
        fail "emit_partial function not found"
    fi
}

# Test: log_info function exists
test_log_info_exists() {
    log_test "log_info function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type log_info" >/dev/null 2>&1; then
        pass
    else
        fail "log_info function not found"
    fi
}

# Test: log_error function exists
test_log_error_exists() {
    log_test "log_error function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type log_error" >/dev/null 2>&1; then
        pass
    else
        fail "log_error function not found"
    fi
}

# Test: require_command function exists
test_require_command_exists() {
    log_test "require_command function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type require_command" >/dev/null 2>&1; then
        pass
    else
        fail "require_command function not found"
    fi
}

# Test: get_project_root function exists
test_get_project_root_exists() {
    log_test "get_project_root function exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if bash -c "source '$COMMON_SH' && type get_project_root" >/dev/null 2>&1; then
        pass
    else
        fail "get_project_root function not found"
    fi
}

# Run all tests
main() {
    echo "=========================================="
    echo "Testing: tools/lib/common.sh"
    echo "=========================================="
    echo ""

    test_common_sh_exists
    test_common_sh_sourceable
    test_json_escape_exists
    test_json_escape_quotes
    test_emit_result_exists
    test_emit_result_valid_json
    test_emit_result_has_success
    test_emit_error_exists
    test_emit_error_valid_json
    test_emit_error_has_success_false
    test_emit_partial_exists
    test_log_info_exists
    test_log_error_exists
    test_require_command_exists
    test_get_project_root_exists

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
