"""Idea Handler for Slack HITL Bridge.

Handles capturing ideas from Slack slash commands
for the Brainflare Hub ideas repository.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.infrastructure.slack_bridge.config import SlackBridgeConfig
from src.orchestrator.api.models.idea import CreateIdeaRequest, Idea

if TYPE_CHECKING:
    from src.orchestrator.services.ideas_service import IdeasService

logger = logging.getLogger(__name__)


class IdeaHandler:
    """Handler for capturing ideas from Slack slash commands.

    Processes /idea-new commands to capture ideas and forward them
    to the Brainflare Hub.

    Attributes:
        ideas_service: Service for creating/managing ideas.
        slack_client: Slack WebClient for API calls.
        config: SlackBridgeConfig with channel and emoji settings.

    Example:
        ```python
        handler = IdeaHandler(
            ideas_service=ideas_service,
            slack_client=slack_client,
            config=config,
        )

        # Create idea from /idea-new command
        idea = await handler.create_idea_from_command(
            user_id="U001",
            text="My great idea",
            channel_id="C-IDEAS",
        )
        ```
    """

    def __init__(
        self,
        ideas_service: IdeasService,
        slack_client: Any,
        config: SlackBridgeConfig,
    ) -> None:
        """Initialize the IdeaHandler.

        Args:
            ideas_service: Service for creating/managing ideas.
            slack_client: Slack WebClient for API calls.
            config: SlackBridgeConfig with channel and emoji settings.
        """
        self.ideas_service = ideas_service
        self.slack_client = slack_client
        self.config = config

    async def _get_user_name(self, user_id: str) -> str:
        """Get display name for a Slack user.

        Args:
            user_id: Slack user ID.

        Returns:
            str: User's display name, or user_id if lookup fails.
        """
        try:
            result = await self.slack_client.users_info(user=user_id)
            if result.get("ok"):
                return result.get("user", {}).get("real_name", user_id)
            return user_id
        except Exception as e:
            logger.warning(f"Failed to get user info for {user_id}: {e}")
            return user_id

    async def create_idea_from_command(
        self, user_id: str, text: str, channel_id: str
    ) -> Idea | None:
        """Create idea from /idea-new slash command.

        Args:
            user_id: Slack user ID who invoked the command.
            text: The idea content from the command.
            channel_id: Channel where command was invoked.

        Returns:
            Idea | None: The created idea, or None if creation failed.
        """
        # Get author display name
        author_name = await self._get_user_name(user_id)

        # Build source label for traceability
        source_label = f"source_ref:slack:command:{channel_id}:{user_id}"

        # Create the idea request
        request = CreateIdeaRequest(
            content=text,
            author_id=user_id,
            author_name=author_name,
            labels=[source_label],
        )

        try:
            idea = await self.ideas_service.create_idea(request)
            logger.info(f"Created idea {idea.id} from /idea-new command by {user_id}")
            return idea
        except ValueError as e:
            # Handle word limit or validation errors
            logger.warning(f"Failed to create idea from command: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating idea from command: {e}")
            return None
