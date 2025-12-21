"""Ollama embedding backend.

Provides embedding via local Ollama server using HTTP API.
No API key required - uses localhost:11434 by default.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from kgshred.embed.base import EmbedderConfig, EmbeddingError


class OllamaEmbedder:
    """Ollama embedding backend using local HTTP API.

    Ollama must be running locally with an embedding model pulled.

    Example:
        embedder = OllamaEmbedder(EmbedderConfig(model="nomic-embed-text"))
        vectors = embedder.embed(["Hello world"])
    """

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, config: EmbedderConfig) -> None:
        """Initialize Ollama embedder.

        Args:
            config: Embedder configuration.
        """
        self._model = config.model
        self._base_url = config.base_url or self.DEFAULT_BASE_URL
        self._timeout = config.timeout
        self._dimensions: int | None = None

    @property
    def model(self) -> str:
        """Return the model name."""
        return self._model

    @property
    def dimensions(self) -> int | None:
        """Return embedding dimensions if known."""
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Ollama API.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding fails.
        """
        if not texts:
            return []

        embeddings: list[list[float]] = []

        for text in texts:
            vector = self._embed_single(text)
            embeddings.append(vector)

            # Track dimensions from first result
            if self._dimensions is None and vector:
                self._dimensions = len(vector)

        return embeddings

    def _embed_single(self, text: str) -> list[float]:
        """Embed a single text."""
        url = f"{self._base_url}/api/embed"
        payload = {"model": self._model, "input": text}

        return self._make_request(url, payload)

    def _make_request(self, url: str, payload: dict[str, Any]) -> list[float]:
        """Make HTTP request to Ollama API."""
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        request = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                return self._parse_response(response_data)
        except urllib.error.URLError as e:
            raise EmbeddingError(f"Connection to Ollama failed: {e}") from e
        except json.JSONDecodeError as e:
            raise EmbeddingError(f"Invalid JSON response from Ollama: {e}") from e

    def _parse_response(self, data: dict[str, Any]) -> list[float]:
        """Parse Ollama API response."""
        # Ollama returns {"embeddings": [[...]]} for /api/embed
        if "embeddings" in data and data["embeddings"]:
            embeddings = data["embeddings"]
            if isinstance(embeddings, list) and embeddings:
                first = embeddings[0]
                if isinstance(first, list):
                    return first

        # Legacy format: {"embedding": [...]}
        if "embedding" in data:
            embedding = data["embedding"]
            if isinstance(embedding, list):
                return embedding

        raise EmbeddingError(f"Unexpected response format from Ollama: {data}")
