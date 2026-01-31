"""Redis repository implementations.

This package contains Redis implementations of the repository interfaces
defined in src/orchestrator/repositories/interfaces.py.

These implementations provide backward compatibility with the existing
Redis-based storage while the project transitions to PostgreSQL.

Exports:
    RedisSessionRepository: Session persistence operations.
    RedisMessageRepository: Message persistence operations.
    RedisRequirementRepository: Requirement persistence operations.
    RedisMaturityRepository: Maturity state persistence operations.
    RedisPRDRepository: PRD draft and user story persistence operations.
    RedisRepositoryFactory: Factory for creating Redis repositories.
"""

from src.orchestrator.repositories.redis.factory import (
    RedisRepositoryFactory,
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

__all__ = [
    "RedisSessionRepository",
    "RedisMessageRepository",
    "RedisRequirementRepository",
    "RedisMaturityRepository",
    "RedisPRDRepository",
    "RedisRepositoryFactory",
]
