# P01-F02: Bash Tool Abstraction Layer - Technical Design

## Overview

Replace stub tool wrappers with real implementations while maintaining the standardized JSON contract established in P01-F01. These tools enable agents to interact with development operations (linting, testing, security scanning) through a consistent interface.

## Scope

Implement production backends for the following bash tool wrappers:

| Tool | Description | Backend | Priority |
|------|-------------|---------|----------|
| lint.sh | Run Python linter | ruff | High |
| test.sh | Run test suite | pytest | High |
| sast.sh | Static security analysis | bandit | Medium |
| sca.sh | Dependency vulnerability scan | pip-audit | Medium |
| ast.sh | AST parsing for code analysis | Python ast module | Medium |
| e2e.sh | End-to-end tests | pytest + docker | High |

## JSON Contract

All tools MUST emit output conforming to this schema (unchanged from stubs):

```json
{
  "success": true|false,
  "results": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "error|warning|info",
      "message": "Description of finding",
      "rule": "rule-id"
    }
  ],
  "errors": [
    "Error message if tool execution failed"
  ]
}
```

### Field Definitions

- **success**: `true` if tool executed without errors (findings are not errors), `false` if tool crashed or failed to run
- **results**: Array of findings/results from the tool. Empty array means no findings.
- **errors**: Array of error messages if tool failed to execute. Empty array on success.

## Interfaces

### Input Interface

All tools accept a single optional positional argument specifying the target path:
```bash
./tools/<tool>.sh [target_path]
```

### Output Interface (JSON Contract)

All tools emit JSON to stdout with the following schema:
```json
{
  "success": boolean,
  "results": Array<Finding>,
  "errors": Array<string>
}
```

Where `Finding` is:
```json
{
  "file": string,
  "line": number,
  "severity": "error" | "warning" | "info",
  "message": string,
  "rule": string
}
```

## Technical Approach

1. **Parser Library**: Create tool-specific parsers in `tools/lib/parsers/` that convert native tool output to the JSON contract
2. **Wrapper Pattern**: Each tool follows a consistent wrapper pattern: check dependencies, execute tool, parse output, emit JSON
3. **Error Isolation**: Tool failures are captured and returned as JSON errors rather than crashing the wrapper
4. **Graceful Degradation**: If a backend tool is not installed, return a helpful error message with installation instructions

## File Structure

```
tools/
├── lib/
│   ├── common.sh         # Shared functions (exists from P01-F01)
│   └── parsers/          # Tool-specific output parsers
│       ├── ruff.sh
│       ├── pytest.sh
│       ├── bandit.sh
│       └── pip_audit.sh
├── lint.sh               # Linter wrapper
├── test.sh               # Test runner wrapper
├── sast.sh               # Security analysis wrapper
├── sca.sh                # Dependency scan wrapper
├── ast.sh                # AST parser wrapper
├── e2e.sh                # E2E test wrapper
└── README.md             # Tool documentation
```

### Tool Implementation Pattern

Each tool follows this structure:

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Check required tool is installed
require_command "tool_name"

main() {
    local target="${1:-.}"

    log_info "Running tool on: $target"

    # Execute tool and capture output
    local raw_output
    raw_output=$(run_tool "$target" 2>&1) || true

    # Parse tool output to JSON
    local parsed
    parsed=$(parse_tool_output "$raw_output")

    # Emit standardized result
    emit_result "$parsed"
}

