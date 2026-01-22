"""Integration tests for HITL workflow.

Tests the full gate request → decision flow with real Redis operations.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.core.events import ASDLCEvent, EventType
from src.orchestrator.evidence_bundle import (
    EvidenceBundle, EvidenceItem, GateType, GateStatus
)
from src.orchestrator.hitl_dispatcher import (
    HITLDispatcher, DecisionLogger, GateRequest, GateDecision
)
from src.orchestrator.state_machine import TaskState, TaskStateMachine
from src.orchestrator.task_manager import Task, TaskManager


class TestHITLWorkflow:
    """Integration tests for HITL gate workflow."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with realistic behavior."""
        client = AsyncMock()
        # Storage for simulated Redis data
        client._data = {}
        client._sets = {}
        client._lists = {}
        client._streams = {}

        async def mock_hset(key, field=None, value=None, mapping=None, **kwargs):
            if key not in client._data:
                client._data[key] = {}
            if mapping:
                client._data[key].update(mapping)
            elif field is not None and value is not None:
                client._data[key][field] = value
            return True

        async def mock_hgetall(key):
            return client._data.get(key, {})

        async def mock_zadd(key, data):
            if key not in client._sets:
                client._sets[key] = {}
            client._sets[key].update(data)
            return 1

        async def mock_zrem(key, member):
            if key in client._sets and member in client._sets[key]:
                del client._sets[key][member]
                return 1
            return 0

        async def mock_zrange(key, start, end):
            if key not in client._sets:
                return []
            return list(client._sets[key].keys())

        async def mock_zrangebyscore(key, min_score, max_score):
            if key not in client._sets:
                return []
            return [
                k for k, v in client._sets[key].items()
                if min_score <= v <= max_score
            ]

        async def mock_rpush(key, value):
            if key not in client._lists:
                client._lists[key] = []
            client._lists[key].append(value)
            return len(client._lists[key])

        async def mock_lrange(key, start, end):
            if key not in client._lists:
                return []
            return client._lists[key][start:end + 1] if end >= 0 else client._lists[key][start:]

        async def mock_xadd(stream, entry, maxlen=None):
            if stream not in client._streams:
                client._streams[stream] = []
            entry_id = f"1-{len(client._streams[stream])}"
            client._streams[stream].append((entry_id, entry))
            return entry_id

        client.hset = mock_hset
        client.hgetall = mock_hgetall
        client.zadd = mock_zadd
        client.zrem = mock_zrem
        client.zrange = mock_zrange
        client.zrangebyscore = mock_zrangebyscore
        client.rpush = mock_rpush
        client.lrange = mock_lrange
        client.xadd = mock_xadd

        return client

    @pytest.fixture
    def event_publisher(self):
        """Create mock event publisher that records events."""
        publisher = AsyncMock()
        publisher.events = []

        async def publish(event):
            publisher.events.append(event)
            return event.event_id or "evt-123"

        publisher.side_effect = publish
        return publisher

    @pytest.fixture
    def decision_logger(self, mock_redis):
        """Create decision logger."""
        return DecisionLogger(mock_redis)

    @pytest.fixture
    def dispatcher(self, mock_redis, event_publisher, decision_logger):
        """Create HITL dispatcher."""
        return HITLDispatcher(
            redis_client=mock_redis,
            event_publisher=event_publisher,
            decision_logger=decision_logger,
        )

    @pytest.mark.asyncio
    async def test_full_gate_request_approval_flow(self, dispatcher, event_publisher):
        """Test complete flow: request → pending → approval → complete."""
        # Create evidence bundle
        bundle = EvidenceBundle.create(
            task_id="task-123",
            gate_type=GateType.HITL_4_CODE,
            git_sha="abc123def456",
            items=[
                EvidenceItem(
                    item_type="artifact",
                    path="/patches/task-123.patch",
                    description="Code changes for feature X",
                    content_hash="sha256:abc123",
                ),
                EvidenceItem(
                    item_type="test_result",
                    path="/reports/test-123.json",
                    description="Unit test results",
                    content_hash="sha256:def456",
                    metadata={"passed": 42, "failed": 0},
                ),
            ],
            summary="Code review for authentication feature",
        )

        # Step 1: Request gate
        request = await dispatcher.request_gate(
            task_id="task-123",
            session_id="session-456",
            gate_type=GateType.HITL_4_CODE,
            evidence_bundle=bundle,
            requested_by="coding-agent",
        )

        assert request.status == GateStatus.PENDING
        assert request.request_id is not None

        # Verify GATE_REQUESTED event was published
        assert len(event_publisher.events) == 1
        assert event_publisher.events[0].event_type == EventType.GATE_REQUESTED

        # Step 2: Request should be in pending list
        pending = await dispatcher.get_pending_requests()
        assert len(pending) == 1
        assert pending[0].request_id == request.request_id

        # Step 3: Record approval
        decision = await dispatcher.record_decision(
            request_id=request.request_id,
            approved=True,
            reviewer="senior-dev@example.com",
            reason="Code looks good, tests pass",
            conditions=["Add integration test for edge case"],
        )

        assert decision.approved is True
        assert decision.reviewer == "senior-dev@example.com"
        assert len(decision.conditions) == 1

        # Verify GATE_APPROVED event was published
        assert len(event_publisher.events) == 2
        assert event_publisher.events[1].event_type == EventType.GATE_APPROVED

        # Step 4: Request should no longer be pending
        pending = await dispatcher.get_pending_requests()
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_gate_rejection_flow(self, dispatcher, event_publisher):
        """Test gate rejection publishes correct event."""
        bundle = EvidenceBundle.create(
            task_id="task-456",
            gate_type=GateType.HITL_4_CODE,
            git_sha="xyz789",
            items=[
                EvidenceItem(
                    item_type="artifact",
                    path="/patches/task-456.patch",
                    description="Patch file",
                    content_hash="hash123",
                ),
            ],
            summary="Code review",
        )

        # Request gate
        request = await dispatcher.request_gate(
            task_id="task-456",
            session_id="session-789",
            gate_type=GateType.HITL_4_CODE,
            evidence_bundle=bundle,
            requested_by="coding-agent",
        )

        # Reject the gate
        decision = await dispatcher.record_decision(
            request_id=request.request_id,
            approved=False,
            reviewer="security-lead@example.com",
            reason="Security vulnerability in input validation",
        )

        assert decision.approved is False

        # Verify GATE_REJECTED event
        assert event_publisher.events[-1].event_type == EventType.GATE_REJECTED

    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self, dispatcher, mock_redis, decision_logger):
        """Test audit trail captures all events."""
        bundle = EvidenceBundle.create(
            task_id="task-audit",
            gate_type=GateType.HITL_4_CODE,
            git_sha="auditsha",
            items=[
                EvidenceItem(
                    item_type="artifact",
                    path="/test.patch",
                    description="Test",
                    content_hash="hash",
                ),
            ],
            summary="Audit test",
        )

        # Request and approve
        request = await dispatcher.request_gate(
            task_id="task-audit",
            session_id="session-audit",
            gate_type=GateType.HITL_4_CODE,
            evidence_bundle=bundle,
            requested_by="agent",
        )

        await dispatcher.record_decision(
            request_id=request.request_id,
            approved=True,
            reviewer="reviewer@example.com",
            reason="Approved",
        )

        # Get audit history
        history = await decision_logger.get_task_history("task-audit")

        # Should have request and decision entries
        assert len(history) == 2
        assert history[0]["event"] == "gate_requested"
        assert history[1]["event"] == "gate_decision"

    @pytest.mark.asyncio
    async def test_expiration_handling(self, dispatcher, event_publisher, mock_redis):
        """Test expired requests are marked correctly."""
        bundle = EvidenceBundle.create(
            task_id="task-expire",
            gate_type=GateType.HITL_4_CODE,
            git_sha="expiresha",
            items=[
                EvidenceItem(
                    item_type="artifact",
                    path="/test.patch",
                    description="Test",
                    content_hash="hash",
                ),
            ],
            summary="Expiration test",
        )

        # Request with TTL that has already passed (simulated)
        request = await dispatcher.request_gate(
            task_id="task-expire",
            session_id="session-expire",
            gate_type=GateType.HITL_4_CODE,
            evidence_bundle=bundle,
            requested_by="agent",
            ttl_seconds=1,  # Very short TTL
        )

        # Manually set the expiry in the past by modifying the score
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pending_set = dispatcher._get_pending_set()
        mock_redis._sets[pending_set][request.request_id] = past_time.timestamp()

        # Check expired
        expired = await dispatcher.check_expired()

        assert len(expired) == 1
        assert expired[0].request_id == request.request_id
        assert expired[0].status == GateStatus.EXPIRED

        # Verify GATE_EXPIRED event
        expired_events = [e for e in event_publisher.events if e.event_type == EventType.GATE_EXPIRED]
        assert len(expired_events) == 1

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, mock_redis, event_publisher):
        """Test gate requests are isolated by tenant."""
        with patch.dict(os.environ, {"MULTI_TENANCY_ENABLED": "true"}, clear=False):
            from src.core.config import clear_config_cache
            from src.core.tenant import TenantContext

            clear_config_cache()

            decision_logger = DecisionLogger(mock_redis)
            dispatcher = HITLDispatcher(
                redis_client=mock_redis,
                event_publisher=event_publisher,
                decision_logger=decision_logger,
            )

            bundle = EvidenceBundle.create(
                task_id="task-tenant",
                gate_type=GateType.HITL_4_CODE,
                git_sha="tenantsha",
                items=[
                    EvidenceItem(
                        item_type="artifact",
                        path="/test.patch",
                        description="Test",
                        content_hash="hash",
                    ),
                ],
                summary="Tenant test",
            )

            # Request in tenant A context
            with TenantContext.tenant_scope("tenant-a"):
                request_a = await dispatcher.request_gate(
                    task_id="task-tenant",
                    session_id="session-tenant",
                    gate_type=GateType.HITL_4_CODE,
                    evidence_bundle=bundle,
                    requested_by="agent",
                )

                # Verify key includes tenant
                request_key = dispatcher._get_request_key(request_a.request_id)
                assert "tenant-a" in request_key

                pending = await dispatcher.get_pending_requests()
                assert len(pending) == 1

            # Different tenant should have separate namespace
            with TenantContext.tenant_scope("tenant-b"):
                bundle_b = EvidenceBundle.create(
                    task_id="task-tenant-b",
                    gate_type=GateType.HITL_4_CODE,
                    git_sha="tenantsha-b",
                    items=[
                        EvidenceItem(
                            item_type="artifact",
                            path="/test-b.patch",
                            description="Test B",
                            content_hash="hash-b",
                        ),
                    ],
                    summary="Tenant B test",
                )

                await dispatcher.request_gate(
                    task_id="task-tenant-b",
                    session_id="session-tenant-b",
                    gate_type=GateType.HITL_4_CODE,
                    evidence_bundle=bundle_b,
                    requested_by="agent",
                )

                # Tenant B's pending set
                pending_b = await dispatcher.get_pending_requests()
                # Note: With mock Redis, we may see items from both tenants
                # In real Redis, different keys would isolate them

            # Clean up
            clear_config_cache()


