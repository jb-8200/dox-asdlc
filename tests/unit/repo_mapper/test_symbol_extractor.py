"""Unit tests for SymbolExtractor."""

from __future__ import annotations

from src.workers.repo_mapper.models import (
    ParsedFile,
    SymbolInfo,
    SymbolKind,
)
from src.workers.repo_mapper.symbol_extractor import SymbolExtractor


class TestSymbolExtractorBasic:
    """Basic tests for SymbolExtractor."""

    def test_create_extractor(self):
        """Test creating a SymbolExtractor instance."""
        extractor = SymbolExtractor()
        assert extractor is not None

    def test_extract_from_empty_description(self):
        """Test extracting symbols from empty description."""
        extractor = SymbolExtractor()
        symbols = extractor.extract_symbol_names("")
        assert symbols == []


class TestExtractSymbolNames:
    """Tests for extracting symbol names from task descriptions."""

    def test_extract_function_name(self):
        """Test extracting function names from description."""
        extractor = SymbolExtractor()
        description = "Fix the calculate_total() function"

        symbols = extractor.extract_symbol_names(description)
        assert "calculate_total" in symbols

    def test_extract_class_name(self):
        """Test extracting class names from description."""
        extractor = SymbolExtractor()
        description = "Update the UserService class to handle errors"

        symbols = extractor.extract_symbol_names(description)
        assert "UserService" in symbols

    def test_extract_multiple_symbols(self):
        """Test extracting multiple symbol names."""
        extractor = SymbolExtractor()
        description = "Refactor calculate_tax() and apply_discount() in OrderProcessor"

        symbols = extractor.extract_symbol_names(description)
        assert "calculate_tax" in symbols
        assert "apply_discount" in symbols
        assert "OrderProcessor" in symbols

    def test_extract_camel_case_symbols(self):
        """Test extracting CamelCase symbols."""
        extractor = SymbolExtractor()
        description = "Fix bug in calculateTotal and applyDiscount methods"

        symbols = extractor.extract_symbol_names(description)
        assert "calculateTotal" in symbols
        assert "applyDiscount" in symbols

    def test_extract_snake_case_symbols(self):
        """Test extracting snake_case symbols."""
        extractor = SymbolExtractor()
        description = "Update process_payment and validate_card functions"

        symbols = extractor.extract_symbol_names(description)
        assert "process_payment" in symbols
        assert "validate_card" in symbols

    def test_ignore_common_words(self):
        """Test that common English words are not extracted as symbols."""
        extractor = SymbolExtractor()
        description = "The function should return the result"

        symbols = extractor.extract_symbol_names(description)
        # Common words should not be extracted
        assert "the" not in symbols
        assert "should" not in symbols
        assert "return" not in symbols


class TestMatchSymbols:
    """Tests for matching extracted symbols against repository."""

    def test_match_symbols_exact_match(self):
        """Test matching symbols with exact name match."""
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="calculate_total",
                    kind=SymbolKind.FUNCTION,
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    signature="def calculate_total()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=["calculate_total"],
            raw_content="",
            line_count=5,
        )

        extractor = SymbolExtractor()
        extractor.add_parsed_file(parsed_file)

        matches = extractor.match_symbols(["calculate_total"])
        assert len(matches) == 1
        assert matches[0].name == "calculate_total"

    def test_match_symbols_partial_match(self):
        """Test matching symbols with partial name match."""
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="calculate_total_with_tax",
                    kind=SymbolKind.FUNCTION,
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    signature="def calculate_total_with_tax()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=[],
            raw_content="",
            line_count=5,
        )

        extractor = SymbolExtractor()
        extractor.add_parsed_file(parsed_file)

        # Should find partial matches
        matches = extractor.match_symbols(["calculate_total"])
        assert len(matches) >= 1

    def test_match_symbols_no_match(self):
        """Test matching symbols with no matches."""
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="other_function",
                    kind=SymbolKind.FUNCTION,
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    signature="def other_function()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=[],
            raw_content="",
            line_count=5,
        )

        extractor = SymbolExtractor()
        extractor.add_parsed_file(parsed_file)

        matches = extractor.match_symbols(["nonexistent"])
        assert len(matches) == 0


class TestScoreRelevance:
    """Tests for scoring symbol relevance."""

    def test_score_exact_match(self):
        """Test that exact matches get high scores."""
        symbol = SymbolInfo(
            name="calculate_total",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def calculate_total()",
            docstring=None,
            references=[],
        )

        extractor = SymbolExtractor()
        score = extractor.score_relevance(symbol, ["calculate_total"])

        assert score > 0.9  # Very high score for exact match

    def test_score_partial_match(self):
        """Test that partial matches get medium scores."""
        symbol = SymbolInfo(
            name="calculate_total_with_tax",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def calculate_total_with_tax()",
            docstring=None,
            references=[],
        )

        extractor = SymbolExtractor()
        score = extractor.score_relevance(symbol, ["calculate_total"])

        assert 0.3 < score < 0.9  # Medium score for partial match

    def test_score_no_match(self):
        """Test that non-matches get low scores."""
        symbol = SymbolInfo(
            name="other_function",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def other_function()",
            docstring=None,
            references=[],
        )

        extractor = SymbolExtractor()
        score = extractor.score_relevance(symbol, ["calculate_total"])

        assert score < 0.3  # Low score for no match


class TestFindRelatedSymbols:
    """Tests for finding related symbols."""

    def test_find_class_methods(self):
        """Test finding methods of a class."""
        class_symbol = SymbolInfo(
            name="Calculator",
            kind=SymbolKind.CLASS,
            file_path="test.py",
            start_line=1,
            end_line=20,
            signature="class Calculator",
            docstring=None,
            references=[],
        )

        method_symbol = SymbolInfo(
            name="add",
            kind=SymbolKind.METHOD,
            file_path="test.py",
            start_line=5,
            end_line=7,
            signature="def add(self, x, y)",
            docstring=None,
            references=[],
        )

        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[class_symbol, method_symbol],
            imports=[],
            exports=[],
            raw_content="",
            line_count=20,
        )

        extractor = SymbolExtractor()
        extractor.add_parsed_file(parsed_file)

        # Find methods related to Calculator class
        related = extractor.find_related_symbols(class_symbol)
        assert len(related) >= 1  # Should find the method

    def test_find_symbols_in_same_file(self):
        """Test finding symbols in the same file."""
        symbol1 = SymbolInfo(
            name="func1",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def func1()",
            docstring=None,
            references=[],
        )

        symbol2 = SymbolInfo(
            name="func2",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=7,
            end_line=10,
            signature="def func2()",
            docstring=None,
            references=[],
        )

        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            symbols=[symbol1, symbol2],
            imports=[],
            exports=[],
            raw_content="",
            line_count=10,
        )

        extractor = SymbolExtractor()
        extractor.add_parsed_file(parsed_file)

        related = extractor.find_related_symbols(symbol1)
        # Should include other symbols from same file
        assert any(s.name == "func2" for s in related)
