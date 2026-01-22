"""Unit tests for KnowledgeStore factory function.

Tests factory pattern and singleton behavior.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.knowledge_store.config import KnowledgeStoreConfig


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client."""
    with patch(
        "src.infrastructure.knowledge_store.chromadb_store.chromadb.HttpClient"
    ) as mock_client:
        mock_collection = MagicMock()
        mock_collection.name = "test_collection"
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        mock_client.return_value.heartbeat.return_value = 123456
        yield mock_client


class TestGetKnowledgeStore:
    """Tests for get_knowledge_store factory function."""

    def test_factory_returns_knowledge_store(self, mock_chromadb) -> None:
        """Test factory returns KnowledgeStore instance."""
        from src.infrastructure.knowledge_store.factory import (
            get_knowledge_store,
            reset_knowledge_store,
        )

        reset_knowledge_store()

        store = get_knowledge_store()

        assert store is not None

    def test_factory_returns_singleton(self, mock_chromadb) -> None:
        """Test factory returns same instance on subsequent calls."""
        from src.infrastructure.knowledge_store.factory import (
            get_knowledge_store,
            reset_knowledge_store,
        )

        reset_knowledge_store()

        store1 = get_knowledge_store()
        store2 = get_knowledge_store()

        assert store1 is store2

    def test_factory_uses_config_from_env(self, mock_chromadb) -> None:
        """Test factory uses configuration from environment."""
        import os
        from unittest.mock import patch

        from src.infrastructure.knowledge_store.factory import (
            get_knowledge_store,
            reset_knowledge_store,
        )

        reset_knowledge_store()

        with patch.dict(
            os.environ,
            {
                "KNOWLEDGE_STORE_HOST": "custom-host",
                "KNOWLEDGE_STORE_PORT": "9999",
            },
        ):
            store = get_knowledge_store()

            assert store.config.host == "custom-host"
            assert store.config.port == 9999

    def test_factory_accepts_custom_config(self, mock_chromadb) -> None:
        """Test factory accepts custom configuration."""
        from src.infrastructure.knowledge_store.factory import (
            get_knowledge_store,
            reset_knowledge_store,
        )

        reset_knowledge_store()

        config = KnowledgeStoreConfig(
            host="custom-host",
            port=1234,
            collection_name="custom_collection",
        )

        store = get_knowledge_store(config=config)

        assert store.config.host == "custom-host"
        assert store.config.port == 1234
        assert store.config.collection_name == "custom_collection"


class TestResetKnowledgeStore:
    """Tests for reset_knowledge_store function."""

    def test_reset_clears_singleton(self, mock_chromadb) -> None:
        """Test reset_knowledge_store clears the singleton."""
        from src.infrastructure.knowledge_store.factory import (
            get_knowledge_store,
            reset_knowledge_store,
        )

        reset_knowledge_store()

        store1 = get_knowledge_store()
        reset_knowledge_store()
        store2 = get_knowledge_store()

        # After reset, should get new instance
        assert store1 is not store2
