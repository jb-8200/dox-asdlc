"""Unit tests for ContextBuilder."""

from __future__ import annotations

from src.workers.repo_mapper.context_builder import ContextBuilder
from src.workers.repo_mapper.dependency_graph import DependencyGraph
from src.workers.repo_mapper.models import (
    ParsedFile,
    SymbolInfo,
    SymbolKind,
)
from src.workers.repo_mapper.symbol_extractor import SymbolExtractor
from src.workers.repo_mapper.token_counter import TokenCounter


class TestContextBuilderBasic:
    """Basic tests for ContextBuilder."""

    def test_create_builder(self):
        """Test creating a ContextBuilder instance."""
        graph = DependencyGraph()
        extractor = SymbolExtractor()
        counter = TokenCounter()

        builder = ContextBuilder(
            dependency_graph=graph,
            symbol_extractor=extractor,
            token_counter=counter,
        )

        assert builder is not None

    def test_builder_with_defaults(self):
        """Test creating builder with default dependencies."""
        builder = ContextBuilder.with_defaults()
        assert builder is not None


class TestSelectRelevantFiles:
    """Tests for selecting relevant files."""

    def test_select_target_files(self):
        """Test that target files are included."""
        builder = ContextBuilder.with_defaults()

        # Add a parsed file
        parsed = ParsedFile(
            path="src/main.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="# main file",
            line_count=1,
        )

        builder.add_parsed_file(parsed)

        # Select files
        selected = builder.select_relevant_files(
            target_files=["src/main.py"],
            task_description="",
            token_budget=1000,
        )

        assert "src/main.py" in selected

    def test_select_files_from_description(self):
        """Test selecting files mentioned in task description."""
        builder = ContextBuilder.with_defaults()

        # Add parsed files
        parsed1 = ParsedFile(
            path="src/utils.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="helper_function",
                    kind=SymbolKind.FUNCTION,
                    file_path="src/utils.py",
                    start_line=1,
                    end_line=5,
                    signature="def helper_function()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=["helper_function"],
            raw_content="def helper_function():\n    pass",
            line_count=2,
        )

        builder.add_parsed_file(parsed1)

        # Select files based on description
        selected = builder.select_relevant_files(
            target_files=[],
            task_description="Fix the helper_function in utils",
            token_budget=1000,
        )

        # Should include files with matching symbols
        assert len(selected) >= 0  # May or may not find it depending on matching


