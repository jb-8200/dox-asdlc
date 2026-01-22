# P03-F02: Repo Mapper - Context Pack Generation - Design

## Overview

The Repo Mapper generates deterministic context packs for agent execution. It extracts relevant symbols, interfaces, and dependency neighborhoods for each task, ensuring agents receive focused context without token waste.

## Architecture

### Component Model

```
┌────────────────────────────────────────────────────────────────┐
│                       Repo Mapper Service                      │
│                                                                │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   ASTParser     │    │  SymbolExtractor│                   │
│  │   (per-lang)    │───▶│                 │                   │
│  └─────────────────┘    └────────┬────────┘                   │
│                                  │                             │
│                                  ▼                             │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │ DependencyGraph │◀───│ ContextBuilder  │                   │
│  │                 │    │                 │                   │
│  └────────┬────────┘    └────────┬────────┘                   │
│           │                      │                             │
│           ▼                      ▼                             │
│  ┌─────────────────────────────────────────┐                  │
│  │           ContextPack Generator          │                  │
│  │                                         │                  │
│  │  - Symbol neighborhood extraction       │                  │
│  │  - Token budget management              │                  │
│  │  - Relevance scoring                    │                  │
│  └─────────────────────────────────────────┘                  │
│                                                                │
└───────────────────────────┬────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      ┌───────────────┐           ┌───────────────┐
      │  Git Repo     │           │ context/packs │
      │  (source)     │           │ (output)      │
      └───────────────┘           └───────────────┘
```

### Key Components

1. **ASTParser** - Language-specific AST parsing (Python, TypeScript, etc.)
2. **SymbolExtractor** - Extract functions, classes, interfaces, imports
3. **DependencyGraph** - Build import/call graph for dependency tracing
4. **ContextBuilder** - Select relevant content based on task requirements
5. **ContextPackGenerator** - Assemble final context pack with token budgeting

## Interfaces

### RepoMapper Interface

```python
class RepoMapper:
    """Generates context packs for agent tasks."""

    async def generate_context_pack(
        self,
        task_id: str,
        task_description: str,
        target_files: list[str],
        role: AgentRole,
        token_budget: int = 100_000,
    ) -> ContextPack:
        """Generate a context pack for the given task.

        Args:
            task_id: Unique task identifier
            task_description: Natural language description of the task
            target_files: Files directly relevant to the task
            role: Agent role for role-specific context selection
            token_budget: Maximum tokens for context pack

        Returns:
            ContextPack with relevant code and symbols
        """
        ...

    async def refresh_ast_context(self, repo_path: str) -> ASTContext:
        """Refresh the cached AST context for a repository.

        Called when repository content changes significantly.
        """
        ...
```

### ASTParser Protocol

```python
class ASTParser(Protocol):
    """Language-specific AST parsing."""

    def parse_file(self, file_path: str) -> ParsedFile:
        """Parse a single file and extract symbols."""
        ...

    def get_supported_extensions(self) -> list[str]:
        """Return file extensions this parser handles."""
        ...
```

### DependencyGraph Interface

```python
class DependencyGraph:
    """Tracks dependencies between files and symbols."""

    def add_file(self, parsed: ParsedFile) -> None:
        """Add a parsed file to the dependency graph."""
        ...

    def get_dependencies(
        self, symbol: str, max_depth: int = 3
    ) -> list[DependencyInfo]:
        """Get dependencies for a symbol up to max_depth."""
        ...

    def get_dependents(
        self, symbol: str, max_depth: int = 2
    ) -> list[DependencyInfo]:
        """Get symbols that depend on the given symbol."""
        ...
```

## Data Models

### ParsedFile

```python
@dataclass
class ParsedFile:
    """Result of parsing a source file."""
    path: str
    language: str
    symbols: list[SymbolInfo]
    imports: list[ImportInfo]
    exports: list[str]
    raw_content: str
    line_count: int
```

### SymbolInfo

