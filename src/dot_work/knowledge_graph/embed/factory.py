"""Factory for creating embedding providers."""

from __future__ import annotations

from dot_work.knowledge_graph.embed.base import Embedder, EmbedderConfig


def get_embedder(config: EmbedderConfig | None = None) -> Embedder:
    """Create an embedder instance based on configuration.

    Args:
        config: Embedder configuration. If None, uses defaults (Ollama).

    Returns:
        Configured Embedder instance.

    Raises:
        ValueError: If provider is not supported.
    """
    if config is None:
        config = EmbedderConfig()

    provider = config.provider.lower()

    if provider == "ollama":
        from dot_work.knowledge_graph.embed.ollama import OllamaEmbedder

        return OllamaEmbedder(config)
    elif provider == "openai":
        from dot_work.knowledge_graph.embed.openai import OpenAIEmbedder

        return OpenAIEmbedder(config)
    else:
        msg = f"Unknown embedding provider: {provider}"
        raise ValueError(msg)
