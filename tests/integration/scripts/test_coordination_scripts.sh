#!/bin/bash
# Integration tests for coordination bash scripts.
#
# Tests hybrid mode detection and fallback behavior.
# Requires: Redis running for Redis mode tests
#
# Usage:
#   ./tests/integration/scripts/test_coordination_scripts.sh
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test instance ID
export CLAUDE_INSTANCE_ID="test-cli-$$"

# Cleanup function
cleanup() {
    # Clean up test messages from filesystem
    rm -f "$PROJECT_ROOT/.claude/coordination/messages/"*"-test-cli-"* 2>/dev/null || true
    rm -f "$PROJECT_ROOT/.claude/coordination/pending-acks/"*"-test-cli-"* 2>/dev/null || true

    # Unset environment
    unset CLAUDE_INSTANCE_ID
    unset DISABLE_REDIS_COORDINATION
}

trap cleanup EXIT

# Test helper functions
log_test() {
    echo -e "\n${YELLOW}TEST:${NC} $1"
}

pass() {
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

fail() {
    echo -e "${RED}FAIL${NC}: $1"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

# Check if Redis is available
redis_available() {
    redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ping 2>/dev/null | grep -q "PONG"
}

# =============================================================================
# Filesystem Mode Tests
# =============================================================================

test_publish_filesystem_mode() {
    log_test "publish-message.sh in filesystem mode"

    # Force filesystem mode
    export DISABLE_REDIS_COORDINATION=true

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        GENERAL \
        "Test Subject $$" \
        "Test Description" \
        --to orchestrator \
        2>&1)

    if echo "$output" | grep -q "Message published:"; then
        if echo "$output" | grep -q "Type: GENERAL"; then
            pass
        else
            fail "Missing type in output"
        fi
    else
        fail "Publish failed: $output"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_check_filesystem_mode() {
    log_test "check-messages.sh in filesystem mode"

    # Force filesystem mode
    export DISABLE_REDIS_COORDINATION=true

    # First publish a message
    "$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        GENERAL \
        "Check Test $$" \
        "Test Description" \
        --to orchestrator \
        >/dev/null 2>&1

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/check-messages.sh" --all 2>&1)

    if echo "$output" | grep -q "=== Coordination Messages ==="; then
        pass
    else
        fail "Check failed: $output"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_ack_filesystem_mode() {
    log_test "ack-message.sh in filesystem mode"

    # Force filesystem mode
    export DISABLE_REDIS_COORDINATION=true

    # Publish a message that requires ack
    local publish_output
    publish_output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        READY_FOR_REVIEW \
        "Ack Test $$" \
        "Test Description" \
        --to orchestrator \
        2>&1)

    # Extract message ID
    local msg_id
    msg_id=$(echo "$publish_output" | grep "ID:" | head -1 | awk '{print $2}')

    if [[ -z "$msg_id" ]]; then
        fail "Could not extract message ID from publish output"
        return
    fi

    # Acknowledge it
    local ack_output
    ack_output=$("$PROJECT_ROOT/scripts/coordination/ack-message.sh" \
        "$msg_id" \
        --comment "Test acknowledgment" \
        2>&1)

    if echo "$ack_output" | grep -q "Message acknowledged:"; then
        pass
    else
        fail "Ack failed: $ack_output"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_pending_filter_filesystem() {
    log_test "check-messages.sh --pending in filesystem mode"

    export DISABLE_REDIS_COORDINATION=true

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/check-messages.sh" --pending 2>&1)

    if echo "$output" | grep -q "Messages Pending Acknowledgment:"; then
        pass
    else
        fail "Pending filter failed: $output"
    fi

    unset DISABLE_REDIS_COORDINATION
}

# =============================================================================
# Backend Detection Tests
# =============================================================================

test_backend_detection_with_redis_disabled() {
    log_test "Backend detection with DISABLE_REDIS_COORDINATION=true"

    export DISABLE_REDIS_COORDINATION=true

    # Source common.sh and test detection
    source "$PROJECT_ROOT/scripts/coordination/lib/common.sh"

    local backend
    backend=$(check_coordination_backend)

    if [[ "$backend" == "filesystem" ]]; then
        pass
    else
        fail "Expected 'filesystem', got '$backend'"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_backend_detection_without_instance_id() {
    log_test "Backend detection without CLAUDE_INSTANCE_ID"

    # Save and unset instance ID
    local saved_id="$CLAUDE_INSTANCE_ID"
    unset CLAUDE_INSTANCE_ID

    source "$PROJECT_ROOT/scripts/coordination/lib/common.sh"

    local backend
    backend=$(check_coordination_backend)

    # Should fall back to filesystem without instance ID
    if [[ "$backend" == "filesystem" ]]; then
        pass
    else
        fail "Expected 'filesystem', got '$backend'"
    fi

    # Restore
    export CLAUDE_INSTANCE_ID="$saved_id"
}

# =============================================================================
# Redis Mode Tests (only if Redis available)
# =============================================================================

test_publish_redis_mode() {
    if ! redis_available; then
        echo -e "${YELLOW}SKIP${NC}: Redis not available"
        return
    fi

    log_test "publish-message.sh with Redis backend"

    # Ensure Redis mode is enabled (unset the disable flag)
    unset DISABLE_REDIS_COORDINATION

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        GENERAL \
        "Redis Test $$" \
        "Test Description" \
        --to orchestrator \
        2>&1) || true

    # Check if it used Redis backend
    if echo "$output" | grep -q "Backend: Redis"; then
        if echo "$output" | grep -q "Message published:"; then
            pass
        else
            fail "Publish failed: $output"
        fi
    elif echo "$output" | grep -q "Message published:"; then
        # Fallback to filesystem is also acceptable
        echo -e "${YELLOW}NOTE${NC}: Fell back to filesystem mode"
        pass
    else
        fail "Publish failed: $output"
    fi
}

test_check_redis_mode() {
    if ! redis_available; then
        echo -e "${YELLOW}SKIP${NC}: Redis not available"
        return
    fi

    log_test "check-messages.sh with Redis backend"

    unset DISABLE_REDIS_COORDINATION

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/check-messages.sh" --all 2>&1) || true

    if echo "$output" | grep -q "=== Coordination Messages ==="; then
        pass
    else
        fail "Check failed: $output"
    fi
}

# =============================================================================
# Output Format Compatibility Tests
# =============================================================================

test_publish_output_format() {
    log_test "publish-message.sh output format compatibility"

    export DISABLE_REDIS_COORDINATION=true

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        GENERAL \
        "Format Test" \
        "Description" \
        --to orchestrator \
        2>&1)

    # Check required output fields
    local has_id has_type has_from has_subject
    has_id=$(echo "$output" | grep -c "ID:") || true
    has_type=$(echo "$output" | grep -c "Type:") || true
    has_from=$(echo "$output" | grep -c "From:") || true
    has_subject=$(echo "$output" | grep -c "Subject:") || true

    if [[ "$has_id" -gt 0 && "$has_type" -gt 0 && "$has_from" -gt 0 && "$has_subject" -gt 0 ]]; then
        pass
    else
        fail "Missing required output fields"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_ack_output_format() {
    log_test "ack-message.sh output format compatibility"

    export DISABLE_REDIS_COORDINATION=true

    # Publish then ack
    local publish_output
    publish_output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        READY_FOR_REVIEW \
        "Ack Format Test" \
        "Description" \
        --to orchestrator \
        2>&1)

    local msg_id
    msg_id=$(echo "$publish_output" | grep "ID:" | head -1 | awk '{print $2}')

    local output
    output=$("$PROJECT_ROOT/scripts/coordination/ack-message.sh" "$msg_id" 2>&1)

    # Check required output fields
    local has_id has_acker has_time
    has_id=$(echo "$output" | grep -c "ID:") || true
    has_acker=$(echo "$output" | grep -c "Acknowledged by:") || true
    has_time=$(echo "$output" | grep -c "Time:") || true

    if [[ "$has_id" -gt 0 && "$has_acker" -gt 0 && "$has_time" -gt 0 ]]; then
        pass
    else
        fail "Missing required output fields: $output"
    fi

    unset DISABLE_REDIS_COORDINATION
}

# =============================================================================
# Error Handling Tests
# =============================================================================

test_publish_invalid_type() {
    log_test "publish-message.sh rejects invalid message type"

    export DISABLE_REDIS_COORDINATION=true

    local output
    local exit_code=0
    output=$("$PROJECT_ROOT/scripts/coordination/publish-message.sh" \
        INVALID_TYPE \
        "Test" \
        "Description" \
        2>&1) || exit_code=$?

    if [[ "$exit_code" -ne 0 ]] && echo "$output" | grep -qi "invalid"; then
        pass
    else
        fail "Should reject invalid type (exit code: $exit_code)"
    fi

    unset DISABLE_REDIS_COORDINATION
}

test_ack_nonexistent_message() {
    log_test "ack-message.sh handles nonexistent message"

    export DISABLE_REDIS_COORDINATION=true

    local output
    local exit_code=0
    output=$("$PROJECT_ROOT/scripts/coordination/ack-message.sh" \
        "msg-nonexistent-$$" \
        2>&1) || exit_code=$?

    if [[ "$exit_code" -ne 0 ]] && echo "$output" | grep -qi "not found"; then
        pass
    else
        fail "Should handle nonexistent message (exit code: $exit_code)"
    fi

    unset DISABLE_REDIS_COORDINATION
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
    echo ""
    echo "=== Coordination Bash Script Integration Tests ==="
    echo ""
    echo "Test instance: $CLAUDE_INSTANCE_ID"
    echo ""

    # Filesystem mode tests
    echo -e "\n${YELLOW}--- Filesystem Mode Tests ---${NC}"
    test_publish_filesystem_mode
    test_check_filesystem_mode
    test_ack_filesystem_mode
    test_pending_filter_filesystem

    # Backend detection tests
    echo -e "\n${YELLOW}--- Backend Detection Tests ---${NC}"
    test_backend_detection_with_redis_disabled
    test_backend_detection_without_instance_id

    # Redis mode tests
    echo -e "\n${YELLOW}--- Redis Mode Tests ---${NC}"
    test_publish_redis_mode
    test_check_redis_mode

    # Output format tests
    echo -e "\n${YELLOW}--- Output Format Tests ---${NC}"
    test_publish_output_format
    test_ack_output_format

    # Error handling tests
    echo -e "\n${YELLOW}--- Error Handling Tests ---${NC}"
    test_publish_invalid_type
    test_ack_nonexistent_message

    # Summary
    echo ""
    echo "=== Test Summary ==="
    echo "  Total:  $TESTS_RUN"
    echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
    if [[ "$TESTS_FAILED" -gt 0 ]]; then
        echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
        exit 1
    else
        echo "  Failed: 0"
        echo ""
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"
