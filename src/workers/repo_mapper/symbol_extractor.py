"""Symbol extraction from task descriptions."""

from __future__ import annotations

import re

from src.workers.repo_mapper.models import ParsedFile, SymbolInfo


class SymbolExtractor:
    """Extracts and matches symbols from task descriptions against repository.

    Uses regex and heuristics to identify function names, class names, and other
    symbols mentioned in natural language task descriptions.
    """

    # Common English words that should not be treated as symbols
    COMMON_WORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "should",
        "could",
        "may",
        "might",
        "must",
        "can",
        "shall",
        "return",
        "if",
        "else",
        "then",
        "when",
        "where",
        "which",
        "who",
        "what",
        "why",
        "how",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "not",
        "function",
        "class",
        "method",
        "variable",
        "file",
        "code",
        "bug",
        "fix",
        "update",
        "add",
        "remove",
        "delete",
        "refactor",
    }

    def __init__(self) -> None:
        """Initialize the symbol extractor."""
        self._parsed_files: dict[str, ParsedFile] = {}
        self._all_symbols: list[SymbolInfo] = []

    def add_parsed_file(self, parsed_file: ParsedFile) -> None:
        """Add a parsed file to the symbol index.

        Args:
            parsed_file: ParsedFile to add to the index
        """
        self._parsed_files[parsed_file.path] = parsed_file
        self._all_symbols.extend(parsed_file.symbols)

    def extract_symbol_names(self, description: str) -> list[str]:
        """Extract potential symbol names from task description.

        Uses regex patterns to identify:
        - snake_case identifiers
        - camelCase identifiers
        - PascalCase identifiers
        - Function calls (identifier followed by parentheses)

        Args:
            description: Natural language task description

        Returns:
            List of extracted symbol names
        """
        if not description:
            return []

        symbols = set()

        # Pattern for function calls: identifier()
        function_pattern = r"\b([a-z_][a-z0-9_]*)\(\)"
        for match in re.finditer(function_pattern, description, re.IGNORECASE):
            symbol = match.group(1)
            if symbol.lower() not in self.COMMON_WORDS:
                symbols.add(symbol)

        # Pattern for snake_case identifiers (at least one underscore)
        snake_case_pattern = r"\b([a-z][a-z0-9]*_[a-z0-9_]+)\b"
        for match in re.finditer(snake_case_pattern, description):
            symbol = match.group(1)
            if symbol.lower() not in self.COMMON_WORDS:
                symbols.add(symbol)

        # Pattern for camelCase identifiers (starts lowercase)
        camel_case_pattern = r"\b([a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*)\b"
        for match in re.finditer(camel_case_pattern, description):
            symbol = match.group(1)
            if symbol.lower() not in self.COMMON_WORDS:
                symbols.add(symbol)

        # Pattern for PascalCase identifiers (starts uppercase)
        pascal_case_pattern = r"\b([A-Z][a-z0-9]*[A-Z][a-zA-Z0-9]*)\b"
        for match in re.finditer(pascal_case_pattern, description):
            symbol = match.group(1)
            if symbol.lower() not in self.COMMON_WORDS:
                symbols.add(symbol)

        # Pattern for simple PascalCase (like "User", "Order")
        simple_pascal_pattern = r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b"
        for match in re.finditer(simple_pascal_pattern, description):
            symbol = match.group(1)
            if symbol.lower() not in self.COMMON_WORDS and len(symbol) > 2:
                symbols.add(symbol)

        return list(symbols)

    def match_symbols(self, symbol_names: list[str]) -> list[SymbolInfo]:
        """Match extracted symbol names against repository symbols.

        Finds exact matches and partial matches (substring matching).

        Args:
            symbol_names: List of symbol names to match

        Returns:
            List of matching SymbolInfo objects
        """
        matches = []
        symbol_names_lower = [s.lower() for s in symbol_names]

        for symbol in self._all_symbols:
            symbol_name_lower = symbol.name.lower()

            # Exact match
            if symbol_name_lower in symbol_names_lower:
                matches.append(symbol)
                continue

            # Partial match: symbol name contains any of the search terms
            for search_term in symbol_names_lower:
                if search_term in symbol_name_lower or symbol_name_lower in search_term:
                    matches.append(symbol)
                    break

        return matches

    def score_relevance(self, symbol: SymbolInfo, symbol_names: list[str]) -> float:
        """Score how relevant a symbol is to the search terms.

        Scoring:
        - 1.0: Exact match
        - 0.7: Symbol name contains search term
        - 0.5: Search term contains symbol name
        - 0.1: Same file as matched symbol
        - 0.0: No match

        Args:
            symbol: Symbol to score
            symbol_names: List of search terms

        Returns:
            Relevance score between 0.0 and 1.0
        """
        symbol_name_lower = symbol.name.lower()
        symbol_names_lower = [s.lower() for s in symbol_names]

        # Exact match
        if symbol_name_lower in symbol_names_lower:
            return 1.0

        # Symbol name contains search term
        for search_term in symbol_names_lower:
            if search_term in symbol_name_lower:
                # Longer match = higher score
                score = 0.7 * (len(search_term) / len(symbol_name_lower))
                return min(score, 0.9)

        # Search term contains symbol name (shorter symbol in longer term)
        for search_term in symbol_names_lower:
            if symbol_name_lower in search_term:
                return 0.5

        # No direct match
        return 0.0

    def find_related_symbols(self, symbol: SymbolInfo) -> list[SymbolInfo]:
        """Find symbols related to the given symbol.

        Related symbols include:
        - Methods of the same class (if symbol is a class)
        - Other symbols in the same file
        - Symbols that reference this symbol

        Args:
            symbol: Symbol to find relations for

        Returns:
            List of related SymbolInfo objects
        """
        related = []

        # Get the parsed file containing this symbol
        parsed_file = self._parsed_files.get(symbol.file_path)
        if not parsed_file:
            return related

        # If this is a class, find its methods
        if symbol.kind.value == "class":
            for other_symbol in parsed_file.symbols:
                if other_symbol.kind.value == "method":
                    # Methods are typically defined within class line range
                    if (
                        other_symbol.start_line >= symbol.start_line
                        and other_symbol.end_line <= symbol.end_line
                    ):
                        related.append(other_symbol)

        # Add other symbols from the same file
        for other_symbol in parsed_file.symbols:
            if other_symbol.name != symbol.name:
                related.append(other_symbol)

        # Find symbols that reference this one
        for other_symbol in self._all_symbols:
            if symbol.file_path in other_symbol.references:
                related.append(other_symbol)

        return related