main "$@"
```

## Tool Specifications

### 1. lint.sh (ruff)

**Backend**: [ruff](https://github.com/astral-sh/ruff) - Fast Python linter

**Input**: Directory or file path (default: current directory)

**Execution**:
```bash
ruff check --output-format=json "$target"
```

**Output Mapping**:
| ruff field | JSON field |
|------------|------------|
| filename | file |
| location.row | line |
| code | rule |
| message | message |
| fix.applicability | severity (auto-fixable = warning, else error) |

### 2. test.sh (pytest)

**Backend**: [pytest](https://pytest.org/) with JSON reporting

**Input**: Test directory or file path (default: tests/)

**Execution**:
```bash
pytest --tb=short -q --json-report --json-report-file=/tmp/report.json "$target"
```

**Output Mapping**:
- Each test result becomes a result entry
- severity: "error" for failed, "warning" for skipped, "info" for passed
- message: test outcome and any failure details

### 3. sast.sh (bandit)

**Backend**: [bandit](https://bandit.readthedocs.io/) - Python security linter

**Input**: Directory or file path (default: src/)

**Execution**:
```bash
bandit -r -f json "$target"
```

**Output Mapping**:
| bandit field | JSON field |
|--------------|------------|
| filename | file |
| line_number | line |
| test_id | rule |
| issue_text | message |
| issue_severity | severity (HIGH=error, MEDIUM=warning, LOW=info) |

### 4. sca.sh (pip-audit)

**Backend**: [pip-audit](https://pypi.org/project/pip-audit/) - Dependency vulnerability scanner

**Input**: requirements.txt path (default: requirements.txt)

**Execution**:
```bash
pip-audit -r "$target" --format=json
```

**Output Mapping**:
| pip-audit field | JSON field |
|-----------------|------------|
| name | file (package name) |
| version | line (version string) |
| vulns[].id | rule |
| vulns[].description | message |
| vulns[].fix_versions | severity (fix available = warning, else error) |

### 5. ast.sh (Python ast)

**Backend**: Python standard library `ast` module

**Input**: Python file path (required)

**Execution**:
```bash
python3 -c "import ast, json, sys; ..." "$target"
```

**Output**: Structured code analysis including:
- Function definitions with signatures
- Class definitions with methods
- Import statements
- Global variables

### 6. e2e.sh (pytest + docker)

**Backend**: pytest with Docker Compose integration

**Input**: Test suite path (default: tests/e2e/)

**Execution**:
```bash
# Ensure containers are running
docker compose -f docker/docker-compose.yml up -d

# Run E2E tests
pytest tests/e2e/ --tb=short -q --json-report

# Parse and emit results
```

## Dependencies

### P01-F01 Dependencies (COMPLETE)

- `tools/lib/common.sh` - Shared bash functions
- `docker/docker-compose.yml` - Container topology
- Python 3.11+ environment

### External Tool Dependencies

All tools must be installable via pip:

```
ruff>=0.1.0
pytest>=7.0.0
pytest-json-report>=1.5.0
bandit>=1.7.0
pip-audit>=2.6.0
```

Add to `requirements-dev.txt` (to be created).

## Error Handling

### Tool Not Installed

If a required tool is not installed:
```json
{
  "success": false,
  "results": [],
  "errors": ["Required tool 'ruff' is not installed. Install with: pip install ruff"]
}
```

### Tool Execution Failure

If tool crashes or times out:
```json
{
  "success": false,
  "results": [],
  "errors": ["Tool execution failed: <error details>"]
}
```

### Parse Failure

If tool output cannot be parsed:
```json
{
  "success": false,
  "results": [],
  "errors": ["Failed to parse tool output: <raw output snippet>"]
}
```

## Testing Strategy

### Unit Tests

Each tool parser should have unit tests with:
- Sample tool output fixtures
- Expected JSON conversion
- Error case handling

### Integration Tests

Test each tool against real code:
- Create test fixtures with known issues
- Verify correct detection and reporting
- Test with clean code (empty results)

### E2E Tests

Test tools within the full container environment:
- Verify tools work inside Docker containers
- Test inter-tool workflows

## Security Considerations

1. **Input Validation**: Sanitize file paths to prevent directory traversal
2. **Timeout Protection**: All tool executions have configurable timeouts
3. **Output Sanitization**: Escape special characters in error messages
4. **No Shell Injection**: Use arrays for command arguments, not string interpolation

## Success Criteria

1. All six tools return valid JSON conforming to the contract
2. Tools detect real issues in test fixtures
3. Tools handle errors gracefully without crashing
4. All existing bash tests continue to pass
5. Documentation is complete with usage examples
