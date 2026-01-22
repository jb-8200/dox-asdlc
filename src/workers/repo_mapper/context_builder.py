"""Context builder for selecting relevant content within token budgets."""

from __future__ import annotations

from src.workers.repo_mapper.dependency_graph import DependencyGraph
from src.workers.repo_mapper.models import ParsedFile
from src.workers.repo_mapper.symbol_extractor import SymbolExtractor
from src.workers.repo_mapper.token_counter import TokenCounter


class ContextBuilder:
    """Builds context packs by selecting relevant content within token budgets.

    Combines DependencyGraph, SymbolExtractor, and TokenCounter to:
    1. Extract symbols from task descriptions
    2. Find relevant files and symbols
    3. Score files by relevance
    4. Select content within token budget
    """

    def __init__(
        self,
        dependency_graph: DependencyGraph,
        symbol_extractor: SymbolExtractor,
        token_counter: TokenCounter,
    ) -> None:
        """Initialize the context builder.

        Args:
            dependency_graph: Graph of file dependencies
            symbol_extractor: Extractor for finding symbols
            token_counter: Counter for token budgets
        """
        self._dependency_graph = dependency_graph
        self._symbol_extractor = symbol_extractor
        self._token_counter = token_counter
        self._parsed_files: dict[str, ParsedFile] = {}

    @classmethod
    def with_defaults(cls) -> ContextBuilder:
        """Create a ContextBuilder with default dependencies.

        Returns:
            ContextBuilder instance with default components
        """
        return cls(
            dependency_graph=DependencyGraph(),
            symbol_extractor=SymbolExtractor(),
            token_counter=TokenCounter(),
        )

    def add_parsed_file(self, parsed_file: ParsedFile) -> None:
        """Add a parsed file to the context builder.

        Args:
            parsed_file: ParsedFile to add
        """
        self._parsed_files[parsed_file.path] = parsed_file
        self._dependency_graph.add_file(parsed_file)
        self._symbol_extractor.add_parsed_file(parsed_file)

    def select_relevant_files(
        self,
        target_files: list[str],
        task_description: str,
        token_budget: int,
        role: str = "coding",
    ) -> list[str]:
        """Select relevant files within token budget.

        Args:
            target_files: Explicitly specified target files
            task_description: Natural language task description
            token_budget: Maximum tokens for selected content
            role: Agent role for filtering (e.g., "coding", "utest")

        Returns:
            List of selected file paths
        """
        # Extract symbol names from description
        symbol_names = self._symbol_extractor.extract_symbol_names(task_description)

        # Score all files by relevance
        file_scores: list[tuple[str, float, int]] = []

        for file_path, parsed_file in self._parsed_files.items():
            score = self.score_file_relevance(
                parsed_file=parsed_file,
                target_files=target_files,
                symbol_names=symbol_names,
            )

            # Count tokens for this file
            token_count = self._token_counter.count_parsed_file(parsed_file)

            file_scores.append((file_path, score, token_count))

        # Sort by relevance (descending)
        file_scores.sort(key=lambda x: x[1], reverse=True)

        # Select files within budget
        selected_files = []
        total_tokens = 0

        for file_path, score, token_count in file_scores:
            # Always include target files if they fit
            if file_path in target_files:
                if total_tokens + token_count <= token_budget:
                    selected_files.append(file_path)
                    total_tokens += token_count
                continue

            # Include high-relevance files if they fit
            if score > 0.3 and total_tokens + token_count <= token_budget:
                selected_files.append(file_path)
                total_tokens += token_count

        return selected_files

    def score_file_relevance(
        self,
        parsed_file: ParsedFile,
        target_files: list[str],
        symbol_names: list[str],
    ) -> float:
        """Score how relevant a file is to the task.

        Scoring factors:
        - 1.0: File is in target_files
        - 0.8: File contains exact symbol match
        - 0.6: File contains partial symbol match
        - 0.4: File is a direct dependency of target
        - 0.2: File has matching exports

        Args:
            parsed_file: File to score
            target_files: Explicitly specified target files
            symbol_names: Symbol names extracted from task description

        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Target files get max score
        if parsed_file.path in target_files:
            return 1.0

        max_score = 0.0

        # Check for symbol matches
        if symbol_names:
            for symbol in parsed_file.symbols:
                symbol_score = self._symbol_extractor.score_relevance(
                    symbol, symbol_names
                )
                max_score = max(max_score, symbol_score * 0.8)

        # Check if file exports match symbol names
        for export in parsed_file.exports:
            export_lower = export.lower()
            for symbol_name in symbol_names:
                if symbol_name.lower() in export_lower:
                    max_score = max(max_score, 0.2)

        # Check if file is a dependency of target files
        for target_file in target_files:
            deps = self._dependency_graph.get_dependencies(target_file, max_depth=1)
            if any(dep.target_file == parsed_file.path for dep in deps):
                max_score = max(max_score, 0.4)

        return max_score

    def build_context(
        self,
        target_files: list[str],
        task_description: str,
        token_budget: int,
        role: str = "coding",
    ) -> dict[str, ParsedFile]:
        """Build context by selecting relevant files.

        Args:
            target_files: Explicitly specified target files
            task_description: Natural language task description
            token_budget: Maximum tokens for context
            role: Agent role for filtering

        Returns:
            Dictionary mapping file paths to ParsedFile objects
        """
        selected_paths = self.select_relevant_files(
            target_files=target_files,
            task_description=task_description,
            token_budget=token_budget,
            role=role,
        )

        context = {}
        for file_path in selected_paths:
            if file_path in self._parsed_files:
                context[file_path] = self._parsed_files[file_path]

        return context

    def get_relevance_scores(
        self,
        target_files: list[str],
        task_description: str,
    ) -> dict[str, float]:
        """Get relevance scores for all files.

        Args:
            target_files: Explicitly specified target files
            task_description: Natural language task description

        Returns:
            Dictionary mapping file paths to relevance scores
        """
        symbol_names = self._symbol_extractor.extract_symbol_names(task_description)

        scores = {}
        for file_path, parsed_file in self._parsed_files.items():
            score = self.score_file_relevance(
                parsed_file=parsed_file,
                target_files=target_files,
                symbol_names=symbol_names,
            )
            scores[file_path] = score

        return scores
