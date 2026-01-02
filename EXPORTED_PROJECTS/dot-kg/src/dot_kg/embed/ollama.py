"""Ollama embedding provider.

Uses the Ollama API running locally for generating embeddings.
Default endpoint: http://localhost:11434
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any

from dot_kg.embed.base import Embedder, EmbedderConfig, EmbeddingError


class OllamaEmbedder(Embedder):
    """Embedder using Ollama's local API.

    Attributes:
        base_url: Base URL for the Ollama API.
        model: Model to use for embeddings.
    """

    DEFAULT_URL = "http://localhost:11434"

    def __init__(self, config: EmbedderConfig) -> None:
        """Initialize Ollama embedder.

        Args:
            config: Embedder configuration.
        """
        super().__init__(config)
        self.base_url = config.base_url or self.DEFAULT_URL
        self.model = config.model or "nomic-embed-text"
        self._dimensions = config.dimensions
        self._dimensions_lock = threading.Lock()
        self._dimensions_discovered = False

    @property
    def dimensions(self) -> int | None:
        """Get the embedding dimensions.

        Returns:
            Dimensions if known, None if not yet discovered.
        """
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Ollama.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding fails.
        """
        results: list[list[float]] = []

        for text in texts:
            payload = {
                "model": self.model,
                "prompt": text,
            }

            try:
                embedding = self._request_embedding(payload)
                # Update dimensions if not set (thread-safe)
                if not self._dimensions_discovered and self._dimensions is None:
                    with self._dimensions_lock:
                        if not self._dimensions_discovered and self._dimensions is None:
                            self._dimensions = len(embedding)
                            self._dimensions_discovered = True
                results.append(embedding)
            except Exception as e:
                raise EmbeddingError(f"Ollama embedding failed: {e}") from e

        return results

    def _request_embedding(self, payload: dict[str, Any]) -> list[float]:
        """Make embedding request to Ollama API.

        Args:
            payload: Request payload.

        Returns:
            Embedding vector.

        Raises:
            EmbeddingError: If request fails.
        """
        url = f"{self.base_url}/api/embeddings"
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Handle both modern (embeddings) and legacy (embedding) formats
                if "embeddings" in result:
                    embeddings = result["embeddings"]
                    if len(embeddings) != 1:
                        msg = f"Expected single embedding, got {len(embeddings)}"
                        raise EmbeddingError(msg) from None
                    return embeddings[0]
                elif "embedding" in result:
                    return result["embedding"]
                else:
                    msg = "Ollama response missing 'embedding' or 'embeddings' field"
                    raise EmbeddingError(msg) from None
        except urllib.error.URLError as e:
            msg = f"Failed to connect to Ollama at {self.base_url}: {e}"
            raise EmbeddingError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON response from Ollama: {e}"
            raise EmbeddingError(msg) from e
        except KeyError:
            msg = "Ollama response missing 'embedding' field"
            raise EmbeddingError(msg) from None
