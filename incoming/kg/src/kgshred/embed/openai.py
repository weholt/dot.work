"""OpenAI-compatible embedding backend.

Provides embedding via OpenAI API or compatible endpoints (OpenRouter).
Requires API key for authentication.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from kgshred.embed.base import EmbedderConfig, EmbeddingError, RateLimitError


class OpenAIEmbedder:
    """OpenAI embedding backend.

    Works with OpenAI API and compatible endpoints like OpenRouter.

    Example:
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-..."
        )
        embedder = OpenAIEmbedder(config)
        vectors = embedder.embed(["Hello world"])
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: EmbedderConfig) -> None:
        """Initialize OpenAI embedder.

        Args:
            config: Embedder configuration.

        Raises:
            EmbeddingError: If API key is missing.
        """
        if not config.api_key:
            raise EmbeddingError("API key required for OpenAI backend")

        self._model = config.model
        self._api_key = config.api_key
        self._timeout = config.timeout
        self._batch_size = config.batch_size
        self._dimensions: int | None = None

        # Determine base URL
        if config.base_url:
            self._base_url = config.base_url.rstrip("/")
        elif config.backend == "openrouter":
            self._base_url = self.OPENROUTER_BASE_URL
        else:
            self._base_url = self.DEFAULT_BASE_URL

    @property
    def model(self) -> str:
        """Return the model name."""
        return self._model

    @property
    def dimensions(self) -> int | None:
        """Return embedding dimensions if known."""
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding fails.
            RateLimitError: If rate limit is exceeded.
        """
        if not texts:
            return []

        # Batch if needed
        if len(texts) <= self._batch_size:
            return self._embed_batch(texts)

        # Process in batches
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        url = f"{self._base_url}/embeddings"
        payload = {"model": self._model, "input": texts}

        return self._make_request(url, payload)

    def _make_request(self, url: str, payload: dict[str, Any]) -> list[list[float]]:
        """Make HTTP request to OpenAI API."""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        request = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                return self._parse_response(response_data)
        except urllib.error.HTTPError as e:
            self._handle_http_error(e)
        except urllib.error.URLError as e:
            raise EmbeddingError(f"Connection to OpenAI failed: {e}") from e
        except json.JSONDecodeError as e:
            raise EmbeddingError(f"Invalid JSON response from OpenAI: {e}") from e

        return []  # Unreachable, but satisfies type checker

    def _handle_http_error(self, error: urllib.error.HTTPError) -> None:
        """Handle HTTP errors from OpenAI API."""
        if error.code == 429:
            retry_after = error.headers.get("Retry-After")
            retry_seconds = float(retry_after) if retry_after else None
            raise RateLimitError(retry_seconds)
        elif error.code == 401:
            raise EmbeddingError("Invalid API key")
        elif error.code == 400:
            try:
                body = json.loads(error.read().decode("utf-8"))
                msg = body.get("error", {}).get("message", str(error))
            except (json.JSONDecodeError, AttributeError):
                msg = str(error)
            raise EmbeddingError(f"Bad request: {msg}")
        else:
            raise EmbeddingError(f"OpenAI API error: {error.code} {error.reason}")

    def _parse_response(self, data: dict[str, Any]) -> list[list[float]]:
        """Parse OpenAI API response."""
        # OpenAI returns {"data": [{"embedding": [...], "index": 0}, ...]}
        if "data" not in data:
            raise EmbeddingError(f"Unexpected response format: {data}")

        # Sort by index to maintain order
        sorted_data = sorted(data["data"], key=lambda x: x.get("index", 0))

        embeddings = []
        for item in sorted_data:
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise EmbeddingError(f"Invalid embedding in response: {item}")
            embeddings.append(embedding)

            # Track dimensions from first result
            if self._dimensions is None and embedding:
                self._dimensions = len(embedding)

        return embeddings
