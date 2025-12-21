"""Embedding backends for semantic search.

This module provides pluggable embedding backends for generating vector
embeddings from text. Supported backends:

- Ollama: Local embedding via HTTP (no API key required)
- OpenAI: OpenAI API embedding
- OpenRouter: OpenRouter API embedding (OpenAI-compatible)

Example:
    from kgshred.embed import get_embedder, EmbedderConfig

    config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
    embedder = get_embedder(config)
    vectors = embedder.embed(["Hello world", "Another text"])
"""

from kgshred.embed.base import (
    Embedder,
    EmbedderConfig,
    EmbeddingError,
    RateLimitError,
)
from kgshred.embed.factory import get_embedder

__all__ = [
    "Embedder",
    "EmbedderConfig",
    "EmbeddingError",
    "RateLimitError",
    "get_embedder",
]
