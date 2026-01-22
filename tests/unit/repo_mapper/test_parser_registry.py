"""Unit tests for Parser Registry."""

from __future__ import annotations

from pathlib import Path

from src.workers.repo_mapper.parsers import (
    ParserRegistry,
    get_parser_for_file,
)
from src.workers.repo_mapper.parsers.python_parser import PythonParser


class TestParserRegistry:
    """Tests for ParserRegistry."""

    def test_create_registry(self):
        """Test creating a ParserRegistry instance."""
        registry = ParserRegistry()
        assert registry is not None

    def test_register_parser(self):
        """Test registering a parser."""
        registry = ParserRegistry()
        parser = PythonParser()

        registry.register_parser(".py", parser)

        # Should be able to get it back
        retrieved = registry.get_parser(".py")
        assert retrieved is parser

    def test_register_multiple_extensions(self):
        """Test registering a parser for multiple extensions."""
        registry = ParserRegistry()
        parser = PythonParser()

        registry.register_parser(".py", parser)
        registry.register_parser(".pyi", parser)

        assert registry.get_parser(".py") is parser
        assert registry.get_parser(".pyi") is parser

    def test_get_unknown_extension_returns_none(self):
        """Test that unknown extension returns None."""
        registry = ParserRegistry()

        parser = registry.get_parser(".unknown")
        assert parser is None

    def test_get_parser_for_file(self):
        """Test getting parser for a file path."""
        registry = ParserRegistry()
        python_parser = PythonParser()
        registry.register_parser(".py", python_parser)

        parser = registry.get_parser_for_file("test.py")
        assert parser is python_parser

    def test_get_parser_for_file_with_path_object(self):
        """Test getting parser for a Path object."""
        registry = ParserRegistry()
        python_parser = PythonParser()
        registry.register_parser(".py", python_parser)

        parser = registry.get_parser_for_file(Path("test.py"))
        assert parser is python_parser

    def test_get_parser_for_file_unknown_extension(self):
        """Test that unknown file extension returns None."""
        registry = ParserRegistry()

        parser = registry.get_parser_for_file("test.unknown")
        assert parser is None

    def test_list_supported_extensions(self):
        """Test listing all supported extensions."""
        registry = ParserRegistry()
        python_parser = PythonParser()

        registry.register_parser(".py", python_parser)
        registry.register_parser(".pyi", python_parser)

        extensions = registry.list_supported_extensions()
        assert ".py" in extensions
        assert ".pyi" in extensions


class TestDefaultParserRegistry:
    """Tests for default parser registry with pre-registered parsers."""

    def test_default_registry_has_python(self):
        """Test that default registry includes Python parser."""
        registry = ParserRegistry.default()

        parser = registry.get_parser(".py")
        assert parser is not None
        assert isinstance(parser, PythonParser)

    def test_default_registry_singleton(self):
        """Test that default registry returns the same instance."""
        registry1 = ParserRegistry.default()
        registry2 = ParserRegistry.default()

        assert registry1 is registry2


class TestGetParserForFile:
    """Tests for module-level get_parser_for_file function."""

    def test_get_parser_for_python_file(self):
        """Test getting parser for Python file."""
        parser = get_parser_for_file("test.py")
        assert parser is not None
        assert isinstance(parser, PythonParser)

    def test_get_parser_for_unknown_file(self):
        """Test getting parser for unknown file type."""
        parser = get_parser_for_file("test.unknown")
        assert parser is None
