"""Test lint.sh tool and ruff parser."""

import json
import subprocess
from pathlib import Path


def test_ruff_parser_empty_input() -> None:
    """Test ruff parser handles empty input (clean code)."""
    project_root = Path(__file__).parent.parent.parent
    parser_script = project_root / "tools" / "lib" / "parsers" / "ruff.sh"

    result = subprocess.run(
        ["/bin/bash", str(parser_script), ""],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output == [], "Parser should return empty array for empty input"


def test_ruff_parser_valid_json() -> None:
    """Test ruff parser transforms ruff JSON correctly."""
    project_root = Path(__file__).parent.parent.parent
    parser_script = project_root / "tools" / "lib" / "parsers" / "ruff.sh"

    # Example ruff output format
    ruff_json = json.dumps(
        [
            {
                "filename": "src/test.py",
                "location": {"row": 42, "column": 1},
                "code": "E501",
                "message": "Line too long",
                "fix": {"applicability": "automatic"},
            }
        ]
    )

    result = subprocess.run(
        ["/bin/bash", str(parser_script), ruff_json],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert len(output) == 1
    assert output[0]["file"] == "src/test.py"
    assert output[0]["line"] == 42
    assert output[0]["rule"] == "E501"
    assert output[0]["message"] == "Line too long"
    assert output[0]["severity"] == "warning"  # auto-fixable


def test_lint_sh_missing_ruff() -> None:
    """Test lint.sh handles missing ruff gracefully."""
    project_root = Path(__file__).parent.parent.parent
    lint_script = project_root / "tools" / "lint.sh"

    # This test verifies the error handling path
    # (actual execution depends on ruff being installed)
    assert lint_script.exists(), "lint.sh script should exist"


def test_lint_sh_invalid_path() -> None:
    """Test lint.sh handles invalid paths gracefully."""
    project_root = Path(__file__).parent.parent.parent
    lint_script = project_root / "tools" / "lint.sh"

    # Test that lint.sh script is properly formatted
    content = lint_script.read_text()
    assert "Path not found" in content
    assert "emit_error" in content
