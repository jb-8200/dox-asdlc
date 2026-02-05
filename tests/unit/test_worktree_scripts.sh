#!/bin/bash
# Unit tests for git worktree management scripts
#
# Usage: bash tests/unit/test_worktree_scripts.sh
# Returns: 0 if all tests pass, 1 otherwise
#
# Note: These tests verify script existence, permissions, help text, and
# argument validation. Integration tests in tests/integration/ test actual
# git worktree operations.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
WORKTREE_SCRIPTS_DIR="$PROJECT_ROOT/scripts/worktree"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

skip() {
    echo -e "${YELLOW}  SKIP: $1${NC}"
}

# ==============================================================================
# T01: setup-agent.sh tests
# ==============================================================================

test_setup_agent_exists() {
    log_test "setup-agent.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$WORKTREE_SCRIPTS_DIR/setup-agent.sh" ]]; then
        pass
    else
        fail "File not found: $WORKTREE_SCRIPTS_DIR/setup-agent.sh"
    fi
}

test_setup_agent_executable() {
    log_test "setup-agent.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$WORKTREE_SCRIPTS_DIR/setup-agent.sh" ]]; then
        pass
    else
        fail "File not executable: $WORKTREE_SCRIPTS_DIR/setup-agent.sh"
    fi
}

test_setup_agent_shebang() {
    log_test "setup-agent.sh has bash shebang"
    TESTS_RUN=$((TESTS_RUN + 1))
    local first_line
    first_line=$(head -n 1 "$WORKTREE_SCRIPTS_DIR/setup-agent.sh")
    if [[ "$first_line" == "#!/bin/bash" ]]; then
        pass
    else
        fail "Invalid shebang: $first_line"
    fi
}

test_setup_agent_strict_mode() {
    log_test "setup-agent.sh uses strict mode"
    TESTS_RUN=$((TESTS_RUN + 1))
    if grep -q "set -euo pipefail" "$WORKTREE_SCRIPTS_DIR/setup-agent.sh"; then
        pass
    else
        fail "Missing: set -euo pipefail"
    fi
}

test_setup_agent_shows_help_no_args() {
    log_test "setup-agent.sh shows help with no args"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/setup-agent.sh" 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_setup_agent_shows_help_h_flag() {
    log_test "setup-agent.sh shows help with -h flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/setup-agent.sh" -h 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_setup_agent_shows_help_help_flag() {
    log_test "setup-agent.sh shows help with --help flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/setup-agent.sh" --help 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_setup_agent_rejects_invalid_role() {
    log_test "setup-agent.sh rejects invalid role"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    local exit_code=0
    output=$("$WORKTREE_SCRIPTS_DIR/setup-agent.sh" "invalid_role" 2>&1) || exit_code=$?
    if [[ $exit_code -ne 0 ]] && echo "$output" | grep -qi "invalid\|error\|unknown"; then
        pass
    else
        fail "Did not reject invalid role (exit=$exit_code)"
    fi
}

test_setup_agent_valid_roles_list() {
    log_test "setup-agent.sh help shows valid roles"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/setup-agent.sh" --help 2>&1 || true)
    # Should show at least backend, frontend, orchestrator, devops
    if echo "$output" | grep -q "backend" && \
       echo "$output" | grep -q "frontend" && \
       echo "$output" | grep -q "orchestrator" && \
       echo "$output" | grep -q "devops"; then
        pass
    else
        fail "Help does not list all valid roles"
    fi
}

# ==============================================================================
# T02: list-agents.sh tests
# ==============================================================================

test_list_agents_exists() {
    log_test "list-agents.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$WORKTREE_SCRIPTS_DIR/list-agents.sh" ]]; then
        pass
    else
        fail "File not found: $WORKTREE_SCRIPTS_DIR/list-agents.sh"
    fi
}

test_list_agents_executable() {
    log_test "list-agents.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$WORKTREE_SCRIPTS_DIR/list-agents.sh" ]]; then
        pass
    else
        fail "File not executable: $WORKTREE_SCRIPTS_DIR/list-agents.sh"
    fi
}

