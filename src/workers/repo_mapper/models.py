"""Data models for Repo Mapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SymbolKind(str, Enum):
    """Types of code symbols."""

    FUNCTION = "function"
    CLASS = "class"
    INTERFACE = "interface"
    VARIABLE = "variable"
    METHOD = "method"
    CONSTANT = "constant"


@dataclass
class SymbolInfo:
    """Information about a code symbol.

    Attributes:
        name: Symbol name
        kind: Symbol type (function, class, etc.)
        file_path: Path to file containing the symbol
        start_line: Starting line number
        end_line: Ending line number
        signature: Function/method signature if applicable
        docstring: Documentation string if present
        references: List of files that reference this symbol
    """

    name: str
    kind: SymbolKind
    file_path: str
    start_line: int
    end_line: int
    signature: str | None
    docstring: str | None
    references: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the symbol
        """
        return {
            "name": self.name,
            "kind": self.kind.value,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "signature": self.signature,
            "docstring": self.docstring,
            "references": self.references,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SymbolInfo:
        """Create SymbolInfo from dictionary.

        Args:
            data: Dictionary with symbol data

        Returns:
            SymbolInfo instance
        """
        return cls(
            name=data["name"],
            kind=SymbolKind(data["kind"]),
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            signature=data.get("signature"),
            docstring=data.get("docstring"),
            references=data.get("references", []),
        )


@dataclass
class ImportInfo:
    """Information about an import statement.

    Attributes:
        source: Module or file being imported
        names: List of symbols imported from the source
        is_relative: True if this is a relative import
        line_number: Line number of the import statement
    """

    source: str
    names: list[str]
    is_relative: bool
    line_number: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the import
        """
        return {
            "source": self.source,
            "names": self.names,
            "is_relative": self.is_relative,
            "line_number": self.line_number,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImportInfo:
        """Create ImportInfo from dictionary.

        Args:
            data: Dictionary with import data

        Returns:
            ImportInfo instance
        """
        return cls(
            source=data["source"],
            names=data["names"],
            is_relative=data["is_relative"],
            line_number=data["line_number"],
        )


@dataclass
class ParsedFile:
    """Result of parsing a source file.

    Attributes:
        path: File path
        language: Programming language (e.g., "python", "typescript")
        symbols: List of symbols defined in the file
        imports: List of import statements
        exports: List of exported symbol names
        raw_content: Original file content
        line_count: Number of lines in the file
    """

    path: str
    language: str
    symbols: list[SymbolInfo]
    imports: list[ImportInfo]
    exports: list[str]
    raw_content: str
    line_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the parsed file
        """
        return {
            "path": self.path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [i.to_dict() for i in self.imports],
            "exports": self.exports,
            "raw_content": self.raw_content,
            "line_count": self.line_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParsedFile:
        """Create ParsedFile from dictionary.

        Args:
            data: Dictionary with parsed file data

        Returns:
            ParsedFile instance
        """
        return cls(
            path=data["path"],
            language=data["language"],
            symbols=[SymbolInfo.from_dict(s) for s in data.get("symbols", [])],
            imports=[ImportInfo.from_dict(i) for i in data.get("imports", [])],
            exports=data.get("exports", []),
            raw_content=data.get("raw_content", ""),
            line_count=data.get("line_count", 0),
        )


@dataclass
class DependencyInfo:
    """Information about a dependency between files.

    Attributes:
        source_file: File that imports/depends on another
        target_file: File being depended upon
        imported_symbols: Symbols imported from target
        depth: Depth in dependency graph (0 = direct, 1+ = transitive)
    """

    source_file: str
    target_file: str
    imported_symbols: list[str]
    depth: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the dependency
        """
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "imported_symbols": self.imported_symbols,
            "depth": self.depth,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DependencyInfo:
        """Create DependencyInfo from dictionary.

        Args:
            data: Dictionary with dependency data

        Returns:
            DependencyInfo instance
        """
        return cls(
            source_file=data["source_file"],
            target_file=data["target_file"],
            imported_symbols=data.get("imported_symbols", []),
            depth=data.get("depth", 0),
        )


@dataclass
class ASTContext:
    """Cached AST analysis for a repository.

    Attributes:
        repo_path: Path to the repository root
        git_sha: Git commit SHA for this context
        files: Mapping of file paths to parsed file data
        dependency_graph: Dependency relationships (stored as dict for now)
        created_at: Timestamp when this context was created
        token_estimate: Estimated total tokens for all content
    """

    repo_path: str
    git_sha: str
    files: dict[str, ParsedFile]
    dependency_graph: dict[str, Any]  # Will be proper DependencyGraph in T05
    created_at: datetime
    token_estimate: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the AST context
        """
        return {
            "repo_path": self.repo_path,
            "git_sha": self.git_sha,
            "files": {path: file.to_dict() for path, file in self.files.items()},
            "dependency_graph": self.dependency_graph,
            "created_at": self.created_at.isoformat(),
            "token_estimate": self.token_estimate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ASTContext:
        """Create ASTContext from dictionary.

        Args:
            data: Dictionary with AST context data

        Returns:
            ASTContext instance
        """
        return cls(
            repo_path=data["repo_path"],
            git_sha=data["git_sha"],
            files={
                path: ParsedFile.from_dict(file_data)
                for path, file_data in data.get("files", {}).items()
            },
            dependency_graph=data.get("dependency_graph", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            token_estimate=data.get("token_estimate", 0),
        )


@dataclass
class FileContent:
    """File content for context pack."""
    path: str
    content: str
    language: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "content": self.content, "language": self.language}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileContent:
        return cls(path=data["path"], content=data["content"], language=data["language"])


@dataclass
class ContextPack:
    """Context pack for agent execution."""
    task_id: str
    role: str
    git_sha: str
    files: list[FileContent]
    symbols: list[SymbolInfo]
    dependencies: list[DependencyInfo]
    metadata: dict[str, Any]
    token_count: int
    relevance_scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "role": self.role, "git_sha": self.git_sha, "files": [f.to_dict() for f in self.files], "symbols": [s.to_dict() for s in self.symbols], "dependencies": [d.to_dict() for d in self.dependencies], "metadata": self.metadata, "token_count": self.token_count, "relevance_scores": self.relevance_scores}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextPack:
        return cls(task_id=data["task_id"], role=data["role"], git_sha=data["git_sha"], files=[FileContent.from_dict(f) for f in data["files"]], symbols=[SymbolInfo.from_dict(s) for s in data["symbols"]], dependencies=[DependencyInfo.from_dict(d) for d in data["dependencies"]], metadata=data["metadata"], token_count=data["token_count"], relevance_scores=data["relevance_scores"])
