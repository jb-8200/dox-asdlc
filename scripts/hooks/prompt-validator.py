#!/usr/bin/env python3
"""
UserPromptSubmit hook for CLI Agent Identity Enforcement.

This hook runs before each user prompt is processed to:
1. Verify an identity file exists (launcher was used)
2. Verify the current branch matches the expected prefix
3. BLOCK the prompt if either check fails

Blocking mechanism:
  - Output JSON: {"decision": "block", "reason": "..."}
  - Exit 0 to block the prompt with the given reason

Exit codes:
  0 - Always (either allow or block via JSON output)
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Find the project root by looking for .claude directory."""
    cwd = Path.cwd()
    for path in [cwd] + list(cwd.parents):
        if (path / ".claude").is_dir():
            return path
    return cwd


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def block(reason: str):
    """Block the prompt with the given reason."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def allow():
    """Allow the prompt to proceed."""
    # Output nothing, just exit 0
    sys.exit(0)


def main():
    project_root = get_project_root()
    identity_file = project_root / ".claude" / "instance-identity.json"

    # Check 1: Identity file must exist
    if not identity_file.exists():
        block(
            "NO LAUNCHER USED\n\n"
            "You must start Claude Code using a launcher script:\n"
            "  ./start-backend.sh      # For backend development\n"
            "  ./start-frontend.sh     # For frontend development\n"
            "  ./start-orchestrator.sh # For review/merge operations\n\n"
            "Please exit and restart using the appropriate launcher."
        )

    # Load identity configuration
    try:
        with open(identity_file) as f:
            identity = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        block(f"IDENTITY FILE CORRUPT\n\nCould not read identity file: {e}\n\nRestart using a launcher script.")

    instance_id = identity.get("instance_id", "unknown")
    branch_prefix = identity.get("branch_prefix", "")

    # Check 2: Branch must match expected prefix (for non-orchestrator)
    if branch_prefix:
        current_branch = get_current_branch()

        if not current_branch:
            # Detached HEAD or git error - allow but warn
            allow()

        if not current_branch.startswith(branch_prefix):
            block(
                f"WRONG BRANCH\n\n"
                f"Instance: {instance_id}\n"
                f"Expected branch prefix: {branch_prefix}\n"
                f"Current branch: {current_branch}\n\n"
                f"Switch to the correct branch before continuing:\n"
                f"  git checkout -b {branch_prefix}<feature-name>\n"
                f"  git checkout {branch_prefix}<existing-branch>\n\n"
                f"Or restart with a different launcher if this is the wrong role."
            )

    # All checks passed
    allow()


if __name__ == "__main__":
    main()
