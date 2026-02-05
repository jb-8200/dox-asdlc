#!/bin/bash
# Create and configure an agent worktree for isolated parallel development.
#
# Usage: ./scripts/worktree/setup-agent.sh <role>
#
# This script:
# - Creates a git worktree at .worktrees/<role>/
# - Creates branch agent/<role>/active from main
# - Configures git identity (user.email, user.name)
# - Is idempotent (safe to run multiple times)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Valid roles for agent worktrees
VALID_ROLES=("backend" "frontend" "orchestrator" "devops")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <role>"
    echo ""
    echo "Create and configure an agent worktree for isolated parallel development."
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
    echo "  $0 backend           # Create backend agent worktree"
    echo "  $0 frontend          # Create frontend agent worktree"
    echo ""
    echo "Worktree location: .worktrees/<role>/"
    echo "Branch: agent/<role>/active"
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
                    log_error "Too many arguments"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Validate role
    if [[ -z "$role" ]]; then
        log_error "Missing required argument: role"
        usage
        exit 1
    fi

    if ! validate_role "$role"; then
        log_error "Invalid role: $role"
        echo "Valid roles: ${VALID_ROLES[*]}"
        exit 1
    fi

    # Define paths
    local worktree_dir="$PROJECT_ROOT/.worktrees/$role"
    local branch_name="agent/$role/active"
    local git_email="claude-${role}@asdlc.local"
    local git_name="Claude $(capitalize "$role") Agent"

    # Change to project root
    cd "$PROJECT_ROOT"

    # Check if worktree already exists
    if [[ -d "$worktree_dir" ]]; then
        log_info "Worktree already exists at: $worktree_dir"

        # Verify it's a valid worktree
        if git worktree list | grep -q "$worktree_dir"; then
            log_info "Verifying git configuration..."

            # Ensure git identity is set correctly in the worktree
            pushd "$worktree_dir" > /dev/null
            git config user.email "$git_email"
            git config user.name "$git_name"
            popd > /dev/null

            log_info "Git identity verified: $git_email ($git_name)"
            log_info "Worktree is ready for use"
            echo ""
            echo "To use this worktree:"
            echo "  cd $worktree_dir"
            echo "  export CLAUDE_INSTANCE_ID=$role"
            echo "  claude"
            exit 0
        else
            log_error "Directory exists but is not a valid worktree"
            log_error "Please remove manually and retry: rm -rf $worktree_dir"
            exit 1
        fi
    fi

    # Check if branch already exists
    local branch_exists=false
    if git show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
        branch_exists=true
        log_info "Branch $branch_name already exists"
    fi

    # Create worktree directory parent if needed
    mkdir -p "$(dirname "$worktree_dir")"

    # Create worktree
    log_info "Creating worktree at: $worktree_dir"
    if [[ "$branch_exists" == "true" ]]; then
        # Use existing branch
        git worktree add "$worktree_dir" "$branch_name"
    else
        # Create new branch from main
        # First ensure we have the latest main
        local main_branch="main"
        if ! git show-ref --verify --quiet "refs/heads/$main_branch"; then
            main_branch="master"
        fi

        git worktree add -b "$branch_name" "$worktree_dir" "$main_branch"
    fi

    log_info "Worktree created successfully"

    # Configure git identity in the worktree
    log_info "Configuring git identity..."
    pushd "$worktree_dir" > /dev/null
    git config user.email "$git_email"
    git config user.name "$git_name"
    popd > /dev/null

    log_info "Git identity configured: $git_email ($git_name)"

    # Ensure .worktrees is in .gitignore
    local gitignore="$PROJECT_ROOT/.gitignore"
    if [[ -f "$gitignore" ]]; then
        if ! grep -q "^\.worktrees/$" "$gitignore" && ! grep -q "^\.worktrees$" "$gitignore"; then
            log_info "Adding .worktrees/ to .gitignore"
            echo "" >> "$gitignore"
            echo "# Agent worktrees (parallel session isolation)" >> "$gitignore"
            echo ".worktrees/" >> "$gitignore"
        fi
    fi

    echo ""
    echo -e "${GREEN}Worktree setup complete!${NC}"
    echo ""
    echo "Location: $worktree_dir"
    echo "Branch: $branch_name"
    echo "Identity: $git_email"
    echo ""
    echo "To use this worktree:"
    echo "  cd $worktree_dir"
    echo "  export CLAUDE_INSTANCE_ID=$role"
    echo "  claude"
}

main "$@"
