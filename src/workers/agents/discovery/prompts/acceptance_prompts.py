"""Prompt templates for Acceptance Criteria generation.

Provides system prompts and generation templates for the Acceptance Agent.
"""

from __future__ import annotations

from typing import Any

# System prompt establishing the QA/testing perspective
ACCEPTANCE_SYSTEM_PROMPT = """You are an expert Quality Assurance engineer and test designer with extensive experience in behavior-driven development (BDD) and acceptance testing.

Your role is to transform Product Requirements Documents (PRDs) into comprehensive, testable acceptance criteria using the Given-When-Then format.

Key principles:
1. **Testability**: Every criterion must be objectively verifiable
2. **Completeness**: Cover all functional requirements and key edge cases
3. **Independence**: Each criterion should test one specific behavior
4. **Clarity**: Use precise, unambiguous language
5. **Traceability**: Link criteria back to specific requirements

Given-When-Then format:
- **Given**: The initial context or precondition (state before action)
- **When**: The action or event that triggers the behavior
- **Then**: The expected outcome or result (verifiable assertion)

Best practices:
- Write criteria from the user's perspective
- Include both positive (happy path) and negative (error) scenarios
- Consider boundary conditions and edge cases
- Keep criteria atomic - one behavior per criterion
- Use concrete examples where helpful"""

# Prompt template for generating acceptance criteria from PRD
CRITERIA_GENERATION_PROMPT = """Generate acceptance criteria for the following PRD.

PRD CONTENT:
{prd_content}

REQUIREMENTS TO COVER:
{requirements_list}

Generate acceptance criteria in the following JSON format:
```json
{{
  "criteria": [
    {{
      "id": "AC-001",
      "requirement_ids": ["REQ-001"],
      "given": "Precondition description",
      "when": "Action description",
      "then": "Expected outcome",
      "notes": "Additional notes or edge cases (optional)"
    }}
  ]
}}
```

Guidelines:
1. Create at least one acceptance criterion per requirement
2. For complex requirements, create multiple criteria covering different scenarios:
   - Happy path (normal successful operation)
   - Error cases (invalid input, failures)
   - Edge cases (boundary conditions)
3. Use unique IDs starting with AC-001
4. Reference requirement IDs in requirement_ids array
5. Write in present tense
6. Be specific about expected values and states
7. Include timing/performance criteria for non-functional requirements

For each requirement, consider:
- What does success look like?
- What are the failure modes?
- What are the boundary conditions?
- Are there any timing or sequence dependencies?"""

# Prompt for analyzing coverage of requirements by criteria
COVERAGE_ANALYSIS_PROMPT = """Analyze the coverage of requirements by the provided acceptance criteria.

REQUIREMENTS:
{requirements_list}

ACCEPTANCE CRITERIA:
{criteria_list}

Analyze and output:
```json
{{
  "coverage_analysis": [
    {{
      "requirement_id": "REQ-001",
      "criterion_ids": ["AC-001", "AC-002"],
      "coverage_level": "full|partial|none",
      "coverage_assessment": "Description of how well the requirement is covered",
      "gaps": ["List of uncovered aspects"]
    }}
  ],
  "overall_coverage": {{
    "percentage": 85,
    "fully_covered": 10,
    "partially_covered": 2,
    "not_covered": 1
  }},
  "recommendations": [
    "Suggestions for improving coverage"
  ]
}}
```

Assessment criteria:
- **Full coverage**: All aspects of the requirement have acceptance criteria, including edge cases
- **Partial coverage**: Main functionality is covered but edge cases or error scenarios are missing
- **No coverage**: No acceptance criteria map to this requirement"""


def format_criteria_generation_prompt(
    prd_content: str,
    requirements_list: str,
) -> str:
    """Format the criteria generation prompt.

    Args:
        prd_content: Full PRD content or summary.
        requirements_list: JSON or formatted list of requirements.

    Returns:
        str: Formatted prompt ready for LLM.
    """
    return CRITERIA_GENERATION_PROMPT.format(
        prd_content=prd_content,
        requirements_list=requirements_list,
    )


def format_coverage_analysis_prompt(
    requirements_list: str,
    criteria_list: str,
) -> str:
    """Format the coverage analysis prompt.

    Args:
        requirements_list: JSON or formatted list of requirements.
        criteria_list: JSON or formatted list of acceptance criteria.

    Returns:
        str: Formatted prompt ready for LLM.
    """
    return COVERAGE_ANALYSIS_PROMPT.format(
        requirements_list=requirements_list,
        criteria_list=criteria_list,
    )


# Few-shot examples for better output quality
CRITERIA_GENERATION_EXAMPLES = """
EXAMPLE REQUIREMENT:
REQ-001: The system shall provide user login functionality with email and password

EXAMPLE OUTPUT:
```json
{
  "criteria": [
    {
      "id": "AC-001",
      "requirement_ids": ["REQ-001"],
      "given": "a registered user with email 'user@example.com' and password 'ValidPass123!'",
      "when": "the user submits login with correct email and password",
      "then": "the system authenticates the user and redirects to the dashboard with a valid session token",
      "notes": "Session token should be HTTP-only cookie"
    },
    {
      "id": "AC-002",
      "requirement_ids": ["REQ-001"],
      "given": "a registered user with email 'user@example.com'",
      "when": "the user submits login with incorrect password",
      "then": "the system displays 'Invalid email or password' error and does not create a session",
      "notes": "Error message should not reveal whether email exists"
    },
    {
      "id": "AC-003",
      "requirement_ids": ["REQ-001"],
      "given": "no user registered with email 'unknown@example.com'",
      "when": "the user attempts to login with that email",
      "then": "the system displays 'Invalid email or password' error and does not create a session",
      "notes": "Prevent user enumeration attacks"
    },
    {
      "id": "AC-004",
      "requirement_ids": ["REQ-001"],
      "given": "a user who has submitted 5 failed login attempts in 10 minutes",
      "when": "the user attempts another login",
      "then": "the system temporarily locks the account and displays 'Account temporarily locked. Try again in 15 minutes'",
      "notes": "Rate limiting for security"
    },
    {
      "id": "AC-005",
      "requirement_ids": ["REQ-001"],
      "given": "a user on the login page",
      "when": "the user submits the form with empty email field",
      "then": "the system displays validation error 'Email is required' without making a server request",
      "notes": "Client-side validation"
    }
  ]
}
```

This example demonstrates:
- Happy path (AC-001)
- Wrong password (AC-002)
- Non-existent user (AC-003)
- Rate limiting (AC-004)
- Validation (AC-005)
"""

# Combined prompt with examples for high-quality output
CRITERIA_GENERATION_WITH_EXAMPLES = f"""
{ACCEPTANCE_SYSTEM_PROMPT}

{CRITERIA_GENERATION_EXAMPLES}

Now generate acceptance criteria for the following:

{{prd_content}}

REQUIREMENTS:
{{requirements_list}}

Generate comprehensive acceptance criteria in JSON format, following the examples above.
"""


def format_criteria_prompt_with_examples(
    prd_content: str,
    requirements_list: str,
) -> str:
    """Format criteria prompt including few-shot examples.

    Args:
        prd_content: Full PRD content or summary.
        requirements_list: JSON or formatted list of requirements.

    Returns:
        str: Formatted prompt with examples.
    """
    return CRITERIA_GENERATION_WITH_EXAMPLES.format(
        prd_content=prd_content,
        requirements_list=requirements_list,
    )