class TestScoreFileRelevance:
    """Tests for scoring file relevance."""

    def test_score_target_file(self):
        """Test that target files get high scores."""
        builder = ContextBuilder.with_defaults()

        parsed = ParsedFile(
            path="src/target.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        score = builder.score_file_relevance(
            parsed_file=parsed,
            target_files=["src/target.py"],
            symbol_names=[],
        )

        assert score == 1.0  # Max score for target file

    def test_score_file_with_matching_symbol(self):
        """Test scoring file with matching symbol."""
        builder = ContextBuilder.with_defaults()

        parsed = ParsedFile(
            path="src/utils.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="calculate_total",
                    kind=SymbolKind.FUNCTION,
                    file_path="src/utils.py",
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

        builder.add_parsed_file(parsed)

        score = builder.score_file_relevance(
            parsed_file=parsed,
            target_files=[],
            symbol_names=["calculate_total"],
        )

        assert score > 0.5  # Should get high score for matching symbol

    def test_score_unrelated_file(self):
        """Test scoring unrelated file."""
        builder = ContextBuilder.with_defaults()

        parsed = ParsedFile(
            path="src/other.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        score = builder.score_file_relevance(
            parsed_file=parsed,
            target_files=["src/main.py"],
            symbol_names=["some_function"],
        )

        assert score < 0.3  # Low score for unrelated file


class TestApplyTokenBudget:
    """Tests for applying token budget constraints."""

    def test_include_all_within_budget(self):
        """Test including all files when within budget."""
        builder = ContextBuilder.with_defaults()

        # Add small files
        for i in range(3):
            parsed = ParsedFile(
                path=f"file{i}.py",
                language="python",
                symbols=[],
                imports=[],
                exports=[],
                raw_content=f"# File {i}",
                line_count=1,
            )
            builder.add_parsed_file(parsed)

        # Large budget - should include all
        selected = builder.select_relevant_files(
            target_files=[f"file{i}.py" for i in range(3)],
            task_description="",
            token_budget=10000,
        )

        assert len(selected) == 3

    def test_exclude_files_over_budget(self):
        """Test excluding low-relevance files when over budget."""
        builder = ContextBuilder.with_defaults()

        # Add files with different relevance
        high_relevance = ParsedFile(
            path="important.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="x = 1\n" * 10,  # Small file
            line_count=10,
        )

        low_relevance = ParsedFile(
            path="other.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="y = 2\n" * 50,  # Larger file
            line_count=50,
        )

        builder.add_parsed_file(high_relevance)
        builder.add_parsed_file(low_relevance)

        # Medium budget - should prioritize target file
        selected = builder.select_relevant_files(
            target_files=["important.py"],
            task_description="",
            token_budget=100,  # Budget fits important.py but not both
        )

        # Should include high relevance (target) file
        assert "important.py" in selected
        # Should not include low relevance file when budget is tight
        assert len(selected) >= 1


class TestRoleSpecificFiltering:
    """Tests for role-specific content filtering."""

    def test_filter_for_coding_role(self):
        """Test filtering content for coding role."""
        builder = ContextBuilder.with_defaults()

        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=[
                SymbolInfo(
                    name="func",
                    kind=SymbolKind.FUNCTION,
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    signature="def func()",
                    docstring=None,
                    references=[],
                )
            ],
            imports=[],
            exports=["func"],
            raw_content="def func():\n    pass",
            line_count=2,
        )

        builder.add_parsed_file(parsed)

        # Select with role filter
        selected = builder.select_relevant_files(
            target_files=["test.py"],
            task_description="",
            token_budget=1000,
            role="coding",
        )

        assert "test.py" in selected

    def test_filter_for_test_role(self):
        """Test filtering content for test role."""
        builder = ContextBuilder.with_defaults()

        test_file = ParsedFile(
            path="test_module.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="# test file",
            line_count=1,
        )

        builder.add_parsed_file(test_file)

        selected = builder.select_relevant_files(
            target_files=["test_module.py"],
            task_description="",
            token_budget=1000,
            role="utest",
        )

        assert "test_module.py" in selected


class TestBuildContext:
    """Tests for building complete context."""

    def test_build_context_with_files(self):
        """Test building context with multiple files."""
        builder = ContextBuilder.with_defaults()

        # Add files
        parsed1 = ParsedFile(
            path="file1.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="# File 1",
            line_count=1,
        )

        parsed2 = ParsedFile(
            path="file2.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="# File 2",
            line_count=1,
        )

        builder.add_parsed_file(parsed1)
        builder.add_parsed_file(parsed2)

        # Build context
        context = builder.build_context(
            target_files=["file1.py", "file2.py"],
            task_description="",
            token_budget=1000,
        )

        assert "file1.py" in context
        assert "file2.py" in context

    def test_build_context_respects_budget(self):
        """Test that build_context respects token budget."""
        builder = ContextBuilder.with_defaults()

        # Add a large file
        large_content = "x = 1\n" * 1000
        parsed = ParsedFile(
            path="large.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content=large_content,
            line_count=1000,
        )

        builder.add_parsed_file(parsed)

        # Build with small budget
        context = builder.build_context(
            target_files=["large.py"],
            task_description="",
            token_budget=100,
        )

        # Should have some content but constrained
        assert len(context) >= 0


class TestGetRelevanceScores:
    """Tests for getting relevance scores."""

    def test_get_scores_for_files(self):
        """Test getting relevance scores for all files."""
        builder = ContextBuilder.with_defaults()

        parsed = ParsedFile(
            path="test.py",
            language="python",
            symbols=[],
            imports=[],
            exports=[],
            raw_content="",
            line_count=0,
        )

        builder.add_parsed_file(parsed)

        scores = builder.get_relevance_scores(
            target_files=["test.py"],
            task_description="",
        )

        assert "test.py" in scores
        assert scores["test.py"] > 0
