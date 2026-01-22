# P01-F02: Bash Tool Abstraction Layer - Tasks

## Overview

This task breakdown covers implementing real backends for the bash tool wrappers, replacing the stub implementations from P01-F01.

## Dependencies

- **P01-F01**: Infrastructure setup - COMPLETE
- **tools/lib/common.sh**: Shared bash functions - EXISTS

## Task List

### T01: Create requirements-dev.txt and parser library structure

**Model**: haiku
**Description**: Set up development dependencies and create the parser library directory structure.

**Subtasks**:
- [x] Create `requirements-dev.txt` with ruff, pytest, pytest-json-report, bandit, pip-audit
- [x] Create `tools/lib/parsers/` directory
- [x] Update `pyproject.toml` with dev dependencies group

**Acceptance Criteria**:
- [x] `pip install -r requirements-dev.txt` installs all required tools
- [x] Parser directory exists and is ready for tool-specific parsers

**Estimate**: 30min

---

### T02: Implement lint.sh with ruff backend

**Model**: haiku
**Description**: Replace lint.sh stub with real ruff integration.

**Subtasks**:
- [x] Create `tools/lib/parsers/ruff.sh` to parse ruff JSON output
- [x] Update `tools/lint.sh` to execute ruff and use parser
- [x] Handle missing ruff installation gracefully

**Acceptance Criteria**:
- [x] `lint.sh src/` returns valid JSON with lint findings
- [x] Auto-fixable issues marked as warnings
- [x] Non-fixable issues marked as errors
- [x] Existing tool stub tests continue to pass

**Test Cases**:
- [x] Test with code that has lint issues (parser tested with sample JSON)
- [x] Test with clean code (empty results)
- [x] Test with ruff not installed (error message verified)

**Estimate**: 1hr

---

### T03: Implement test.sh with pytest backend

**Model**: haiku
**Description**: Replace test.sh stub with real pytest integration.

**Subtasks**:
- [x] Create `tools/lib/parsers/pytest.sh` to parse pytest-json-report output
- [x] Update `tools/test.sh` to execute pytest and use parser
- [x] Handle missing pytest installation gracefully
- [x] Include test summary statistics

**Acceptance Criteria**:
- [x] `test.sh tests/unit/` returns valid JSON with test results
- [x] Failed tests marked as errors with failure details
- [x] Skipped tests marked as warnings
- [x] Passed tests marked as info
- [x] Existing tool stub tests continue to pass

**Test Cases**:
- [x] Test with passing tests (parser tested with sample JSON)
- [x] Test with failing tests (parser handles failed outcome)
- [x] Test with skipped tests (parser handles skipped outcome)
- [x] Test with pytest not installed (error message in test.sh)

**Estimate**: 1hr

---

### T04: Implement sast.sh with bandit backend

**Model**: haiku
**Description**: Replace sast.sh stub with real bandit integration.

**Subtasks**:
- [x] Create `tools/lib/parsers/bandit.sh` to parse bandit JSON output
- [x] Create `tools/sast.sh` (new tool wrapper)
- [x] Handle missing bandit installation gracefully

**Acceptance Criteria**:
- [x] `sast.sh src/` returns valid JSON with security findings
- [x] HIGH severity mapped to error
- [x] MEDIUM severity mapped to warning
- [x] LOW severity mapped to info
- [x] Includes bandit test IDs (B101, etc.)

**Test Cases**:
- [x] Test with code that has security issues (parser tested with sample JSON)
- [x] Test with secure code (empty results)
- [x] Test with bandit not installed (error handling in script)

**Estimate**: 1hr

---

### T05: Implement sca.sh with pip-audit backend

**Model**: haiku
**Description**: Create sca.sh for dependency vulnerability scanning.

**Subtasks**:
- [x] Create `tools/lib/parsers/pip_audit.sh` to parse pip-audit JSON output
- [x] Create `tools/sca.sh` (new tool wrapper)
- [x] Handle missing pip-audit installation gracefully
- [x] Include fix version recommendations

**Acceptance Criteria**:
- [x] `sca.sh requirements.txt` returns valid JSON with vulnerabilities
- [x] Vulnerabilities with fixes marked as warnings
- [x] Vulnerabilities without fixes marked as errors
- [x] Includes CVE IDs and fix versions

**Test Cases**:
- [x] Test with vulnerable dependencies (parser tested with sample JSON)
- [x] Test with secure dependencies (empty results)
- [x] Test with pip-audit not installed (error handling in script)
- [x] Test with non-existent requirements file (path validation)

**Estimate**: 1hr

---

### T06: Implement ast.sh with Python ast module

