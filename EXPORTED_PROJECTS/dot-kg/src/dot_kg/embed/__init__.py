"""Embedding backends for semantic search.

This module provides a pluggable embedding system with support
for multiple providers:

- Ollama: Local embeddings (default, no API key needed)
- OpenAI: OpenAI API embeddings
"""

from dot_kg.embed.base import (
    Embedder,
    EmbedderConfig,
    EmbeddingError,
    RateLimitError,
)
from dot_kg.embed.factory import get_embedder

__all__ = [
    "Embedder",
    "EmbedderConfig",
    "EmbeddingError",
    "RateLimitError",
    "get_embedder",
]
