"""PRD Agent for generating Product Requirements Documents.

Transforms raw user requirements into structured PRD documents
following the BaseAgent protocol.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TYPE_CHECKING

from src.workers.agents.protocols import AgentContext, AgentResult, BaseAgent
from src.workers.agents.discovery.config import DiscoveryConfig
from src.workers.agents.discovery.models import (
    PRDDocument,
    PRDSection,
    Requirement,
    RequirementPriority,
    RequirementType,
)
from src.workers.agents.discovery.prompts.prd_prompts import (
    PRD_SYSTEM_PROMPT,
    format_requirements_extraction_prompt,
    format_prd_prompt,
    format_ambiguity_detection_prompt,
)

if TYPE_CHECKING:
    from src.workers.llm.client import LLMClient
    from src.workers.artifacts.writer import ArtifactWriter
    from src.workers.rlm.integration import RLMIntegration

logger = logging.getLogger(__name__)


class PRDAgentError(Exception):
    """Raised when PRD agent operations fail."""

    pass


class PRDAgent:
    """Agent that generates structured PRD documents from raw requirements.

    Implements the BaseAgent protocol to be dispatched by the worker pool.
    Uses LLM to extract requirements and generate comprehensive PRD documents.

    Example:
        agent = PRDAgent(
            llm_client=client,
            artifact_writer=writer,
            config=DiscoveryConfig(),
        )
        result = await agent.execute(context, event_metadata)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        artifact_writer: ArtifactWriter,
        config: DiscoveryConfig,
        rlm_integration: RLMIntegration | None = None,
    ) -> None:
        """Initialize the PRD agent.

        Args:
            llm_client: LLM client for text generation.
            artifact_writer: Writer for persisting artifacts.
            config: Agent configuration.
            rlm_integration: Optional RLM integration for exploration.
        """
        self._llm_client = llm_client
        self._artifact_writer = artifact_writer
        self._config = config
        self._rlm_integration = rlm_integration

    @property
    def agent_type(self) -> str:
        """Return the agent type identifier."""
        return "prd_agent"

    async def execute(
        self,
        context: AgentContext,
        event_metadata: dict[str, Any],
    ) -> AgentResult:
        """Execute PRD generation from raw requirements.

        Args:
            context: Execution context with session/task info.
            event_metadata: Additional metadata from triggering event.
                Expected keys:
                - raw_requirements: Raw user input (required)
                - project_title: Title for the PRD (optional)
                - project_context: Additional context (optional)

        Returns:
            AgentResult: Result with artifact paths on success.
        """
        logger.info(f"PRD Agent starting for task {context.task_id}")

        try:
            # Extract raw requirements from metadata
            raw_requirements = event_metadata.get("raw_requirements", "")
            if not raw_requirements:
                return AgentResult(
                    success=False,
                    agent_type=self.agent_type,
                    task_id=context.task_id,
                    error_message="No raw_requirements provided in event_metadata",
                    should_retry=False,
                )

            project_title = event_metadata.get("project_title", "Untitled Project")
            project_context = event_metadata.get("project_context", "")

            # Step 1: Check if RLM exploration is needed for ambiguous requirements
            if self._config.enable_rlm and self._rlm_integration:
                rlm_context = await self._check_and_explore_rlm(
                    raw_requirements, project_context, context
                )
                if rlm_context:
                    project_context = f"{project_context}\n\n{rlm_context}"

            # Step 2: Extract structured requirements
            requirements = await self._extract_requirements(
                raw_requirements, project_context
            )

            if not requirements:
                return AgentResult(
                    success=False,
                    agent_type=self.agent_type,
                    task_id=context.task_id,
                    error_message="Failed to extract requirements from input",
                    should_retry=True,
                )

            # Step 3: Generate full PRD document
            prd = await self._generate_prd(requirements, project_title, project_context)

            # Step 4: Write artifact
            artifact_path = await self._write_artifact(context, prd)

            logger.info(
                f"PRD Agent completed for task {context.task_id}, "
                f"requirements: {len(prd.all_requirements)}"
            )

            return AgentResult(
                success=True,
                agent_type=self.agent_type,
                task_id=context.task_id,
                artifact_paths=[artifact_path],
                metadata={
                    "requirement_count": len(prd.all_requirements),
                    "prd_version": prd.version,
                    "prd_title": prd.title,
                },
            )

        except Exception as e:
            logger.error(f"PRD Agent failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_type=self.agent_type,
                task_id=context.task_id,
                error_message=str(e),
                should_retry=True,
            )

    async def _extract_requirements(
        self,
        raw_requirements: str,
        project_context: str,
    ) -> list[Requirement]:
        """Extract structured requirements from raw input.

        Args:
            raw_requirements: Raw user input text.
            project_context: Additional project context.

        Returns:
            list[Requirement]: Extracted requirements.
        """
        prompt = format_requirements_extraction_prompt(raw_requirements, project_context)

        for attempt in range(self._config.max_retries):
            try:
                response = await self._llm_client.generate(
                    prompt=prompt,
                    system=PRD_SYSTEM_PROMPT,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                )

                # Parse JSON from response
                requirements_data = self._parse_json_from_response(response.content)

                if not requirements_data or "requirements" not in requirements_data:
                    logger.warning(f"Invalid requirements response on attempt {attempt + 1}")
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(self._config.retry_delay_seconds)
                    continue

                # Convert to Requirement objects
                requirements = []
                for req_data in requirements_data["requirements"]:
                    try:
                        req = Requirement(
                            id=req_data.get("id", f"REQ-{len(requirements) + 1:03d}"),
                            description=req_data.get("description", ""),
                            priority=RequirementPriority(
                                req_data.get("priority", "should_have")
                            ),
                            type=RequirementType(req_data.get("type", "functional")),
                            rationale=req_data.get("rationale", ""),
                            source=req_data.get("source", ""),
                        )
                        requirements.append(req)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid requirement: {e}")
                        continue

                return requirements

            except Exception as e:
                logger.warning(f"Requirements extraction attempt {attempt + 1} failed: {e}")
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(self._config.retry_delay_seconds)

        return []

    async def _generate_prd(
        self,
        requirements: list[Requirement],
        project_title: str,
        additional_context: str,
    ) -> PRDDocument:
        """Generate full PRD document from requirements.

        Args:
            requirements: List of extracted requirements.
            project_title: Title for the PRD.
            additional_context: Additional context information.

        Returns:
            PRDDocument: Generated PRD document.
        """
        requirements_json = json.dumps(
            [r.to_dict() for r in requirements], indent=2
        )

        prompt = format_prd_prompt(requirements_json, project_title, additional_context)

        for attempt in range(self._config.max_retries):
            try:
                response = await self._llm_client.generate(
                    prompt=prompt,
                    system=PRD_SYSTEM_PROMPT,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                )

                prd_data = self._parse_json_from_response(response.content)

                if not prd_data:
                    logger.warning(f"Invalid PRD response on attempt {attempt + 1}")
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(self._config.retry_delay_seconds)
                    continue

                # Build PRD document from response
                prd = self._build_prd_from_response(prd_data, requirements)
                return prd

            except Exception as e:
                logger.warning(f"PRD generation attempt {attempt + 1} failed: {e}")
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(self._config.retry_delay_seconds)

        # Fallback: create minimal PRD from requirements
        return self._create_fallback_prd(requirements, project_title)

    def _build_prd_from_response(
        self,
        prd_data: dict[str, Any],
        requirements: list[Requirement],
    ) -> PRDDocument:
        """Build PRDDocument from LLM response data.

        Args:
            prd_data: Parsed JSON from LLM response.
            requirements: Original requirements list.

        Returns:
            PRDDocument: Constructed PRD document.
        """
        # Build sections
        sections = []
        for section_data in prd_data.get("sections", []):
            section_reqs = []
            for req_data in section_data.get("requirements", []):
                # Try to find matching requirement or create new one
                req_id = req_data.get("id", "")
                matching = next(
                    (r for r in requirements if r.id == req_id), None
                )
                if matching:
                    section_reqs.append(matching)
                else:
                    section_reqs.append(Requirement.from_dict(req_data))

            sections.append(PRDSection(
                title=section_data.get("title", ""),
                content=section_data.get("content", ""),
                requirements=section_reqs,
                subsections=[
                    PRDSection.from_dict(sub)
                    for sub in section_data.get("subsections", [])
                ],
            ))

        objectives = PRDSection.from_dict(prd_data.get("objectives", {}))
        scope = PRDSection.from_dict(prd_data.get("scope", {}))

        return PRDDocument.create(
            title=prd_data.get("title", "Untitled Project"),
            executive_summary=prd_data.get("executive_summary", ""),
            objectives=objectives,
            scope=scope,
            sections=sections,
            version=prd_data.get("version", "1.0.0"),
        )

    def _create_fallback_prd(
        self,
        requirements: list[Requirement],
        project_title: str,
    ) -> PRDDocument:
        """Create minimal PRD as fallback when generation fails.

        Args:
            requirements: List of requirements.
            project_title: Project title.

        Returns:
            PRDDocument: Minimal PRD document.
        """
        # Group requirements by type
        functional = [r for r in requirements if r.type == RequirementType.FUNCTIONAL]
        non_functional = [r for r in requirements if r.type == RequirementType.NON_FUNCTIONAL]
        constraints = [r for r in requirements if r.type == RequirementType.CONSTRAINT]
        assumptions = [r for r in requirements if r.type == RequirementType.ASSUMPTION]

        sections = []

        if functional:
            sections.append(PRDSection(
                title="Functional Requirements",
                content="Core functionality requirements.",
                requirements=functional,
            ))

        if non_functional:
            sections.append(PRDSection(
                title="Non-Functional Requirements",
                content="Quality and performance requirements.",
                requirements=non_functional,
            ))

        if constraints:
            sections.append(PRDSection(
                title="Technical Constraints",
                content="Technical limitations and constraints.",
                requirements=constraints,
            ))

        if assumptions:
            sections.append(PRDSection(
                title="Assumptions",
                content="Project assumptions.",
                requirements=assumptions,
            ))

        return PRDDocument.create(
            title=project_title,
            executive_summary="This PRD was generated from extracted requirements.",
            objectives=PRDSection(title="Objectives", content="Define project objectives."),
            scope=PRDSection(title="Scope", content="Define project scope."),
            sections=sections,
        )

    async def _write_artifact(
        self,
        context: AgentContext,
        prd: PRDDocument,
    ) -> str:
        """Write PRD artifact to filesystem.

        Args:
            context: Agent context with session info.
            prd: PRD document to write.

        Returns:
            str: Path to written artifact.
        """
        from src.workers.artifacts.writer import ArtifactType

        # Write both JSON and markdown versions
        json_content = prd.to_json()
        md_content = prd.to_markdown()

        # Write JSON artifact (primary)
        json_path = await self._artifact_writer.write_artifact(
            session_id=context.session_id,
            task_id=context.task_id,
            content=json_content,
            artifact_type=ArtifactType.REPORT,
            filename=f"{context.task_id}_prd.json",
        )

        # Write markdown artifact (human-readable)
        await self._artifact_writer.write_artifact(
            session_id=context.session_id,
            task_id=context.task_id,
            content=md_content,
            artifact_type=ArtifactType.TEXT,
            filename=f"{context.task_id}_prd.md",
        )

        return json_path

    async def _check_and_explore_rlm(
        self,
        raw_requirements: str,
        project_context: str,
        context: AgentContext,
    ) -> str | None:
        """Check if RLM exploration is needed and execute if so.

        Args:
            raw_requirements: Raw requirements text.
            project_context: Project context.
            context: Agent context.

        Returns:
            str | None: RLM exploration results or None.
        """
        if not self._rlm_integration:
            return None

        try:
            # Check for ambiguities
            ambiguity_prompt = format_ambiguity_detection_prompt(
                raw_requirements, project_context
            )

            response = await self._llm_client.generate(
                prompt=ambiguity_prompt,
                system=PRD_SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.2,
            )

            analysis = self._parse_json_from_response(response.content)

            if not analysis:
                return None

            # Check if RLM exploration is recommended
            if analysis.get("recommended_action") != "research":
                return None

            # Check if we have issues that need research
            issues_needing_research = [
                issue for issue in analysis.get("issues", [])
                if issue.get("research_needed", False)
            ]

            if not issues_needing_research:
                return None

            # Build research query
            research_queries = [
                issue.get("description", "") for issue in issues_needing_research
            ]
            combined_query = (
                f"Research the following technical aspects for PRD generation:\n"
                + "\n".join(f"- {q}" for q in research_queries)
            )

            # Execute RLM exploration
            trigger_result = self._rlm_integration.should_use_rlm(
                query=combined_query,
                context_tokens=len(raw_requirements) // 4,
                agent_type=self.agent_type,
            )

            if not trigger_result.should_trigger:
                return None

            logger.info(f"PRD Agent triggering RLM exploration for task {context.task_id}")

            rlm_result = await self._rlm_integration.explore(
                query=combined_query,
                context_hints=["docs/", "README.md", "requirements/"],
                task_id=context.task_id,
            )

            if rlm_result.error:
                logger.warning(f"RLM exploration failed: {rlm_result.error}")
                return None

            return rlm_result.formatted_output

        except Exception as e:
            logger.warning(f"RLM check/exploration failed: {e}")
            return None

    def _parse_json_from_response(self, content: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response, handling code blocks.

        Args:
            content: Raw LLM response content.

        Returns:
            dict | None: Parsed JSON or None if parsing fails.
        """
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from code blocks
        import re

        # Match ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*\n?(.*?)\n?```',
            r'```\s*\n?(.*?)\n?```',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Try finding JSON-like content
        json_start = content.find('{')
        json_end = content.rfind('}')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            try:
                return json.loads(content[json_start:json_end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def validate_context(self, context: AgentContext) -> bool:
        """Validate that context is suitable for execution.

        Args:
            context: Agent context to validate.

        Returns:
            bool: True if context is valid.
        """
        return bool(
            context.session_id
            and context.task_id
            and context.workspace_path
        )
