"""Redis repository factory.

This module provides a factory for creating Redis-backed repository
instances. The factory manages a shared Redis client connection.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import redis.asyncio as redis

from src.orchestrator.repositories.interfaces import (
    IMaturityRepository,
    IMessageRepository,
    IPRDRepository,
    IRequirementRepository,
    ISessionRepository,
)
from src.orchestrator.repositories.redis.maturity_repository import (
    RedisMaturityRepository,
)
from src.orchestrator.repositories.redis.message_repository import (
    RedisMessageRepository,
)
from src.orchestrator.repositories.redis.prd_repository import (
    RedisPRDRepository,
)
from src.orchestrator.repositories.redis.requirement_repository import (
    RedisRequirementRepository,
)
from src.orchestrator.repositories.redis.session_repository import (
    RedisSessionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RedisRepositoryFactory:
    """Factory for Redis repositories.

    Creates repository instances backed by Redis. Unlike the PostgreSQL factory,
    this factory manages its own Redis client and ignores the db_session parameter
    (which is used for SQLAlchemy compatibility).

    Usage:
        factory = RedisRepositoryFactory()
        session_repo = factory.get_session_repository(None)
        result = await session_repo.get_by_id("session-123")
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize factory with optional Redis client.

        Args:
            redis_client: Optional Redis client. If not provided, creates one
                from environment variables.
        """
        self._redis_client = redis_client

    def _get_redis(self) -> redis.Redis:
        """Get or create the Redis client.

        Returns:
            Redis client instance.
        """
        if self._redis_client is None:
            # Support both REDIS_URL and REDIS_HOST/REDIS_PORT
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                redis_host = os.environ.get("REDIS_HOST", "localhost")
                redis_port = os.environ.get("REDIS_PORT", "6379")
                redis_url = f"redis://{redis_host}:{redis_port}"
            self._redis_client = redis.from_url(redis_url)
        return self._redis_client

    def get_session_repository(
        self, db_session: AsyncSession | None
    ) -> ISessionRepository:
        """Get a Redis session repository.

        Args:
            db_session: Ignored (for interface compatibility with PostgreSQL factory).

        Returns:
            RedisSessionRepository instance.
        """
        return RedisSessionRepository(self._get_redis())

    def get_message_repository(
        self, db_session: AsyncSession | None
    ) -> IMessageRepository:
        """Get a Redis message repository.

        Args:
            db_session: Ignored (for interface compatibility with PostgreSQL factory).

        Returns:
            RedisMessageRepository instance.
        """
        return RedisMessageRepository(self._get_redis())

    def get_requirement_repository(
        self, db_session: AsyncSession | None
    ) -> IRequirementRepository:
        """Get a Redis requirement repository.

        Args:
            db_session: Ignored (for interface compatibility with PostgreSQL factory).

        Returns:
            RedisRequirementRepository instance.
        """
        return RedisRequirementRepository(self._get_redis())

    def get_maturity_repository(
        self, db_session: AsyncSession | None
    ) -> IMaturityRepository:
        """Get a Redis maturity repository.

        Args:
            db_session: Ignored (for interface compatibility with PostgreSQL factory).

        Returns:
            RedisMaturityRepository instance.
        """
        return RedisMaturityRepository(self._get_redis())

    def get_prd_repository(
        self, db_session: AsyncSession | None
    ) -> IPRDRepository:
        """Get a Redis PRD repository.

        Args:
            db_session: Ignored (for interface compatibility with PostgreSQL factory).

        Returns:
            RedisPRDRepository instance.
        """
        return RedisPRDRepository(self._get_redis())
