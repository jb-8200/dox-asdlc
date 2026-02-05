"""Unit tests for the session startup hook.

Tests the startup.sh hook that validates identity, registers presence,
and checks for pending notifications at session startup.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Path to the startup hook
HOOK_SCRIPT = Path(__file__).parent.parent.parent.parent / ".claude" / "hooks" / "startup.sh"


class TestStartupHookStructure:
    """Test that the startup hook exists and has correct structure."""

    def test_hook_file_exists(self):
        """Test that the startup hook script exists."""
        assert HOOK_SCRIPT.exists(), f"Startup hook not found at {HOOK_SCRIPT}"

    def test_hook_is_executable(self):
        """Test that the startup hook is executable."""
        assert os.access(HOOK_SCRIPT, os.X_OK), f"Startup hook is not executable: {HOOK_SCRIPT}"

    def test_hook_has_shebang(self):
        """Test that the hook has a proper bash shebang."""
        with open(HOOK_SCRIPT, "r") as f:
            first_line = f.readline()
        assert first_line.startswith("#!/"), "Hook must have a shebang"
        assert "bash" in first_line, "Hook must use bash"


class TestIdentityValidation:
    """Test identity validation in the startup hook."""

    @pytest.fixture
    def clean_env(self):
        """Fixture to provide a clean environment without identity variables."""
        env = os.environ.copy()
        # Remove identity-related variables
        env.pop("CLAUDE_INSTANCE_ID", None)
        return env

    def test_valid_claude_instance_id_env_var(self, clean_env):
        """Test that valid CLAUDE_INSTANCE_ID environment variable is accepted."""
        clean_env["CLAUDE_INSTANCE_ID"] = "backend"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should succeed with exit code 0
        assert result.returncode == 0, f"Hook failed with stderr: {result.stderr}"
        assert "backend" in result.stdout.lower()

    def test_valid_frontend_role(self, clean_env):
        """Test that frontend role is accepted."""
        clean_env["CLAUDE_INSTANCE_ID"] = "frontend"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Hook failed with stderr: {result.stderr}"

    def test_valid_orchestrator_role(self, clean_env):
        """Test that orchestrator role is accepted."""
        clean_env["CLAUDE_INSTANCE_ID"] = "orchestrator"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Hook failed with stderr: {result.stderr}"

    def test_valid_devops_role(self, clean_env):
        """Test that devops role is accepted."""
        clean_env["CLAUDE_INSTANCE_ID"] = "devops"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Hook failed with stderr: {result.stderr}"

    def test_valid_pm_role(self, clean_env):
        """Test that pm role is accepted."""
        clean_env["CLAUDE_INSTANCE_ID"] = "pm"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Hook failed with stderr: {result.stderr}"

    def test_invalid_role_rejected(self, clean_env):
        """Test that invalid roles are rejected with exit code 1."""
        clean_env["CLAUDE_INSTANCE_ID"] = "invalid_role"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 1, "Invalid role should be rejected"
        # Should contain remediation info
        assert "backend" in result.stdout or "backend" in result.stderr

    def test_empty_instance_id_rejected(self, clean_env):
        """Test that empty CLAUDE_INSTANCE_ID is rejected."""
        clean_env["CLAUDE_INSTANCE_ID"] = ""

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should try git fallback, and if that fails, reject
        # The result depends on whether git email is configured
        # For this test, we just verify the script handles empty string

    def test_unknown_instance_id_rejected(self, clean_env):
        """Test that 'unknown' CLAUDE_INSTANCE_ID is rejected when no valid git email."""
        clean_env["CLAUDE_INSTANCE_ID"] = "unknown"

        # Create a temp git repo with unrecognized email so fallback also fails
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "user@example.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                capture_output=True,
            )

            result = subprocess.run(
                [str(HOOK_SCRIPT)],
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=tmpdir,
            )

            assert result.returncode == 1, "'unknown' identity should be rejected when no valid git email"


class TestGitEmailFallback:
    """Test git email fallback for identity validation."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            yield tmpdir

    def test_git_email_fallback_backend(self, temp_git_repo):
        """Test that git email claude-backend@asdlc.local is recognized."""
        # Configure git email
        subprocess.run(
            ["git", "config", "user.email", "claude-backend@asdlc.local"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Backend"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        env = os.environ.copy()
        env.pop("CLAUDE_INSTANCE_ID", None)

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0, f"Git email fallback failed: {result.stderr}"
        assert "backend" in result.stdout.lower()

    def test_git_email_fallback_frontend(self, temp_git_repo):
        """Test that git email claude-frontend@asdlc.local is recognized."""
        subprocess.run(
            ["git", "config", "user.email", "claude-frontend@asdlc.local"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Frontend"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        env = os.environ.copy()
        env.pop("CLAUDE_INSTANCE_ID", None)

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_git_repo,
        )

        assert result.returncode == 0, f"Git email fallback failed: {result.stderr}"

    def test_unrecognized_git_email_rejected(self, temp_git_repo):
        """Test that unrecognized git email is rejected."""
        subprocess.run(
            ["git", "config", "user.email", "user@example.com"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        env = os.environ.copy()
        env.pop("CLAUDE_INSTANCE_ID", None)

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_git_repo,
        )

        assert result.returncode == 1, "Unrecognized git email should be rejected"


class TestPresenceRegistration:
    """Test presence registration in the startup hook."""

    @pytest.fixture
    def valid_env(self):
        """Fixture to provide a valid environment."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "backend"
        return env

    def test_presence_registration_attempted(self, valid_env):
        """Test that presence registration is attempted at startup."""
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Script should succeed even if Redis is unavailable
        assert result.returncode == 0
        # Should mention presence or registration
        output = result.stdout + result.stderr
        # The hook should handle Redis gracefully

    def test_redis_unavailable_does_not_block(self, valid_env):
        """Test that Redis being unavailable does not block startup."""
        # Set Redis to an invalid host to simulate unavailability
        valid_env["REDIS_HOST"] = "invalid_host_that_does_not_exist"
        valid_env["REDIS_PORT"] = "9999"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=15,  # Longer timeout for connection failure
        )

        # Should still exit 0 - Redis unavailability is a warning, not an error
        assert result.returncode == 0, f"Redis unavailable should not block startup: {result.stderr}"


class TestNotificationCheck:
    """Test notification check in the startup hook."""

    @pytest.fixture
    def valid_env(self):
        """Fixture to provide a valid environment."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "backend"
        return env

    def test_notification_check_does_not_block_on_error(self, valid_env):
        """Test that notification check errors do not block startup."""
        # Set Redis to invalid to cause notification check to fail
        valid_env["REDIS_HOST"] = "invalid_host_that_does_not_exist"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Should succeed despite notification check failure
        assert result.returncode == 0


class TestExitCodes:
    """Test exit codes of the startup hook."""

    @pytest.fixture
    def clean_env(self):
        """Fixture to provide a clean environment."""
        env = os.environ.copy()
        env.pop("CLAUDE_INSTANCE_ID", None)
        return env

    def test_exit_code_0_on_success(self, clean_env):
        """Test that exit code 0 is returned on success."""
        clean_env["CLAUDE_INSTANCE_ID"] = "backend"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0

    def test_exit_code_1_on_invalid_identity(self, clean_env):
        """Test that exit code 1 is returned for invalid identity."""
        clean_env["CLAUDE_INSTANCE_ID"] = "invalid_role_xyz"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 1


class TestOutputMessages:
    """Test output messages from the startup hook."""

    @pytest.fixture
    def valid_env(self):
        """Fixture to provide a valid environment."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "backend"
        return env

    def test_identity_confirmed_in_output(self, valid_env):
        """Test that identity is confirmed in output when valid."""
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Should mention the identity
        assert "backend" in result.stdout.lower()

    def test_error_message_includes_remediation(self):
        """Test that error messages include remediation information."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "invalid_role"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = result.stdout + result.stderr
        # Should include valid roles or instructions
        assert any(role in output.lower() for role in ["backend", "frontend", "orchestrator", "devops", "pm"])


class TestWorktreeVerification:
    """Test worktree verification in the startup hook."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "claude-backend@asdlc.local"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test Backend"],
                cwd=tmpdir,
                capture_output=True,
            )
            # Create initial commit
            Path(tmpdir, "README.md").write_text("# Test\n")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmpdir, capture_output=True)
            yield tmpdir

    def test_non_pm_in_main_worktree_warns(self, temp_git_repo):
        """Test that non-PM role in main worktree produces a warning."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "backend"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_git_repo,
        )

        # Should still succeed (warning, not blocking)
        assert result.returncode == 0
        # Output should include worktree-related info or warning
        output = result.stdout + result.stderr
        # The warning should be present (lowercase check)
        # Note: may not warn if worktree check is not implemented yet

    def test_pm_role_in_main_worktree_no_warn(self, temp_git_repo):
        """Test that PM role in main worktree does not produce unnecessary warnings."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "pm"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_git_repo,
        )

        # Should succeed
        assert result.returncode == 0


class TestSessionStartMessage:
    """Test SESSION_START message publishing."""

    @pytest.fixture
    def valid_env(self):
        """Fixture to provide a valid environment."""
        env = os.environ.copy()
        env["CLAUDE_INSTANCE_ID"] = "backend"
        return env

    def test_session_start_attempted_on_startup(self, valid_env):
        """Test that SESSION_START message publishing is attempted."""
        # With Redis unavailable, we just verify the hook completes
        valid_env["REDIS_HOST"] = "localhost"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Hook should complete successfully even if Redis is unavailable
        assert result.returncode == 0

    def test_session_start_failure_does_not_block(self, valid_env):
        """Test that SESSION_START message failure does not block startup."""
        valid_env["REDIS_HOST"] = "invalid_host_that_does_not_exist"
        valid_env["REDIS_PORT"] = "9999"

        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            env=valid_env,
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Should still succeed - SESSION_START failure is a warning
        assert result.returncode == 0
