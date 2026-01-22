#!/bin/bash
# Tests for Kubernetes scripts (P06-F01-T06, T07, T08)
#
# Usage: ./tests/unit/test_k8s_scripts.sh
#
# These tests verify script structure and help output without
# actually running minikube or helm commands.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts/k8s"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

log_test() {
    echo "  Testing: $1"
}

pass() {
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "    ${GREEN}PASS${NC}"
}

fail() {
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "    ${RED}FAIL${NC}: $1"
}

# Test: start-minikube.sh exists and is executable
test_start_minikube_exists() {
    log_test "start-minikube.sh exists and is executable"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    if [ -f "$script" ] && [ -x "$script" ]; then
        pass
    else
        fail "Script not found or not executable: $script"
    fi
}

# Test: start-minikube.sh has shebang
test_start_minikube_shebang() {
    log_test "start-minikube.sh has bash shebang"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    if head -1 "$script" | grep -q "#!/bin/bash"; then
        pass
    else
        fail "Script should have #!/bin/bash shebang"
    fi
}

# Test: start-minikube.sh has set -euo pipefail
test_start_minikube_strict_mode() {
    log_test "start-minikube.sh uses strict mode"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    if grep -q "set -euo pipefail" "$script"; then
        pass
    else
        fail "Script should use 'set -euo pipefail'"
    fi
}

# Test: start-minikube.sh has help option
test_start_minikube_help() {
    log_test "start-minikube.sh has --help option"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    if grep -q "\-\-help" "$script"; then
        pass
    else
        fail "Script should support --help option"
    fi
}

# Test: start-minikube.sh configures profile name
test_start_minikube_profile() {
    log_test "start-minikube.sh uses dox-asdlc profile"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    if grep -q "dox-asdlc" "$script"; then
        pass
    else
        fail "Script should use 'dox-asdlc' profile name"
    fi
}

# Test: start-minikube.sh enables required addons
test_start_minikube_addons() {
    log_test "start-minikube.sh enables required addons"
    local script="$SCRIPTS_DIR/start-minikube.sh"

    local missing_addons=()
    for addon in "ingress" "metrics-server" "storage-provisioner"; do
        if ! grep -q "$addon" "$script"; then
            missing_addons+=("$addon")
        fi
    done

    if [ ${#missing_addons[@]} -eq 0 ]; then
        pass
    else
        fail "Missing addons: ${missing_addons[*]}"
    fi
}

# Test: deploy.sh exists and is executable
test_deploy_exists() {
    log_test "deploy.sh exists and is executable"
    local script="$SCRIPTS_DIR/deploy.sh"

    if [ -f "$script" ] && [ -x "$script" ]; then
        pass
    else
        fail "Script not found or not executable: $script"
    fi
}

# Test: deploy.sh references the helm chart
test_deploy_chart_path() {
    log_test "deploy.sh references helm chart path"
    local script="$SCRIPTS_DIR/deploy.sh"

    if grep -q "helm/dox-asdlc" "$script"; then
        pass
    else
        fail "Script should reference helm/dox-asdlc chart"
    fi
}

# Test: deploy.sh uses helm upgrade --install
test_deploy_helm_command() {
    log_test "deploy.sh uses helm upgrade --install"
    local script="$SCRIPTS_DIR/deploy.sh"

    if grep -q "upgrade" "$script" && grep -q "install" "$script"; then
        pass
    else
        fail "Script should use 'helm upgrade --install'"
    fi
}

# Test: deploy.sh supports dry-run
test_deploy_dry_run() {
    log_test "deploy.sh supports --dry-run option"
    local script="$SCRIPTS_DIR/deploy.sh"

    if grep -q "\-\-dry-run" "$script"; then
        pass
    else
        fail "Script should support --dry-run option"
    fi
}

# Test: deploy.sh lints chart before deployment
test_deploy_lint() {
    log_test "deploy.sh lints chart before deployment"
    local script="$SCRIPTS_DIR/deploy.sh"

    if grep -q "helm lint" "$script"; then
        pass
    else
        fail "Script should lint chart before deployment"
    fi
}

# Test: teardown.sh exists and is executable
test_teardown_exists() {
    log_test "teardown.sh exists and is executable"
    local script="$SCRIPTS_DIR/teardown.sh"

    if [ -f "$script" ] && [ -x "$script" ]; then
        pass
    else
        fail "Script not found or not executable: $script"
    fi
}

# Test: teardown.sh uses helm uninstall
test_teardown_helm_command() {
    log_test "teardown.sh uses helm uninstall"
    local script="$SCRIPTS_DIR/teardown.sh"

    if grep -q "helm uninstall" "$script"; then
        pass
    else
        fail "Script should use 'helm uninstall'"
    fi
}

# Test: teardown.sh supports --delete-namespace
test_teardown_delete_namespace() {
    log_test "teardown.sh supports --delete-namespace option"
    local script="$SCRIPTS_DIR/teardown.sh"

    if grep -q "\-\-delete-namespace" "$script"; then
        pass
    else
        fail "Script should support --delete-namespace option"
    fi
}

# Test: teardown.sh supports --delete-data
test_teardown_delete_data() {
    log_test "teardown.sh supports --delete-data option"
    local script="$SCRIPTS_DIR/teardown.sh"

    if grep -q "\-\-delete-data" "$script"; then
        pass
    else
        fail "Script should support --delete-data option"
    fi
}

# Test: teardown.sh has confirmation prompt
test_teardown_confirm() {
    log_test "teardown.sh has confirmation prompt"
    local script="$SCRIPTS_DIR/teardown.sh"

    if grep -q "confirm" "$script" || grep -q "read -p" "$script"; then
        pass
    else
        fail "Script should have confirmation before destructive operations"
    fi
}

# Test: teardown.sh supports --force to skip confirmation
test_teardown_force() {
    log_test "teardown.sh supports --force option"
    local script="$SCRIPTS_DIR/teardown.sh"

    if grep -q "\-\-force" "$script" || grep -q "\-f)" "$script"; then
        pass
    else
        fail "Script should support --force option"
    fi
}

# Run all tests
main() {
    echo "========================================"
    echo "  Kubernetes Scripts Unit Tests"
    echo "========================================"
    echo ""

    echo "Testing start-minikube.sh:"
    test_start_minikube_exists
    test_start_minikube_shebang
    test_start_minikube_strict_mode
    test_start_minikube_help
    test_start_minikube_profile
    test_start_minikube_addons

    echo ""
    echo "Testing deploy.sh:"
    test_deploy_exists
    test_deploy_chart_path
    test_deploy_helm_command
    test_deploy_dry_run
    test_deploy_lint

    echo ""
    echo "Testing teardown.sh:"
    test_teardown_exists
    test_teardown_helm_command
    test_teardown_delete_namespace
    test_teardown_delete_data
    test_teardown_confirm
    test_teardown_force

    echo ""
    echo "========================================"
    echo "  Results: $TESTS_PASSED/$TESTS_RUN passed"
    echo "========================================"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}$TESTS_FAILED test(s) failed${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed${NC}"
        exit 0
    fi
}

main "$@"
