"""Unit tests for Repo Mapper configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.workers.repo_mapper.config import RepoMapperConfig, get_repo_mapper_config


class TestRepoMapperConfig:
    """Tests for RepoMapperConfig."""

    def test_create_config(self):
        """Test creating a RepoMapperConfig instance."""
        config = RepoMapperConfig(
            context_pack_dir=Path("context/packs"),
            ast_cache_ttl=3600,
            default_token_budget=100000,
            max_dependency_depth=3,
            min_relevance_score=0.2,
            repo_path=Path("."),
        )

        assert config.context_pack_dir == Path("context/packs")
        assert config.ast_cache_ttl == 3600
        assert config.default_token_budget == 100000
        assert config.max_dependency_depth == 3
        assert config.min_relevance_score == 0.2
        assert config.repo_path == Path(".")

    def test_from_env_defaults(self, monkeypatch):
        """Test creating config from environment with defaults."""
        # Clear any existing env vars
        for key in [
            "CONTEXT_PACK_DIR",
            "AST_CACHE_TTL",
            "DEFAULT_TOKEN_BUDGET",
            "MAX_DEPENDENCY_DEPTH",
            "MIN_RELEVANCE_SCORE",
            "REPO_PATH",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = RepoMapperConfig.from_env()

        assert config.context_pack_dir == Path("context/packs")
        assert config.ast_cache_ttl == 3600
        assert config.default_token_budget == 100000
        assert config.max_dependency_depth == 3
        assert config.min_relevance_score == 0.2
        assert config.repo_path == Path(".")

    def test_from_env_custom_values(self, monkeypatch):
        """Test creating config from environment with custom values."""
        monkeypatch.setenv("CONTEXT_PACK_DIR", "/custom/path")
        monkeypatch.setenv("AST_CACHE_TTL", "7200")
        monkeypatch.setenv("DEFAULT_TOKEN_BUDGET", "50000")
        monkeypatch.setenv("MAX_DEPENDENCY_DEPTH", "5")
        monkeypatch.setenv("MIN_RELEVANCE_SCORE", "0.5")
        monkeypatch.setenv("REPO_PATH", "/repo")

        config = RepoMapperConfig.from_env()

        assert config.context_pack_dir == Path("/custom/path")
        assert config.ast_cache_ttl == 7200
        assert config.default_token_budget == 50000
        assert config.max_dependency_depth == 5
        assert config.min_relevance_score == 0.5
        assert config.repo_path == Path("/repo")

    def test_config_immutable(self):
        """Test that config is immutable (frozen dataclass)."""
        config = RepoMapperConfig(
            context_pack_dir=Path("test"),
            ast_cache_ttl=100,
            default_token_budget=1000,
            max_dependency_depth=1,
            min_relevance_score=0.1,
            repo_path=Path("."),
        )

        with pytest.raises(AttributeError):  # Frozen dataclass
            config.ast_cache_ttl = 200  # type: ignore[misc]


class TestRepoMapperConfigValidation:
    """Tests for configuration validation."""

    def test_negative_cache_ttl_fails(self):
        """Test that negative cache TTL raises error."""
        with pytest.raises(ValueError, match="ast_cache_ttl must be non-negative"):
            RepoMapperConfig(
                context_pack_dir=Path("test"),
                ast_cache_ttl=-1,
                default_token_budget=1000,
                max_dependency_depth=1,
                min_relevance_score=0.1,
                repo_path=Path("."),
            )

    def test_zero_token_budget_fails(self):
        """Test that zero token budget raises error."""
        with pytest.raises(ValueError, match="default_token_budget must be positive"):
            RepoMapperConfig(
                context_pack_dir=Path("test"),
                ast_cache_ttl=100,
                default_token_budget=0,
                max_dependency_depth=1,
                min_relevance_score=0.1,
                repo_path=Path("."),
            )

    def test_negative_dependency_depth_fails(self):
        """Test that negative dependency depth raises error."""
        with pytest.raises(
            ValueError, match="max_dependency_depth must be non-negative"
        ):
            RepoMapperConfig(
                context_pack_dir=Path("test"),
                ast_cache_ttl=100,
                default_token_budget=1000,
                max_dependency_depth=-1,
                min_relevance_score=0.1,
                repo_path=Path("."),
            )

    def test_relevance_score_out_of_range_fails(self):
        """Test that relevance score outside [0, 1] raises error."""
        with pytest.raises(
            ValueError, match="min_relevance_score must be between 0 and 1"
        ):
            RepoMapperConfig(
                context_pack_dir=Path("test"),
                ast_cache_ttl=100,
                default_token_budget=1000,
                max_dependency_depth=1,
                min_relevance_score=1.5,
                repo_path=Path("."),
            )


class TestGetRepoMapperConfig:
    """Tests for get_repo_mapper_config function."""

    def test_get_config_returns_config(self, monkeypatch):
        """Test that get_repo_mapper_config returns a RepoMapperConfig."""
        # Clear env
        for key in [
            "CONTEXT_PACK_DIR",
            "AST_CACHE_TTL",
            "DEFAULT_TOKEN_BUDGET",
            "MAX_DEPENDENCY_DEPTH",
            "MIN_RELEVANCE_SCORE",
            "REPO_PATH",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Clear cache
        get_repo_mapper_config.cache_clear()

        config = get_repo_mapper_config()
        assert isinstance(config, RepoMapperConfig)

    def test_get_config_cached(self, monkeypatch):
        """Test that get_repo_mapper_config caches the result."""
        # Clear env and cache
        for key in [
            "CONTEXT_PACK_DIR",
            "AST_CACHE_TTL",
            "DEFAULT_TOKEN_BUDGET",
            "MAX_DEPENDENCY_DEPTH",
            "MIN_RELEVANCE_SCORE",
            "REPO_PATH",
        ]:
            monkeypatch.delenv(key, raising=False)

        get_repo_mapper_config.cache_clear()

        config1 = get_repo_mapper_config()
        config2 = get_repo_mapper_config()

        assert config1 is config2  # Same object due to caching
