"""Acceptance Agent for generating acceptance criteria.

Transforms PRD documents into testable acceptance criteria
using Given-When-Then format.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TYPE_CHECKING

from src.workers.agents.protocols import AgentContext, AgentResult, BaseAgent
from src.workers.agents.discovery.config import DiscoveryConfig
from src.workers.agents.discovery.models import (
    AcceptanceCriteria,
    AcceptanceCriterion,
    PRDDocument,
)
from src.workers.agents.discovery.prompts.acceptance_prompts import (
    ACCEPTANCE_SYSTEM_PROMPT,
    format_criteria_generation_prompt,
    format_coverage_analysis_prompt,
)

if TYPE_CHECKING:
    from src.workers.llm.client import LLMClient
    from src.workers.artifacts.writer import ArtifactWriter

logger = logging.getLogger(__name__)


class AcceptanceAgentError(Exception):
    """Raised when Acceptance agent operations fail."""

    pass


class AcceptanceAgent:
    """Agent that generates acceptance criteria from PRD documents.

    Implements the BaseAgent protocol to be dispatched by the worker pool.
    Uses LLM to generate Given-When-Then acceptance criteria and
    builds a coverage matrix mapping requirements to criteria.

    Example:
        agent = AcceptanceAgent(
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
    ) -> None:
        """Initialize the Acceptance agent.

        Args:
            llm_client: LLM client for text generation.
            artifact_writer: Writer for persisting artifacts.
            config: Agent configuration.
        """
        self._llm_client = llm_client
        self._artifact_writer = artifact_writer
        self._config = config

    @property
    def agent_type(self) -> str:
        """Return the agent type identifier."""
        return "acceptance_agent"

    async def execute(
        self,
        context: AgentContext,
        event_metadata: dict[str, Any],
    ) -> AgentResult:
        """Execute acceptance criteria generation from PRD.

        Args:
            context: Execution context with session/task info.
            event_metadata: Additional metadata from triggering event.
                Expected keys:
                - prd_document: PRDDocument instance or dict (required)
                - prd_path: Path to PRD artifact (alternative to prd_document)

        Returns:
            AgentResult: Result with artifact paths on success.
        """
        logger.info(f"Acceptance Agent starting for task {context.task_id}")

        try:
            # Get PRD document from metadata
            prd = await self._get_prd_document(context, event_metadata)

            if not prd:
                return AgentResult(
                    success=False,
                    agent_type=self.agent_type,
                    task_id=context.task_id,
                    error_message="No PRD document available in event_metadata",
                    should_retry=False,
                )

            if not prd.all_requirements:
                return AgentResult(
                    success=False,
                    agent_type=self.agent_type,
                    task_id=context.task_id,
                    error_message="PRD document has no requirements to generate criteria for",
                    should_retry=False,
                )

            # Step 1: Generate acceptance criteria
            criteria = await self._generate_criteria(prd)

            if not criteria:
                return AgentResult(
                    success=False,
                    agent_type=self.agent_type,
                    task_id=context.task_id,
                    error_message="Failed to generate acceptance criteria",
                    should_retry=True,
                )

            # Step 2: Build acceptance criteria document with coverage matrix
            requirement_ids = [r.id for r in prd.all_requirements]
            acceptance_doc = AcceptanceCriteria.create(
                prd_version=prd.version,
                criteria=criteria,
                requirement_ids=requirement_ids,
            )

            # Step 3: Write artifact
            artifact_path = await self._write_artifact(context, acceptance_doc)

            # Calculate coverage stats
            coverage_pct = acceptance_doc.get_coverage_percentage()
            uncovered = acceptance_doc.get_uncovered_requirements()

            logger.info(
                f"Acceptance Agent completed for task {context.task_id}, "
                f"criteria: {len(criteria)}, coverage: {coverage_pct:.1f}%"
            )

            return AgentResult(
                success=True,
                agent_type=self.agent_type,
                task_id=context.task_id,
                artifact_paths=[artifact_path],
                metadata={
                    "criteria_count": len(criteria),
                    "requirement_count": len(requirement_ids),
                    "coverage_percentage": coverage_pct,
                    "uncovered_requirements": uncovered,
                    "prd_version": prd.version,
                },
            )

        except Exception as e:
            logger.error(f"Acceptance Agent failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                agent_type=self.agent_type,
                task_id=context.task_id,
                error_message=str(e),
                should_retry=True,
            )

    async def _get_prd_document(
        self,
        context: AgentContext,
        event_metadata: dict[str, Any],
    ) -> PRDDocument | None:
        """Get PRD document from metadata or file.

        Args:
            context: Agent context.
            event_metadata: Event metadata.

        Returns:
            PRDDocument | None: PRD document if available.
        """
        # Try to get PRD from metadata directly
        prd_data = event_metadata.get("prd_document")

        if prd_data:
            if isinstance(prd_data, PRDDocument):
                return prd_data
            elif isinstance(prd_data, dict):
                return PRDDocument.from_dict(prd_data)

        # Try to load from artifact path
        prd_path = event_metadata.get("prd_path")
        if prd_path:
            try:
                from pathlib import Path
                path = Path(prd_path)
                if path.exists():
                    content = path.read_text()
                    return PRDDocument.from_json(content)
            except Exception as e:
                logger.warning(f"Failed to load PRD from path {prd_path}: {e}")

        # Try to find PRD in context pack
        if context.context_pack:
            prd_data = context.context_pack.get("prd_document")
            if prd_data:
                return PRDDocument.from_dict(prd_data)

        return None

    async def _generate_criteria(
        self,
        prd: PRDDocument,
    ) -> list[AcceptanceCriterion]:
        """Generate acceptance criteria from PRD.

        Args:
            prd: PRD document to generate criteria from.

        Returns:
            list[AcceptanceCriterion]: Generated acceptance criteria.
        """
        # Format PRD content for prompt
        prd_content = prd.to_markdown()

        # Format requirements list
        requirements_list = json.dumps(
            [r.to_dict() for r in prd.all_requirements], indent=2
        )

        prompt = format_criteria_generation_prompt(prd_content, requirements_list)

        for attempt in range(self._config.max_retries):
            try:
                response = await self._llm_client.generate(
                    prompt=prompt,
                    system=ACCEPTANCE_SYSTEM_PROMPT,
                    max_tokens=self._config.max_tokens,
                    temperature=self._config.temperature,
                )

                # Parse JSON from response
                criteria_data = self._parse_json_from_response(response.content)

                if not criteria_data or "criteria" not in criteria_data:
                    logger.warning(f"Invalid criteria response on attempt {attempt + 1}")
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(self._config.retry_delay_seconds)
                    continue

                # Convert to AcceptanceCriterion objects
                criteria = []
                for idx, crit_data in enumerate(criteria_data["criteria"]):
                    try:
                        criterion = AcceptanceCriterion(
                            id=crit_data.get("id", f"AC-{idx + 1:03d}"),
                            requirement_ids=crit_data.get("requirement_ids", []),
                            given=crit_data.get("given", ""),
                            when=crit_data.get("when", ""),
                            then=crit_data.get("then", ""),
                            notes=crit_data.get("notes", ""),
                        )

                        # Validate criterion has meaningful content
                        if criterion.given and criterion.when and criterion.then:
                            criteria.append(criterion)
                        else:
                            logger.warning(
                                f"Skipping incomplete criterion: {criterion.id}"
                            )

                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid criterion: {e}")
                        continue

                if criteria:
                    return criteria

            except Exception as e:
                logger.warning(f"Criteria generation attempt {attempt + 1} failed: {e}")
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(self._config.retry_delay_seconds)

        # Fallback: generate minimal criteria
        return self._create_fallback_criteria(prd)

    def _create_fallback_criteria(
        self,
        prd: PRDDocument,
    ) -> list[AcceptanceCriterion]:
        """Create minimal acceptance criteria as fallback.

        Args:
            prd: PRD document.

        Returns:
            list[AcceptanceCriterion]: Minimal criteria.
        """
        criteria = []

        for idx, req in enumerate(prd.all_requirements):
            criterion = AcceptanceCriterion(
                id=f"AC-{idx + 1:03d}",
                requirement_ids=[req.id],
                given=f"the system is operational",
                when=f"the user performs the action described in {req.id}",
                then=f"the expected outcome as defined in {req.id} occurs",
                notes=f"Generated as fallback. Original requirement: {req.description[:100]}",
            )
            criteria.append(criterion)

        return criteria

    async def _write_artifact(
        self,
        context: AgentContext,
        acceptance_doc: AcceptanceCriteria,
    ) -> str:
        """Write acceptance criteria artifact to filesystem.

        Args:
            context: Agent context with session info.
            acceptance_doc: Acceptance criteria document to write.

        Returns:
            str: Path to written artifact.
        """
        from src.workers.artifacts.writer import ArtifactType

        # Write both JSON and markdown versions
        json_content = acceptance_doc.to_json()
        md_content = acceptance_doc.to_markdown()

        # Write JSON artifact (primary)
        json_path = await self._artifact_writer.write_artifact(
            session_id=context.session_id,
            task_id=context.task_id,
            content=json_content,
            artifact_type=ArtifactType.REPORT,
            filename=f"{context.task_id}_acceptance_criteria.json",
        )

        # Write markdown artifact (human-readable)
        await self._artifact_writer.write_artifact(
            session_id=context.session_id,
            task_id=context.task_id,
            content=md_content,
            artifact_type=ArtifactType.TEXT,
            filename=f"{context.task_id}_acceptance_criteria.md",
        )

        return json_path

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
