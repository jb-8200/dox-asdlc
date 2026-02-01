"""Unit tests for Slack Bridge Idea Handler.

Tests the IdeaHandler class for processing Slack /idea-new commands
to capture ideas for the Brainflare Hub.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from src.infrastructure.slack_bridge.config import SlackBridgeConfig
from src.orchestrator.api.models.idea import Idea, IdeaStatus


class TestIdeaHandlerInitialization:
    """Tests for IdeaHandler initialization."""

    @pytest.fixture
    def config(self) -> SlackBridgeConfig:
        """Sample config for testing."""
        return SlackBridgeConfig(
            bot_token=SecretStr("xoxb-test"),
            app_token=SecretStr("xapp-test"),
            signing_secret=SecretStr("secret"),
            routing_policy={},
            rbac_map={},
            ideas_channels=["C-IDEAS-1", "C-IDEAS-2"],
            ideas_emoji="bulb",
        )

    @pytest.fixture
    def mock_ideas_service(self) -> AsyncMock:
        """Mock IdeasService."""
        mock = AsyncMock()
        mock.create_idea = AsyncMock(
            return_value=Idea(
                id="idea-abc123",
                content="Test idea",
                author_id="U001",
                author_name="Test User",
                status=IdeaStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                word_count=2,
            )
        )
        return mock

    @pytest.fixture
    def mock_slack(self) -> MagicMock:
        """Mock Slack WebClient."""
        mock = MagicMock()
        mock.users_info = AsyncMock(
            return_value={"ok": True, "user": {"real_name": "Test User"}}
        )
        return mock

    def test_handler_initialization(
        self, config: SlackBridgeConfig, mock_ideas_service: AsyncMock, mock_slack: MagicMock
    ):
        """Handler initializes with correct config and ideas service."""
        from src.infrastructure.slack_bridge.idea_handler import IdeaHandler

        handler = IdeaHandler(
            ideas_service=mock_ideas_service,
            slack_client=mock_slack,
            config=config,
        )
        assert handler.config == config
        assert handler.ideas_service == mock_ideas_service


class TestCreateIdeaFromCommand:
    """Tests for create_idea_from_command method."""

    @pytest.fixture
    def config(self) -> SlackBridgeConfig:
        """Sample config for testing."""
        return SlackBridgeConfig(
            bot_token=SecretStr("xoxb-test"),
            app_token=SecretStr("xapp-test"),
            signing_secret=SecretStr("secret"),
            routing_policy={},
            rbac_map={},
            ideas_channels=["C-IDEAS"],
            ideas_emoji="bulb",
        )

    @pytest.fixture
    def mock_ideas_service(self) -> AsyncMock:
        """Mock IdeasService."""
        mock = AsyncMock()
        mock.create_idea = AsyncMock(
            return_value=Idea(
                id="idea-cmd123",
                content="Command idea",
                author_id="U001",
                author_name="Command User",
                status=IdeaStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                word_count=2,
            )
        )
        return mock

    @pytest.fixture
    def mock_slack(self) -> MagicMock:
        """Mock Slack WebClient."""
        mock = MagicMock()
        mock.users_info = AsyncMock(
            return_value={"ok": True, "user": {"real_name": "Command User"}}
        )
        return mock

    @pytest.fixture
    def handler(
        self,
        config: SlackBridgeConfig,
        mock_ideas_service: AsyncMock,
        mock_slack: MagicMock,
    ):
        """Create IdeaHandler instance."""
        from src.infrastructure.slack_bridge.idea_handler import IdeaHandler

        return IdeaHandler(
            ideas_service=mock_ideas_service,
            slack_client=mock_slack,
            config=config,
        )

    @pytest.mark.asyncio
    async def test_create_idea_from_command_success(
        self, handler, mock_ideas_service: AsyncMock
    ):
        """Successfully creates idea from command."""
        result = await handler.create_idea_from_command(
            user_id="U001",
            text="This is my idea from a command",
            channel_id="C-IDEAS",
        )

        assert result is not None
        assert result.id == "idea-cmd123"
        mock_ideas_service.create_idea.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_idea_from_command_sets_author_info(
        self, handler, mock_ideas_service: AsyncMock
    ):
        """Command idea includes correct author info."""
        await handler.create_idea_from_command(
            user_id="U001",
            text="My command idea",
            channel_id="C-IDEAS",
        )

        call_args = mock_ideas_service.create_idea.call_args
        request = call_args[0][0]
        assert request.author_id == "U001"
        assert request.author_name == "Command User"

    @pytest.mark.asyncio
    async def test_create_idea_from_command_builds_source_label(
        self, handler, mock_ideas_service: AsyncMock
    ):
        """Source label follows source_ref:slack:command:{channel}:{user} format."""
        await handler.create_idea_from_command(
            user_id="U001",
            text="My command idea",
            channel_id="C-IDEAS",
        )

        call_args = mock_ideas_service.create_idea.call_args
        request = call_args[0][0]
        assert "source_ref:slack:command:C-IDEAS:U001" in request.labels

    @pytest.mark.asyncio
    async def test_create_idea_from_command_handles_value_error(
        self, handler, mock_ideas_service: AsyncMock
    ):
        """ValueError (e.g., word limit) returns None."""
        mock_ideas_service.create_idea = AsyncMock(
            side_effect=ValueError("Idea exceeds 144 word limit")
        )

        result = await handler.create_idea_from_command(
            user_id="U001",
            text="Word " * 150,  # Exceeds limit
            channel_id="C-IDEAS",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_idea_from_command_handles_exception(
        self, handler, mock_ideas_service: AsyncMock
    ):
        """Unexpected exceptions return None."""
        mock_ideas_service.create_idea = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await handler.create_idea_from_command(
            user_id="U001",
            text="My idea",
            channel_id="C-IDEAS",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_idea_from_command_gets_user_display_name(
        self, handler, mock_slack: MagicMock
    ):
        """User display name is fetched from Slack."""
        await handler.create_idea_from_command(
            user_id="U001",
            text="My idea",
            channel_id="C-IDEAS",
        )

        mock_slack.users_info.assert_called_once_with(user="U001")


class TestGetUserName:
    """Tests for _get_user_name method."""

    @pytest.fixture
    def config(self) -> SlackBridgeConfig:
        """Sample config for testing."""
        return SlackBridgeConfig(
            bot_token=SecretStr("xoxb-test"),
            app_token=SecretStr("xapp-test"),
            signing_secret=SecretStr("secret"),
            routing_policy={},
            rbac_map={},
            ideas_channels=["C-IDEAS"],
            ideas_emoji="bulb",
        )

    @pytest.fixture
    def mock_ideas_service(self) -> AsyncMock:
        """Mock IdeasService."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_user_name_success(
        self, config: SlackBridgeConfig, mock_ideas_service: AsyncMock
    ):
        """Returns user's real name when API call succeeds."""
        from src.infrastructure.slack_bridge.idea_handler import IdeaHandler

        mock_slack = MagicMock()
        mock_slack.users_info = AsyncMock(
            return_value={"ok": True, "user": {"real_name": "John Doe"}}
        )

        handler = IdeaHandler(
            ideas_service=mock_ideas_service,
            slack_client=mock_slack,
            config=config,
        )

        result = await handler._get_user_name("U001")
        assert result == "John Doe"

    @pytest.mark.asyncio
    async def test_get_user_name_api_failure(
        self, config: SlackBridgeConfig, mock_ideas_service: AsyncMock
    ):
        """Returns user_id when API call fails."""
        from src.infrastructure.slack_bridge.idea_handler import IdeaHandler

        mock_slack = MagicMock()
        mock_slack.users_info = AsyncMock(side_effect=Exception("API Error"))

        handler = IdeaHandler(
            ideas_service=mock_ideas_service,
            slack_client=mock_slack,
            config=config,
        )

        result = await handler._get_user_name("U001")
        assert result == "U001"

    @pytest.mark.asyncio
    async def test_get_user_name_not_ok_response(
        self, config: SlackBridgeConfig, mock_ideas_service: AsyncMock
    ):
        """Returns user_id when API response is not ok."""
        from src.infrastructure.slack_bridge.idea_handler import IdeaHandler

        mock_slack = MagicMock()
        mock_slack.users_info = AsyncMock(return_value={"ok": False})

        handler = IdeaHandler(
            ideas_service=mock_ideas_service,
            slack_client=mock_slack,
            config=config,
        )

        result = await handler._get_user_name("U001")
        assert result == "U001"
