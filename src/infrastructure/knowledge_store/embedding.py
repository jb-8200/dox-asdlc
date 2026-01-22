"""Embedding function wrapper for KnowledgeStore.

Provides embedding generation using sentence-transformers models.
"""

from __future__ import annotations

import logging
from typing import Any

from src.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# Default model for embeddings (384 dimensions)
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingFunction:
    """Wrapper for sentence-transformers embedding generation.

    Provides a simple interface for generating embeddings from text.
    Can be used to pre-compute embeddings before indexing documents.

    Attributes:
        model_name: Name of the sentence-transformers model.

    Example:
        ```python
        ef = EmbeddingFunction()
        embedding = ef.embed("Hello world")
        # embedding is a list of 384 floats

        # Batch embedding
        embeddings = ef.embed_batch(["Hello", "World"])
        ```
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        """Initialize embedding function with specified model.

        Args:
            model_name: Name of the sentence-transformers model to use.

        Raises:
            EmbeddingError: If model loading fails.
        """
        self.model_name = model_name

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise EmbeddingError(
                f"Failed to load embedding model: {e}",
                details={"model_name": model_name},
            ) from e

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            result = self._model.encode([text])
            # Convert numpy array to Python list
            return [float(x) for x in result[0]]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(
                f"Failed to generate embedding: {e}",
                details={"text_length": len(text)},
            ) from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors (each a list of floats).

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            results = self._model.encode(texts)
            # Convert numpy arrays to Python lists
            return [[float(x) for x in embedding] for embedding in results]
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise EmbeddingError(
                f"Failed to generate batch embeddings: {e}",
                details={"batch_size": len(texts)},
            ) from e

    @property
    def dimension(self) -> int:
        """Get the embedding dimension for this model.

        Returns:
            Integer dimension of the embedding vectors.
        """
        return self._model.get_sentence_embedding_dimension()