test_list_agents_shebang() {
    log_test "list-agents.sh has bash shebang"
    TESTS_RUN=$((TESTS_RUN + 1))
    local first_line
    first_line=$(head -n 1 "$WORKTREE_SCRIPTS_DIR/list-agents.sh")
    if [[ "$first_line" == "#!/bin/bash" ]]; then
        pass
    else
        fail "Invalid shebang: $first_line"
    fi
}

test_list_agents_strict_mode() {
    log_test "list-agents.sh uses strict mode"
    TESTS_RUN=$((TESTS_RUN + 1))
    if grep -q "set -euo pipefail" "$WORKTREE_SCRIPTS_DIR/list-agents.sh"; then
        pass
    else
        fail "Missing: set -euo pipefail"
    fi
}

test_list_agents_outputs_json() {
    log_test "list-agents.sh outputs valid JSON"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/list-agents.sh" 2>&1 || true)
    # Output should be valid JSON (start with [ or {)
    if echo "$output" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        pass
    else
        fail "Output is not valid JSON: $output"
    fi
}

test_list_agents_help_flag() {
    log_test "list-agents.sh shows help with -h flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/list-agents.sh" -h 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

# ==============================================================================
# T03: teardown-agent.sh tests
# ==============================================================================

test_teardown_agent_exists() {
    log_test "teardown-agent.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" ]]; then
        pass
    else
        fail "File not found: $WORKTREE_SCRIPTS_DIR/teardown-agent.sh"
    fi
}

test_teardown_agent_executable() {
    log_test "teardown-agent.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" ]]; then
        pass
    else
        fail "File not executable: $WORKTREE_SCRIPTS_DIR/teardown-agent.sh"
    fi
}

test_teardown_agent_shebang() {
    log_test "teardown-agent.sh has bash shebang"
    TESTS_RUN=$((TESTS_RUN + 1))
    local first_line
    first_line=$(head -n 1 "$WORKTREE_SCRIPTS_DIR/teardown-agent.sh")
    if [[ "$first_line" == "#!/bin/bash" ]]; then
        pass
    else
        fail "Invalid shebang: $first_line"
    fi
}

test_teardown_agent_strict_mode() {
    log_test "teardown-agent.sh uses strict mode"
    TESTS_RUN=$((TESTS_RUN + 1))
    if grep -q "set -euo pipefail" "$WORKTREE_SCRIPTS_DIR/teardown-agent.sh"; then
        pass
    else
        fail "Missing: set -euo pipefail"
    fi
}

test_teardown_agent_shows_help_no_args() {
    log_test "teardown-agent.sh shows help with no args"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_teardown_agent_help_flag() {
    log_test "teardown-agent.sh shows help with --help flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" --help 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_teardown_agent_has_merge_flag() {
    log_test "teardown-agent.sh supports --merge flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" --help 2>&1 || true)
    if echo "$output" | grep -q "\-\-merge"; then
        pass
    else
        fail "Help does not document --merge flag"
    fi
}

test_teardown_agent_has_abandon_flag() {
    log_test "teardown-agent.sh supports --abandon flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" --help 2>&1 || true)
    if echo "$output" | grep -q "\-\-abandon"; then
        pass
    else
        fail "Help does not document --abandon flag"
    fi
}

test_teardown_agent_rejects_invalid_role() {
    log_test "teardown-agent.sh rejects invalid role"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    local exit_code=0
    output=$("$WORKTREE_SCRIPTS_DIR/teardown-agent.sh" "invalid_role" --abandon 2>&1) || exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        pass
    else
        fail "Did not reject invalid role (exit=$exit_code)"
    fi
}

# ==============================================================================
# T04: merge-agent.sh tests
# ==============================================================================

test_merge_agent_exists() {
    log_test "merge-agent.sh exists"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$WORKTREE_SCRIPTS_DIR/merge-agent.sh" ]]; then
        pass
    else
        fail "File not found: $WORKTREE_SCRIPTS_DIR/merge-agent.sh"
    fi
}

