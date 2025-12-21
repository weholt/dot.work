"""Tests for semantic search using cosine similarity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from kgshred.db import Database, Node
from kgshred.search_semantic import (
    SemanticResult,
    cosine_similarity,
    embed_node,
    embed_nodes_batch,
    semsearch,
)


@dataclass
class MockEmbedder:
    """Mock embedder for testing."""

    model: str = "mock-model"
    dimensions: int = 3

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return simple mock embeddings based on text content."""
        result = []
        for text in texts:
            # Simple deterministic embedding based on text
            if "python" in text.lower():
                result.append([1.0, 0.0, 0.0])
            elif "javascript" in text.lower():
                result.append([0.0, 1.0, 0.0])
            elif "rust" in text.lower():
                result.append([0.0, 0.0, 1.0])
            else:
                # Default: mix based on text length
                n = len(text)
                result.append([float(n % 3), float(n % 5), float(n % 7)])
        return result


class FailingEmbedder:
    """Embedder that always fails."""

    model: str = "failing-model"
    dimensions: int = 3

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Always raises an exception."""
        raise RuntimeError("Embedding failed")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """Create a test database."""
    return Database(tmp_path / "test.sqlite")


@pytest.fixture
def embedder() -> MockEmbedder:
    """Create a mock embedder."""
    return MockEmbedder()


@pytest.fixture
def indexed_db(db: Database, embedder: MockEmbedder) -> Database:
    """Create a database with nodes and embeddings."""
    # Create document
    raw = b"# Python Guide\n\nLearn Python.\n\n# JavaScript Guide\n\nLearn JS.\n\n# Rust Guide\n\nLearn Rust."
    db.insert_document("doc1", "test.md", raw)

    # Create nodes
    nodes_data = [
        ("a" * 32, "AAAA", "Python Guide", 0, 30),
        ("b" * 32, "BBBB", "JavaScript Guide", 30, 60),
        ("c" * 32, "CCCC", "Rust Guide", 60, 90),
    ]

    for full_id, short_id, title, start, end in nodes_data:
        node = Node(
            node_pk=None,
            full_id=full_id,
            short_id=short_id,
            doc_id="doc1",
            kind="heading",
            title=title,
            level=1,
            start=start,
            end=end,
        )
        db.insert_node(node)
        # Store embedding
        vectors = embedder.embed([title])
        db.store_embedding(full_id, embedder.model, vectors[0])

    return db


class TestCosineSimilarity:
    """Tests for cosine_similarity function."""

    def test_identical_vectors(self) -> None:
        """Identical vectors have similarity 1.0."""
        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_opposite_vectors(self) -> None:
        """Opposite vectors have similarity -1.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [-1.0, 0.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_orthogonal_vectors(self) -> None:
        """Orthogonal vectors have similarity 0.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_zero_vector_a(self) -> None:
        """Zero vector A returns 0.0."""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_zero_vector_b(self) -> None:
        """Zero vector B returns 0.0."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [0.0, 0.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_both_zero_vectors(self) -> None:
        """Both zero vectors return 0.0."""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [0.0, 0.0, 0.0]
        assert cosine_similarity(vec_a, vec_b) == 0.0

    def test_dimension_mismatch_raises(self) -> None:
        """Dimension mismatch raises ValueError."""
        vec_a = [1.0, 2.0]
        vec_b = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="dimensions must match"):
            cosine_similarity(vec_a, vec_b)

    def test_normalized_vectors(self) -> None:
        """Normalized vectors work correctly."""
        import math

        # 45-degree angle in 2D
        vec_a = [1.0, 0.0]
        vec_b = [1.0 / math.sqrt(2), 1.0 / math.sqrt(2)]
        expected = 1.0 / math.sqrt(2)  # cos(45°)
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(expected)

    def test_high_dimensional_vectors(self) -> None:
        """High-dimensional vectors work correctly."""
        vec_a = [1.0] * 1000
        vec_b = [1.0] * 1000
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(1.0)


class TestSemsearch:
    """Tests for semsearch function."""

    def test_empty_query(self, indexed_db: Database, embedder: MockEmbedder) -> None:
        """Empty query returns empty results."""
        assert semsearch(indexed_db, embedder, "") == []
        assert semsearch(indexed_db, embedder, "   ") == []

    def test_finds_similar_nodes(
        self, indexed_db: Database, embedder: MockEmbedder
    ) -> None:
        """Search finds nodes with similar embeddings."""
        results = semsearch(indexed_db, embedder, "python programming")

        assert len(results) > 0
        # Python node should be first (highest similarity)
        assert results[0].title == "Python Guide"

    def test_returns_correct_result_type(
        self, indexed_db: Database, embedder: MockEmbedder
    ) -> None:
        """Results are SemanticResult objects with all fields."""
        results = semsearch(indexed_db, embedder, "python")

        assert len(results) > 0
        result = results[0]
        assert isinstance(result, SemanticResult)
        assert result.short_id == "AAAA"
        assert result.full_id == "a" * 32
        assert result.doc_id == "doc1"
        assert result.kind == "heading"
        assert result.title == "Python Guide"
        assert -1.0 <= result.score <= 1.0

    def test_respects_k_limit(
        self, indexed_db: Database, embedder: MockEmbedder
    ) -> None:
        """Search respects the k limit."""
        results = semsearch(indexed_db, embedder, "programming", k=2)
        assert len(results) <= 2

    def test_results_sorted_by_similarity(
        self, indexed_db: Database, embedder: MockEmbedder
    ) -> None:
        """Results are sorted by similarity descending."""
        results = semsearch(indexed_db, embedder, "test", k=10)

        if len(results) > 1:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_empty_corpus(self, db: Database, embedder: MockEmbedder) -> None:
        """Search on empty corpus returns empty results."""
        results = semsearch(db, embedder, "python")
        assert results == []

    def test_no_embeddings(self, db: Database, embedder: MockEmbedder) -> None:
        """Search with no embeddings returns empty results."""
        # Create document and nodes but no embeddings
        raw = b"# Test\n\nContent."
        db.insert_document("doc1", "test.md", raw)
        node = Node(
            node_pk=None,
            full_id="x" * 32,
            short_id="XXXX",
            doc_id="doc1",
            kind="heading",
            title="Test",
            level=1,
            start=0,
            end=20,
        )
        db.insert_node(node)

        results = semsearch(db, embedder, "test")
        assert results == []