```python
@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    kind: SymbolKind  # FUNCTION, CLASS, INTERFACE, VARIABLE, etc.
    file_path: str
    start_line: int
    end_line: int
    signature: str | None
    docstring: str | None
    references: list[str]  # Files that reference this symbol
```

### ImportInfo

```python
@dataclass
class ImportInfo:
    """Information about an import statement."""
    source: str  # Module/file being imported
    names: list[str]  # Symbols imported
    is_relative: bool
    line_number: int
```

### ASTContext

```python
@dataclass
class ASTContext:
    """Cached AST analysis for a repository."""
    repo_path: str
    git_sha: str
    files: dict[str, ParsedFile]
    dependency_graph: DependencyGraph
    created_at: datetime
    token_estimate: int
```

### ContextPack (from P03-F01)

```python
@dataclass
class ContextPack:
    """Context pack for agent execution."""
    task_id: str
    role: str
    files: list[FileContent]
    symbols: list[SymbolInfo]
    dependencies: list[DependencyInfo]
    metadata: dict[str, Any]
    token_count: int
    relevance_scores: dict[str, float]
```

## Context Selection Algorithm

### Step 1: Identify Seed Files
- Start with explicitly listed `target_files`
- Add files mentioned in `task_description`

### Step 2: Expand Dependencies
- For each seed file, traverse dependency graph
- Include imported modules (depth-limited)
- Include dependents that may be affected

### Step 3: Extract Relevant Symbols
- Parse task description for symbol references
- Include all symbols from target files
- Include interface definitions for imported symbols

### Step 4: Apply Token Budget
- Score content by relevance
- Prioritize: target files > direct deps > indirect deps
- Truncate or summarize to fit budget
- Include symbol signatures over full implementations when constrained

### Relevance Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Direct target | 1.0 | Explicitly listed in task |
| Task description match | 0.8 | Mentioned in description |
| Direct import | 0.6 | Imported by target file |
| Interface/Protocol | 0.7 | Defines contract for target |
| Test file | 0.5 | Tests for target |
| Indirect dependency | 0.3 | Dependency of dependency |

## Language Support

### Phase 1 (MVP)
- **Python** - Using `ast` module
- **TypeScript/JavaScript** - Using tree-sitter

### Phase 2 (Future)
- Go
- Rust
- Java

## Output Artifacts

### Per-Task Context Pack

Location: `context/packs/<task_id>.json`

```json
{
  "task_id": "task-123",
  "role": "coding",
  "git_sha": "abc123",
  "token_count": 45000,
  "files": [...],
  "symbols": [...],
  "dependencies": [...],
  "metadata": {
    "generated_at": "2026-01-22T10:00:00Z",
    "relevance_threshold": 0.3
  }
}
```

### Repository AST Context

Location: `context/ast_context.json`

Cached AST analysis refreshed on significant changes.

## Dependencies

### Required Components

- P01-F01: File system access
- P03-F01: ContextPack model

### External Dependencies

- `tree-sitter` - Multi-language AST parsing
- `tree-sitter-python` - Python grammar
- `tree-sitter-typescript` - TypeScript grammar
- `tiktoken` - Token counting

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTEXT_PACK_DIR` | `context/packs` | Output directory |
| `AST_CACHE_TTL` | `3600` | AST cache TTL in seconds |
| `DEFAULT_TOKEN_BUDGET` | `100000` | Default token budget |
| `MAX_DEPENDENCY_DEPTH` | `3` | Max depth for dependency tracing |
| `MIN_RELEVANCE_SCORE` | `0.2` | Minimum relevance to include |

## RLM Integration

When context requirements exceed practical limits:
- Repo Mapper can be invoked in RLM mode (P03-F03)
- Iterative exploration with sub-call budget
- Produce summary context pack with citations

## Testing Strategy

- Unit tests: Parse fixtures, verify symbol extraction
- Integration tests: Generate packs for real code
- Accuracy tests: Verify relevance scoring with labeled data
