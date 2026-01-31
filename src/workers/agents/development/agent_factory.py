"""Factory functions for creating development agents with LLM client factory.

Provides factory functions for creating UTest, Coding, Debugger, and Reviewer
agents using the LLMClientFactory to get configured LLM clients.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.workers.agents.development.config import DevelopmentConfig

if TYPE_CHECKING:
    from src.infrastructure.llm.factory import LLMClientFactory
    from src.workers.agents.development.coding_agent import CodingAgent
    from src.workers.agents.development.debugger_agent import DebuggerAgent
    from src.workers.agents.development.reviewer_agent import ReviewerAgent
    from src.workers.agents.development.utest_agent import UTestAgent
    from src.workers.artifacts.writer import ArtifactWriter
    from src.workers.rlm.integration import RLMIntegration


logger = logging.getLogger(__name__)


def get_llm_client_factory() -> "LLMClientFactory":
    """Get the global LLM client factory instance.

    Returns:
        LLMClientFactory: The factory instance.
    """
    from src.infrastructure.llm.factory import get_llm_client_factory
    return get_llm_client_factory()


async def create_utest_agent(
    artifact_writer: "ArtifactWriter",
    config: DevelopmentConfig | None = None,
    factory: "LLMClientFactory | None" = None,
    fallback_to_stub: bool = False,
) -> "UTestAgent":
    """Create a UTestAgent with a factory-provided LLM client.

    Args:
        artifact_writer: Writer for persisting artifacts.
        config: Optional development configuration.
        factory: Optional LLMClientFactory instance. Uses global if not provided.
        fallback_to_stub: If True, use stub client on factory error.

    Returns:
        UTestAgent: Configured agent instance.

    Raises:
        LLMClientError: If factory fails and fallback_to_stub is False.
    """
    from src.workers.agents.development.utest_agent import UTestAgent

    if config is None:
        config = DevelopmentConfig()

    llm_client = await _get_llm_client("utest", factory, fallback_to_stub)

    return UTestAgent(
        llm_client=llm_client,
        artifact_writer=artifact_writer,
        config=config,
    )


async def create_coding_agent(
    artifact_writer: "ArtifactWriter",
    config: DevelopmentConfig | None = None,
    factory: "LLMClientFactory | None" = None,
    rlm_integration: "RLMIntegration | None" = None,
    fallback_to_stub: bool = False,
) -> "CodingAgent":
    """Create a CodingAgent with a factory-provided LLM client.

    Args:
        artifact_writer: Writer for persisting artifacts.
        config: Optional development configuration.
        factory: Optional LLMClientFactory instance. Uses global if not provided.
        rlm_integration: Optional RLM integration for complex tasks.
        fallback_to_stub: If True, use stub client on factory error.

    Returns:
        CodingAgent: Configured agent instance.

    Raises:
        LLMClientError: If factory fails and fallback_to_stub is False.
    """
    from src.workers.agents.development.coding_agent import CodingAgent

    if config is None:
        config = DevelopmentConfig()

    llm_client = await _get_llm_client("coding", factory, fallback_to_stub)

    return CodingAgent(
        llm_client=llm_client,
        artifact_writer=artifact_writer,
        config=config,
        rlm_integration=rlm_integration,
    )


async def create_debugger_agent(
    artifact_writer: "ArtifactWriter",
    config: DevelopmentConfig | None = None,
    factory: "LLMClientFactory | None" = None,
    rlm_integration: "RLMIntegration | None" = None,
    fallback_to_stub: bool = False,
) -> "DebuggerAgent":
    """Create a DebuggerAgent with a factory-provided LLM client.

    Args:
        artifact_writer: Writer for persisting artifacts.
        config: Optional development configuration.
        factory: Optional LLMClientFactory instance. Uses global if not provided.
        rlm_integration: Optional RLM integration for codebase exploration.
        fallback_to_stub: If True, use stub client on factory error.

    Returns:
        DebuggerAgent: Configured agent instance.

    Raises:
        LLMClientError: If factory fails and fallback_to_stub is False.
    """
    from src.workers.agents.development.debugger_agent import DebuggerAgent

    if config is None:
        config = DevelopmentConfig()

    llm_client = await _get_llm_client("debugger", factory, fallback_to_stub)

    return DebuggerAgent(
        llm_client=llm_client,
        artifact_writer=artifact_writer,
        config=config,
        rlm_integration=rlm_integration,
    )


async def create_reviewer_agent(
    artifact_writer: "ArtifactWriter",
    config: DevelopmentConfig | None = None,
    factory: "LLMClientFactory | None" = None,
    fallback_to_stub: bool = False,
) -> "ReviewerAgent":
    """Create a ReviewerAgent with a factory-provided LLM client.

    Args:
        artifact_writer: Writer for persisting artifacts.
        config: Optional development configuration.
        factory: Optional LLMClientFactory instance. Uses global if not provided.
        fallback_to_stub: If True, use stub client on factory error.

    Returns:
        ReviewerAgent: Configured agent instance.

    Raises:
        LLMClientError: If factory fails and fallback_to_stub is False.
    """
    from src.workers.agents.development.reviewer_agent import ReviewerAgent

    if config is None:
        config = DevelopmentConfig()

    llm_client = await _get_llm_client("reviewer", factory, fallback_to_stub)

    return ReviewerAgent(
        llm_client=llm_client,
        artifact_writer=artifact_writer,
        config=config,
    )


async def _get_llm_client(
    role: str,
    factory: "LLMClientFactory | None",
    fallback_to_stub: bool,
):
    """Get an LLM client from the factory with optional fallback.

    Args:
        role: The agent role (utest, coding, debugger, reviewer).
        factory: Optional factory instance.
        fallback_to_stub: If True, return stub client on error.

    Returns:
        LLM client instance.

    Raises:
        LLMClientError: If factory fails and fallback_to_stub is False.
    """
    from src.infrastructure.llm.factory import LLMClientError

    if factory is None:
        factory = get_llm_client_factory()

    try:
        return await factory.get_client(role)
    except LLMClientError:
        if fallback_to_stub:
            logger.warning(
                f"Failed to get LLM client for {role}, falling back to stub"
            )
            from src.workers.llm.client import StubLLMClient
            return StubLLMClient(model_name=f"stub-{role}")
        raise
