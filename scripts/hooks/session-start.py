#!/usr/bin/env python3
"""
SessionStart hook for Claude Code sessions.

This hook runs at the start of each Claude Code session to display
environment information. Role-specific behavior is now handled by
subagents (backend.md, frontend.md, orchestrator.md).

Exit codes:
  0 - Success (context injected)
  Non-zero - Error (but session continues)
"""

import subprocess
import sys


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


def get_git_email() -> str:
    """Get the current git user.email config."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    current_branch = get_current_branch()
    git_email = get_git_email()

    print("startup hook success: " + "=" * 50)
    print("  aSDLC Development Session")
    print("=" * 50)
    print("")
    print(f"Branch: {current_branch or '(detached HEAD)'}")

    if git_email:
        # Show current git identity if set (may be from previous subagent)
        if "backend" in git_email:
            print(f"Last identity: Backend ({git_email})")
        elif "frontend" in git_email:
            print(f"Last identity: Frontend ({git_email})")
        elif "orchestrator" in git_email:
            print(f"Last identity: Orchestrator ({git_email})")
        else:
            print(f"Git email: {git_email}")

    print("")
    print("Invoke a subagent for role-specific work:")
    print("  - backend: workers, infrastructure, P01-P03/P06")
    print("  - frontend: HITL UI, React, P05")
    print("  - orchestrator: meta files, contracts, coordination")
    print("")
    print("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    main()