test_merge_agent_executable() {
    log_test "merge-agent.sh is executable"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -x "$WORKTREE_SCRIPTS_DIR/merge-agent.sh" ]]; then
        pass
    else
        fail "File not executable: $WORKTREE_SCRIPTS_DIR/merge-agent.sh"
    fi
}

test_merge_agent_shebang() {
    log_test "merge-agent.sh has bash shebang"
    TESTS_RUN=$((TESTS_RUN + 1))
    local first_line
    first_line=$(head -n 1 "$WORKTREE_SCRIPTS_DIR/merge-agent.sh")
    if [[ "$first_line" == "#!/bin/bash" ]]; then
        pass
    else
        fail "Invalid shebang: $first_line"
    fi
}

test_merge_agent_strict_mode() {
    log_test "merge-agent.sh uses strict mode"
    TESTS_RUN=$((TESTS_RUN + 1))
    if grep -q "set -euo pipefail" "$WORKTREE_SCRIPTS_DIR/merge-agent.sh"; then
        pass
    else
        fail "Missing: set -euo pipefail"
    fi
}

test_merge_agent_shows_help_no_args() {
    log_test "merge-agent.sh shows help with no args"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/merge-agent.sh" 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_merge_agent_help_flag() {
    log_test "merge-agent.sh shows help with --help flag"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    output=$("$WORKTREE_SCRIPTS_DIR/merge-agent.sh" --help 2>&1 || true)
    if echo "$output" | grep -qi "usage"; then
        pass
    else
        fail "No usage message found in output"
    fi
}

test_merge_agent_rejects_invalid_role() {
    log_test "merge-agent.sh rejects invalid role"
    TESTS_RUN=$((TESTS_RUN + 1))
    local output
    local exit_code=0
    output=$("$WORKTREE_SCRIPTS_DIR/merge-agent.sh" "invalid_role" 2>&1) || exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        pass
    else
        fail "Did not reject invalid role (exit=$exit_code)"
    fi
}

# ==============================================================================
# Main test runner
# ==============================================================================

main() {
    echo "=========================================="
    echo "Testing: scripts/worktree/*.sh"
    echo "=========================================="
    echo ""

    # Check if scripts directory exists first
    if [[ ! -d "$WORKTREE_SCRIPTS_DIR" ]]; then
        echo -e "${RED}ERROR: scripts/worktree/ directory does not exist${NC}"
        echo "Run the implementation first, then re-run tests."
        exit 1
    fi

    echo "--- T01: setup-agent.sh ---"
    test_setup_agent_exists
    test_setup_agent_executable
    test_setup_agent_shebang
    test_setup_agent_strict_mode
    test_setup_agent_shows_help_no_args
    test_setup_agent_shows_help_h_flag
    test_setup_agent_shows_help_help_flag
    test_setup_agent_rejects_invalid_role
    test_setup_agent_valid_roles_list
    echo ""

    echo "--- T02: list-agents.sh ---"
    test_list_agents_exists
    test_list_agents_executable
    test_list_agents_shebang
    test_list_agents_strict_mode
    test_list_agents_outputs_json
    test_list_agents_help_flag
    echo ""

    echo "--- T03: teardown-agent.sh ---"
    test_teardown_agent_exists
    test_teardown_agent_executable
    test_teardown_agent_shebang
    test_teardown_agent_strict_mode
    test_teardown_agent_shows_help_no_args
    test_teardown_agent_help_flag
    test_teardown_agent_has_merge_flag
    test_teardown_agent_has_abandon_flag
    test_teardown_agent_rejects_invalid_role
    echo ""

    echo "--- T04: merge-agent.sh ---"
    test_merge_agent_exists
    test_merge_agent_executable
    test_merge_agent_shebang
    test_merge_agent_strict_mode
    test_merge_agent_shows_help_no_args
    test_merge_agent_help_flag
    test_merge_agent_rejects_invalid_role
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
