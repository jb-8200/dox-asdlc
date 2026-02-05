"""Unit tests for the start-agent-session.sh script.

Tests the unified agent session launcher that:
- Creates/verifies worktree via setup-agent.sh
- Sets git identity in worktree
- Exports CLAUDE_INSTANCE_ID
- Outputs next steps instructions
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

# Path to the script (will be created)
SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "start-agent-session.sh"
SETUP_AGENT_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "worktree" / "setup-agent.sh"


class TestStartAgentSessionStructure:
    """Test that the script exists and has correct structure."""

    def test_script_file_exists(self):
        """Test that the start-agent-session.sh script exists."""
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


class TestStartAgentSessionHelp:
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
        assert "backend" in result.stdout
        assert "frontend" in result.stdout

    def test_help_long_flag(self):
        """Test that --help flag shows help."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()


class TestStartAgentSessionArgumentParsing:
    """Test argument parsing."""

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
        assert "role" in result.stderr.lower() or "role" in result.stdout.lower()

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

    def test_too_many_arguments_shows_error(self):
        """Test that too many arguments shows an error."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "backend", "extra_arg"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "argument" in output.lower() or "too many" in output.lower()


class TestStartAgentSessionValidRoles:
    """Test valid role arguments."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                capture_output=True,
            )
            # Create initial commit so we have a branch
            Path(tmpdir, "README.md").write_text("# Test\n")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmpdir, capture_output=True)
            yield tmpdir

    @pytest.mark.parametrize("role", ["backend", "frontend", "orchestrator", "devops"])
    def test_valid_role_accepted(self, role):
        """Test that valid roles are accepted (script parses them correctly)."""
        # Just test that the script recognizes the role without actually creating worktrees
        # We test with --help-like validation by checking the role is in the valid roles
        result = subprocess.run(
            [str(SCRIPT_PATH), role],
            capture_output=True,
            text=True,
            timeout=30,
            # Run from project root
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Should either succeed or fail for reasons other than invalid role
        output = result.stdout + result.stderr
        assert "Invalid role" not in output or role not in output


class TestStartAgentSessionOutput:
    """Test output messages."""

    def test_outputs_instructions(self):
        """Test that the script outputs next steps instructions."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Help should mention key concepts
        output = result.stdout
        assert any(term in output for term in ["worktree", "CLAUDE_INSTANCE_ID", "identity", "session"])

    def test_mentions_claude_instance_id(self):
        """Test that the script mentions CLAUDE_INSTANCE_ID."""
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Help should mention the environment variable
        assert "CLAUDE_INSTANCE_ID" in result.stdout


class TestStartAgentSessionIdempotency:
    """Test that the script is idempotent."""

    def test_help_is_idempotent(self):
        """Test that running help multiple times gives same result."""
        result1 = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result2 = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result1.returncode == result2.returncode
        assert result1.stdout == result2.stdout
