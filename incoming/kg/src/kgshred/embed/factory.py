"""Factory function for creating embedders.

Provides a unified interface to create embedder instances
based on configuration.
"""

from __future__ import annotations

from kgshred.embed.base import Embedder, EmbedderConfig, EmbeddingError


def get_embedder(config: EmbedderConfig) -> Embedder:
    """Create an embedder instance based on configuration.

    Args:
        config: Embedder configuration specifying backend and settings.

    Returns:
        An embedder instance implementing the Embedder protocol.

    Raises:
        EmbeddingError: If the backend is unknown or configuration is invalid.

    Example:
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = get_embedder(config)
        vectors = embedder.embed(["Hello world"])
    """
    backend = config.backend.lower()

    if backend == "ollama":
        from kgshred.embed.ollama import OllamaEmbedder

        return OllamaEmbedder(config)

    if backend in ("openai", "openrouter"):
        from kgshred.embed.openai import OpenAIEmbedder

        return OpenAIEmbedder(config)

    raise EmbeddingError(f"Unknown embedding backend: {config.backend}")
