#!/bin/bash
# Unified agent session launcher.
#
# Usage: ./scripts/start-agent-session.sh <role>
#
# This script:
# - Calls setup-agent.sh to create/verify worktree
# - Sets git identity in the worktree
# - Exports CLAUDE_INSTANCE_ID
# - Changes to worktree directory
# - Outputs next steps instructions for user
#
# The script is idempotent (safe to run multiple times).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Valid roles for agent sessions
VALID_ROLES=("backend" "frontend" "orchestrator" "devops")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <role>"
    echo ""
    echo "Unified agent session launcher for multi-session infrastructure."
    echo ""
    echo "This script performs the complete setup for an agent session:"
    echo "  1. Creates/verifies git worktree for the role"
    echo "  2. Configures git identity (user.email, user.name)"
    echo "  3. Sets CLAUDE_INSTANCE_ID environment variable"
    echo "  4. Changes to worktree directory"
    echo "  5. Outputs next steps instructions"
    echo ""
    echo "Arguments:"
    echo "  role    Agent role (required)"
    echo ""
    echo "Valid roles:"
    echo "  backend      - Backend development (workers, infra, core)"
    echo "  frontend     - Frontend development (HITL UI)"
    echo "  orchestrator - Coordination, docs, meta files"
    echo "  devops       - Infrastructure, Docker, K8s"
    echo ""
    echo "Options:"
    echo "  -h, --help   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backend           # Start backend agent session"
    echo "  $0 frontend          # Start frontend agent session"
    echo ""
    echo "After running this script, you will be in the agent worktree with:"
    echo "  - Git identity configured for the role"
    echo "  - CLAUDE_INSTANCE_ID set for coordination"
    echo ""
    echo "The script is idempotent - safe to run multiple times."
}

log_info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}WARN:${NC} $1"
}

log_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

log_step() {
    echo -e "${BLUE}==>${NC} $1"
}

validate_role() {
    local role="$1"
    for valid in "${VALID_ROLES[@]}"; do
        if [[ "$role" == "$valid" ]]; then
            return 0
        fi
    done
    return 1
}

capitalize() {
    # Compatible with bash 3.x (macOS default)
    echo "$1" | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}'
}

main() {
    local role=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [[ -z "$role" ]]; then
                    role="$1"
                else
                    log_error "Too many arguments: only one role expected"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Validate role is provided
    if [[ -z "$role" ]]; then
        log_error "Missing required argument: role"
        echo ""
        echo "Valid roles: ${VALID_ROLES[*]}"
        echo ""
        echo "Run '$0 --help' for usage information."
        exit 1
    fi

    # Validate role is valid
    if ! validate_role "$role"; then
        log_error "Invalid role: $role"
        echo ""
        echo "Valid roles: ${VALID_ROLES[*]}"
        exit 1
    fi

    # Define paths and identities
    local worktree_dir="$PROJECT_ROOT/.worktrees/$role"
    local branch_name="agent/$role/active"
    local git_email="claude-${role}@asdlc.local"
    local git_name="Claude $(capitalize "$role") Agent"

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Agent Session Launcher: $role${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Step 1: Create/verify worktree via setup-agent.sh
    log_step "Step 1: Setting up worktree..."

    local setup_script="$SCRIPT_DIR/worktree/setup-agent.sh"
    if [[ ! -x "$setup_script" ]]; then
        log_error "setup-agent.sh not found or not executable at: $setup_script"
        exit 1
    fi

    # Run setup-agent.sh (it is idempotent)
    if ! "$setup_script" "$role"; then
        log_error "Failed to set up worktree for role: $role"
        exit 1
    fi

    # Step 2: Verify git identity in worktree
    log_step "Step 2: Verifying git identity..."

    if [[ ! -d "$worktree_dir" ]]; then
        log_error "Worktree directory not found after setup: $worktree_dir"
        exit 1
    fi

    pushd "$worktree_dir" > /dev/null

    # Set git identity (setup-agent.sh should have done this, but verify)
    git config user.email "$git_email"
    git config user.name "$git_name"

    local actual_email
    actual_email=$(git config user.email)
    if [[ "$actual_email" != "$git_email" ]]; then
        log_error "Failed to set git email. Expected: $git_email, Got: $actual_email"
        popd > /dev/null
        exit 1
    fi

    log_info "Git identity: $git_email ($git_name)"

    popd > /dev/null

    # Step 3: Export CLAUDE_INSTANCE_ID
    log_step "Step 3: Setting CLAUDE_INSTANCE_ID..."
    export CLAUDE_INSTANCE_ID="$role"
    log_info "CLAUDE_INSTANCE_ID=$role"

    # Output next steps
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Session Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Worktree: $worktree_dir"
    echo "Branch: $branch_name"
    echo "Identity: $git_email"
    echo "Instance ID: $role"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "  1. Change to worktree directory:"
    echo "     cd $worktree_dir"
    echo ""
    echo "  2. Set environment variable in your shell:"
    echo "     export CLAUDE_INSTANCE_ID=$role"
    echo ""
    echo "  3. Start Claude CLI:"
    echo "     claude"
    echo ""
    echo -e "${BLUE}Quick command (copy/paste):${NC}"
    echo "  cd $worktree_dir && export CLAUDE_INSTANCE_ID=$role && claude"
    echo ""

    # Check if we should output shell source command
    # Note: The script cannot change the parent shell's directory or env vars
    # So we provide instructions instead
}

main "$@"
