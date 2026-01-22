"""MCP contract tests for coordination tools.

These tests verify that MCP tool schemas and responses match
the expected format for compatibility with bash scripts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.coordination.mcp_server import CoordinationMCPServer
from src.infrastructure.coordination.types import (
    CoordinationMessage,
    MessagePayload,
    MessageType,
    PresenceInfo,
)


class TestMCPToolSchemas:
    """Tests for MCP tool schema definitions."""

    @pytest.fixture
    def server(self) -> CoordinationMCPServer:
        """Create test server."""
        with patch.dict("os.environ", {"CLAUDE_INSTANCE_ID": "test-instance"}):
            return CoordinationMCPServer()

    def test_all_required_tools_present(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test that all required tools are defined."""
        schemas = server.get_tool_schemas()
        tool_names = {s["name"] for s in schemas}

        required_tools = {
            "coord_publish_message",
            "coord_check_messages",
            "coord_ack_message",
            "coord_get_presence",
        }

        assert required_tools.issubset(tool_names)

    def test_publish_schema_matches_bash_interface(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test publish tool schema matches bash script interface."""
        schemas = server.get_tool_schemas()
        publish = next(s for s in schemas if s["name"] == "coord_publish_message")

        # Required fields match bash positional args
        required = publish["inputSchema"]["required"]
        assert "msg_type" in required
        assert "subject" in required
        assert "description" in required

        # Optional fields match bash options
        properties = publish["inputSchema"]["properties"]
        assert "to_instance" in properties
        assert "requires_ack" in properties

        # msg_type has enum of valid types
        assert "enum" in properties["msg_type"]
        assert "READY_FOR_REVIEW" in properties["msg_type"]["enum"]
        assert "GENERAL" in properties["msg_type"]["enum"]

    def test_check_schema_matches_bash_interface(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test check tool schema matches bash script interface."""
        schemas = server.get_tool_schemas()
        check = next(s for s in schemas if s["name"] == "coord_check_messages")

        # All fields optional (matches bash flags)
        properties = check["inputSchema"]["properties"]
        assert "to_instance" in properties
        assert "from_instance" in properties
        assert "msg_type" in properties
        assert "pending_only" in properties
        assert "limit" in properties

    def test_ack_schema_matches_bash_interface(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test ack tool schema matches bash script interface."""
        schemas = server.get_tool_schemas()
        ack = next(s for s in schemas if s["name"] == "coord_ack_message")

        # message_id required (bash positional arg)
        required = ack["inputSchema"]["required"]
        assert "message_id" in required

        # comment optional (bash --comment flag)
        properties = ack["inputSchema"]["properties"]
        assert "comment" in properties

    def test_presence_schema_has_no_required_fields(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test presence tool has no required fields."""
        schemas = server.get_tool_schemas()
        presence = next(s for s in schemas if s["name"] == "coord_get_presence")

        # No required fields
        required = presence["inputSchema"].get("required", [])
        assert len(required) == 0


class TestMCPToolOutputFormats:
    """Tests for MCP tool output format compatibility."""

    @pytest.fixture
    def server(self) -> CoordinationMCPServer:
        """Create test server."""
        with patch.dict("os.environ", {"CLAUDE_INSTANCE_ID": "test-instance"}):
            return CoordinationMCPServer()

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock coordination client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_publish_output_format(
        self,
        server: CoordinationMCPServer,
        mock_client: AsyncMock,
    ) -> None:
        """Test publish output matches expected JSON format."""
        mock_message = CoordinationMessage(
            id="msg-test123",
            type=MessageType.READY_FOR_REVIEW,
            from_instance="backend",
            to_instance="orchestrator",
            timestamp=datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc),
            requires_ack=True,
            payload=MessagePayload(subject="Test", description="Desc"),
        )
        mock_client.publish_message = AsyncMock(return_value=mock_message)
        server._client = mock_client

        result = await server.coord_publish_message(
            msg_type="READY_FOR_REVIEW",
            subject="Test",
            description="Desc",
        )

        # Verify output format
        assert result["success"] is True
        assert "message_id" in result
        assert "type" in result
        assert "from" in result
        assert "to" in result
        assert result["message_id"] == "msg-test123"
        assert result["type"] == "READY_FOR_REVIEW"

    @pytest.mark.asyncio
    async def test_check_output_format(
        self,
        server: CoordinationMCPServer,
        mock_client: AsyncMock,
    ) -> None:
        """Test check output matches expected JSON format."""
        mock_messages = [
            CoordinationMessage(
                id="msg-001",
                type=MessageType.GENERAL,
                from_instance="backend",
                to_instance="orchestrator",
                timestamp=datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc),
                requires_ack=True,
                payload=MessagePayload(subject="Test 1", description="Desc 1"),
            ),
        ]
        mock_client.get_messages = AsyncMock(return_value=mock_messages)
        server._client = mock_client

        result = await server.coord_check_messages(pending_only=True)

        # Verify output format
        assert result["success"] is True
        assert "count" in result
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_ack_output_format(
        self,
        server: CoordinationMCPServer,
        mock_client: AsyncMock,
    ) -> None:
        """Test ack output matches expected JSON format."""
        mock_client.acknowledge_message = AsyncMock(return_value=True)
        server._client = mock_client

        result = await server.coord_ack_message(
            message_id="msg-test123",
            comment="Acknowledged",
        )

        # Verify output format
        assert result["success"] is True
        assert "message_id" in result
        assert "acknowledged_by" in result
        assert result["message_id"] == "msg-test123"

    @pytest.mark.asyncio
    async def test_ack_not_found_output_format(
        self,
        server: CoordinationMCPServer,
        mock_client: AsyncMock,
    ) -> None:
        """Test ack not found output format."""
        mock_client.acknowledge_message = AsyncMock(return_value=False)
        server._client = mock_client

        result = await server.coord_ack_message(message_id="msg-notfound")

        # Verify output format
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_presence_output_format(
        self,
        server: CoordinationMCPServer,
        mock_client: AsyncMock,
    ) -> None:
        """Test presence output matches expected JSON format."""
        mock_presence = {
            "backend": PresenceInfo(
                instance_id="backend",
                active=True,
                last_heartbeat=datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc),
            ),
            "frontend": PresenceInfo(
                instance_id="frontend",
                active=True,
                last_heartbeat=datetime(2026, 1, 23, 12, 1, 0, tzinfo=timezone.utc),
            ),
        }
        mock_client.get_presence = AsyncMock(return_value=mock_presence)
        server._client = mock_client

        result = await server.coord_get_presence()

        # Verify output format
        assert result["success"] is True
        assert "instances" in result
        assert "backend" in result["instances"]
        assert "frontend" in result["instances"]
        assert result["instances"]["backend"]["active"] is True


