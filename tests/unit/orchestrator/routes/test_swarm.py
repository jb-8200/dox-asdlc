"""Unit tests for Swarm Review API endpoints.

Tests the REST API endpoints for parallel review swarm functionality (P04-F05).

Endpoints tested:
- POST /api/swarm/review - Trigger a swarm review
- GET /api/swarm/review/{swarm_id} - Get swarm status and results
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.workers.swarm.models import (
    ReviewerResult,
    ReviewFinding,
    Severity,
    SwarmSession,
    SwarmStatus,
    UnifiedReport,
)


@pytest.fixture
def mock_dispatcher() -> AsyncMock:
    """Create a mock SwarmDispatcher."""
    dispatcher = AsyncMock()
    return dispatcher


@pytest.fixture
def mock_session_manager() -> AsyncMock:
    """Create a mock SwarmSessionManager."""
    manager = AsyncMock()
    return manager


@pytest.fixture
def mock_redis_store() -> AsyncMock:
    """Create a mock SwarmRedisStore."""
    store = AsyncMock()
    store.get_all_results = AsyncMock(return_value={})
    return store


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock SwarmConfig."""
    config = MagicMock()
    config.max_concurrent_swarms = 5
    config.allowed_path_prefixes = ["src/", "docker/", "tests/"]
    config.default_reviewers = ["security", "performance", "style"]
    config.task_timeout_seconds = 300
    return config


@pytest.fixture
def mock_registry() -> MagicMock:
    """Create a mock ReviewerRegistry."""
    registry = MagicMock()
    registry.list_types.return_value = ["security", "performance", "style"]
    return registry


@pytest.fixture
def client(
    mock_dispatcher: AsyncMock,
    mock_session_manager: AsyncMock,
    mock_config: MagicMock,
    mock_registry: MagicMock,
    mock_redis_store: AsyncMock,
) -> TestClient:
    """Create test client with mocked dependencies."""
    from src.orchestrator.routes.swarm import (
        router,
        get_swarm_dispatcher,
        get_swarm_session_manager,
        get_swarm_config,
        get_reviewer_registry,
        get_swarm_redis_store,
    )

    app = FastAPI()
    app.include_router(router)

    # Override dependencies
    app.dependency_overrides[get_swarm_dispatcher] = lambda: mock_dispatcher
    app.dependency_overrides[get_swarm_session_manager] = lambda: mock_session_manager
    app.dependency_overrides[get_swarm_config] = lambda: mock_config
    app.dependency_overrides[get_reviewer_registry] = lambda: mock_registry
    app.dependency_overrides[get_swarm_redis_store] = lambda: mock_redis_store

    return TestClient(app)


