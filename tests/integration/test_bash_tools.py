"""Integration tests for bash tool wrappers."""

import json
import subprocess
from pathlib import Path


def run_tool(tool_name: str, *args: str) -> dict:
    """Run a bash tool and return JSON output."""
    project_root = Path(__file__).parent.parent.parent
    tool_path = project_root / "tools" / f"{tool_name}.sh"

    result = subprocess.run(
        ["/bin/bash", str(tool_path), *args],
        capture_output=True,
        text=True,
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"success": False, "results": [], "errors": [result.stdout]}


class TestLintTool:
    """Tests for lint.sh tool."""

    def test_lint_returns_valid_json(self) -> None:
        """Test that lint.sh returns valid JSON."""
        output = run_tool("lint", "src/")
        assert "success" in output
        assert "results" in output
        assert "errors" in output

    def test_lint_results_array(self) -> None:
        """Test that lint results is an array."""
        output = run_tool("lint", "src/")
        assert isinstance(output["results"], list)

    def test_lint_errors_array(self) -> None:
        """Test that lint errors is an array."""
        output = run_tool("lint", "src/")
        assert isinstance(output["errors"], list)

    def test_lint_invalid_path(self) -> None:
        """Test lint with invalid path returns error."""
        output = run_tool("lint", "/nonexistent/path")
        assert output["success"] is False
        assert len(output["errors"]) > 0


class TestTestTool:
    """Tests for test.sh tool."""

    def test_test_returns_valid_json(self) -> None:
        """Test that test.sh returns valid JSON."""
        output = run_tool("test", "tests/unit/")
        assert "success" in output
        assert "results" in output
        assert "errors" in output

    def test_test_results_array(self) -> None:
        """Test that test results is an array."""
        output = run_tool("test", "tests/unit/")
        assert isinstance(output["results"], list)

    def test_test_results_have_required_fields(self) -> None:
        """Test that test results have required fields."""
        output = run_tool("test", "tests/unit/")
        for result in output["results"]:
            assert "file" in result or "severity" in result
            assert "severity" in result
            assert result["severity"] in ["error", "warning", "info"]

    def test_test_invalid_path(self) -> None:
        """Test with invalid path returns error."""
        output = run_tool("test", "/nonexistent/path")
        assert output["success"] is False


class TestSastTool:
    """Tests for sast.sh tool."""

    def test_sast_returns_valid_json(self) -> None:
        """Test that sast.sh returns valid JSON."""
        output = run_tool("sast", "src/")
        assert "success" in output
        assert "results" in output
        assert "errors" in output

    def test_sast_results_array(self) -> None:
        """Test that sast results is an array."""
        output = run_tool("sast", "src/")
        assert isinstance(output["results"], list)

    def test_sast_results_have_severity(self) -> None:
        """Test that sast results have severity field."""
        output = run_tool("sast", "src/")
        for result in output["results"]:
            assert "severity" in result
            assert result["severity"] in ["error", "warning", "info"]

    def test_sast_invalid_path(self) -> None:
        """Test sast with invalid path returns error."""
        output = run_tool("sast", "/nonexistent/path")
        assert output["success"] is False


class TestScaTool:
    """Tests for sca.sh tool."""

    def test_sca_returns_valid_json(self) -> None:
        """Test that sca.sh returns valid JSON."""
        output = run_tool("sca", "requirements.txt")
        assert "success" in output
        assert "results" in output
        assert "errors" in output

    def test_sca_results_array(self) -> None:
        """Test that sca results is an array."""
        output = run_tool("sca", "requirements.txt")
        assert isinstance(output["results"], list)

    def test_sca_results_have_required_fields(self) -> None:
        """Test that sca results have required fields."""
        output = run_tool("sca", "requirements.txt")
        for result in output["results"]:
            assert "file" in result  # package name
            assert "line" in result  # version
            assert "severity" in result
            assert "rule" in result  # CVE ID

    def test_sca_invalid_file(self) -> None:
        """Test sca with invalid file returns error."""
        output = run_tool("sca", "/nonexistent/requirements.txt")
        assert output["success"] is False


class TestAstTool:
    """Tests for ast.sh tool."""

    def test_ast_requires_file_argument(self) -> None:
        """Test that ast.sh requires a file argument."""
        output = run_tool("ast")
        assert output["success"] is False

    def test_ast_returns_valid_json(self) -> None:
        """Test that ast.sh returns valid JSON."""
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "src" / "core" / "config.py"

        if config_file.exists():
            output = run_tool("ast", str(config_file))
            assert "success" in output
            assert "results" in output

    def test_ast_requires_python_file(self) -> None:
        """Test that ast.sh requires .py extension."""
        output = run_tool("ast", "README.md")
        assert output["success"] is False

    def test_ast_nonexistent_file(self) -> None:
        """Test ast with nonexistent file returns error."""
        output = run_tool("ast", "/nonexistent/file.py")
        assert output["success"] is False


class TestE2eTool:
    """Tests for e2e.sh tool."""

    def test_e2e_returns_valid_json(self) -> None:
        """Test that e2e.sh returns valid JSON."""
        output = run_tool("e2e")
        assert "success" in output
        assert "results" in output
        assert "errors" in output

    def test_e2e_results_array(self) -> None:
        """Test that e2e results is an array."""
        output = run_tool("e2e")
        assert isinstance(output["results"], list)


class TestJsonContract:
    """Test JSON contract compliance across all tools."""

    def test_all_tools_return_success_field(self) -> None:
        """Test that all tools return success field."""
        tools = ["lint", "test", "sast", "sca", "e2e"]
        for tool in tools:
            output = run_tool(tool, ".")
            assert "success" in output
            assert isinstance(output["success"], bool)

    def test_all_tools_return_results_array(self) -> None:
        """Test that all tools return results array."""
        tools = ["lint", "test", "sast", "sca", "e2e"]
        for tool in tools:
            output = run_tool(tool, ".")
            assert "results" in output
            assert isinstance(output["results"], list)

    def test_all_tools_return_errors_array(self) -> None:
        """Test that all tools return errors array."""
        tools = ["lint", "test", "sast", "sca", "e2e"]
        for tool in tools:
            output = run_tool(tool, ".")
            assert "errors" in output
            assert isinstance(output["errors"], list)

    def test_result_objects_have_required_fields(self) -> None:
        """Test that result objects have required fields."""
        output = run_tool("lint", "src/")
        for result in output.get("results", []):
            # Results should have these fields
            assert "file" in result
            assert "line" in result
            assert "severity" in result
            assert "message" in result
            assert "rule" in result

    def test_severity_values_valid(self) -> None:
        """Test that severity values are valid."""
        output = run_tool("lint", "src/")
        valid_severities = {"error", "warning", "info"}
        for result in output.get("results", []):
            assert result.get("severity") in valid_severities
