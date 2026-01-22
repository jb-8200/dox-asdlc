"""Configuration for KnowledgeStore backends.

Provides environment-based configuration for knowledge store connections.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeStoreConfig:
    """Configuration for knowledge store connection.

    Attributes:
        backend: Backend type: "chromadb" or "mock_anthology".
        host: Hostname of the knowledge store backend.
        port: Port number for the backend.
        collection_name: Name of the document collection.
        embedding_model: Name of the embedding model to use.
    """

    backend: str = "chromadb"
    host: str = "localhost"
    port: int = 8000
    collection_name: str = "asdlc_documents"
    embedding_model: str = "all-MiniLM-L6-v2"

    @classmethod
    def from_env(cls) -> KnowledgeStoreConfig:
        """Create configuration from environment variables.

        Environment variables:
            KNOWLEDGE_STORE_BACKEND: Backend type: chromadb or mock_anthology (default: chromadb)
            KNOWLEDGE_STORE_HOST: Backend hostname (default: localhost)
            KNOWLEDGE_STORE_PORT: Backend port (default: 8000)
            KNOWLEDGE_STORE_COLLECTION: Collection name (default: asdlc_documents)
            KNOWLEDGE_STORE_EMBEDDING_MODEL: Embedding model (default: all-MiniLM-L6-v2)

        Returns:
            KnowledgeStoreConfig instance with values from environment.
        """
        return cls(
            backend=os.getenv("KNOWLEDGE_STORE_BACKEND", "chromadb"),
            host=os.getenv("KNOWLEDGE_STORE_HOST", "localhost"),
            port=int(os.getenv("KNOWLEDGE_STORE_PORT", "8000")),
            collection_name=os.getenv(
                "KNOWLEDGE_STORE_COLLECTION", "asdlc_documents"
            ),
            embedding_model=os.getenv(
                "KNOWLEDGE_STORE_EMBEDDING_MODEL", "all-MiniLM-L6-v2"
            ),
        )

    @property
    def connection_url(self) -> str:
        """Get the connection URL for the backend.

        Returns:
            HTTP URL for connecting to the backend.
        """
        return f"http://{self.host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "backend": self.backend,
            "host": self.host,
            "port": self.port,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
        }
