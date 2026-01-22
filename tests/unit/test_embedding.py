"""Unit tests for embedding function wrapper.

Tests embedding generation with mocked sentence-transformers.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import EmbeddingError


# Create mock for sentence_transformers module
@pytest.fixture
def mock_sentence_transformers():
    """Mock sentence_transformers module."""
    mock_module = MagicMock()
    mock_model = MagicMock()
    mock_module.SentenceTransformer.return_value = mock_model

    with patch.dict(sys.modules, {"sentence_transformers": mock_module}):
        yield mock_module, mock_model


class TestEmbeddingFunction:
    """Tests for EmbeddingFunction class."""

    def test_embedding_function_creation(self, mock_sentence_transformers) -> None:
        """Test EmbeddingFunction can be created."""
        mock_module, mock_model = mock_sentence_transformers

        # Import after mocking
        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction(model_name="all-MiniLM-L6-v2")

        assert ef is not None
        mock_module.SentenceTransformer.assert_called_with("all-MiniLM-L6-v2")

    def test_embedding_function_default_model(self, mock_sentence_transformers) -> None:
        """Test EmbeddingFunction uses default model."""
        mock_module, mock_model = mock_sentence_transformers

        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction()

        mock_module.SentenceTransformer.assert_called_with("all-MiniLM-L6-v2")

    def test_embed_single_text(self, mock_sentence_transformers) -> None:
        """Test embedding a single text."""
        mock_module, mock_model = mock_sentence_transformers
        mock_model.encode.return_value = [[0.1] * 384]

        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction()
        result = ef.embed("Hello world")

        assert len(result) == 384
        mock_model.encode.assert_called_once()

    def test_embed_batch(self, mock_sentence_transformers) -> None:
        """Test embedding a batch of texts."""
        mock_module, mock_model = mock_sentence_transformers
        mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384]

        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction()
        result = ef.embed_batch(["Hello", "World"])

        assert len(result) == 2
        assert len(result[0]) == 384

    def test_embed_error_handling(self, mock_sentence_transformers) -> None:
        """Test embedding error raises EmbeddingError."""
        mock_module, mock_model = mock_sentence_transformers
        mock_model.encode.side_effect = Exception("Model error")

        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction()

        with pytest.raises(EmbeddingError) as exc_info:
            ef.embed("test")

        assert "Model error" in str(exc_info.value)

    def test_model_loading_error(self) -> None:
        """Test model loading error raises EmbeddingError."""
        mock_module = MagicMock()
        mock_module.SentenceTransformer.side_effect = Exception("Model not found")

        with patch.dict(sys.modules, {"sentence_transformers": mock_module}):
            # Need to reimport to pick up the mock
            import importlib
            import src.infrastructure.knowledge_store.embedding as emb_module
            importlib.reload(emb_module)

            with pytest.raises(EmbeddingError) as exc_info:
                emb_module.EmbeddingFunction(model_name="nonexistent-model")

            assert "Failed to load embedding model" in str(exc_info.value)


class TestEmbeddingDimensions:
    """Tests for embedding dimensions."""

    def test_embedding_returns_list(self, mock_sentence_transformers) -> None:
        """Test embedding returns Python list."""
        import numpy as np

        mock_module, mock_model = mock_sentence_transformers
        # Simulate numpy array return
        mock_model.encode.return_value = [np.array([0.1] * 384)]

        from src.infrastructure.knowledge_store.embedding import EmbeddingFunction

        ef = EmbeddingFunction()
        result = ef.embed("test")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