class TestEmbedNode:
    """Tests for embed_node function."""

    def test_embeds_and_stores(self, db: Database, embedder: MockEmbedder) -> None:
        """embed_node creates and stores embedding."""
        # Create document and node
        raw = b"# Python Basics\n\nContent."
        db.insert_document("doc1", "test.md", raw)
        node = Node(
            node_pk=None,
            full_id="n" * 32,
            short_id="NNNN",
            doc_id="doc1",
            kind="heading",
            title="Python Basics",
            level=1,
            start=0,
            end=25,
        )
        db.insert_node(node)

        # Embed
        result = embed_node(db, embedder, "n" * 32, "Python Basics")
        assert result is True

        # Verify stored
        emb = db.get_embedding("n" * 32, embedder.model)
        assert emb is not None
        assert emb.vector == [1.0, 0.0, 0.0]  # MockEmbedder returns this for "python"

    def test_empty_text_returns_false(
        self, db: Database, embedder: MockEmbedder
    ) -> None:
        """Empty text returns False without storing."""
        result = embed_node(db, embedder, "x" * 32, "")
        assert result is False

        result = embed_node(db, embedder, "x" * 32, "   ")
        assert result is False

    def test_failing_embedder_returns_false(self, db: Database) -> None:
        """Failing embedder returns False without raising."""
        failing = FailingEmbedder()
        result = embed_node(db, failing, "x" * 32, "some text")
        assert result is False


class TestEmbedNodesBatch:
    """Tests for embed_nodes_batch function."""

    def test_embeds_multiple_nodes(
        self, db: Database, embedder: MockEmbedder
    ) -> None:
        """Batch embed creates embeddings for all nodes."""
        # Create document
        raw = b"# Python\n\n# JavaScript\n\n# Rust"
        db.insert_document("doc1", "test.md", raw)

        nodes = [
            ("a" * 32, "Python programming"),
            ("b" * 32, "JavaScript development"),
            ("c" * 32, "Rust systems"),
        ]

        count = embed_nodes_batch(db, embedder, nodes)
        assert count == 3

        # Verify all stored
        assert db.get_embedding("a" * 32, embedder.model) is not None
        assert db.get_embedding("b" * 32, embedder.model) is not None
        assert db.get_embedding("c" * 32, embedder.model) is not None

    def test_skips_existing_embeddings(
        self, db: Database, embedder: MockEmbedder
    ) -> None:
        """Batch embed skips nodes that already have embeddings."""
        # Pre-store one embedding
        db.store_embedding("a" * 32, embedder.model, [0.5, 0.5, 0.0])

        nodes = [
            ("a" * 32, "Python"),  # Already exists
            ("b" * 32, "JavaScript"),  # New
        ]

        count = embed_nodes_batch(db, embedder, nodes)
        assert count == 1  # Only one new

        # Original should be unchanged
        emb = db.get_embedding("a" * 32, embedder.model)
        assert emb is not None
        assert emb.vector == [0.5, 0.5, 0.0]

    def test_skips_empty_texts(self, db: Database, embedder: MockEmbedder) -> None:
        """Batch embed skips empty texts."""
        nodes = [
            ("a" * 32, "Python"),
            ("b" * 32, ""),  # Empty
            ("c" * 32, "   "),  # Whitespace only
        ]

        count = embed_nodes_batch(db, embedder, nodes)
        assert count == 1

    def test_empty_batch(self, db: Database, embedder: MockEmbedder) -> None:
        """Empty batch returns 0."""
        count = embed_nodes_batch(db, embedder, [])
        assert count == 0

    def test_all_skipped_returns_zero(
        self, db: Database, embedder: MockEmbedder
    ) -> None:
        """All nodes skipped returns 0."""
        # All empty texts
        nodes = [
            ("a" * 32, ""),
            ("b" * 32, "   "),
        ]

        count = embed_nodes_batch(db, embedder, nodes)
        assert count == 0

    def test_failing_embedder_returns_zero(self, db: Database) -> None:
        """Failing embedder returns 0 without raising."""
        failing = FailingEmbedder()
        nodes = [
            ("a" * 32, "Python"),
            ("b" * 32, "JavaScript"),
        ]

        count = embed_nodes_batch(db, failing, nodes)
        assert count == 0


class TestSemanticResult:
    """Tests for SemanticResult dataclass."""

    def test_dataclass_fields(self) -> None:
        """SemanticResult has correct fields."""
        result = SemanticResult(
            short_id="AAAA",
            full_id="a" * 32,
            score=0.95,
            doc_id="doc1",
            kind="heading",
            title="Test",
        )

        assert result.short_id == "AAAA"
        assert result.full_id == "a" * 32
        assert result.score == 0.95
        assert result.doc_id == "doc1"
        assert result.kind == "heading"
        assert result.title == "Test"

    def test_title_can_be_none(self) -> None:
        """Title can be None."""
        result = SemanticResult(
            short_id="AAAA",
            full_id="a" * 32,
            score=0.5,
            doc_id="doc1",
            kind="paragraph",
            title=None,
        )

        assert result.title is None
