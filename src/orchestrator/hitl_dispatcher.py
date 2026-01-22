"""HITL Dispatcher for gate request management.

Manages human-in-the-loop gate requests, decisions, and audit logging.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Awaitable, Any

import redis.asyncio as redis

from src.core.config import get_tenant_config
from src.core.events import ASDLCEvent, EventType
from src.core.exceptions import HITLError
from src.core.tenant import TenantContext
from src.orchestrator.evidence_bundle import (
    EvidenceBundle, GateType, GateStatus, validate_evidence_for_gate
)

logger = logging.getLogger(__name__)


@dataclass
class GateDecision:
    """Human decision on a gate request."""

    decision_id: str
    request_id: str
    approved: bool
    reviewer: str           # Human reviewer ID
    reason: str             # Explanation for decision
    decided_at: datetime
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, str]:
        """Serialize for Redis storage."""
        import json
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "approved": "true" if self.approved else "false",
            "reviewer": self.reviewer,
            "reason": self.reason,
            "decided_at": self.decided_at.isoformat(),
            "conditions": json.dumps(self.conditions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateDecision:
        """Deserialize from Redis format."""
        import json
        conditions_str = data.get("conditions", "[]")
        if isinstance(conditions_str, str):
            conditions = json.loads(conditions_str)
        else:
            conditions = conditions_str

        return cls(
            decision_id=data.get("decision_id", ""),
            request_id=data.get("request_id", ""),
            approved=data.get("approved", "false").lower() == "true",
            reviewer=data.get("reviewer", ""),
            reason=data.get("reason", ""),
            decided_at=datetime.fromisoformat(
                data.get("decided_at", datetime.now(timezone.utc).isoformat())
            ),
            conditions=conditions,
        )


@dataclass
class GateRequest:
    """Request for human approval at a gate."""

    request_id: str
    task_id: str
    session_id: str
    gate_type: GateType
    status: GateStatus
    evidence_bundle: EvidenceBundle
    requested_by: str
    requested_at: datetime
    expires_at: datetime | None = None
    decision: GateDecision | None = None

    def to_dict(self) -> dict[str, str]:
        """Serialize for Redis storage."""
        data = {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "gate_type": self.gate_type.value,
            "status": self.status.value,
            "evidence_bundle_id": self.evidence_bundle.bundle_id,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
        }

        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        evidence_bundle: EvidenceBundle | None = None,
    ) -> GateRequest:
        """Deserialize from Redis format."""
        # Create a placeholder bundle if not provided
        if evidence_bundle is None:
            evidence_bundle = EvidenceBundle.create(
                task_id=data.get("task_id", ""),
                gate_type=GateType(data.get("gate_type", "hitl_4_code")),
                git_sha="",
                items=[],
                summary="Placeholder",
            )
            evidence_bundle.bundle_id = data.get("evidence_bundle_id", "")

        expires_str = data.get("expires_at")
        expires_at = (
            datetime.fromisoformat(expires_str) if expires_str else None
        )

        return cls(
            request_id=data.get("request_id", ""),
            task_id=data.get("task_id", ""),
            session_id=data.get("session_id", ""),
            gate_type=GateType(data.get("gate_type", "hitl_4_code")),
            status=GateStatus(data.get("status", "pending")),
            evidence_bundle=evidence_bundle,
            requested_by=data.get("requested_by", ""),
            requested_at=datetime.fromisoformat(
                data.get("requested_at", datetime.now(timezone.utc).isoformat())
            ),
            expires_at=expires_at,
        )


class DecisionLogger:
    """Maintains audit trail of all gate decisions."""

    LOG_KEY_PREFIX = "asdlc:decision_log:"
    AUDIT_STREAM = "asdlc:audit"

    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client

    def _get_key(self, task_id: str) -> str:
        """Get tenant-prefixed key."""
        base_key = f"{self.LOG_KEY_PREFIX}{task_id}"

        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                tenant_id = TenantContext.get_current_tenant()
                return f"tenant:{tenant_id}:{base_key}"
            except Exception:
                return f"tenant:{tenant_config.default_tenant}:{base_key}"

        return base_key

    def _get_audit_stream(self) -> str:
        """Get tenant-prefixed audit stream."""
        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                tenant_id = TenantContext.get_current_tenant()
                return f"tenant:{tenant_id}:{self.AUDIT_STREAM}"
            except Exception:
                return f"tenant:{tenant_config.default_tenant}:{self.AUDIT_STREAM}"

        return self.AUDIT_STREAM

    async def log_request(self, request: GateRequest) -> None:
        """Log gate request creation."""
        import json

        entry = {
            "event": "gate_requested",
            "request_id": request.request_id,
            "task_id": request.task_id,
            "gate_type": request.gate_type.value,
            "requested_by": request.requested_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Append to task log
        key = self._get_key(request.task_id)
        await self.client.rpush(key, json.dumps(entry))

        # Append to audit stream
        await self.client.xadd(
            self._get_audit_stream(),
            entry,
            maxlen=100000,
        )

        logger.debug(f"Logged gate request: {request.request_id}")

    async def log_decision(
        self,
        request: GateRequest,
        decision: GateDecision,
    ) -> None:
        """Log gate decision with full context."""
        import json

        entry = {
            "event": "gate_decision",
            "request_id": request.request_id,
            "decision_id": decision.decision_id,
            "task_id": request.task_id,
            "gate_type": request.gate_type.value,
            "approved": "true" if decision.approved else "false",
            "reviewer": decision.reviewer,
            "reason": decision.reason,
            "timestamp": decision.decided_at.isoformat(),
        }

        # Append to task log
        key = self._get_key(request.task_id)
        await self.client.rpush(key, json.dumps(entry))

        # Append to audit stream
        await self.client.xadd(
            self._get_audit_stream(),
            entry,
            maxlen=100000,
        )

        logger.info(
            f"Logged gate decision: {decision.decision_id} "
            f"({'approved' if decision.approved else 'rejected'})"
        )

    async def get_task_history(self, task_id: str) -> list[dict]:
        """Get all gate decisions for a task."""
        import json

        key = self._get_key(task_id)
        entries = await self.client.lrange(key, 0, -1)

        return [json.loads(entry) for entry in entries]


class HITLDispatcher:
    """Manages HITL gate requests and decisions."""

    REQUEST_KEY_PREFIX = "asdlc:gate_request:"
    BUNDLE_KEY_PREFIX = "asdlc:evidence_bundle:"
    PENDING_SET = "asdlc:pending_gates"

    def __init__(
        self,
        redis_client: redis.Redis,
        event_publisher: Callable[[ASDLCEvent], Awaitable[str]],
        decision_logger: DecisionLogger,
    ):
        """Initialize the HITL dispatcher.

        Args:
            redis_client: Redis client for storage.
            event_publisher: Function to publish events.
            decision_logger: Logger for audit trail.
        """
        self.client = redis_client
        self.event_publisher = event_publisher
        self.decision_logger = decision_logger

    def _get_request_key(self, request_id: str) -> str:
        """Get tenant-prefixed request key."""
        base_key = f"{self.REQUEST_KEY_PREFIX}{request_id}"

        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                tenant_id = TenantContext.get_current_tenant()
                return f"tenant:{tenant_id}:{base_key}"
            except Exception:
                return f"tenant:{tenant_config.default_tenant}:{base_key}"

        return base_key

    def _get_bundle_key(self, bundle_id: str) -> str:
        """Get tenant-prefixed bundle key."""
        base_key = f"{self.BUNDLE_KEY_PREFIX}{bundle_id}"

        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                tenant_id = TenantContext.get_current_tenant()
                return f"tenant:{tenant_id}:{base_key}"
            except Exception:
                return f"tenant:{tenant_config.default_tenant}:{base_key}"

        return base_key

    def _get_pending_set(self) -> str:
        """Get tenant-prefixed pending set key."""
        tenant_config = get_tenant_config()
        if tenant_config.enabled:
            try:
                tenant_id = TenantContext.get_current_tenant()
                return f"tenant:{tenant_id}:{self.PENDING_SET}"
            except Exception:
                return f"tenant:{tenant_config.default_tenant}:{self.PENDING_SET}"

        return self.PENDING_SET

    async def request_gate(
        self,
        task_id: str,
        session_id: str,
        gate_type: GateType,
        evidence_bundle: EvidenceBundle,
        requested_by: str,
        ttl_seconds: int | None = None,
    ) -> GateRequest:
        """Create a gate request and publish event.

        Args:
            task_id: Task requesting gate.
            session_id: Session context.
            gate_type: Type of gate.
            evidence_bundle: Evidence for review.
            requested_by: Agent requesting gate.
            ttl_seconds: Optional TTL in seconds.

        Returns:
            The created gate request.
        """
        # Validate evidence
        validate_evidence_for_gate(evidence_bundle)

        now = datetime.now(timezone.utc)
        expires_at = None
        if ttl_seconds:
            from datetime import timedelta
            expires_at = now + timedelta(seconds=ttl_seconds)

        request = GateRequest(
            request_id=str(uuid.uuid4()),
            task_id=task_id,
            session_id=session_id,
            gate_type=gate_type,
            status=GateStatus.PENDING,
            evidence_bundle=evidence_bundle,
            requested_by=requested_by,
            requested_at=now,
            expires_at=expires_at,
        )

        # Store request
        request_key = self._get_request_key(request.request_id)
        await self.client.hset(request_key, mapping=request.to_dict())

        # Store evidence bundle
        bundle_key = self._get_bundle_key(evidence_bundle.bundle_id)
        await self.client.hset(bundle_key, mapping=evidence_bundle.to_dict())

        # Add to pending set (score = expires_at or max timestamp)
        score = expires_at.timestamp() if expires_at else float("inf")
        pending_set = self._get_pending_set()
        await self.client.zadd(pending_set, {request.request_id: score})

        # Log the request
        await self.decision_logger.log_request(request)

        # Publish event
        event = ASDLCEvent(
            event_type=EventType.GATE_REQUESTED,
            session_id=session_id,
            task_id=task_id,
            timestamp=now,
            metadata={
                "request_id": request.request_id,
                "gate_type": gate_type.value,
                "evidence_bundle_id": evidence_bundle.bundle_id,
            },
        )
        await self.event_publisher(event)

        logger.info(f"Created gate request: {request.request_id}")
        return request

    async def record_decision(
        self,
        request_id: str,
        approved: bool,
        reviewer: str,
        reason: str,
        conditions: list[str] | None = None,
    ) -> GateDecision:
        """Record human decision and publish event.

        Args:
            request_id: The request being decided.
            approved: Whether gate is approved.
            reviewer: Human reviewer identifier.
            reason: Explanation for decision.
            conditions: Optional approval conditions.

        Returns:
            The recorded decision.
        """
        # Get existing request
        request_key = self._get_request_key(request_id)
        data = await self.client.hgetall(request_key)

        if not data:
            raise HITLError(
                f"Gate request not found: {request_id}",
                details={"request_id": request_id},
            )

        request = GateRequest.from_dict(data)

        if request.status != GateStatus.PENDING:
            raise HITLError(
                f"Gate request is not pending: {request_id}",
                details={
                    "request_id": request_id,
                    "status": request.status.value,
                },
            )

        # Create decision
        now = datetime.now(timezone.utc)
        decision = GateDecision(
            decision_id=str(uuid.uuid4()),
            request_id=request_id,
            approved=approved,
            reviewer=reviewer,
            reason=reason,
            decided_at=now,
            conditions=conditions or [],
        )

        # Update request status
        new_status = GateStatus.APPROVED if approved else GateStatus.REJECTED
        await self.client.hset(request_key, "status", new_status.value)

        # Remove from pending set
        pending_set = self._get_pending_set()
        await self.client.zrem(pending_set, request_id)

        # Log decision
        request.status = new_status
        await self.decision_logger.log_decision(request, decision)

        # Publish event
        event_type = EventType.GATE_APPROVED if approved else EventType.GATE_REJECTED
        event = ASDLCEvent(
            event_type=event_type,
            session_id=request.session_id,
            task_id=request.task_id,
            timestamp=now,
            metadata={
                "request_id": request_id,
                "decision_id": decision.decision_id,
                "reviewer": reviewer,
                "reason": reason,
                "conditions": conditions or [],
            },
        )
        await self.event_publisher(event)

        logger.info(
            f"Recorded decision for {request_id}: "
            f"{'approved' if approved else 'rejected'}"
        )
        return decision

    async def get_pending_requests(
        self,
        gate_type: GateType | None = None,
    ) -> list[GateRequest]:
        """Get all pending gate requests.

        Args:
            gate_type: Optional filter by gate type.

        Returns:
            List of pending requests.
        """
        pending_set = self._get_pending_set()
        request_ids = await self.client.zrange(pending_set, 0, -1)

        requests = []
        for request_id in request_ids:
            request_key = self._get_request_key(request_id)
            data = await self.client.hgetall(request_key)

            if data:
                request = GateRequest.from_dict(data)
                if gate_type is None or request.gate_type == gate_type:
                    requests.append(request)

        return requests

    async def get_request_by_id(self, request_id: str) -> GateRequest | None:
        """Get a gate request by ID."""
        request_key = self._get_request_key(request_id)
        data = await self.client.hgetall(request_key)

        if not data:
            return None

        return GateRequest.from_dict(data)

    async def check_expired(self) -> list[GateRequest]:
        """Find and mark expired requests.

        Returns:
            List of expired requests.
        """
        now = datetime.now(timezone.utc)
        pending_set = self._get_pending_set()

        # Get requests with expiry <= now
        expired_ids = await self.client.zrangebyscore(
            pending_set, 0, now.timestamp()
        )

        expired = []
        for request_id in expired_ids:
            request_key = self._get_request_key(request_id)
            data = await self.client.hgetall(request_key)

            if data and data.get("status") == GateStatus.PENDING.value:
                # Mark as expired
                await self.client.hset(request_key, "status", GateStatus.EXPIRED.value)
                await self.client.zrem(pending_set, request_id)

                request = GateRequest.from_dict(data)
                request.status = GateStatus.EXPIRED
                expired.append(request)

                # Publish expired event
                event = ASDLCEvent(
                    event_type=EventType.GATE_EXPIRED,
                    session_id=request.session_id,
                    task_id=request.task_id,
                    timestamp=now,
                    metadata={"request_id": request_id},
                )
                await self.event_publisher(event)

                logger.warning(f"Gate request expired: {request_id}")

        return expired
