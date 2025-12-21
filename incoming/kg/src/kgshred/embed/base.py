"""Base classes and protocols for embedders.

Defines the Embedder protocol and common configuration/exception classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class EmbeddingError(Exception):
    """Raised when embedding operation fails."""

    pass


class RateLimitError(EmbeddingError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after}s"
        super().__init__(msg)


@dataclass
class EmbedderConfig:
    """Configuration for embedding backends.

    Attributes:
        backend: Backend name ("ollama", "openai", "openrouter").
        model: Model name for embedding (e.g., "nomic-embed-text").
        api_key: API key for authenticated backends.
        base_url: Override base URL for API requests.
        timeout: Request timeout in seconds.
        batch_size: Maximum texts per batch request.
    """

    backend: str = "ollama"
    model: str = "nomic-embed-text"
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 30.0
    batch_size: int = 32
    extra: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding backends.

    All embedding backends must implement this protocol.
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).
            Each vector is a list of floats.

        Raises:
            EmbeddingError: If embedding fails.
            RateLimitError: If rate limit is exceeded.
        """
        ...

    @property
    def model(self) -> str:
        """Return the model name used for embedding."""
        ...

    @property
    def dimensions(self) -> int | None:
        """Return embedding dimensions if known, None otherwise."""
        ...