class TestMCPErrorHandling:
    """Tests for MCP error handling."""

    @pytest.fixture
    def server(self) -> CoordinationMCPServer:
        """Create test server."""
        with patch.dict("os.environ", {"CLAUDE_INSTANCE_ID": "test-instance"}):
            return CoordinationMCPServer()

    @pytest.mark.asyncio
    async def test_invalid_message_type_error(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test error for invalid message type."""
        result = await server.coord_publish_message(
            msg_type="INVALID_TYPE",
            subject="Test",
            description="Test",
        )

        assert result["success"] is False
        assert "Invalid message type" in result["error"]
        assert "valid_types" in result

    @pytest.mark.asyncio
    async def test_redis_error_handling(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test handling of Redis errors."""
        mock_client = AsyncMock()
        mock_client.publish_message = AsyncMock(
            side_effect=Exception("Redis connection lost")
        )
        server._client = mock_client

        result = await server.coord_publish_message(
            msg_type="GENERAL",
            subject="Test",
            description="Test",
        )

        assert result["success"] is False
        assert "error" in result


class TestMCPRequestHandling:
    """Tests for JSON-RPC request handling."""

    @pytest.fixture
    def server(self) -> CoordinationMCPServer:
        """Create test server."""
        with patch.dict("os.environ", {"CLAUDE_INSTANCE_ID": "test-instance"}):
            return CoordinationMCPServer()

    @pytest.mark.asyncio
    async def test_tools_list_returns_all_tools(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test tools/list returns all tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = await server.handle_request(request)

        assert response["id"] == 1
        assert "result" in response
        assert len(response["result"]["tools"]) == 4

    @pytest.mark.asyncio
    async def test_tools_call_returns_content(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test tools/call returns content array."""
        mock_client = AsyncMock()
        mock_client.get_presence = AsyncMock(return_value={})
        server._client = mock_client

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "coord_get_presence",
                "arguments": {},
            },
        }

        response = await server.handle_request(request)

        assert response["id"] == 2
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["content"][0]["type"] == "text"

        # Content should be valid JSON
        content = json.loads(response["result"]["content"][0]["text"])
        assert content["success"] is True

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(
        self,
        server: CoordinationMCPServer,
    ) -> None:
        """Test unknown tool returns proper error."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {},
            },
        }

        response = await server.handle_request(request)

        assert response["id"] == 3
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Unknown tool" in response["error"]["message"]
