#!/bin/bash
# Launcher script for Frontend CLI instance.
#
# This script creates a persistent identity file and launches Claude Code
# with frontend agent permissions. Use this script to start a session for
# frontend development (HITL Web UI).
#
# Usage: ./start-frontend.sh [claude arguments...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
IDENTITY_FILE="$PROJECT_ROOT/.claude/instance-identity.json"

# Ensure .claude directory exists
mkdir -p "$PROJECT_ROOT/.claude"

# Create identity file with frontend configuration
cat > "$IDENTITY_FILE" << 'EOF'
{
  "instance_id": "frontend",
  "branch_prefix": "ui/",
  "allowed_paths": [
    "src/hitl_ui/",
    "docker/hitl-ui/",
    "tests/unit/hitl_ui/",
    "tests/e2e/",
    ".workitems/P05-*"
  ],
  "forbidden_paths": [
    "src/workers/",
    "src/orchestrator/",
    "src/infrastructure/",
    "docker/workers/",
    "docker/orchestrator/",
    ".workitems/P01-*",
    ".workitems/P02-*",
    ".workitems/P03-*",
    ".workitems/P06-*",
    "CLAUDE.md",
    "README.md",
    ".claude/rules/",
    ".claude/skills/",
    "docs/",
    "contracts/"
  ],
  "can_merge": false,
  "can_modify_meta": false,
  "created_at": "TIMESTAMP_PLACEHOLDER",
  "launcher": "start-frontend.sh"
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

# Set git identity for attribution
cd "$PROJECT_ROOT"
git config user.name "Claude Frontend"
git config user.email "claude-frontend@asdlc.local"

echo "=========================================="
echo "  Frontend CLI Instance Activated"
echo "=========================================="
echo ""
echo "Identity:        frontend"
echo "Branch prefix:   ui/"
echo "Git identity:    Claude Frontend <claude-frontend@asdlc.local>"
echo "Can merge:       No"
echo ""
echo "Allowed paths:"
echo "  - src/hitl_ui/, docker/hitl-ui/"
echo "  - .workitems/P05-*"
echo ""
echo "Forbidden paths:"
echo "  - src/workers/, src/orchestrator/, CLAUDE.md, docs/, contracts/"
echo ""
echo "Starting Claude Code..."
echo ""

# Launch Claude with all passed arguments
exec claude "$@"
