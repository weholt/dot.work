"""Unit tests for embedding backends."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from dot_work.knowledge_graph.embed import (
    Embedder,
    EmbedderConfig,
    EmbeddingError,
    RateLimitError,
    get_embedder,
)
from dot_work.knowledge_graph.embed.ollama import OllamaEmbedder
from dot_work.knowledge_graph.embed.openai import OpenAIEmbedder


class TestEmbedderConfig:
    """Tests for EmbedderConfig dataclass."""

    def test_config_defaults(self) -> None:
        """Test default values are set correctly."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")

        assert config.backend == "ollama"
        assert config.model == "nomic-embed-text"
        assert config.api_key is None
        assert config.base_url is None
        assert config.timeout == 30.0
        assert config.batch_size == 32

    def test_config_custom_values(self) -> None:
        """Test custom values are preserved."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
            base_url="https://custom.api.com",
            timeout=60.0,
            batch_size=16,
        )

        assert config.api_key == "sk-test"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60.0
        assert config.batch_size == 16


class TestGetEmbedder:
    """Tests for get_embedder factory function."""

    def test_get_ollama_embedder(self) -> None:
        """Test creating Ollama embedder."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = get_embedder(config)

        assert isinstance(embedder, OllamaEmbedder)
        assert embedder.model == "nomic-embed-text"

    def test_get_openai_embedder(self) -> None:
        """Test creating OpenAI embedder."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = get_embedder(config)

        assert isinstance(embedder, OpenAIEmbedder)
        assert embedder.model == "text-embedding-3-small"

    def test_get_openrouter_embedder(self) -> None:
        """Test creating OpenRouter embedder uses OpenAI backend."""
        config = EmbedderConfig(
            backend="openrouter",
            model="openai/text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = get_embedder(config)

        assert isinstance(embedder, OpenAIEmbedder)

    def test_unknown_backend_raises(self) -> None:
        """Test unknown backend raises EmbeddingError."""
        config = EmbedderConfig(backend="unknown", model="model")

        with pytest.raises(EmbeddingError, match="Unknown embedding backend"):
            get_embedder(config)

    def test_embedder_protocol(self) -> None:
        """Test embedders implement Embedder protocol."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = get_embedder(config)

        assert isinstance(embedder, Embedder)


