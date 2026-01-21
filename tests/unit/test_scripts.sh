#!/bin/bash
# Test suite for development scripts
#
# Usage: bash tests/unit/test_scripts.sh
# Returns: 0 if all tests pass, 1 otherwise

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

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

# Test: new-feature.sh exists
test_new_feature_exists() {
    log_test "new-feature.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$SCRIPTS_DIR/new-feature.sh" ]]; then
        pass
    else
        fail "File not found: $SCRIPTS_DIR/new-feature.sh"
    fi
}

# Test: new-feature.sh is executable
test_new_feature_executable() {
    log_test "new-feature.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$SCRIPTS_DIR/new-feature.sh" ]]; then
        pass
    else
        fail "File not executable: $SCRIPTS_DIR/new-feature.sh"
    fi
}

# Test: new-feature.sh has usage help
test_new_feature_usage() {
    log_test "new-feature.sh shows usage on no args"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$SCRIPTS_DIR/new-feature.sh" 2>&1 || true)
    if echo "$output" | grep -q -i "usage"; then
        pass
    else
        fail "No usage message found"
    fi
}

# Test: check-planning.sh exists
test_check_planning_exists() {
    log_test "check-planning.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$SCRIPTS_DIR/check-planning.sh" ]]; then
        pass
    else
        fail "File not found: $SCRIPTS_DIR/check-planning.sh"
    fi
}

# Test: check-planning.sh is executable
test_check_planning_executable() {
    log_test "check-planning.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$SCRIPTS_DIR/check-planning.sh" ]]; then
        pass
    else
        fail "File not executable: $SCRIPTS_DIR/check-planning.sh"
    fi
}

# Test: check-completion.sh exists
test_check_completion_exists() {
    log_test "check-completion.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$SCRIPTS_DIR/check-completion.sh" ]]; then
        pass
    else
        fail "File not found: $SCRIPTS_DIR/check-completion.sh"
    fi
}

# Test: check-completion.sh is executable
test_check_completion_executable() {
    log_test "check-completion.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$SCRIPTS_DIR/check-completion.sh" ]]; then
        pass
    else
        fail "File not executable: $SCRIPTS_DIR/check-completion.sh"
    fi
}

# Test: scripts use set -euo pipefail
test_scripts_strict_mode() {
    log_test "scripts use strict mode (set -euo pipefail)"
    TESTS_RUN=$((TESTS_RUN + 1))
    local all_strict=true
    for script in "$SCRIPTS_DIR"/*.sh; do
        if [[ -f "$script" ]]; then
            if ! grep -q "set -euo pipefail" "$script"; then
                fail "Missing strict mode in: $(basename "$script")"
                all_strict=false
            fi
        fi
    done
    if [[ "$all_strict" == "true" ]]; then
        pass
    fi
}

# Test: scripts have shebang
test_scripts_shebang() {
    log_test "scripts have bash shebang"
    TESTS_RUN=$((TESTS_RUN + 1))
    local all_have_shebang=true
    for script in "$SCRIPTS_DIR"/*.sh; do
        if [[ -f "$script" ]]; then
            local first_line
            first_line=$(head -n 1 "$script")
            if [[ "$first_line" != "#!/bin/bash" ]]; then
                fail "Invalid shebang in: $(basename "$script")"
                all_have_shebang=false
            fi
        fi
    done
    if [[ "$all_have_shebang" == "true" ]]; then
        pass
    fi
}

# Run all tests
main() {
    echo "=========================================="
    echo "Testing: scripts/*.sh"
    echo "=========================================="
    echo ""

    test_new_feature_exists
    test_new_feature_executable
    test_new_feature_usage
    test_check_planning_exists
    test_check_planning_executable
    test_check_completion_exists
    test_check_completion_executable
    test_scripts_strict_mode
    test_scripts_shebang

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
