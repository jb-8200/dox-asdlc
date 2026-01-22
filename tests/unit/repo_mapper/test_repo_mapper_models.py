"""Unit tests for Repo Mapper data models."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from src.workers.repo_mapper.models import (
    ASTContext,
    DependencyInfo,
    ImportInfo,
    ParsedFile,
    SymbolInfo,
    SymbolKind,
)


class TestSymbolKind:
    """Tests for SymbolKind enum."""

    def test_symbol_kinds_exist(self):
        """Test that all expected symbol kinds are defined."""
        assert SymbolKind.FUNCTION
        assert SymbolKind.CLASS
        assert SymbolKind.INTERFACE
        assert SymbolKind.VARIABLE
        assert SymbolKind.METHOD
        assert SymbolKind.CONSTANT

    def test_symbol_kind_values(self):
        """Test symbol kind string values."""
        assert SymbolKind.FUNCTION.value == "function"
        assert SymbolKind.CLASS.value == "class"
        assert SymbolKind.INTERFACE.value == "interface"


class TestSymbolInfo:
    """Tests for SymbolInfo dataclass."""

    def test_create_symbol_info(self):
        """Test creating a SymbolInfo instance."""
        symbol = SymbolInfo(
            name="my_function",
            kind=SymbolKind.FUNCTION,
            file_path="src/module.py",
            start_line=10,
            end_line=20,
            signature="def my_function(x: int) -> str",
            docstring="My function docstring",
            references=["src/caller.py"],
        )

        assert symbol.name == "my_function"
        assert symbol.kind == SymbolKind.FUNCTION
        assert symbol.file_path == "src/module.py"
        assert symbol.start_line == 10
        assert symbol.end_line == 20
        assert symbol.signature == "def my_function(x: int) -> str"
        assert symbol.docstring == "My function docstring"
        assert symbol.references == ["src/caller.py"]

    def test_symbol_info_optional_fields(self):
        """Test SymbolInfo with None for optional fields."""
        symbol = SymbolInfo(
            name="MyClass",
            kind=SymbolKind.CLASS,
            file_path="src/module.py",
            start_line=1,
            end_line=10,
            signature=None,
            docstring=None,
            references=[],
        )

        assert symbol.signature is None
        assert symbol.docstring is None
        assert symbol.references == []

    def test_symbol_info_to_dict(self):
        """Test converting SymbolInfo to dict for JSON serialization."""
        symbol = SymbolInfo(
            name="test",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def test()",
            docstring="Test function",
            references=[],
        )

        data = symbol.to_dict()
        assert data["name"] == "test"
        assert data["kind"] == "function"
        assert data["file_path"] == "test.py"
        assert data["start_line"] == 1

    def test_symbol_info_from_dict(self):
        """Test creating SymbolInfo from dict."""
        data = {
            "name": "test",
            "kind": "function",
            "file_path": "test.py",
            "start_line": 1,
            "end_line": 5,
            "signature": "def test()",
            "docstring": "Test",
            "references": [],
        }

        symbol = SymbolInfo.from_dict(data)
        assert symbol.name == "test"
        assert symbol.kind == SymbolKind.FUNCTION


class TestImportInfo:
    """Tests for ImportInfo dataclass."""

    def test_create_import_info(self):
        """Test creating an ImportInfo instance."""
        import_info = ImportInfo(
            source="os.path",
            names=["join", "exists"],
            is_relative=False,
            line_number=5,
        )

        assert import_info.source == "os.path"
        assert import_info.names == ["join", "exists"]
        assert import_info.is_relative is False
        assert import_info.line_number == 5

    def test_relative_import(self):
        """Test ImportInfo for relative import."""
        import_info = ImportInfo(
            source=".models", names=["User"], is_relative=True, line_number=10
        )

        assert import_info.is_relative is True

    def test_import_info_to_dict(self):
        """Test converting ImportInfo to dict."""
        import_info = ImportInfo(
            source="typing", names=["List"], is_relative=False, line_number=1
        )

        data = import_info.to_dict()
        assert data["source"] == "typing"
        assert data["names"] == ["List"]
        assert data["is_relative"] is False


class TestParsedFile:
    """Tests for ParsedFile dataclass."""

    def test_create_parsed_file(self):
        """Test creating a ParsedFile instance."""
        symbols = [
            SymbolInfo(
                name="test",
                kind=SymbolKind.FUNCTION,
                file_path="test.py",
                start_line=1,
                end_line=5,
                signature=None,
                docstring=None,
                references=[],
            )
        ]
        imports = [
            ImportInfo(source="os", names=["path"], is_relative=False, line_number=1)
        ]

        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=symbols,
            imports=imports,
            exports=["test"],
            raw_content="def test():\n    pass",
            line_count=2,
        )

        assert parsed.path == "test.py"
        assert parsed.language == "python"
        assert len(parsed.symbols) == 1
        assert len(parsed.imports) == 1
        assert parsed.exports == ["test"]
        assert parsed.line_count == 2

    def test_parsed_file_to_dict(self):
        """Test converting ParsedFile to dict."""
        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        data = parsed.to_dict()
        assert data["path"] == "test.py"
        assert data["language"] == "python"
        assert data["symbols"] == []


class TestDependencyInfo:
    """Tests for DependencyInfo dataclass."""

    def test_create_dependency_info(self):
        """Test creating a DependencyInfo instance."""
        dep = DependencyInfo(
            source_file="src/module.py",
            target_file="src/dependency.py",
            imported_symbols=["MyClass", "helper"],
            depth=1,
        )

        assert dep.source_file == "src/module.py"
        assert dep.target_file == "src/dependency.py"
        assert dep.imported_symbols == ["MyClass", "helper"]
        assert dep.depth == 1

    def test_dependency_info_to_dict(self):
        """Test converting DependencyInfo to dict."""
        dep = DependencyInfo(
            source_file="a.py",
            target_file="b.py",
            imported_symbols=["x"],
            depth=2,
        )

        data = dep.to_dict()
        assert data["source_file"] == "a.py"
        assert data["depth"] == 2


class TestASTContext:
    """Tests for ASTContext dataclass."""

    def test_create_ast_context(self):
        """Test creating an ASTContext instance."""
        now = datetime.now(UTC)
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        context = ASTContext(
            repo_path="/path/to/repo",
            git_sha="abc123",
            files={"test.py": parsed_file},
            dependency_graph={},
            created_at=now,
            token_estimate=1000,
        )

        assert context.repo_path == "/path/to/repo"
        assert context.git_sha == "abc123"
        assert "test.py" in context.files
        assert context.created_at == now
        assert context.token_estimate == 1000

    def test_ast_context_to_dict(self):
        """Test converting ASTContext to dict."""
        now = datetime.now(UTC)
        context = ASTContext(
            repo_path="/repo",
            git_sha="abc",
            files={},
            dependency_graph={},
            created_at=now,
            token_estimate=500,
        )

        data = context.to_dict()
        assert data["repo_path"] == "/repo"
        assert data["git_sha"] == "abc"
        assert data["token_estimate"] == 500

    def test_ast_context_serialization(self):
        """Test full JSON serialization of ASTContext."""
        now = datetime.now(UTC)
        context = ASTContext(
            repo_path="/repo",
            git_sha="abc",
            files={},
            dependency_graph={},
            created_at=now,
            token_estimate=100,
        )

        # Should be JSON serializable
        json_str = json.dumps(context.to_dict())
        assert json_str
        assert "abc" in json_str
