"""Unit tests for PRD prompt templates."""

from __future__ import annotations

import pytest

from src.workers.agents.discovery.prompts.prd_prompts import (
    PRD_SYSTEM_PROMPT,
    REQUIREMENTS_EXTRACTION_PROMPT,
    PRD_GENERATION_PROMPT,
    AMBIGUITY_DETECTION_PROMPT,
    format_requirements_extraction_prompt,
    format_prd_prompt,
    format_ambiguity_detection_prompt,
)


class TestPRDSystemPrompt:
    """Tests for PRD system prompt."""

    def test_system_prompt_establishes_prd_expert_role(self) -> None:
        """Test that system prompt establishes PRD expert role."""
        assert "PRD" in PRD_SYSTEM_PROMPT
        assert "Product Requirements Document" in PRD_SYSTEM_PROMPT

    def test_system_prompt_includes_key_principles(self) -> None:
        """Test that system prompt includes key principles."""
        assert "Clarity" in PRD_SYSTEM_PROMPT
        assert "Completeness" in PRD_SYSTEM_PROMPT
        assert "Traceability" in PRD_SYSTEM_PROMPT
        assert "Testability" in PRD_SYSTEM_PROMPT
        assert "Prioritization" in PRD_SYSTEM_PROMPT

    def test_system_prompt_mentions_moscow_prioritization(self) -> None:
        """Test that system prompt mentions MoSCoW prioritization."""
        assert "MoSCoW" in PRD_SYSTEM_PROMPT
        assert "Must Have" in PRD_SYSTEM_PROMPT


class TestRequirementsExtractionPrompt:
    """Tests for requirements extraction prompt template."""

    def test_extraction_prompt_has_placeholders(self) -> None:
        """Test that extraction prompt has required placeholders."""
        assert "{user_input}" in REQUIREMENTS_EXTRACTION_PROMPT
        assert "{project_context}" in REQUIREMENTS_EXTRACTION_PROMPT

    def test_extraction_prompt_specifies_json_format(self) -> None:
        """Test that extraction prompt specifies JSON output format."""
        assert "JSON" in REQUIREMENTS_EXTRACTION_PROMPT or "json" in REQUIREMENTS_EXTRACTION_PROMPT
        assert '"requirements"' in REQUIREMENTS_EXTRACTION_PROMPT

    def test_extraction_prompt_includes_requirement_fields(self) -> None:
        """Test that extraction prompt includes required fields."""
        assert '"id"' in REQUIREMENTS_EXTRACTION_PROMPT
        assert '"description"' in REQUIREMENTS_EXTRACTION_PROMPT
        assert '"priority"' in REQUIREMENTS_EXTRACTION_PROMPT
        assert '"type"' in REQUIREMENTS_EXTRACTION_PROMPT


class TestPRDGenerationPrompt:
    """Tests for PRD generation prompt template."""

    def test_generation_prompt_has_placeholders(self) -> None:
        """Test that generation prompt has required placeholders."""
        assert "{requirements_json}" in PRD_GENERATION_PROMPT
        assert "{project_title}" in PRD_GENERATION_PROMPT
        assert "{additional_context}" in PRD_GENERATION_PROMPT

    def test_generation_prompt_specifies_structure(self) -> None:
        """Test that generation prompt specifies PRD structure."""
        assert '"executive_summary"' in PRD_GENERATION_PROMPT
        assert '"objectives"' in PRD_GENERATION_PROMPT
        assert '"scope"' in PRD_GENERATION_PROMPT
        assert '"sections"' in PRD_GENERATION_PROMPT


class TestAmbiguityDetectionPrompt:
    """Tests for ambiguity detection prompt template."""

    def test_ambiguity_prompt_has_placeholders(self) -> None:
        """Test that ambiguity prompt has required placeholders."""
        assert "{requirements_text}" in AMBIGUITY_DETECTION_PROMPT
        assert "{project_context}" in AMBIGUITY_DETECTION_PROMPT

    def test_ambiguity_prompt_identifies_issue_types(self) -> None:
        """Test that ambiguity prompt identifies issue types."""
        assert "Ambiguous" in AMBIGUITY_DETECTION_PROMPT
        assert "Missing" in AMBIGUITY_DETECTION_PROMPT
        assert "Conflicting" in AMBIGUITY_DETECTION_PROMPT

    def test_ambiguity_prompt_specifies_severity_levels(self) -> None:
        """Test that ambiguity prompt specifies severity levels."""
        assert "critical" in AMBIGUITY_DETECTION_PROMPT
        assert "major" in AMBIGUITY_DETECTION_PROMPT
        assert "minor" in AMBIGUITY_DETECTION_PROMPT


class TestFormatRequirementsExtractionPrompt:
    """Tests for format_requirements_extraction_prompt function."""

    def test_formats_with_user_input(self) -> None:
        """Test that function formats prompt with user input."""
        result = format_requirements_extraction_prompt(
            user_input="Build a login system",
        )

        assert "Build a login system" in result
        assert "{user_input}" not in result

    def test_formats_with_project_context(self) -> None:
        """Test that function formats prompt with project context."""
        result = format_requirements_extraction_prompt(
            user_input="Build something",
            project_context="This is a web application",
        )

        assert "This is a web application" in result

    def test_uses_default_context_when_empty(self) -> None:
        """Test that function uses default when context is empty."""
        result = format_requirements_extraction_prompt(
            user_input="Build something",
            project_context="",
        )

        assert "No additional context provided" in result


class TestFormatPRDPrompt:
    """Tests for format_prd_prompt function."""

    def test_formats_with_requirements_json(self) -> None:
        """Test that function formats prompt with requirements JSON."""
        result = format_prd_prompt(
            requirements_json='[{"id": "REQ-001"}]',
            project_title="Test Project",
        )

        assert '{"id": "REQ-001"}' in result
        assert "Test Project" in result

    def test_formats_with_additional_context(self) -> None:
        """Test that function formats prompt with additional context."""
        result = format_prd_prompt(
            requirements_json="[]",
            project_title="Test",
            additional_context="Extra info",
        )

        assert "Extra info" in result

    def test_uses_default_context_when_empty(self) -> None:
        """Test that function uses default when context is empty."""
        result = format_prd_prompt(
            requirements_json="[]",
            project_title="Test",
            additional_context="",
        )

        assert "None provided" in result


class TestFormatAmbiguityDetectionPrompt:
    """Tests for format_ambiguity_detection_prompt function."""

    def test_formats_with_requirements_text(self) -> None:
        """Test that function formats prompt with requirements text."""
        result = format_ambiguity_detection_prompt(
            requirements_text="User can login with password",
        )

        assert "User can login with password" in result

    def test_formats_with_project_context(self) -> None:
        """Test that function formats prompt with project context."""
        result = format_ambiguity_detection_prompt(
            requirements_text="Some requirements",
            project_context="Web app context",
        )

        assert "Web app context" in result
