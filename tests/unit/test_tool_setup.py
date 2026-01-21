"""Test tool setup and configuration."""

import os
from pathlib import Path


def test_requirements_dev_exists() -> None:
    """Test that requirements-dev.txt exists."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "requirements-dev.txt"
    assert req_file.exists(), "requirements-dev.txt not found"


def test_requirements_dev_has_dev_tools() -> None:
    """Test that requirements-dev.txt contains required tools."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "requirements-dev.txt"
    content = req_file.read_text()

    required_tools = ["ruff", "pytest", "pytest-json-report", "bandit", "pip-audit"]
    for tool in required_tools:
        assert tool in content, f"Tool {tool} not found in requirements-dev.txt"


def test_parsers_directory_exists() -> None:
    """Test that tools/lib/parsers directory exists."""
    project_root = Path(__file__).parent.parent.parent
    parsers_dir = project_root / "tools" / "lib" / "parsers"
    assert parsers_dir.exists(), "tools/lib/parsers directory not found"
    assert parsers_dir.is_dir(), "tools/lib/parsers is not a directory"


def test_pyproject_has_dev_dependencies() -> None:
    """Test that pyproject.toml has dev dependencies configured."""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    content = pyproject.read_text()

    assert "[project.optional-dependencies]" in content
    assert "dev = [" in content

    required_tools = ["ruff", "pytest", "pytest-json-report", "bandit", "pip-audit"]
    for tool in required_tools:
        assert tool in content, f"Tool {tool} not found in pyproject.toml"
