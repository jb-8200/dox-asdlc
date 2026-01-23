"""Prompt templates for Discovery agents.

Provides structured prompts for PRD generation and acceptance criteria.
"""

from src.workers.agents.discovery.prompts.prd_prompts import (
    PRD_SYSTEM_PROMPT,
    REQUIREMENTS_EXTRACTION_PROMPT,
    PRD_GENERATION_PROMPT,
    AMBIGUITY_DETECTION_PROMPT,
    format_prd_prompt,
    format_requirements_extraction_prompt,
    format_ambiguity_detection_prompt,
)
from src.workers.agents.discovery.prompts.acceptance_prompts import (
    ACCEPTANCE_SYSTEM_PROMPT,
    CRITERIA_GENERATION_PROMPT,
    COVERAGE_ANALYSIS_PROMPT,
    format_criteria_generation_prompt,
    format_coverage_analysis_prompt,
)

__all__ = [
    # PRD prompts
    "PRD_SYSTEM_PROMPT",
    "REQUIREMENTS_EXTRACTION_PROMPT",
    "PRD_GENERATION_PROMPT",
    "AMBIGUITY_DETECTION_PROMPT",
    "format_prd_prompt",
    "format_requirements_extraction_prompt",
    "format_ambiguity_detection_prompt",
    # Acceptance prompts
    "ACCEPTANCE_SYSTEM_PROMPT",
    "CRITERIA_GENERATION_PROMPT",
    "COVERAGE_ANALYSIS_PROMPT",
    "format_criteria_generation_prompt",
    "format_coverage_analysis_prompt",
]
