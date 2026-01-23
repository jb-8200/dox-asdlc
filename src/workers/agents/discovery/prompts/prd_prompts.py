"""Prompt templates for PRD generation.

Provides system prompts, extraction prompts, and generation templates
for the PRD Agent.
"""

from __future__ import annotations

from typing import Any

# System prompt establishing the PRD expert role
PRD_SYSTEM_PROMPT = """You are an expert Product Requirements Document (PRD) writer with extensive experience in software development and product management.

Your role is to transform raw user requirements, feature requests, and project ideas into structured, comprehensive PRD documents that development teams can use to build software.

Key principles:
1. **Clarity**: Write clear, unambiguous requirements that leave no room for misinterpretation
2. **Completeness**: Ensure all aspects of the feature/product are covered
3. **Traceability**: Each requirement should be uniquely identifiable and trackable
4. **Testability**: Requirements should be written so they can be verified through testing
5. **Prioritization**: Use MoSCoW prioritization (Must Have, Should Have, Could Have, Won't Have)

Output format:
- Use markdown formatting for structure
- Use consistent heading levels
- Include unique requirement IDs (REQ-001, REQ-002, etc.)
- Categorize requirements by type (Functional, Non-Functional, Constraint, Assumption)

When analyzing requirements, consider:
- User needs and pain points
- Technical feasibility
- Edge cases and error scenarios
- Security implications
- Performance requirements
- Scalability considerations
- Integration points"""

# Prompt template for extracting structured requirements from raw input
REQUIREMENTS_EXTRACTION_PROMPT = """Analyze the following user input and extract structured requirements.

USER INPUT:
{user_input}

PROJECT CONTEXT:
{project_context}

Extract requirements in the following JSON format:
```json
{{
  "requirements": [
    {{
      "id": "REQ-001",
      "description": "Clear description of the requirement",
      "priority": "must_have|should_have|could_have|wont_have",
      "type": "functional|non_functional|constraint|assumption",
      "rationale": "Why this requirement exists",
      "source": "Where this requirement came from"
    }}
  ],
  "ambiguous_areas": [
    "List any areas that need clarification"
  ],
  "suggested_questions": [
    "Questions to ask for clarification"
  ]
}}
```

Guidelines:
1. Create a unique ID for each requirement starting with REQ-001
2. Extract both explicit and implicit requirements
3. Identify any gaps or ambiguities in the input
4. Suggest clarifying questions for ambiguous areas
5. Assign appropriate priority based on business value and technical dependencies"""

# Prompt template for generating the full PRD document
PRD_GENERATION_PROMPT = """Generate a comprehensive Product Requirements Document (PRD) based on the following requirements.

REQUIREMENTS:
{requirements_json}

PROJECT TITLE: {project_title}

ADDITIONAL CONTEXT:
{additional_context}

Generate the PRD in the following JSON structure:
```json
{{
  "title": "Project Title",
  "version": "1.0.0",
  "executive_summary": "Brief overview of the project (2-3 paragraphs)",
  "objectives": {{
    "title": "Objectives",
    "content": "What this project aims to achieve",
    "requirements": []
  }},
  "scope": {{
    "title": "Scope",
    "content": "In scope and out of scope items",
    "requirements": []
  }},
  "sections": [
    {{
      "title": "Functional Requirements",
      "content": "Overview of functional requirements",
      "requirements": [
        {{
          "id": "REQ-001",
          "description": "...",
          "priority": "must_have",
          "type": "functional",
          "rationale": "...",
          "source": "..."
        }}
      ],
      "subsections": []
    }},
    {{
      "title": "Non-Functional Requirements",
      "content": "Performance, security, scalability requirements",
      "requirements": [],
      "subsections": []
    }},
    {{
      "title": "Technical Constraints",
      "content": "Technical limitations and constraints",
      "requirements": [],
      "subsections": []
    }},
    {{
      "title": "Assumptions and Dependencies",
      "content": "Project assumptions and external dependencies",
      "requirements": [],
      "subsections": []
    }}
  ]
}}
```

Guidelines:
1. Write clear, professional prose for each section
2. Organize requirements logically within sections
3. Ensure all requirements from input are included
4. Add necessary context and explanation for each requirement
5. Include relevant technical details where appropriate"""

