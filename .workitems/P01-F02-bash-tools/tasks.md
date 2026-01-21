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
- [ ] Create `tools/lib/parsers/bandit.sh` to parse bandit JSON output
- [ ] Create `tools/sast.sh` (new tool wrapper)
- [ ] Handle missing bandit installation gracefully

**Acceptance Criteria**:
- [ ] `sast.sh src/` returns valid JSON with security findings
- [ ] HIGH severity mapped to error
- [ ] MEDIUM severity mapped to warning
- [ ] LOW severity mapped to info
- [ ] Includes bandit test IDs (B101, etc.)

**Test Cases**:
- [ ] Test with code that has security issues
- [ ] Test with secure code (empty results)
- [ ] Test with bandit not installed

**Estimate**: 1hr

---

### T05: Implement sca.sh with pip-audit backend

**Model**: haiku
**Description**: Create sca.sh for dependency vulnerability scanning.

**Subtasks**:
- [ ] Create `tools/lib/parsers/pip_audit.sh` to parse pip-audit JSON output
- [ ] Create `tools/sca.sh` (new tool wrapper)
- [ ] Handle missing pip-audit installation gracefully
- [ ] Include fix version recommendations

**Acceptance Criteria**:
- [ ] `sca.sh requirements.txt` returns valid JSON with vulnerabilities
- [ ] Vulnerabilities with fixes marked as warnings
- [ ] Vulnerabilities without fixes marked as errors
- [ ] Includes CVE IDs and fix versions

**Test Cases**:
- [ ] Test with vulnerable dependencies (use test fixture)
- [ ] Test with secure dependencies (empty results)
- [ ] Test with pip-audit not installed
- [ ] Test with non-existent requirements file

**Estimate**: 1hr

---

### T06: Implement ast.sh with Python ast module

**Model**: haiku
**Description**: Create ast.sh for code structure analysis.

**Subtasks**:
- [ ] Create Python script `tools/lib/ast_parser.py` for AST parsing
- [ ] Create `tools/ast.sh` wrapper that invokes the Python script
- [ ] Extract functions, classes, imports, and global variables
- [ ] Handle syntax errors gracefully

**Acceptance Criteria**:
- [ ] `ast.sh src/core/config.py` returns valid JSON with code structure
- [ ] Includes function definitions with signatures
- [ ] Includes class definitions with methods
- [ ] Includes import statements
- [ ] Handles Python 3.11+ syntax

**Test Cases**:
- [ ] Test with valid Python file
- [ ] Test with syntax errors
- [ ] Test with empty file
- [ ] Test with non-existent file

**Estimate**: 2hr

---

### T07: Update e2e.sh with Docker integration

**Model**: haiku
**Description**: Enhance e2e.sh to manage Docker containers and run E2E tests.

**Subtasks**:
- [ ] Add Docker container health check before running tests
- [ ] Start containers if not running
- [ ] Execute pytest on tests/e2e/
- [ ] Use pytest parser for results
- [ ] Handle Docker not available

**Acceptance Criteria**:
- [ ] `e2e.sh` starts containers if needed
- [ ] Returns valid JSON with E2E test results
- [ ] Handles Docker unavailable gracefully
- [ ] Container startup errors in errors array

**Test Cases**:
- [ ] Test with containers running
- [ ] Test with containers stopped
- [ ] Test with Docker not available

**Estimate**: 1hr

---

### T08: Create tools/README.md documentation

**Model**: haiku
**Description**: Document all tools with usage examples and JSON schema.

**Subtasks**:
- [ ] Document JSON contract schema
- [ ] Add usage examples for each tool
- [ ] Document error handling behavior
- [ ] Include installation requirements
- [ ] Add troubleshooting section

**Acceptance Criteria**:
- [ ] README.md exists with complete documentation
- [ ] Each tool has at least one usage example
- [ ] JSON schema is fully documented
- [ ] Error cases are documented

**Estimate**: 30min

---

### T09: Integration tests for all tools

**Model**: haiku
**Description**: Create integration tests that verify tools work with real code.

**Subtasks**:
- [ ] Create test fixtures with known issues for each tool
- [ ] Create `tests/integration/test_bash_tools.py`
- [ ] Test each tool against fixtures
- [ ] Verify JSON output structure
- [ ] Test error handling paths

**Acceptance Criteria**:
- [ ] Each tool has at least 3 integration tests
- [ ] Tests verify JSON structure
- [ ] Tests verify issue detection
- [ ] Tests verify error handling

**Test Cases**:
- [ ] lint.sh detects known lint issues
- [ ] test.sh reports test failures correctly
- [ ] sast.sh detects known security issues
- [ ] sca.sh detects known vulnerabilities
- [ ] ast.sh parses known code structure
- [ ] e2e.sh runs with Docker (skip if unavailable)

**Estimate**: 2hr

---

## Progress

- **Started**: 2026-01-21
- **Tasks Complete**: 3/9
- **Percentage**: 33%
- **Status**: IN_PROGRESS
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

- [ ] All tasks in Task List are marked complete
- [ ] All unit tests pass: `./tools/test.sh tests/unit/`
- [ ] All integration tests pass: `./tools/test.sh tests/integration/`
- [ ] E2E tests pass: `./tools/e2e.sh`
- [ ] Linter passes: `./tools/lint.sh src/`
- [ ] No type errors
- [ ] Documentation updated (tools/README.md)
- [ ] Interface contracts verified against dependents
- [ ] Progress marked as 100% in tasks.md
