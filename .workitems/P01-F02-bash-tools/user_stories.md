# P01-F02: Bash Tool Abstraction Layer - User Stories

## Overview

These user stories define the behavior expected from the bash tool abstraction layer. The primary users are **agent workers** that invoke these tools programmatically and parse the JSON output for decision-making.

---

## US-1: Linting with lint.sh

**As an** agent worker
**I want to** run `lint.sh` on Python code and receive standardized JSON output
**So that** I can identify code style issues and violations to fix

### Acceptance Criteria

- [ ] `lint.sh src/` executes ruff on the specified directory
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Each lint finding includes `file`, `line`, `severity`, `message`, and `rule`
- [ ] `success: true` when ruff executes (even with findings)
- [ ] `success: false` with error message when ruff is not installed
- [ ] Auto-fixable issues are marked with `severity: "warning"`
- [ ] Non-fixable issues are marked with `severity: "error"`

### Test Scenarios

| Scenario | Input | Expected Outcome |
|----------|-------|------------------|
| Code with lint issues | `lint.sh tests/fixtures/lint_issues.py` | JSON with findings array populated |
| Clean code | `lint.sh tests/fixtures/clean.py` | JSON with empty results array |
| Ruff not installed | `lint.sh src/` (without ruff) | JSON with success=false and installation error |
| Invalid path | `lint.sh /nonexistent/` | JSON with success=false and path error |

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "src/core/config.py",
      "line": 42,
      "severity": "warning",
      "message": "Line too long (105 > 100 characters)",
      "rule": "E501"
    }
  ],
  "errors": []
}
```

---

## US-2: Testing with test.sh

**As an** agent worker
**I want to** run `test.sh` on a test suite and receive standardized JSON output
**So that** I can determine which tests passed, failed, or were skipped

### Acceptance Criteria

- [ ] `test.sh tests/unit/` executes pytest on the specified path
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Each test result includes `file`, `line`, `severity`, `message`, and `rule` (test name)
- [ ] Failed tests have `severity: "error"` with failure details in message
- [ ] Skipped tests have `severity: "warning"` with skip reason
- [ ] Passed tests have `severity: "info"`
- [ ] `success: true` when pytest executes (even with failures)
- [ ] `success: false` with error message when pytest is not installed
- [ ] Summary statistics are included in the output

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "tests/unit/test_config.py",
      "line": 15,
      "severity": "error",
      "message": "AssertionError: expected 42 but got 41",
      "rule": "test_config_loads_defaults"
    },
    {
      "file": "tests/unit/test_config.py",
      "line": 25,
      "severity": "info",
      "message": "PASSED",
      "rule": "test_config_validates_types"
    }
  ],
  "errors": []
}
```

---

## US-3: Security Analysis with sast.sh

**As an** agent worker
**I want to** run `sast.sh` on Python code and receive standardized JSON output
**So that** I can identify security vulnerabilities in the codebase

### Acceptance Criteria

- [ ] `sast.sh src/` executes bandit on the specified directory
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Each security finding includes `file`, `line`, `severity`, `message`, and `rule`
- [ ] HIGH severity issues map to `severity: "error"`
- [ ] MEDIUM severity issues map to `severity: "warning"`
- [ ] LOW severity issues map to `severity: "info"`
- [ ] `success: true` when bandit executes (even with findings)
- [ ] `success: false` with error message when bandit is not installed
- [ ] Findings include bandit test ID (e.g., B101, B301)

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "src/core/config.py",
      "line": 78,
      "severity": "warning",
      "message": "Use of assert detected. Assertions are removed when compiling to optimized bytecode.",
      "rule": "B101"
    }
  ],
  "errors": []
}
```

---

## US-4: Dependency Scanning with sca.sh

**As an** agent worker
**I want to** run `sca.sh` on dependency files and receive standardized JSON output
**So that** I can identify vulnerable dependencies that need updating

### Acceptance Criteria

- [ ] `sca.sh requirements.txt` executes pip-audit on the specified file
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Each vulnerability includes `file` (package name), `line` (version), `severity`, `message`, and `rule` (CVE ID)
- [ ] Vulnerabilities with available fixes map to `severity: "warning"`
- [ ] Vulnerabilities without fixes map to `severity: "error"`
- [ ] `success: true` when pip-audit executes (even with findings)
- [ ] `success: false` with error message when pip-audit is not installed
- [ ] Fix version recommendations are included in message when available

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "requests",
      "line": "2.28.0",
      "severity": "warning",
      "message": "CVE-2023-32681: Unintended leak of Proxy-Authorization header. Fix available in 2.31.0",
      "rule": "CVE-2023-32681"
    }
  ],
  "errors": []
}
```

---

## US-5: Code Structure Analysis with ast.sh

**As an** agent worker
**I want to** run `ast.sh` on a Python file and receive standardized JSON output
**So that** I can understand the code structure for analysis and refactoring

### Acceptance Criteria

- [ ] `ast.sh src/core/config.py` parses the specified Python file
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Results include function definitions with name, line, and signature
- [ ] Results include class definitions with name, line, and methods
- [ ] Results include import statements with module names
- [ ] Results include global variable assignments
- [ ] `success: true` when parsing succeeds
- [ ] `success: false` with syntax error details when parsing fails
- [ ] Works with Python 3.11+ syntax features

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "src/core/config.py",
      "line": 1,
      "severity": "info",
      "message": "import: from pathlib import Path",
      "rule": "import"
    },
    {
      "file": "src/core/config.py",
      "line": 15,
      "severity": "info",
      "message": "class: Config(BaseModel)",
      "rule": "class"
    },
    {
      "file": "src/core/config.py",
      "line": 42,
      "severity": "info",
      "message": "function: load_config(path: Path) -> Config",
      "rule": "function"
    }
  ],
  "errors": []
}
```

---

## US-6: End-to-End Testing with e2e.sh

**As an** agent worker
**I want to** run `e2e.sh` and receive standardized JSON output
**So that** I can verify the full system works correctly

### Acceptance Criteria

- [ ] `e2e.sh` executes pytest on tests/e2e/ directory
- [ ] Docker containers are started if not running
- [ ] Output is valid JSON with `success`, `results`, and `errors` fields
- [ ] Test results follow the same format as test.sh
- [ ] `success: true` when e2e tests execute (even with failures)
- [ ] `success: false` if Docker is not available or containers fail to start
- [ ] Container startup errors are included in errors array

### Example Output

```json
{
  "success": true,
  "results": [
    {
      "file": "tests/e2e/test_workflow.py",
      "line": 10,
      "severity": "info",
      "message": "PASSED",
      "rule": "test_full_pipeline_execution"
    }
  ],
  "errors": []
}
```

---

## Non-Functional Requirements

### NFR-1: Performance

- Each tool should complete within 60 seconds for typical project size
- Tools should not consume more than 1GB memory
- JSON parsing should handle outputs up to 10MB

### NFR-2: Reliability

- Tools must never crash the calling process
- All errors must be captured and returned in JSON format
- Tools must be idempotent (same input = same output)

### NFR-3: Compatibility

- Tools must work on macOS and Linux
- Tools must work inside Docker containers
- Tools must work with Python 3.11+

### NFR-4: Documentation

- Each tool must have usage examples in README.md
- Error messages must include remediation steps
- JSON schema must be documented with examples
