"""Factory for creating embedding providers."""

from __future__ import annotations

from dot_kg.embed.base import Embedder, EmbedderConfig, EmbeddingError


def get_embedder(config: EmbedderConfig | None = None) -> Embedder:
    """Create an embedder instance based on configuration.

    Args:
        config: Embedder configuration. If None, uses defaults (Ollama).

    Returns:
        Configured Embedder instance.

    Raises:
        ValueError: If backend is not supported.
    """
    if config is None:
        config = EmbedderConfig()

    backend = config.backend.lower()

    if backend == "ollama":
        from dot_kg.embed.ollama import OllamaEmbedder

        return OllamaEmbedder(config)
    elif backend == "openai" or backend == "openrouter":
        from dot_kg.embed.openai import OpenAIEmbedder

        return OpenAIEmbedder(config)
    else:
        msg = f"Unknown embedding backend: {backend}"
        raise EmbeddingError(msg)