class TestOllamaEmbedder:
    """Tests for OllamaEmbedder."""

    def test_init_defaultbase_url(self) -> None:
        """Test default base URL is set."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        assert embedder.base_url == "http://localhost:11434"

    def test_init_custombase_url(self) -> None:
        """Test custom base URL is used."""
        config = EmbedderConfig(
            backend="ollama",
            model="nomic-embed-text",
            base_url="http://remote:11434",
        )
        embedder = OllamaEmbedder(config)

        assert embedder.base_url == "http://remote:11434"

    def test_model_property(self) -> None:
        """Test model property returns correct value."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        assert embedder.model == "nomic-embed-text"

    def test_dimensions_initially_none(self) -> None:
        """Test dimensions is None before first embedding."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        assert embedder.dimensions is None

    def test_embed_empty_list(self) -> None:
        """Test embedding empty list returns empty list."""
        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        result = embedder.embed([])

        assert result == []

    @patch("dot_work.knowledge_graph.embed.ollama.urllib.request.urlopen")
    def test_embed_single_text(self, mock_urlopen: MagicMock) -> None:
        """Test embedding single text."""
        # Mock response
        response_data = {"embeddings": [[0.1, 0.2, 0.3]]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        result = embedder.embed(["Hello world"])

        assert result == [[0.1, 0.2, 0.3]]
        assert embedder.dimensions == 3

    @patch("dot_work.knowledge_graph.embed.ollama.urllib.request.urlopen")
    def test_embed_multiple_texts(self, mock_urlopen: MagicMock) -> None:
        """Test embedding multiple texts."""
        # Mock responses for each text
        responses = [
            {"embeddings": [[0.1, 0.2, 0.3]]},
            {"embeddings": [[0.4, 0.5, 0.6]]},
        ]
        mock_responses: list[MagicMock] = []
        for resp in responses:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(resp).encode()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_responses.append(mock_resp)

        mock_urlopen.side_effect = mock_responses

        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        result = embedder.embed(["Hello", "World"])

        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    @patch("dot_work.knowledge_graph.embed.ollama.urllib.request.urlopen")
    def test_embed_legacy_response_format(self, mock_urlopen: MagicMock) -> None:
        """Test handling legacy Ollama response format."""
        # Legacy format uses "embedding" instead of "embeddings"
        response_data = {"embedding": [0.1, 0.2, 0.3]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = EmbedderConfig(backend="ollama", model="nomic-embed-text")
        embedder = OllamaEmbedder(config)

        result = embedder.embed(["Hello"])

        assert result == [[0.1, 0.2, 0.3]]


class TestOpenAIEmbedder:
    """Tests for OpenAIEmbedder."""

    def test_init_requires_api_key(self) -> None:
        """Test initialization requires API key."""
        config = EmbedderConfig(backend="openai", model="text-embedding-3-small")

        with pytest.raises(EmbeddingError, match="API key required"):
            OpenAIEmbedder(config)

    def test_init_defaultbase_url(self) -> None:
        """Test default OpenAI base URL is set."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        assert embedder.base_url == "https://api.openai.com/v1"

    def test_init_openrouterbase_url(self) -> None:
        """Test OpenRouter base URL is used for openrouter backend."""
        config = EmbedderConfig(
            backend="openrouter",
            model="openai/text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        assert embedder.base_url == "https://openrouter.ai/api/v1"

    def test_init_custombase_url(self) -> None:
        """Test custom base URL overrides defaults."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
            base_url="https://custom.api.com/",
        )
        embedder = OpenAIEmbedder(config)

        assert embedder.base_url == "https://custom.api.com"

    def test_model_property(self) -> None:
        """Test model property returns correct value."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        assert embedder.model == "text-embedding-3-small"

    def test_dimensions_initially_none(self) -> None:
        """Test dimensions is None before first embedding."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        assert embedder.dimensions is None

    def test_embed_empty_list(self) -> None:
        """Test embedding empty list returns empty list."""
        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        result = embedder.embed([])

        assert result == []

    @patch("dot_work.knowledge_graph.embed.openai.urllib.request.urlopen")
    def test_embed_single_text(self, mock_urlopen: MagicMock) -> None:
        """Test embedding single text via OpenAI API."""
        response_data = {
            "data": [{"embedding": [0.1, 0.2, 0.3], "index": 0}],
            "model": "text-embedding-3-small",
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        result = embedder.embed(["Hello world"])

        assert result == [[0.1, 0.2, 0.3]]
        assert embedder.dimensions == 3

    @patch("dot_work.knowledge_graph.embed.openai.urllib.request.urlopen")
    def test_embed_multiple_texts_batched(self, mock_urlopen: MagicMock) -> None:
        """Test embedding multiple texts in single batch."""
        response_data = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3], "index": 0},
                {"embedding": [0.4, 0.5, 0.6], "index": 1},
            ],
            "model": "text-embedding-3-small",
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        result = embedder.embed(["Hello", "World"])

        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    @patch("dot_work.knowledge_graph.embed.openai.urllib.request.urlopen")
    def test_embed_reorders_by_index(self, mock_urlopen: MagicMock) -> None:
        """Test embeddings are sorted by index from response."""
        # Response with out-of-order indices
        response_data = {
            "data": [
                {"embedding": [0.4, 0.5, 0.6], "index": 1},
                {"embedding": [0.1, 0.2, 0.3], "index": 0},
            ],
            "model": "text-embedding-3-small",
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )
        embedder = OpenAIEmbedder(config)

        result = embedder.embed(["Hello", "World"])

        # Should be sorted by index
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


class TestExceptions:
    """Tests for embedding exceptions."""

    def test_embedding_error_message(self) -> None:
        """Test EmbeddingError stores message."""
        error = EmbeddingError("Test error")

        assert str(error) == "Test error"

    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test RateLimitError stores retry_after."""
        error = RateLimitError("Rate limit exceeded", 60.0)

        assert error.retry_after == 60.0
        assert "Rate limit exceeded" in str(error)

    def test_rate_limit_error_without_retry_after(self) -> None:
        """Test RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded", None)

        assert error.retry_after is None


class TestOpenAIKeyMasking:
    """Tests for API key masking to prevent credential leakage (CR-077)."""

    def test_repr_masks_api_key(self) -> None:
        """Test that __repr__ masks the API key."""
        from dot_work.knowledge_graph.embed.openai import OpenAIEmbedder

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test1234567890abcdef",
        )
        embedder = OpenAIEmbedder(config)

        repr_str = repr(embedder)

        # Should contain model and base_url but NOT the full API key
        assert "text-embedding-3-small" in repr_str
        assert "api.openai.com" in repr_str
        assert "sk-test1234567890abcdef" not in repr_str
        # Should show masked version
        assert "sk-..." in repr_str or "..." in repr_str

    def test_str_masks_api_key(self) -> None:
        """Test that __str__ masks the API key."""
        from dot_work.knowledge_graph.embed.openai import OpenAIEmbedder

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-test1234567890abcdef",
        )
        embedder = OpenAIEmbedder(config)

        str_str = str(embedder)

        # Should NOT contain the full API key
        assert "sk-test1234567890abcdef" not in str_str
        # Should show masked version
        assert "sk-..." in str_str or "..." in str_str

    def test_repr_with_none_api_key(self) -> None:
        """Test that __repr__ handles None API key."""
        from dot_work.knowledge_graph.embed.openai import _mask_api_key

        result = _mask_api_key(None)
        assert result == "<none>"

    def test_repr_with_short_api_key(self) -> None:
        """Test that __repr__ handles very short API keys."""
        from dot_work.knowledge_graph.embed.openai import _mask_api_key

        result = _mask_api_key("abc")
        assert result == "***"

    def test_repr_with_custom_visible_chars(self) -> None:
        """Test that _mask_api_key respects visible parameter."""
        from dot_work.knowledge_graph.embed.openai import _mask_api_key

        key = "sk-test1234567890abcdef"
        result = _mask_api_key(key, visible=8)
        assert result == "sk-...90abcdef"
        assert "test123456789" not in result

    def test_exception_message_does_not_leak_key(self) -> None:
        """Test that error messages don't leak the API key."""
        from dot_work.knowledge_graph.embed.openai import OpenAIEmbedder

        config = EmbedderConfig(
            backend="openai",
            model="text-embedding-3-small",
            api_key="sk-super-secret-key-that-must-not-leak",
        )
        embedder = OpenAIEmbedder(config)

        # Create an error scenario (e.g., connection error)
        # The error message should NOT contain the API key
        try:
            # Force a connection error by using invalid URL
            embedder.base_url = "http://invalid.localdomain:9999"
            embedder.embed(["test"])
            pytest.fail("Expected EmbeddingError")
        except EmbeddingError as e:
            error_msg = str(e)
            # Verify the API key is NOT in the error message
            assert "sk-super-secret-key-that-must-not-leak" not in error_msg
            # The embedder repr in any logging should also be safe
            assert repr(embedder) not in error_msg or "sk-super-secret-key-that-must-not-leak" not in repr(
                embedder
            )