# Prompt for detecting ambiguities that may require RLM exploration
AMBIGUITY_DETECTION_PROMPT = """Analyze the following requirements for ambiguities, gaps, or areas that need clarification.

REQUIREMENTS:
{requirements_text}

PROJECT CONTEXT:
{project_context}

Identify:
1. **Ambiguous terms**: Words or phrases that could be interpreted multiple ways
2. **Missing information**: Critical details not specified
3. **Conflicting requirements**: Requirements that may contradict each other
4. **Technical unknowns**: Areas requiring technical research
5. **Edge cases**: Unspecified behavior for edge cases

For each issue, assess:
- Severity (critical, major, minor)
- Impact on development
- Suggested resolution approach

Output format:
```json
{{
  "needs_clarification": true|false,
  "issues": [
    {{
      "type": "ambiguous|missing|conflicting|unknown|edge_case",
      "description": "Description of the issue",
      "severity": "critical|major|minor",
      "affected_requirements": ["REQ-001", "REQ-002"],
      "suggested_resolution": "How to resolve this issue",
      "research_needed": true|false
    }}
  ],
  "recommended_action": "proceed|clarify|research"
}}
```

Be thorough but practical - only flag issues that would genuinely impact development."""


def format_requirements_extraction_prompt(
    user_input: str,
    project_context: str = "",
) -> str:
    """Format the requirements extraction prompt.

    Args:
        user_input: Raw user input to extract requirements from.
        project_context: Optional project context information.

    Returns:
        str: Formatted prompt ready for LLM.
    """
    return REQUIREMENTS_EXTRACTION_PROMPT.format(
        user_input=user_input,
        project_context=project_context or "No additional context provided.",
    )


def format_prd_prompt(
    requirements_json: str,
    project_title: str,
    additional_context: str = "",
) -> str:
    """Format the PRD generation prompt.

    Args:
        requirements_json: JSON string of extracted requirements.
        project_title: Title for the PRD.
        additional_context: Optional additional context.

    Returns:
        str: Formatted prompt ready for LLM.
    """
    return PRD_GENERATION_PROMPT.format(
        requirements_json=requirements_json,
        project_title=project_title,
        additional_context=additional_context or "None provided.",
    )


def format_ambiguity_detection_prompt(
    requirements_text: str,
    project_context: str = "",
) -> str:
    """Format the ambiguity detection prompt.

    Args:
        requirements_text: Requirements text to analyze.
        project_context: Optional project context.

    Returns:
        str: Formatted prompt ready for LLM.
    """
    return AMBIGUITY_DETECTION_PROMPT.format(
        requirements_text=requirements_text,
        project_context=project_context or "No additional context provided.",
    )


# Few-shot examples for better output quality
REQUIREMENTS_EXTRACTION_EXAMPLES = """
EXAMPLE INPUT:
"I need a user authentication system with login, logout, and password reset. It should support OAuth with Google and GitHub. The system should be secure and fast."

EXAMPLE OUTPUT:
```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "description": "The system shall provide user login functionality with email and password",
      "priority": "must_have",
      "type": "functional",
      "rationale": "Core authentication functionality",
      "source": "User input"
    },
    {
      "id": "REQ-002",
      "description": "The system shall provide user logout functionality that invalidates the session",
      "priority": "must_have",
      "type": "functional",
      "rationale": "Core authentication functionality",
      "source": "User input"
    },
    {
      "id": "REQ-003",
      "description": "The system shall support password reset via email verification",
      "priority": "must_have",
      "type": "functional",
      "rationale": "Essential for user account recovery",
      "source": "User input"
    },
    {
      "id": "REQ-004",
      "description": "The system shall support OAuth 2.0 authentication with Google",
      "priority": "should_have",
      "type": "functional",
      "rationale": "Provides convenient sign-in option",
      "source": "User input"
    },
    {
      "id": "REQ-005",
      "description": "The system shall support OAuth 2.0 authentication with GitHub",
      "priority": "should_have",
      "type": "functional",
      "rationale": "Provides convenient sign-in option for developers",
      "source": "User input"
    },
    {
      "id": "REQ-006",
      "description": "Authentication operations shall complete within 500ms for 95th percentile",
      "priority": "should_have",
      "type": "non_functional",
      "rationale": "User expectation for responsive authentication",
      "source": "Implied from 'fast'"
    },
    {
      "id": "REQ-007",
      "description": "The system shall use industry-standard encryption for password storage (bcrypt/argon2)",
      "priority": "must_have",
      "type": "non_functional",
      "rationale": "Security best practice",
      "source": "Implied from 'secure'"
    }
  ],
  "ambiguous_areas": [
    "Session duration/timeout not specified",
    "Multi-factor authentication requirements unclear",
    "Rate limiting for failed attempts not specified"
  ],
  "suggested_questions": [
    "What should the session timeout duration be?",
    "Is multi-factor authentication required?",
    "What rate limiting should be applied to failed login attempts?"
  ]
}
```
"""
