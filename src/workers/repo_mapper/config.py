"""Configuration for Repo Mapper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class RepoMapperConfig:
    """Configuration for the Repo Mapper service.

    Attributes:
        context_pack_dir: Directory for storing generated context packs
        ast_cache_ttl: TTL for AST context cache in seconds
        default_token_budget: Default maximum tokens for context packs
        max_dependency_depth: Maximum depth for dependency tracing
        min_relevance_score: Minimum relevance score to include content
        repo_path: Path to the repository being analyzed
    """

    context_pack_dir: Path
    ast_cache_ttl: int
    default_token_budget: int
    max_dependency_depth: int
    min_relevance_score: float
    repo_path: Path

    @classmethod
    def from_env(cls) -> RepoMapperConfig:
        """Create configuration from environment variables.

        Returns:
            RepoMapperConfig instance

        Environment Variables:
            CONTEXT_PACK_DIR: Output directory for context packs (default: context/packs)
            AST_CACHE_TTL: AST cache TTL in seconds (default: 3600)
            DEFAULT_TOKEN_BUDGET: Default token budget (default: 100000)
            MAX_DEPENDENCY_DEPTH: Max dependency depth (default: 3)
            MIN_RELEVANCE_SCORE: Min relevance score (default: 0.2)
            REPO_PATH: Repository path (default: current directory)
        """
        return cls(
            context_pack_dir=Path(
                os.getenv("CONTEXT_PACK_DIR", "context/packs")
            ),
            ast_cache_ttl=int(os.getenv("AST_CACHE_TTL", "3600")),
            default_token_budget=int(os.getenv("DEFAULT_TOKEN_BUDGET", "100000")),
            max_dependency_depth=int(os.getenv("MAX_DEPENDENCY_DEPTH", "3")),
            min_relevance_score=float(os.getenv("MIN_RELEVANCE_SCORE", "0.2")),
            repo_path=Path(os.getenv("REPO_PATH", ".")),
        )

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.ast_cache_ttl < 0:
            raise ValueError("ast_cache_ttl must be non-negative")

        if self.default_token_budget <= 0:
            raise ValueError("default_token_budget must be positive")

        if self.max_dependency_depth < 0:
            raise ValueError("max_dependency_depth must be non-negative")

        if not 0 <= self.min_relevance_score <= 1:
            raise ValueError("min_relevance_score must be between 0 and 1")


@lru_cache(maxsize=1)
def get_repo_mapper_config() -> RepoMapperConfig:
    """Get cached Repo Mapper configuration.

    Returns:
        RepoMapperConfig instance
    """
    return RepoMapperConfig.from_env()
