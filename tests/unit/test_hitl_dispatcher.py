"""Unit tests for HITL dispatcher.

Tests GateRequest, GateDecision, and HITLDispatcher functionality.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.evidence_bundle import (
    EvidenceBundle, EvidenceItem, GateType, GateStatus
)


class TestGateRequest:
    """Tests for GateRequest model."""

    def test_create_gate_request(self):
        """GateRequest can be created."""
        from src.orchestrator.hitl_dispatcher import GateRequest

        now = datetime.now(timezone.utc)
        bundle = EvidenceBundle.create(
            task_id="task-123",
            gate_type=GateType.HITL_4_CODE,
            git_sha="sha456",
            items=[],
            summary="Test",
        )

        request = GateRequest(
            request_id="req-001",
            task_id="task-123",
            session_id="session-456",
            gate_type=GateType.HITL_4_CODE,
            status=GateStatus.PENDING,
            evidence_bundle=bundle,
            requested_by="coding-agent",
            requested_at=now,
        )

        assert request.request_id == "req-001"
        assert request.status == GateStatus.PENDING
        assert request.decision is None

    def test_gate_request_serialization(self):
        """GateRequest can be serialized."""
        from src.orchestrator.hitl_dispatcher import GateRequest

        now = datetime.now(timezone.utc)
        bundle = EvidenceBundle.create(
            task_id="task-123",
            gate_type=GateType.HITL_4_CODE,
            git_sha="sha456",
            items=[],
            summary="Test",
        )

        request = GateRequest(
            request_id="req-001",
            task_id="task-123",
            session_id="session-456",
            gate_type=GateType.HITL_4_CODE,
            status=GateStatus.PENDING,
            evidence_bundle=bundle,
            requested_by="coding-agent",
            requested_at=now,
        )

        data = request.to_dict()

        assert data["request_id"] == "req-001"
        assert data["status"] == "pending"
        assert data["gate_type"] == "hitl_4_code"


class TestGateDecision:
    """Tests for GateDecision model."""

    def test_create_gate_decision(self):
        """GateDecision can be created."""
        from src.orchestrator.hitl_dispatcher import GateDecision

        now = datetime.now(timezone.utc)
        decision = GateDecision(
            decision_id="dec-001",
            request_id="req-001",
            approved=True,
            reviewer="john@example.com",
            reason="Looks good!",
            decided_at=now,
        )

        assert decision.approved is True
        assert decision.reviewer == "john@example.com"

    def test_conditional_approval(self):
        """Decision can have conditions."""
        from src.orchestrator.hitl_dispatcher import GateDecision

        decision = GateDecision(
            decision_id="dec-001",
            request_id="req-001",
            approved=True,
            reviewer="john@example.com",
            reason="Approved with conditions",
            decided_at=datetime.now(timezone.utc),
            conditions=["Add more tests", "Update documentation"],
        )

        assert len(decision.conditions) == 2


class TestHITLDispatcher:
    """Tests for HITLDispatcher class."""

    @pytest.mark.asyncio
    async def test_request_gate_creates_request(self):
        """request_gate creates and stores request."""
        from src.orchestrator.hitl_dispatcher import HITLDispatcher

        mock_client = AsyncMock()
        mock_client.hset.return_value = True
        mock_client.zadd.return_value = True
        mock_publisher = AsyncMock()
        mock_logger = AsyncMock()

        dispatcher = HITLDispatcher(
            redis_client=mock_client,
            event_publisher=mock_publisher,
            decision_logger=mock_logger,
        )

        bundle = EvidenceBundle.create(
            task_id="task-123",
            gate_type=GateType.HITL_4_CODE,
            git_sha="sha456",
            items=[
                EvidenceItem(
                    item_type="artifact",
                    path="/test.patch",
                    description="Test",
                    content_hash="hash",
                ),
            ],
            summary="Test bundle",
        )

        request = await dispatcher.request_gate(
            task_id="task-123",
            session_id="session-456",
            gate_type=GateType.HITL_4_CODE,
            evidence_bundle=bundle,
            requested_by="coding-agent",
        )

        assert request.status == GateStatus.PENDING
        mock_client.hset.assert_called()
        mock_publisher.assert_called()

    @pytest.mark.asyncio
    async def test_record_decision_updates_status(self):
        """record_decision updates request status."""
        from src.orchestrator.hitl_dispatcher import HITLDispatcher, GateRequest

        now = datetime.now(timezone.utc)
        bundle = EvidenceBundle.create(
            task_id="task-123",
            gate_type=GateType.HITL_4_CODE,
            git_sha="sha456",
            items=[],
            summary="Test",
        )

        existing_request = GateRequest(
            request_id="req-001",
            task_id="task-123",
            session_id="session-456",
            gate_type=GateType.HITL_4_CODE,
            status=GateStatus.PENDING,
            evidence_bundle=bundle,
            requested_by="coding-agent",
            requested_at=now,
        )

        mock_client = AsyncMock()
        mock_client.hgetall.return_value = existing_request.to_dict()
        mock_client.hset.return_value = True
        mock_client.zrem.return_value = 1
        mock_publisher = AsyncMock()
        mock_logger = AsyncMock()

        dispatcher = HITLDispatcher(
            redis_client=mock_client,
            event_publisher=mock_publisher,
            decision_logger=mock_logger,
        )

        decision = await dispatcher.record_decision(
            request_id="req-001",
            approved=True,
            reviewer="jane@example.com",
            reason="Approved!",
        )

        assert decision.approved is True
        mock_publisher.assert_called()
        mock_logger.log_decision.assert_called()

    @pytest.mark.asyncio
    async def test_get_pending_requests(self):
        """get_pending_requests returns pending only."""
        from src.orchestrator.hitl_dispatcher import HITLDispatcher

        mock_client = AsyncMock()
        mock_client.zrange.return_value = ["req-001", "req-002"]
        mock_client.hgetall.side_effect = [
            {
                "request_id": "req-001",
                "task_id": "task-1",
                "session_id": "session-1",
                "gate_type": "hitl_4_code",
                "status": "pending",
                "evidence_bundle_id": "bundle-1",
                "requested_by": "agent",
                "requested_at": "2026-01-22T10:00:00+00:00",
            },
            {
                "request_id": "req-002",
                "task_id": "task-2",
                "session_id": "session-1",
                "gate_type": "hitl_4_code",
                "status": "pending",
                "evidence_bundle_id": "bundle-2",
                "requested_by": "agent",
                "requested_at": "2026-01-22T10:01:00+00:00",
            },
        ]

        dispatcher = HITLDispatcher(
            redis_client=mock_client,
            event_publisher=AsyncMock(),
            decision_logger=AsyncMock(),
        )

        requests = await dispatcher.get_pending_requests()

        assert len(requests) == 2

    @pytest.mark.asyncio
    async def test_check_expired_marks_expired(self):
        """check_expired marks expired requests."""
        from src.orchestrator.hitl_dispatcher import HITLDispatcher

        # Request that expired an hour ago
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)

        mock_client = AsyncMock()
        mock_client.zrangebyscore.return_value = ["req-001"]
        mock_client.hgetall.return_value = {
            "request_id": "req-001",
            "task_id": "task-1",
            "session_id": "session-1",
            "gate_type": "hitl_4_code",
            "status": "pending",
            "evidence_bundle_id": "bundle-1",
            "requested_by": "agent",
            "requested_at": "2026-01-22T10:00:00+00:00",
            "expires_at": expired_time.isoformat(),
        }
        mock_client.hset.return_value = True
        mock_client.zrem.return_value = 1

        mock_publisher = AsyncMock()

        dispatcher = HITLDispatcher(
            redis_client=mock_client,
            event_publisher=mock_publisher,
            decision_logger=AsyncMock(),
        )

        expired = await dispatcher.check_expired()

        assert len(expired) == 1
        mock_client.hset.assert_called()


class TestTenantIsolation:
    """Tests for tenant isolation in HITL dispatcher."""

    @pytest.mark.asyncio
    async def test_request_uses_tenant_prefix(self):
        """Gate requests use tenant-prefixed keys."""
        from src.orchestrator.hitl_dispatcher import HITLDispatcher
        from src.core.tenant import TenantContext
        from src.core.config import clear_config_cache

        mock_client = AsyncMock()
        mock_client.hset.return_value = True
        mock_client.zadd.return_value = True

        with patch.dict(os.environ, {"MULTI_TENANCY_ENABLED": "true"}, clear=False):
            clear_config_cache()

            dispatcher = HITLDispatcher(
                redis_client=mock_client,
                event_publisher=AsyncMock(),
                decision_logger=AsyncMock(),
            )

            bundle = EvidenceBundle.create(
                task_id="task-123",
                gate_type=GateType.HITL_4_CODE,
                git_sha="sha456",
                items=[
                    EvidenceItem(
                        item_type="artifact",
                        path="/test.patch",
                        description="Test",
                        content_hash="hash",
                    ),
                ],
                summary="Test",
            )

            with TenantContext.tenant_scope("acme-corp"):
                await dispatcher.request_gate(
                    task_id="task-123",
                    session_id="session-456",
                    gate_type=GateType.HITL_4_CODE,
                    evidence_bundle=bundle,
                    requested_by="agent",
                )

            call_args = mock_client.hset.call_args
            key = call_args.args[0]
            assert "acme-corp" in key
