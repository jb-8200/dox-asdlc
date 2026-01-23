"""Unit tests for Acceptance prompt templates."""

from __future__ import annotations

import pytest

from src.workers.agents.discovery.prompts.acceptance_prompts import (
    ACCEPTANCE_SYSTEM_PROMPT,
    CRITERIA_GENERATION_PROMPT,
    COVERAGE_ANALYSIS_PROMPT,
    format_criteria_generation_prompt,
    format_coverage_analysis_prompt,
)


class TestAcceptanceSystemPrompt:
    """Tests for Acceptance system prompt."""

    def test_system_prompt_establishes_qa_role(self) -> None:
        """Test that system prompt establishes QA/testing role."""
        assert "Quality Assurance" in ACCEPTANCE_SYSTEM_PROMPT
        assert "test" in ACCEPTANCE_SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_gwt_format(self) -> None:
        """Test that system prompt mentions Given-When-Then format."""
        assert "Given" in ACCEPTANCE_SYSTEM_PROMPT
        assert "When" in ACCEPTANCE_SYSTEM_PROMPT
        assert "Then" in ACCEPTANCE_SYSTEM_PROMPT

    def test_system_prompt_includes_key_principles(self) -> None:
        """Test that system prompt includes key principles."""
        assert "Testability" in ACCEPTANCE_SYSTEM_PROMPT
        assert "Completeness" in ACCEPTANCE_SYSTEM_PROMPT
        assert "Independence" in ACCEPTANCE_SYSTEM_PROMPT
        assert "Clarity" in ACCEPTANCE_SYSTEM_PROMPT
        assert "Traceability" in ACCEPTANCE_SYSTEM_PROMPT


class TestCriteriaGenerationPrompt:
    """Tests for criteria generation prompt template."""

    def test_generation_prompt_has_placeholders(self) -> None:
        """Test that generation prompt has required placeholders."""
        assert "{prd_content}" in CRITERIA_GENERATION_PROMPT
        assert "{requirements_list}" in CRITERIA_GENERATION_PROMPT

    def test_generation_prompt_specifies_json_format(self) -> None:
        """Test that generation prompt specifies JSON output format."""
        assert '"criteria"' in CRITERIA_GENERATION_PROMPT
        assert '"id"' in CRITERIA_GENERATION_PROMPT
        assert '"requirement_ids"' in CRITERIA_GENERATION_PROMPT

    def test_generation_prompt_includes_gwt_fields(self) -> None:
        """Test that generation prompt includes GWT fields."""
        assert '"given"' in CRITERIA_GENERATION_PROMPT
        assert '"when"' in CRITERIA_GENERATION_PROMPT
        assert '"then"' in CRITERIA_GENERATION_PROMPT

    def test_generation_prompt_mentions_scenarios(self) -> None:
        """Test that generation prompt mentions scenario types."""
        assert "Happy path" in CRITERIA_GENERATION_PROMPT or "happy path" in CRITERIA_GENERATION_PROMPT.lower()
        assert "Error" in CRITERIA_GENERATION_PROMPT or "error" in CRITERIA_GENERATION_PROMPT.lower()
        assert "Edge" in CRITERIA_GENERATION_PROMPT or "edge" in CRITERIA_GENERATION_PROMPT.lower()


class TestCoverageAnalysisPrompt:
    """Tests for coverage analysis prompt template."""

    def test_analysis_prompt_has_placeholders(self) -> None:
        """Test that analysis prompt has required placeholders."""
        assert "{requirements_list}" in COVERAGE_ANALYSIS_PROMPT
        assert "{criteria_list}" in COVERAGE_ANALYSIS_PROMPT

    def test_analysis_prompt_specifies_coverage_levels(self) -> None:
        """Test that analysis prompt specifies coverage levels."""
        assert "full" in COVERAGE_ANALYSIS_PROMPT
        assert "partial" in COVERAGE_ANALYSIS_PROMPT
        assert "none" in COVERAGE_ANALYSIS_PROMPT


class TestFormatCriteriaGenerationPrompt:
    """Tests for format_criteria_generation_prompt function."""

    def test_formats_with_prd_content(self) -> None:
        """Test that function formats prompt with PRD content."""
        result = format_criteria_generation_prompt(
            prd_content="# Test PRD\n\nThis is a test.",
            requirements_list='[{"id": "REQ-001"}]',
        )

        assert "# Test PRD" in result
        assert "This is a test" in result

    def test_formats_with_requirements_list(self) -> None:
        """Test that function formats prompt with requirements list."""
        result = format_criteria_generation_prompt(
            prd_content="PRD content",
            requirements_list='[{"id": "REQ-001", "description": "Test"}]',
        )

        assert "REQ-001" in result

    def test_placeholders_are_replaced(self) -> None:
        """Test that all placeholders are replaced."""
        result = format_criteria_generation_prompt(
            prd_content="PRD",
            requirements_list="[]",
        )

        assert "{prd_content}" not in result
        assert "{requirements_list}" not in result


class TestFormatCoverageAnalysisPrompt:
    """Tests for format_coverage_analysis_prompt function."""

    def test_formats_with_requirements_list(self) -> None:
        """Test that function formats prompt with requirements list."""
        result = format_coverage_analysis_prompt(
            requirements_list='[{"id": "REQ-001"}]',
            criteria_list="[]",
        )

        assert "REQ-001" in result

    def test_formats_with_criteria_list(self) -> None:
        """Test that function formats prompt with criteria list."""
        result = format_coverage_analysis_prompt(
            requirements_list="[]",
            criteria_list='[{"id": "AC-001"}]',
        )

        assert "AC-001" in result

    def test_placeholders_are_replaced(self) -> None:
        """Test that all placeholders are replaced."""
        result = format_coverage_analysis_prompt(
            requirements_list="[]",
            criteria_list="[]",
        )

        assert "{requirements_list}" not in result
        assert "{criteria_list}" not in result
