#!/bin/bash
# Launcher script for Backend CLI instance.
#
# This script creates a persistent identity file and launches Claude Code
# with backend agent permissions. Use this script to start a session for
# backend development (workers, orchestrator, infrastructure).
#
# Usage: ./start-backend.sh [claude arguments...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
IDENTITY_FILE="$PROJECT_ROOT/.claude/instance-identity.json"

# Ensure .claude directory exists
mkdir -p "$PROJECT_ROOT/.claude"

# Create identity file with backend configuration
cat > "$IDENTITY_FILE" << 'EOF'
{
  "instance_id": "backend",
  "branch_prefix": "agent/",
  "allowed_paths": [
    "src/workers/",
    "src/orchestrator/",
    "src/infrastructure/",
    "src/core/",
    "docker/workers/",
    "docker/orchestrator/",
    "tests/unit/workers/",
    "tests/unit/orchestrator/",
    "tests/unit/infrastructure/",
    "tests/integration/",
    ".workitems/P01-*",
    ".workitems/P02-*",
    ".workitems/P03-*",
    ".workitems/P06-*",
    "tools/",
    "scripts/",
    "helm/"
  ],
  "forbidden_paths": [
    "src/hitl_ui/",
    "docker/hitl-ui/",
    "tests/unit/hitl_ui/",
    ".workitems/P05-*",
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
  "launcher": "start-backend.sh"
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
git config user.name "Claude Backend"
git config user.email "claude-backend@asdlc.local"

echo "=========================================="
echo "  Backend CLI Instance Activated"
echo "=========================================="
echo ""
echo "Identity:        backend"
echo "Branch prefix:   agent/"
echo "Git identity:    Claude Backend <claude-backend@asdlc.local>"
echo "Can merge:       No"
echo ""
echo "Allowed paths:"
echo "  - src/workers/, src/orchestrator/, src/infrastructure/"
echo "  - .workitems/P01-*, P02-*, P03-*, P06-*"
echo ""
echo "Forbidden paths:"
echo "  - src/hitl_ui/, CLAUDE.md, docs/, contracts/"
echo ""
echo "Starting Claude Code..."
echo ""

# Launch Claude with all passed arguments
exec claude "$@"
