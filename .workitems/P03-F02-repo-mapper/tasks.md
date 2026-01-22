# P03-F02: Repo Mapper - Context Pack Generation - Tasks

## Overview

Task breakdown for implementing the Repo Mapper context pack generator.

## Dependencies

- **P03-F01**: ContextPack model, AgentRole - (implement in parallel)
- **P01-F02**: AST tool wrapper - COMPLETE

## Task List

### T01: Define Repo Mapper data models

**File:** `src/workers/repo_mapper/models.py`
**Test:** `tests/unit/test_repo_mapper_models.py`

- [ ] Define `SymbolKind` enum (FUNCTION, CLASS, INTERFACE, VARIABLE, etc.)
- [ ] Define `SymbolInfo` dataclass
- [ ] Define `ImportInfo` dataclass
- [ ] Define `ParsedFile` dataclass
- [ ] Define `DependencyInfo` dataclass
- [ ] Define `ASTContext` dataclass
- [ ] Add JSON serialization methods
- [ ] Write unit tests for all models

**Estimate:** 1h

---

### T02: Implement Python AST Parser

**File:** `src/workers/repo_mapper/parsers/python_parser.py`
**Test:** `tests/unit/test_python_parser.py`

- [ ] Create `PythonParser` class implementing `ASTParser` protocol
- [ ] Parse functions with signatures and docstrings
- [ ] Parse classes with methods and bases
- [ ] Parse import statements (absolute and relative)
- [ ] Extract type hints from annotations
- [ ] Handle syntax errors gracefully
- [ ] Write unit tests with Python fixtures

**Estimate:** 2h

---

### T03: Implement TypeScript AST Parser

**File:** `src/workers/repo_mapper/parsers/typescript_parser.py`
**Test:** `tests/unit/test_typescript_parser.py`

- [ ] Create `TypeScriptParser` class implementing `ASTParser` protocol
- [ ] Install and configure tree-sitter with TypeScript grammar
- [ ] Parse functions and arrow functions
- [ ] Parse classes and interfaces
- [ ] Parse import/export statements
- [ ] Handle JSX components
- [ ] Write unit tests with TypeScript fixtures

**Estimate:** 2h

---

### T04: Implement Parser Registry

**File:** `src/workers/repo_mapper/parsers/__init__.py`
**Test:** `tests/unit/test_parser_registry.py`

- [ ] Create `ParserRegistry` class
- [ ] Register Python parser for `.py` files
- [ ] Register TypeScript parser for `.ts`, `.tsx`, `.js`, `.jsx`
- [ ] Implement `get_parser_for_file()` method
- [ ] Handle unknown file types gracefully
- [ ] Write unit tests

**Estimate:** 30min

---

### T05: Implement DependencyGraph

**File:** `src/workers/repo_mapper/dependency_graph.py`
**Test:** `tests/unit/test_dependency_graph.py`

- [ ] Create `DependencyGraph` class
- [ ] Implement `add_file()` to build graph from parsed files
- [ ] Implement `get_dependencies()` with depth limit
- [ ] Implement `get_dependents()` with depth limit
- [ ] Resolve relative imports to absolute paths
- [ ] Handle circular dependencies
- [ ] Implement graph serialization
- [ ] Write unit tests with graph fixtures

**Estimate:** 2h

---

### T06: Implement SymbolExtractor

**File:** `src/workers/repo_mapper/symbol_extractor.py`
**Test:** `tests/unit/test_symbol_extractor.py`

- [ ] Create `SymbolExtractor` class
- [ ] Extract symbols from task description (regex + heuristics)
- [ ] Match symbols against parsed repository
- [ ] Find related symbols (implementations, usages)
- [ ] Score symbol relevance
- [ ] Write unit tests

**Estimate:** 1.5h

---

### T07: Implement TokenCounter

**File:** `src/workers/repo_mapper/token_counter.py`
**Test:** `tests/unit/test_token_counter.py`