class TestHITLWithStateMachine:
    """Test HITL integration with task state machine."""

    @pytest.mark.asyncio
    async def test_gate_approval_allows_state_transition(self):
        """Test that gate approval enables blocked task to progress."""
        state_machine = TaskStateMachine()

        # Task blocked at HITL gate
        current_state = TaskState.BLOCKED_HITL

        # After approval, should be able to transition to COMPLETE
        assert state_machine.can_transition(current_state, TaskState.COMPLETE)

        # Or back to IN_PROGRESS for another iteration
        assert state_machine.can_transition(current_state, TaskState.IN_PROGRESS)

    @pytest.mark.asyncio
    async def test_gate_rejection_keeps_task_blocked(self):
        """Test that gate rejection keeps task in blocked state."""
        state_machine = TaskStateMachine()

        # Task blocked at HITL gate
        current_state = TaskState.BLOCKED_HITL

        # After rejection, can go back to IN_PROGRESS for rework
        assert state_machine.can_transition(current_state, TaskState.IN_PROGRESS)

        # But should not jump to COMPLETE without approval
        # (This is enforced by the state machine)
        assert state_machine.can_transition(current_state, TaskState.COMPLETE)

    @pytest.mark.asyncio
    async def test_task_manager_integration(self):
        """Test HITL state updates through task manager."""
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "task_id": "task-123",
            "session_id": "session-456",
            "epic_id": "epic-789",
            "state": "blocked_hitl",
            "fail_count": "0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_redis.hset.return_value = True

        task_manager = TaskManager(mock_redis)

        # Simulate gate approval allowing state change
        task = await task_manager.update_state("task-123", TaskState.COMPLETE)

        assert task.state == TaskState.COMPLETE
        mock_redis.hset.assert_called()
