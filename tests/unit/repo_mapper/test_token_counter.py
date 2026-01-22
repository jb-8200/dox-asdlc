"""Unit tests for TokenCounter."""

from __future__ import annotations

from src.workers.repo_mapper.models import (
    ParsedFile,
    SymbolInfo,
    SymbolKind,
)
from src.workers.repo_mapper.token_counter import TokenCounter


class TestTokenCounterBasic:
    """Basic tests for TokenCounter."""

    def test_create_counter(self):
        """Test creating a TokenCounter instance."""
        counter = TokenCounter()
        assert counter is not None

    def test_count_empty_string(self):
        """Test counting tokens in empty string."""
        counter = TokenCounter()
        count = counter.count_tokens("")
        assert count == 0


class TestCountTokens:
    """Tests for counting tokens in text."""

    def test_count_simple_text(self):
        """Test counting tokens in simple text."""
        counter = TokenCounter()
        text = "Hello, world!"
        count = counter.count_tokens(text)
        assert count > 0
        assert count < 10  # Should be a small number

    def test_count_code_text(self):
        """Test counting tokens in code."""
        counter = TokenCounter()
        code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""
        count = counter.count_tokens(code)
        assert count > 10
        assert count < 50

    def test_count_large_text(self):
        """Test counting tokens in large text."""
        counter = TokenCounter()
        # Approximate: 1 token ≈ 4 characters
        text = "word " * 1000  # Should be ~1000 tokens
        count = counter.count_tokens(text)
        assert 800 < count < 1500  # Allow some variance


class TestCountSymbol:
    """Tests for counting tokens in symbols."""

    def test_count_function_symbol(self):
        """Test counting tokens for a function symbol."""
        counter = TokenCounter()
        symbol = SymbolInfo(
            name="calculate_total",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            signature="def calculate_total(items: list) -> float",
            docstring="Calculate the total price of items.",
            references=[],
        )

        count = counter.count_symbol(symbol)
        assert count > 0
        assert count < 50  # Just signature + docstring

    def test_count_symbol_without_docstring(self):
        """Test counting tokens for symbol without docstring."""
        counter = TokenCounter()
        symbol = SymbolInfo(
            name="func",
            kind=SymbolKind.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=2,
            signature="def func()",
            docstring=None,
            references=[],
        )

        count = counter.count_symbol(symbol)
        assert count > 0
        assert count < 20  # Just signature


class TestCountParsedFile:
    """Tests for counting tokens in parsed files."""

    def test_count_empty_file(self):
        """Test counting tokens in empty file."""
        counter = TokenCounter()
        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        count = counter.count_parsed_file(parsed)
        assert count == 0

    def test_count_file_with_content(self):
        """Test counting tokens in file with content."""
        counter = TokenCounter()
        content = """def hello():
    print("Hello, world!")
"""
        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="hello",
                    kind=SymbolKind.FUNCTION,
                    file_path="test.py",
                    start_line=1,
                    end_line=2,
                    signature="def hello()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=["hello"],
            raw_content=content,
            line_count=2,
        )

        count = counter.count_parsed_file(parsed)
        assert count > 5
        assert count < 30


class TestCaching:
    """Tests for token count caching."""

    def test_cache_repeated_content(self):
        """Test that repeated content uses cache."""
        counter = TokenCounter()
        text = "This is a test message."

        # First call
        count1 = counter.count_tokens(text)

        # Second call should use cache
        count2 = counter.count_tokens(text)

        assert count1 == count2

    def test_cache_different_content(self):
        """Test that different content gets different counts."""
        counter = TokenCounter()
        text1 = "Short text."
        text2 = "This is a much longer piece of text with more words."

        count1 = counter.count_tokens(text1)
        count2 = counter.count_tokens(text2)

        assert count1 < count2


class TestEstimateSymbolSignature:
    """Tests for estimating token count from symbol signatures."""

    def test_estimate_simple_function(self):
        """Test estimating tokens for simple function signature."""
        counter = TokenCounter()
        estimate = counter.estimate_signature_tokens("def func()")
        assert estimate > 0
        assert estimate < 10

    def test_estimate_complex_function(self):
        """Test estimating tokens for complex function signature."""
        counter = TokenCounter()
        signature = "def process_data(items: list[dict], options: dict[str, Any]) -> tuple[list, dict]"
        estimate = counter.estimate_signature_tokens(signature)
        assert estimate > 10
        assert estimate < 50

    def test_estimate_vs_actual(self):
        """Test that estimates are reasonably close to actual counts."""
        counter = TokenCounter()
        signature = "def calculate(x: int, y: int) -> int"

        estimate = counter.estimate_signature_tokens(signature)
        actual = counter.count_tokens(signature)

        # Estimate should be within 50% of actual
        assert abs(estimate - actual) < actual * 0.5


class TestGetCacheStats:
    """Tests for cache statistics."""

    def test_cache_stats_empty(self):
        """Test cache stats when cache is empty."""
        counter = TokenCounter()
        stats = counter.get_cache_stats()

        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_cache_stats_after_use(self):
        """Test cache stats after using the counter."""
        counter = TokenCounter()

        # Make some calls
        counter.count_tokens("test1")
        counter.count_tokens("test2")
        counter.count_tokens("test1")  # Cache hit

        stats = counter.get_cache_stats()
        assert stats["size"] == 2  # Two unique texts
        assert stats["hits"] > 0
        assert stats["misses"] > 0
