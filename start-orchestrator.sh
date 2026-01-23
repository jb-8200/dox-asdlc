#!/bin/bash
# Launcher script for Orchestrator CLI instance (Master Agent).
#
# This script creates a persistent identity file and launches Claude Code
# with orchestrator (master agent) permissions. Use this script to start
# a session for code review, merging to main, and meta file management.
#
# The orchestrator has EXCLUSIVE ownership of:
#   - CLAUDE.md, README.md
#   - .claude/rules/, .claude/skills/
#   - docs/, contracts/
#
# Usage: ./start-orchestrator.sh [claude arguments...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
IDENTITY_FILE="$PROJECT_ROOT/.claude/instance-identity.json"

# Ensure .claude directory exists
mkdir -p "$PROJECT_ROOT/.claude"

# Create identity file with orchestrator configuration
cat > "$IDENTITY_FILE" << 'EOF'
{
  "instance_id": "orchestrator",
  "branch_prefix": "",
  "allowed_paths": ["*"],
  "forbidden_paths": [],
  "can_merge": true,
  "can_modify_meta": true,
  "meta_files": [
    "CLAUDE.md",
    "README.md",
    ".claude/rules/",
    ".claude/skills/",
    "docs/",
    "contracts/"
  ],
  "created_at": "TIMESTAMP_PLACEHOLDER",
  "launcher": "start-orchestrator.sh"
}
EOF

# Update timestamp
if command -v python3 &> /dev/null; then
    python3 -c "
import json
from datetime import datetime, timezone

with open('$IDENTITY_FILE', 'r') as f:
    data = json.load(f)

data['created_at'] = datetime.now(timezone.utc).isoformat()

with open('$IDENTITY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
fi

# Orchestrator uses Claude's default git identity
# Unset any project-specific git config to use global/default
cd "$PROJECT_ROOT"
git config --unset user.name 2>/dev/null || true
git config --unset user.email 2>/dev/null || true

echo "=========================================="
echo "  Orchestrator CLI Instance (Master Agent)"
echo "=========================================="
echo ""
echo "Identity:        orchestrator"
echo "Branch:          main (exclusive write access)"
echo "Git identity:    (using system default)"
echo "Can merge:       Yes"
echo "Can modify meta: Yes"
echo ""
echo "EXCLUSIVE ownership of:"
echo "  - CLAUDE.md, README.md"
echo "  - .claude/rules/, .claude/skills/"
echo "  - docs/, contracts/"
echo ""
echo "Responsibilities:"
echo "  - Review feature branches from Backend/Frontend CLIs"
echo "  - Run E2E tests before merging"
echo "  - Merge approved branches to main"
echo "  - Maintain project documentation"
echo ""
echo "Starting Claude Code..."
echo ""

# Launch Claude with all passed arguments
exec claude "$@"
