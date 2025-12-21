"""Base classes and protocols for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class EmbeddingError(Exception):
    """Base exception for embedding errors."""


class RateLimitError(EmbeddingError):
    """Raised when rate limited by provider."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class EmbedderConfig:
    """Configuration for embedding providers.

    Attributes:
        provider: The embedding provider ('ollama' or 'openai').
        model: The model to use for embeddings.
        api_key: API key for providers that require it.
        base_url: Base URL for the API endpoint.
        dimensions: Output embedding dimensions (if supported).
        batch_size: Maximum batch size for embedding requests.
        extra: Additional provider-specific options.
    """

    provider: str = "ollama"
    model: str = "nomic-embed-text"
    api_key: str | None = None
    base_url: str | None = None
    dimensions: int | None = None
    batch_size: int = 100
    extra: dict[str, str] = field(default_factory=dict)


class Embedder(ABC):
    """Abstract base class for embedding providers.

    Subclasses must implement the embed() method to generate
    embeddings for a list of text strings.
    """

    def __init__(self, config: EmbedderConfig) -> None:
        """Initialize embedder with configuration.

        Args:
            config: Embedder configuration.
        """
        self.config = config
        self._model: str = config.model

    @property
    def model(self) -> str:
        """Return the model name."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model name."""
        self._model = value

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).

        Raises:
            EmbeddingError: If embedding fails.
            RateLimitError: If rate limited by provider.
        """

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector.
        """
        return self.embed([text])[0]
