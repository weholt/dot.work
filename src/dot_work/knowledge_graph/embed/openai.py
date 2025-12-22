"""OpenAI embedding provider.

Uses the OpenAI API (or compatible endpoints like OpenRouter)
for generating embeddings.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from dot_work.knowledge_graph.embed.base import (
    Embedder,
    EmbedderConfig,
    EmbeddingError,
    RateLimitError,
)


class OpenAIEmbedder(Embedder):
    """Embedder using OpenAI's API.

    Supports OpenAI and compatible APIs (OpenRouter, Azure, etc.)
    through the base_url configuration option.

    Attributes:
        api_key: OpenAI API key.
        base_url: Base URL for the API.
        model: Model to use for embeddings.
    """

    DEFAULT_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "text-embedding-3-small"

    def __init__(self, config: EmbedderConfig) -> None:
        """Initialize OpenAI embedder.

        Args:
            config: Embedder configuration.

        Raises:
            EmbeddingError: If no API key is provided.
        """
        super().__init__(config)

        self.api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            msg = "OpenAI API key required (set OPENAI_API_KEY or pass api_key)"
            raise EmbeddingError(msg)

        # Handle OpenRouter-specific defaults
        if config.backend == "openrouter" and not config.base_url:
            self.base_url = "https://openrouter.ai/api/v1"
        else:
            url = config.base_url or self.DEFAULT_URL
            # Normalize URL by removing trailing slash
            self.base_url = url.rstrip("/")
        self.model = config.model or self.DEFAULT_MODEL
        self.dimensions = config.dimensions
        self.batch_size = config.batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API.

        Batches requests according to batch_size configuration.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding fails.
            RateLimitError: If rate limited.
        """
        results: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            results.extend(batch_embeddings)

        return results

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: Batch of text strings.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If request fails.
            RateLimitError: If rate limited.
        """
        payload: dict[str, Any] = {
            "input": texts,
            "model": self.model,
        }

        if self.dimensions:
            payload["dimensions"] = self.dimensions

        url = f"{self.base_url}/embeddings"
        data = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Add OpenRouter headers if using OpenRouter
        if "openrouter" in self.base_url:
            headers["HTTP-Referer"] = "https://github.com/kgshred/kgshred"
            headers["X-Title"] = "kgshred"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                return self._parse_response(result)
        except urllib.error.HTTPError as e:
            self._handle_http_error(e)
            raise  # Should not reach here
        except urllib.error.URLError as e:
            msg = f"Failed to connect to OpenAI API at {self.base_url}: {e}"
            raise EmbeddingError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON response from OpenAI: {e}"
            raise EmbeddingError(msg) from e

    def _parse_response(self, result: dict[str, Any]) -> list[list[float]]:
        """Parse OpenAI embeddings response.

        Args:
            result: API response.

        Returns:
            List of embedding vectors, sorted by index.

        Raises:
            EmbeddingError: If response format is invalid.
        """
        try:
            data = result["data"]
            # Sort by index to ensure correct order
            sorted_data = sorted(data, key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in sorted_data]

            # Update dimensions if not set
            if self.dimensions is None and embeddings:
                self.dimensions = len(embeddings[0])

            return embeddings
        except (KeyError, TypeError) as e:
            msg = f"Invalid OpenAI response format: {e}"
            raise EmbeddingError(msg) from e

    def _handle_http_error(self, error: urllib.error.HTTPError) -> None:
        """Handle HTTP errors from OpenAI API.

        Args:
            error: HTTP error.

        Raises:
            RateLimitError: If rate limited.
            EmbeddingError: For other errors.
        """
        if error.code == 429:
            # Rate limited
            retry_after = error.headers.get("Retry-After")
            retry_seconds = float(retry_after) if retry_after else 60.0
            msg = f"Rate limited by OpenAI, retry after {retry_seconds}s"
            raise RateLimitError(msg, retry_after=retry_seconds)

        try:
            body = json.loads(error.read().decode("utf-8"))
            error_msg = body.get("error", {}).get("message", str(error))
        except (json.JSONDecodeError, AttributeError):
            error_msg = str(error)

        msg = f"OpenAI API error ({error.code}): {error_msg}"
        raise EmbeddingError(msg) from error

    def embed_with_retry(
        self,
        texts: list[str],
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> list[list[float]]:
        """Embed texts with automatic retry on rate limit.

        Args:
            texts: List of text strings to embed.
            max_retries: Maximum number of retries.
            base_delay: Base delay between retries (exponential backoff).

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If all retries fail.
            RateLimitError: If still rate limited after retries.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return self.embed(texts)
            except RateLimitError as e:
                last_error = e
                if attempt < max_retries:
                    delay = e.retry_after or (base_delay * (2**attempt))
                    time.sleep(delay)
                continue

        if last_error:
            raise last_error
        msg = "Embedding failed after retries"
        raise EmbeddingError(msg)