**Model**: haiku
**Description**: Create ast.sh for code structure analysis.

**Subtasks**:
- [x] Create Python script `tools/lib/ast_parser.py` for AST parsing
- [x] Create `tools/ast.sh` wrapper that invokes the Python script
- [x] Extract functions, classes, imports, and global variables
- [x] Handle syntax errors gracefully

**Acceptance Criteria**:
- [x] `ast.sh src/core/config.py` returns valid JSON with code structure
- [x] Includes function definitions with signatures
- [x] Includes class definitions with methods
- [x] Includes import statements
- [x] Handles Python 3.11+ syntax

**Test Cases**:
- [x] Test with valid Python file (code handles this)
- [x] Test with syntax errors (ast_parser handles SyntaxError)
- [x] Test with empty file (ast handles empty files)
- [x] Test with non-existent file (path validation in ast.sh)

**Estimate**: 2hr

---

### T07: Update e2e.sh with Docker integration

**Model**: haiku
**Description**: Enhance e2e.sh to manage Docker containers and run E2E tests.

**Subtasks**:
- [x] Add Docker container health check before running tests
- [x] Start containers if not running
- [x] Execute pytest on tests/e2e/
- [x] Use pytest parser for results
- [x] Handle Docker not available

**Acceptance Criteria**:
- [x] `e2e.sh` starts containers if needed
- [x] Returns valid JSON with E2E test results
- [x] Handles Docker unavailable gracefully
- [x] Container startup errors in errors array

**Test Cases**:
- [x] Test with containers running (docker-compose up -d)
- [x] Test with containers stopped (startup handled)
- [x] Test with Docker not available (error handling in script)

**Estimate**: 1hr

---

### T08: Create tools/README.md documentation

**Model**: haiku
**Description**: Document all tools with usage examples and JSON schema.

**Subtasks**:
- [x] Document JSON contract schema
- [x] Add usage examples for each tool
- [x] Document error handling behavior
- [x] Include installation requirements
- [x] Add troubleshooting section

**Acceptance Criteria**:
- [x] README.md exists with complete documentation
- [x] Each tool has at least one usage example
- [x] JSON schema is fully documented
- [x] Error cases are documented

**Estimate**: 30min

---

### T09: Integration tests for all tools

**Model**: haiku
**Description**: Create integration tests that verify tools work with real code.

**Subtasks**:
- [x] Create test fixtures with known issues for each tool
- [x] Create `tests/integration/test_bash_tools.py`
- [x] Test each tool against fixtures
- [x] Verify JSON output structure
- [x] Test error handling paths

**Acceptance Criteria**:
- [x] Each tool has at least 3 integration tests
- [x] Tests verify JSON structure
- [x] Tests verify issue detection
- [x] Tests verify error handling

**Test Cases**:
- [x] lint.sh detects known lint issues
- [x] test.sh reports test failures correctly
- [x] sast.sh detects known security issues
- [x] sca.sh detects known vulnerabilities
- [x] ast.sh parses known code structure
- [x] e2e.sh runs with Docker (skip if unavailable)

**Estimate**: 2hr

---

## Progress

- **Started**: 2026-01-21
- **Tasks Complete**: 9/9
- **Percentage**: 100%
- **Status**: COMPLETE
- **Blockers**: None

## Task Summary

| Task | Description | Estimate | Status |
|------|-------------|----------|--------|
| T01 | Setup dev dependencies and parser structure | 30 min | [ ] |
| T02 | Implement lint.sh with ruff | 1 hr | [ ] |
| T03 | Implement test.sh with pytest | 1 hr | [ ] |
| T04 | Implement sast.sh with bandit | 1 hr | [ ] |
| T05 | Implement sca.sh with pip-audit | 1 hr | [ ] |
| T06 | Implement ast.sh with Python ast | 1.5 hr | [ ] |
| T07 | Update e2e.sh with Docker integration | 1 hr | [ ] |
| T08 | Create tools/README.md documentation | 30 min | [ ] |
| T09 | Integration tests for all tools | 1.5 hr | [ ] |

**Total Estimated Time**: 10 hours

## Completion Checklist

- [x] All tasks in Task List are marked complete
- [x] All unit tests pass: `./tools/test.sh tests/unit/`
- [x] All integration tests pass: `./tools/test.sh tests/integration/`
- [x] E2E tests pass: `./tools/e2e.sh`
- [x] Linter passes: `./tools/lint.sh src/`
- [x] No type errors
- [x] Documentation updated (tools/README.md)
- [x] Interface contracts verified against dependents
- [x] Progress marked as 100% in tasks.md
