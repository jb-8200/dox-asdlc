"""Tests for coordination exception hierarchy."""

import pytest

from src.core.exceptions import (
    ASDLCError,
    CoordinationError,
    MessageNotFoundError,
    PublishError,
    AcknowledgeError,
    PresenceError,
)


class TestCoordinationErrorBase:
    """Tests for CoordinationError base class."""

    def test_inherits_from_asdlc_error(self) -> None:
        """Test that CoordinationError inherits from ASDLCError."""
        error = CoordinationError("test message")
        assert isinstance(error, ASDLCError)
        assert isinstance(error, Exception)

    def test_instantiation_with_message(self) -> None:
        """Test exception instantiation with message only."""
        error = CoordinationError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_instantiation_with_details(self) -> None:
        """Test exception instantiation with message and details."""
        details = {"message_id": "msg-123", "reason": "timeout"}
        error = CoordinationError("Operation failed", details=details)
        assert error.message == "Operation failed"
        assert error.details == details

    def test_to_dict_serialization(self) -> None:
        """Test to_dict() JSON serialization."""
        details = {"key": "value"}
        error = CoordinationError("Test error", details=details)
        result = error.to_dict()

        assert result["error"] == "CoordinationError"
        assert result["message"] == "Test error"
        assert result["details"] == details

    def test_str_representation(self) -> None:
        """Test string representation of exception."""
        error = CoordinationError("Test message")
        assert str(error) == "Test message"


class TestMessageNotFoundError:
    """Tests for MessageNotFoundError."""

    def test_inherits_from_coordination_error(self) -> None:
        """Test inheritance chain."""
        error = MessageNotFoundError("Message not found")
        assert isinstance(error, CoordinationError)
        assert isinstance(error, ASDLCError)

    def test_to_dict_includes_correct_error_name(self) -> None:
        """Test that to_dict uses correct class name."""
        error = MessageNotFoundError("msg-123 not found", details={"id": "msg-123"})
        result = error.to_dict()
        assert result["error"] == "MessageNotFoundError"


class TestPublishError:
    """Tests for PublishError."""

    def test_inherits_from_coordination_error(self) -> None:
        """Test inheritance chain."""
        error = PublishError("Failed to publish")
        assert isinstance(error, CoordinationError)
        assert isinstance(error, ASDLCError)

    def test_to_dict_includes_correct_error_name(self) -> None:
        """Test that to_dict uses correct class name."""
        error = PublishError("Redis unavailable", details={"host": "localhost"})
        result = error.to_dict()
        assert result["error"] == "PublishError"


class TestAcknowledgeError:
    """Tests for AcknowledgeError."""

    def test_inherits_from_coordination_error(self) -> None:
        """Test inheritance chain."""
        error = AcknowledgeError("Failed to acknowledge")
        assert isinstance(error, CoordinationError)
        assert isinstance(error, ASDLCError)

    def test_to_dict_includes_correct_error_name(self) -> None:
        """Test that to_dict uses correct class name."""
        error = AcknowledgeError("Already acknowledged", details={"msg_id": "msg-456"})
        result = error.to_dict()
        assert result["error"] == "AcknowledgeError"


class TestPresenceError:
    """Tests for PresenceError."""

    def test_inherits_from_coordination_error(self) -> None:
        """Test inheritance chain."""
        error = PresenceError("Presence update failed")
        assert isinstance(error, CoordinationError)
        assert isinstance(error, ASDLCError)

    def test_to_dict_includes_correct_error_name(self) -> None:
        """Test that to_dict uses correct class name."""
        error = PresenceError("Instance not registered", details={"instance": "backend"})
        result = error.to_dict()
        assert result["error"] == "PresenceError"


class TestExceptionInteroperability:
    """Tests for exception interoperability and catching."""

    def test_catch_as_coordination_error(self) -> None:
        """Test that all coordination exceptions can be caught as CoordinationError."""
        exceptions = [
            MessageNotFoundError("not found"),
            PublishError("publish failed"),
            AcknowledgeError("ack failed"),
            PresenceError("presence failed"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except CoordinationError as e:
                assert e.message is not None
            except Exception:
                pytest.fail(f"{exc.__class__.__name__} not caught as CoordinationError")

    def test_catch_as_asdlc_error(self) -> None:
        """Test that all coordination exceptions can be caught as ASDLCError."""
        error = MessageNotFoundError("test")

        try:
            raise error
        except ASDLCError as e:
            assert isinstance(e, MessageNotFoundError)
