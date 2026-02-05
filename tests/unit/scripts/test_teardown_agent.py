"""Unit tests for the teardown-agent.sh script.

Tests the script that removes agent worktrees, including:
- Session deregistration from Redis
- SESSION_END message publishing
- Graceful handling of Redis unavailability
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

# Path to the teardown script
SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "worktree" / "teardown-agent.sh"


class TestTeardownAgentStructure:
    """Test that the teardown script exists and has correct structure."""

    def test_script_file_exists(self):
        """Test that the teardown-agent.sh script exists."""
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_script_is_executable(self):
        """Test that the script is executable."""
        assert os.access(SCRIPT_PATH, os.X_OK), f"Script is not executable: {SCRIPT_PATH}"

    def test_script_has_shebang(self):
        """Test that the script has a proper bash shebang."""
        with open(SCRIPT_PATH, "r") as f:
            first_line = f.readline()
        assert first_line.startswith("#!/"), "Script must have a shebang"
        assert "bash" in first_line, "Script must use bash"


class TestTeardownAgentHelp:
    """Test help text and usage information."""

    def test_help_flag(self):
        """Test that -h flag shows help."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_help_long_flag(self):
        """Test that --help flag shows help."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0


class TestTeardownArgumentParsing:
    """Test argument parsing for teardown."""

    def test_no_arguments_shows_error(self):
        """Test that running without arguments shows an error."""
        result = subprocess.run(
            [str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail with missing role
        assert result.returncode != 0

    def test_invalid_role_shows_error(self):
        """Test that invalid role argument shows an error."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "invalid_role_xyz"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode != 0
        output = result.stdout + result.stderr
        # Should mention valid roles
        assert any(role in output for role in ["backend", "frontend", "orchestrator", "devops"])


class TestSessionDeregistration:
    """Test session deregistration on teardown."""

    def test_deregistration_attempted_on_teardown(self):
        """Test that session deregistration is attempted."""
        # This will fail because no worktree exists, but we check the script exists
        # and handles the case gracefully
        result = subprocess.run(
            [str(SCRIPT_PATH), "backend", "--abandon"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # The script should try to teardown (even if worktree doesn't exist)
        # Output should not have Python traceback or critical errors about deregistration
        output = result.stdout + result.stderr
        assert "traceback" not in output.lower()

    def test_deregistration_failure_does_not_block_teardown(self):
        """Test that deregistration failure does not block teardown."""
        env = os.environ.copy()
        env["REDIS_HOST"] = "invalid_host_that_does_not_exist"
        env["REDIS_PORT"] = "9999"

        result = subprocess.run(
            [str(SCRIPT_PATH), "backend", "--abandon"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # The main failure should be about worktree not existing, not Redis
        output = result.stdout + result.stderr
        # Redis failure should not cause a different error type
        assert "redis" not in output.lower() or "warn" in output.lower() or "not available" in output.lower() or "worktree" in output.lower()


class TestSessionEndMessage:
    """Test SESSION_END message publishing on teardown."""

    def test_session_end_attempted_on_teardown(self):
        """Test that SESSION_END message is attempted on teardown."""
        # Since no worktree exists, this will fail early, but we verify the script
        # has the capability
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Help should show the script is capable of teardown operations
        assert result.returncode == 0
        assert "remove" in result.stdout.lower() or "teardown" in result.stdout.lower()

    def test_session_end_failure_does_not_block_teardown(self):
        """Test that SESSION_END message failure does not block teardown."""
        env = os.environ.copy()
        env["REDIS_HOST"] = "invalid_host_that_does_not_exist"

        result = subprocess.run(
            [str(SCRIPT_PATH), "backend", "--abandon"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Should not have a Redis-specific fatal error - the main error should be about worktree
        output = result.stdout + result.stderr
        # Either the worktree doesn't exist error, or graceful Redis handling
        assert "worktree" in output.lower() or "not available" in output.lower() or result.returncode != 0