- [ ] Create `TokenCounter` class using tiktoken
- [ ] Count tokens for text content
- [ ] Count tokens for ContextPack
- [ ] Provide estimates for symbol signatures
- [ ] Cache counts for repeated content
- [ ] Write unit tests

**Estimate:** 1h

---

### T08: Implement ContextBuilder

**File:** `src/workers/repo_mapper/context_builder.py`
**Test:** `tests/unit/test_context_builder.py`

- [ ] Create `ContextBuilder` class
- [ ] Inject DependencyGraph, SymbolExtractor, TokenCounter
- [ ] Implement relevance scoring algorithm
- [ ] Implement content selection with budget
- [ ] Support role-specific filtering
- [ ] Truncate low-relevance content when over budget
- [ ] Write unit tests with complex scenarios

**Estimate:** 2h

---

### T09: Implement RepoMapper main class

**File:** `src/workers/repo_mapper/mapper.py`
**Test:** `tests/unit/test_repo_mapper.py`

- [ ] Create `RepoMapper` class
- [ ] Implement `generate_context_pack()` method
- [ ] Implement `refresh_ast_context()` method
- [ ] Implement `save_context_pack()` to write JSON
- [ ] Load AST context from cache when available
- [ ] Validate inputs and outputs
- [ ] Write unit tests

**Estimate:** 1.5h

---

### T10: Implement AST Context Caching

**File:** `src/workers/repo_mapper/cache.py`
**Test:** `tests/unit/test_repo_mapper_cache.py`

- [ ] Create `ASTContextCache` class
- [ ] Implement `get()` with TTL check
- [ ] Implement `save()` to persist cache
- [ ] Implement `invalidate()` on Git SHA change
- [ ] Support partial invalidation for changed files
- [ ] Write unit tests

**Estimate:** 1h

---

### T11: Integration tests for Repo Mapper

**File:** `tests/integration/test_repo_mapper.py`

- [ ] Test parsing this repository's Python files
- [ ] Test dependency graph for real code
- [ ] Test context pack generation for sample tasks
- [ ] Verify token budget enforcement
- [ ] Test cache invalidation

**Estimate:** 2h

---

### T12: Add Repo Mapper exceptions and configuration

**Files:** `src/core/exceptions.py`, `src/workers/repo_mapper/config.py`

- [ ] Add `RepoMapperError` exception
- [ ] Add `ParseError` exception
- [ ] Add `DependencyResolutionError` exception
- [ ] Create `RepoMapperConfig` dataclass
- [ ] Load from environment variables
- [ ] Document configuration options

**Estimate:** 30min

---

## Progress

- **Started**: (not started)
- **Tasks Complete**: 0/12
- **Percentage**: 0%
- **Status**: PENDING
- **Blockers**: None

## Task Summary

| Task | Description | Estimate | Status |
|------|-------------|----------|--------|
| T01 | Data models | 1h | [ ] |
| T02 | Python AST Parser | 2h | [ ] |
| T03 | TypeScript AST Parser | 2h | [ ] |
| T04 | Parser Registry | 30min | [ ] |
| T05 | DependencyGraph | 2h | [ ] |
| T06 | SymbolExtractor | 1.5h | [ ] |
| T07 | TokenCounter | 1h | [ ] |
| T08 | ContextBuilder | 2h | [ ] |
| T09 | RepoMapper main class | 1.5h | [ ] |
| T10 | AST Context Caching | 1h | [ ] |
| T11 | Integration tests | 2h | [ ] |
| T12 | Exceptions and configuration | 30min | [ ] |

**Total Estimated Time**: 16 hours

## Completion Checklist

- [ ] All tasks in Task List are marked complete
- [ ] All unit tests pass: `./tools/test.sh tests/unit/`
- [ ] All integration tests pass: `./tools/test.sh tests/integration/`
- [ ] Linter passes: `./tools/lint.sh src/`
- [ ] No type errors: `mypy src/`
- [ ] Documentation updated
- [ ] Interface contracts verified against design.md
- [ ] Progress marked as 100% in tasks.md
