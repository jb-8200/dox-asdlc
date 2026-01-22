"""Unit tests for Python AST Parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.workers.repo_mapper.models import SymbolKind
from src.workers.repo_mapper.parsers.python_parser import PythonParser


class TestPythonParserBasic:
    """Basic tests for PythonParser."""

    def test_create_parser(self):
        """Test creating a PythonParser instance."""
        parser = PythonParser()
        assert parser is not None

    def test_supported_extensions(self):
        """Test that PythonParser supports .py files."""
        parser = PythonParser()
        extensions = parser.get_supported_extensions()
        assert ".py" in extensions


class TestPythonParserFunctions:
    """Tests for parsing Python functions."""

    def test_parse_simple_function(self, tmp_path: Path):
        """Test parsing a simple function."""
        content = '''def hello():
    """Say hello."""
    return "Hello"
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert parsed.path == str(file_path)
        assert parsed.language == "python"
        assert len(parsed.symbols) == 1

        func = parsed.symbols[0]
        assert func.name == "hello"
        assert func.kind == SymbolKind.FUNCTION
        assert func.start_line == 1
        assert func.docstring == "Say hello."

    def test_parse_function_with_args(self, tmp_path: Path):
        """Test parsing a function with arguments and type hints."""
        content = '''def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        func = parsed.symbols[0]
        assert func.name == "add"
        assert "x: int" in func.signature
        assert "y: int" in func.signature
        assert "-> int" in func.signature

    def test_parse_multiple_functions(self, tmp_path: Path):
        """Test parsing multiple functions in one file."""
        content = '''def first():
    pass

def second():
    pass

def third():
    pass
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert len(parsed.symbols) == 3
        assert {s.name for s in parsed.symbols} == {"first", "second", "third"}


class TestPythonParserClasses:
    """Tests for parsing Python classes."""

    def test_parse_simple_class(self, tmp_path: Path):
        """Test parsing a simple class."""
        content = '''class Person:
    """A person class."""
    pass
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert len(parsed.symbols) >= 1
        cls = next(s for s in parsed.symbols if s.kind == SymbolKind.CLASS)
        assert cls.name == "Person"
        assert cls.docstring == "A person class."

    def test_parse_class_with_methods(self, tmp_path: Path):
        """Test parsing a class with methods."""
        content = '''class Calculator:
    """A calculator class."""

    def add(self, x, y):
        """Add two numbers."""
        return x + y

    def subtract(self, x, y):
        """Subtract two numbers."""
        return x - y
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        # Should have class + methods
        assert len(parsed.symbols) >= 3
        methods = [s for s in parsed.symbols if s.kind == SymbolKind.METHOD]
        assert len(methods) == 2
        assert {m.name for m in methods} == {"add", "subtract"}

    def test_parse_class_with_base(self, tmp_path: Path):
        """Test parsing a class with a base class."""
        content = '''class Child(Parent):
    """A child class."""
    pass
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        cls = next(s for s in parsed.symbols if s.kind == SymbolKind.CLASS)
        assert cls.name == "Child"
        # Signature should mention base class
        assert "Parent" in (cls.signature or "")


class TestPythonParserImports:
    """Tests for parsing import statements."""

    def test_parse_absolute_import(self, tmp_path: Path):
        """Test parsing absolute imports."""
        content = '''import os
import sys
from pathlib import Path
from typing import List, Dict
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert len(parsed.imports) == 4

        # Check specific imports
        os_import = next(i for i in parsed.imports if i.source == "os")
        assert not os_import.is_relative

        path_import = next(i for i in parsed.imports if i.source == "pathlib")
        assert "Path" in path_import.names

    def test_parse_relative_import(self, tmp_path: Path):
        """Test parsing relative imports."""
        content = '''from .models import User
from ..utils import helper
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert len(parsed.imports) == 2

        for imp in parsed.imports:
            assert imp.is_relative

        models_import = next(i for i in parsed.imports if "models" in i.source)
        assert "User" in models_import.names


class TestPythonParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_empty_file(self, tmp_path: Path):
        """Test parsing an empty file."""
        file_path = tmp_path / "empty.py"
        file_path.write_text("")

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert parsed.path == str(file_path)
        assert parsed.language == "python"
        assert parsed.symbols == []
        assert parsed.imports == []

    def test_parse_syntax_error_file(self, tmp_path: Path):
        """Test parsing a file with syntax errors."""
        content = '''def broken(
    # Missing closing paren
    return "oops"
'''
        file_path = tmp_path / "broken.py"
        file_path.write_text(content)

        parser = PythonParser()

        # Should handle syntax errors gracefully
        with pytest.raises(SyntaxError):
            parser.parse_file(str(file_path))

    def test_parse_file_with_comments(self, tmp_path: Path):
        """Test that comments are ignored."""
        content = '''# This is a comment
def test():
    # Another comment
    pass
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        # Should only find the function, not comments
        assert len(parsed.symbols) == 1

    def test_line_count(self, tmp_path: Path):
        """Test that line count is correct."""
        content = '''# line 1
# line 2
# line 3
# line 4
# line 5
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        assert parsed.line_count == 5  # 5 lines

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        parser = PythonParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.py")


class TestPythonParserTypeHints:
    """Tests for extracting type hints."""

    def test_extract_parameter_types(self, tmp_path: Path):
        """Test extracting parameter type hints."""
        content = '''def process(data: list[str], count: int = 10) -> dict[str, int]:
    """Process data."""
    return {}
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        func = parsed.symbols[0]
        assert "list[str]" in func.signature or "List[str]" in func.signature
        assert "int" in func.signature

    def test_extract_return_type(self, tmp_path: Path):
        """Test extracting return type hints."""
        content = '''def get_data() -> tuple[str, int]:
    """Get data."""
    return ("hello", 42)
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(content)

        parser = PythonParser()
        parsed = parser.parse_file(str(file_path))

        func = parsed.symbols[0]
        assert "tuple" in func.signature or "Tuple" in func.signature