class TestTriggerSwarmReview:
    """Tests for POST /api/swarm/review endpoint (T18)."""

    def test_trigger_swarm_review_returns_202(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that POST /api/swarm/review returns 202 with swarm_id and poll_url."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-abc12345"

        response = client.post(
            "/api/swarm/review",
            json={"target_path": "src/workers/"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "swarm_id" in data
        assert data["swarm_id"] == "swarm-abc12345"
        assert "status" in data
        assert data["status"] == "pending"
        assert "poll_url" in data
        assert "/api/swarm/review/swarm-abc12345" in data["poll_url"]

    def test_trigger_swarm_review_with_custom_reviewers(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test triggering swarm with custom reviewer types."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-def67890"

        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "reviewer_types": ["security", "performance"],
            },
        )

        assert response.status_code == 202
        mock_dispatcher.dispatch_swarm.assert_called_once()
        call_args = mock_dispatcher.dispatch_swarm.call_args
        assert call_args.kwargs.get("reviewer_types") == ["security", "performance"]

    def test_trigger_swarm_review_with_custom_timeout(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test triggering swarm with custom timeout."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-ghi11111"

        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "timeout_seconds": 60,
            },
        )

        assert response.status_code == 202
        mock_dispatcher.dispatch_swarm.assert_called_once()
        call_args = mock_dispatcher.dispatch_swarm.call_args
        assert call_args.kwargs.get("timeout_seconds") == 60

    def test_trigger_swarm_review_invalid_path_absolute(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that POST /api/swarm/review with absolute path returns 400."""
        response = client.post(
            "/api/swarm/review",
            json={"target_path": "/etc/passwd"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "absolute" in data["detail"].lower()

    def test_trigger_swarm_review_invalid_path_traversal(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that POST /api/swarm/review with path traversal returns 400."""
        response = client.post(
            "/api/swarm/review",
            json={"target_path": "src/../../../etc/passwd"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "traversal" in data["detail"].lower()

    def test_trigger_swarm_review_invalid_path_prefix(
        self, client: TestClient, mock_dispatcher: AsyncMock, mock_config: MagicMock
    ) -> None:
        """Test that POST /api/swarm/review with disallowed path returns 400."""
        mock_config.allowed_path_prefixes = ["src/", "docker/", "tests/"]

        response = client.post(
            "/api/swarm/review",
            json={"target_path": "etc/config.yaml"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "must start with" in data["detail"].lower()

    def test_trigger_swarm_review_invalid_reviewer_type(
        self, client: TestClient, mock_dispatcher: AsyncMock, mock_registry: MagicMock
    ) -> None:
        """Test that POST /api/swarm/review with unknown reviewer type returns 400."""
        mock_registry.list_types.return_value = ["security", "performance", "style"]

        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "reviewer_types": ["security", "unknown_reviewer"],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "unknown reviewer type" in data["detail"].lower()

    def test_trigger_swarm_review_timeout_below_minimum(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that POST /api/swarm/review with timeout below minimum returns 422."""
        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "timeout_seconds": 10,  # Below minimum of 30
            },
        )

        assert response.status_code == 422

    def test_trigger_swarm_review_timeout_above_maximum(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that POST /api/swarm/review with timeout above maximum returns 422."""
        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "timeout_seconds": 1000,  # Above maximum of 600
            },
        )

        assert response.status_code == 422


class TestTriggerSwarmReviewRateLimit:
    """Tests for rate limiting on POST /api/swarm/review (T20)."""

    def test_trigger_swarm_review_rate_limit_exceeded(
        self,
        mock_dispatcher: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_config: MagicMock,
        mock_registry: MagicMock,
    ) -> None:
        """Test that POST /api/swarm/review returns 429 when at capacity."""
        from src.orchestrator.routes.swarm import (
            router,
            get_swarm_dispatcher,
            get_swarm_session_manager,
            get_swarm_config,
            get_reviewer_registry,
            _active_swarms,
            _active_swarms_lock,
        )

        app = FastAPI()
        app.include_router(router)

        mock_config.max_concurrent_swarms = 2

        app.dependency_overrides[get_swarm_dispatcher] = lambda: mock_dispatcher
        app.dependency_overrides[get_swarm_session_manager] = lambda: mock_session_manager
        app.dependency_overrides[get_swarm_config] = lambda: mock_config
        app.dependency_overrides[get_reviewer_registry] = lambda: mock_registry

        client = TestClient(app)

        # Manually add swarms to simulate being at capacity
        _active_swarms.clear()
        _active_swarms.add("swarm-1")
        _active_swarms.add("swarm-2")

        try:
            response = client.post(
                "/api/swarm/review",
                json={"target_path": "src/workers/"},
            )

            assert response.status_code == 429
            data = response.json()
            assert "too many" in data["detail"].lower()
        finally:
            # Clean up
            _active_swarms.clear()


class TestGetSwarmStatus:
    """Tests for GET /api/swarm/review/{swarm_id} endpoint (T19)."""

    def test_get_swarm_status_pending(
        self, client: TestClient, mock_session_manager: AsyncMock
    ) -> None:
        """Test getting status for a pending swarm."""
        mock_session_manager.get_session.return_value = SwarmSession(
            id="swarm-abc12345",
            target_path="src/workers/",
            reviewers=["security", "performance", "style"],
            status=SwarmStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        response = client.get("/api/swarm/review/swarm-abc12345")

        assert response.status_code == 200
        data = response.json()
        assert data["swarm_id"] == "swarm-abc12345"
        assert data["status"] == "pending"
        assert "reviewers" in data

    def test_get_swarm_status_in_progress(
        self,
        client: TestClient,
        mock_session_manager: AsyncMock,
        mock_redis_store: AsyncMock,
    ) -> None:
        """Test getting status for an in-progress swarm."""
        mock_session = SwarmSession(
            id="swarm-abc12345",
            target_path="src/workers/",
            reviewers=["security", "performance", "style"],
            status=SwarmStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
        )
        mock_session_manager.get_session.return_value = mock_session

        # Results are fetched from the redis store, not session.results
        mock_redis_store.get_all_results.return_value = {
            "security": ReviewerResult(
                reviewer_type="security",
                status="success",
                findings=[],
                duration_seconds=5.5,
                files_reviewed=["src/workers/test.py"],
            ),
        }

        response = client.get("/api/swarm/review/swarm-abc12345")

        assert response.status_code == 200
        data = response.json()
        assert data["swarm_id"] == "swarm-abc12345"
        assert data["status"] == "in_progress"
        assert "security" in data["reviewers"]
        assert data["reviewers"]["security"]["status"] == "success"

    def test_get_swarm_status_complete(
        self, client: TestClient, mock_session_manager: AsyncMock
    ) -> None:
        """Test getting status for a completed swarm includes unified_report."""
        created_at = datetime.now(timezone.utc)
        unified_report = UnifiedReport(
            swarm_id="swarm-abc12345",
            target_path="src/workers/",
            created_at=created_at,
            reviewers_completed=["security", "performance", "style"],
            reviewers_failed=[],
            critical_findings=[],
            high_findings=[],
            medium_findings=[
                ReviewFinding(
                    id="finding-001",
                    reviewer_type="security",
                    severity=Severity.MEDIUM,
                    category="input_validation",
                    title="Missing input validation",
                    description="User input is not validated",
                    file_path="src/workers/handler.py",
                    line_start=42,
                    recommendation="Add input validation",
                    confidence=0.85,
                ),
            ],
            low_findings=[],
            info_findings=[],
            total_findings=1,
            findings_by_reviewer={"security": 1},
            findings_by_category={"input_validation": 1},
            duplicates_removed=0,
        )
        mock_session = SwarmSession(
            id="swarm-abc12345",
            target_path="src/workers/",
            reviewers=["security", "performance", "style"],
            status=SwarmStatus.COMPLETE,
            created_at=created_at,
            completed_at=datetime.now(timezone.utc),
            unified_report=unified_report,
        )
        mock_session_manager.get_session.return_value = mock_session

        response = client.get("/api/swarm/review/swarm-abc12345")

        assert response.status_code == 200
        data = response.json()
        assert data["swarm_id"] == "swarm-abc12345"
        assert data["status"] == "complete"
        assert data["unified_report"] is not None
        assert data["unified_report"]["total_findings"] == 1
        assert "duration_seconds" in data

    def test_get_swarm_status_failed(
        self, client: TestClient, mock_session_manager: AsyncMock
    ) -> None:
        """Test getting status for a failed swarm includes error message."""
        mock_session = SwarmSession(
            id="swarm-abc12345",
            target_path="src/workers/",
            reviewers=["security", "performance", "style"],
            status=SwarmStatus.FAILED,
            created_at=datetime.now(timezone.utc),
        )
        mock_session_manager.get_session.return_value = mock_session

        response = client.get("/api/swarm/review/swarm-abc12345")

        assert response.status_code == 200
        data = response.json()
        assert data["swarm_id"] == "swarm-abc12345"
        assert data["status"] == "failed"

    def test_get_swarm_status_not_found(
        self, client: TestClient, mock_session_manager: AsyncMock
    ) -> None:
        """Test GET /api/swarm/review/{unknown_id} returns 404."""
        mock_session_manager.get_session.return_value = None

        response = client.get("/api/swarm/review/swarm-unknown")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRouterConfiguration:
    """Tests for router configuration."""

    def test_router_has_correct_prefix(self) -> None:
        """Test that router has the correct API prefix."""
        from src.orchestrator.routes.swarm import router

        assert router.prefix == "/api/swarm"

    def test_router_has_correct_tags(self) -> None:
        """Test that router has the correct tags."""
        from src.orchestrator.routes.swarm import router

        assert "swarm" in router.tags


class TestInputValidation:
    """Tests for input validation (T20)."""

    def test_validate_target_path_empty(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that empty target_path returns 422."""
        response = client.post(
            "/api/swarm/review",
            json={"target_path": ""},
        )

        assert response.status_code == 422

    def test_validate_target_path_https_url_accepted(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that HTTPS URLs are accepted as external repo targets."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-url-https"

        response = client.post(
            "/api/swarm/review",
            json={"target_path": "https://github.com/org/repo"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["swarm_id"] == "swarm-url-https"

    def test_validate_target_path_http_url_accepted(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that HTTP URLs are accepted as external repo targets."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-url-http"

        response = client.post(
            "/api/swarm/review",
            json={"target_path": "http://internal-git.example.com/repo"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["swarm_id"] == "swarm-url-http"

    def test_validate_reviewer_types_empty_list(
        self, client: TestClient, mock_dispatcher: AsyncMock
    ) -> None:
        """Test that empty reviewer_types list uses defaults."""
        mock_dispatcher.dispatch_swarm.return_value = "swarm-abc12345"

        response = client.post(
            "/api/swarm/review",
            json={
                "target_path": "src/workers/",
                "reviewer_types": [],
            },
        )

        # Empty list should be treated as None (use defaults)
        assert response.status_code == 202
        mock_dispatcher.dispatch_swarm.assert_called_once()
        call_args = mock_dispatcher.dispatch_swarm.call_args
        # Empty list passed to dispatcher, which will use defaults
        assert call_args.kwargs.get("reviewer_types") == []
