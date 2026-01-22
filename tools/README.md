# Development Tools Documentation

This directory contains bash tool wrappers for automated development operations. All tools follow a standard JSON contract for integration with agent systems.

## JSON Contract

All tools emit JSON output with the following schema:

```json
{
  "success": true|false,
  "results": [
    {
      "file": "path/to/file",
      "line": 42,
      "severity": "error|warning|info",
      "message": "Description of finding",
      "rule": "rule-id"
    }
  ],
  "errors": [
    "Error message if tool failed to execute"
  ]
}
```

### Fields

- **success**: `true` if tool executed successfully (findings are not errors), `false` if tool crashed or couldn't run
- **results**: Array of findings from the tool. Empty array means no findings.
- **errors**: Array of error messages if tool failed. Empty if success is true.
- **file**: Source file path
- **line**: Line number where finding occurs
- **severity**: `error` (high priority), `warning` (medium priority), `info` (informational)
- **message**: Human-readable description
- **rule**: Rule ID, test ID, or issue code

## Tools

### lint.sh - Python Linting

Run code style checks with [ruff](https://github.com/astral-sh/ruff).

**Usage:**
```bash
./tools/lint.sh [path]
```

**Examples:**
```bash
./tools/lint.sh src/                    # Lint entire src directory
./tools/lint.sh src/core/config.py      # Lint specific file
```

**Output Mapping:**
- Auto-fixable issues → `severity: "warning"`
- Non-fixable issues → `severity: "error"`

**Requirements:** `ruff` installed via `pip install ruff`

---

### test.sh - Test Runner

Run tests with [pytest](https://pytest.org/).

**Usage:**
```bash
./tools/test.sh [path]
```

**Examples:**
```bash
./tools/test.sh                         # Run all tests
./tools/test.sh tests/unit/             # Run unit tests only
./tools/test.sh tests/unit/test_foo.py  # Run specific test file
```

**Output Mapping:**
- Failed tests → `severity: "error"` with failure details
- Skipped tests → `severity: "warning"`
- Passed tests → `severity: "info"`

**Requirements:** `pytest` installed via `pip install pytest pytest-json-report`

---

### sast.sh - Security Analysis

Run static security analysis with [bandit](https://bandit.readthedocs.io/).

**Usage:**
```bash
./tools/sast.sh [path]
```

**Examples:**
```bash
./tools/sast.sh src/                    # Analyze entire src directory
./tools/sast.sh src/core/               # Analyze specific directory
```

**Output Mapping:**
- HIGH severity → `severity: "error"`
- MEDIUM severity → `severity: "warning"`
- LOW severity → `severity: "info"`

**Requirements:** `bandit` installed via `pip install bandit`

---

### sca.sh - Dependency Scanning

Run supply chain security analysis with [pip-audit](https://pypi.org/project/pip-audit/).

**Usage:**
```bash
./tools/sca.sh [requirements_file]
```

**Examples:**
```bash
./tools/sca.sh requirements.txt          # Scan default requirements
./tools/sca.sh requirements-dev.txt      # Scan dev requirements
```

**Output Mapping:**
- Vulnerabilities with fixes → `severity: "warning"`
- Vulnerabilities without fixes → `severity: "error"`
- File: package name
- Line: package version

**Requirements:** `pip-audit` installed via `pip install pip-audit`

---

### ast.sh - Code Structure Analysis

Parse Python code structure with the standard library [ast](https://docs.python.org/3/library/ast.html) module.

**Usage:**
```bash
./tools/ast.sh <python_file>
```

**Examples:**
```bash
./tools/ast.sh src/core/config.py       # Parse single file
```

**Output Includes:**
- Function definitions with signatures
- Class definitions with method lists
- Import statements
- Global variable assignments

**Output Mapping:**
- All findings → `severity: "info"`
- Rule types: `function`, `class`, `import`, `from_import`, `assignment`

**Requirements:** Python 3.11+ (built-in ast module)

---

### e2e.sh - End-to-End Testing

Run end-to-end tests with [pytest](https://pytest.org/) and Docker.

**Usage:**
```bash
./tools/e2e.sh
```

**Examples:**
```bash
./tools/e2e.sh                          # Run all E2E tests
```

**Behavior:**
1. Checks Docker and Docker Compose are available
2. Starts containers from `docker/docker-compose.yml`
3. Waits 3 seconds for containers to be ready
4. Runs `pytest tests/e2e/` with json-report plugin
5. Parses and returns test results

**Output Mapping:**
- Same as test.sh: failed → error, skipped → warning, passed → info

**Requirements:**
- Docker installed and running
- Docker Compose installed
- `pytest` installed via `pip install pytest pytest-json-report`

---

## Development Setup

Install all development tool dependencies:

```bash
# Option 1: Use requirements file
pip install -r requirements-dev.txt

# Option 2: Use pyproject.toml extras
pip install -e ".[dev]"
```

## Error Handling

All tools handle missing dependencies gracefully:

```json
{
  "success": false,
  "results": [],
  "errors": ["Required tool 'ruff' is not installed. Install with: pip install ruff"]
}
```

If a tool crashes, the error is returned in JSON format rather than breaking the calling process.

## Parser Library

Tool-specific parsers are in `lib/parsers/`:
- `ruff.sh` - Transform ruff JSON to standard format
- `pytest.sh` - Transform pytest-json-report to standard format
- `bandit.sh` - Transform bandit JSON to standard format
- `pip_audit.sh` - Transform pip-audit JSON to standard format
- `ast_parser.py` - Extract Python code structure

## Common Library

`lib/common.sh` provides shared utilities:
- `emit_result` - Output success JSON
- `emit_error` - Output failure JSON
- `json_escape` - Escape strings for JSON
- `log_info` / `log_warn` / `log_error` - Logging functions
- `require_command` - Check if command is available
- `require_file` - Check if file exists
- `require_directory` - Check if directory exists

## Integration with Agents

Tools are designed for programmatic use:

```bash
#!/bin/bash
result=$(./tools/lint.sh src/)
if echo "$result" | grep -q '"success": true'; then
    # Process results
    findings=$(echo "$result" | jq '.results[]')
else
    # Handle error
    error=$(echo "$result" | jq '.errors[0]')
    echo "Error: $error"
fi
```

## Troubleshooting

**Tool not found errors:**
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Verify installation
ruff --version
pytest --version
bandit --version
pip-audit --version
```

**Docker errors (E2E tests):**
```bash
# Check Docker is running
docker ps

# Check Docker Compose
docker-compose --version

# Verify compose file
docker-compose -f docker/docker-compose.yml config
```

**Permission denied:**
```bash
# Make scripts executable
chmod +x tools/*.sh
chmod +x tools/lib/parsers/*.sh
```
