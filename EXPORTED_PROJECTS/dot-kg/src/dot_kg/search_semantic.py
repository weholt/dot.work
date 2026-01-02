"""Semantic search using brute-force cosine similarity.

Provides vector-based search over embedded content. Uses streaming batch
processing to bound memory usage for large knowledge bases.
"""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy import typing as npt

if TYPE_CHECKING:
    from dot_kg.db import Database, Embedding
    from dot_kg.embed import Embedder

from dot_kg.scope import ScopeFilter, build_scope_sets, node_matches_scope

logger = logging.getLogger(__name__)


# Configuration for memory-bounded search
DEFAULT_EMBEDDING_BATCH_SIZE = 1000
MAX_EMBEDDINGS_TO_SCAN = 100000  # Safety limit to prevent excessive scans


@dataclass
class SemanticResult:
    """Result from semantic search."""

    short_id: str
    full_id: str
    score: float  # Cosine similarity (-1 to 1)
    doc_id: str
    kind: str
    title: str | None


def cosine_similarity(
    vec_a: npt.NDArray[np.float32] | list[float], vec_b: npt.NDArray[np.float32] | list[float]
) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector as numpy array or list.
        vec_b: Second vector as numpy array or list.

    Returns:
        Cosine similarity in range [-1, 1].
        Returns 0.0 if either vector is zero-length.
    """
    # Convert lists to numpy arrays if needed
    if isinstance(vec_a, list):
        vec_a = np.array(vec_a, dtype=np.float32)
    if isinstance(vec_b, list):
        vec_b = np.array(vec_b, dtype=np.float32)

    if vec_a.shape != vec_b.shape:
        raise ValueError(f"Vector dimensions must match: {vec_a.shape} != {vec_b.shape}")

    # Use numpy operations for efficiency
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    # Handle zero vectors
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def semsearch(
    db: Database,
    embedder: Embedder,
    query: str,
    k: int = 10,
    scope: ScopeFilter | None = None,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    max_embeddings: int | None = MAX_EMBEDDINGS_TO_SCAN,
) -> list[SemanticResult]:
    """Search for semantically similar nodes.

    Uses fast vector indexing (sqlite-vec) when available, with automatic
    fallback to memory-bounded streaming brute-force cosine similarity search.
    The streaming approach bounds memory usage by processing embeddings in
    fixed-size batches, keeping only the top-k candidates in memory.

    Args:
        db: Database instance.
        embedder: Embedder to use for query embedding.
        query: Natural language query.
        k: Maximum number of results to return.
        scope: Optional scope filter to limit results.
        batch_size: Number of embeddings to process per batch (bounds memory).
        max_embeddings: Maximum total embeddings to scan (safety limit).

    Returns:
        List of SemanticResult objects, sorted by similarity (descending).

    Raises:
        ValueError: If scope specifies unknown project or topic.
    """
    if not query.strip():
        return []

    # Embed the query
    query_vectors = embedder.embed([query])
    if not query_vectors:
        return []

    query_vector = query_vectors[0]
    model = embedder.model

    # Pre-compute scope membership for filtering
    scope_members: set[str] | None = None
    scope_topics: set[str] | None = None
    exclude_topic_ids: set[str] = set()
    shared_topic_id: str | None = None

    if scope:
        scope_members, scope_topics, exclude_topic_ids, shared_topic_id = build_scope_sets(
            db, scope
        )

    # Try fast vector search if sqlite-vec is available
    if db.vec_available:
        try:
            vec_results = db.vec_search(model, query_vector, k * 2)  # Get more for filtering
        except (RuntimeError, ValueError):
            # Fall back to streaming search if vec_search fails
            vec_results = []

        if vec_results:
            # Convert vector search results to SemanticResult with scope filtering
            vec_search_results: list[SemanticResult] = []
            for full_id, score in vec_results[:k]:
                node = db.get_node_by_full_id(full_id)
                if node is None:
                    continue

                # Apply scope filtering
                if scope and not node_matches_scope(
                    db,
                    node,
                    scope_members,
                    scope_topics,
                    exclude_topic_ids,
                    shared_topic_id,
                ):
                    continue

                vec_search_results.append(
                    SemanticResult(
                        short_id=node.short_id,
                        full_id=full_id,
                        score=score,
                        doc_id=node.doc_id,
                        kind=node.kind,
                        title=node.title,
                    )
                )

                if len(vec_search_results) >= k:
                    break

            return vec_search_results

    # Fallback: Streaming brute-force search with top-k heap
    # Use a min-heap to track top-k results
    # Heap stores (score, index, embedding) to break ties when scores are equal
    # This avoids comparing Embedding objects directly
    top_k_heap: list[tuple[float, int, Embedding]] = []
    heap_index = 0  # Unique tie-breaker for equal scores

    # Stream embeddings in batches
    total_scanned = 0
    for batch in db.stream_embeddings_for_model(model, batch_size):
        # Check max embeddings limit
        if max_embeddings and total_scanned >= max_embeddings:
            break

        for emb in batch:
            # Check max embeddings limit
            if max_embeddings and total_scanned >= max_embeddings:
                break
            total_scanned += 1

            try:
                score = cosine_similarity(query_vector, emb.vector)

                # Maintain top-k using min-heap
                if len(top_k_heap) < k:
                    heapq.heappush(top_k_heap, (score, heap_index, emb))
                    heap_index += 1
                elif score > top_k_heap[0][0]:
                    heapq.heapreplace(top_k_heap, (score, heap_index, emb))
                    heap_index += 1

            except ValueError:
                # Dimension mismatch - skip this embedding
                continue

    if not top_k_heap:
        return []

    # Extract and sort results by score (descending)
    top_k_heap.sort(key=lambda x: x[0], reverse=True)

    # Convert to results with scope filtering
    results: list[SemanticResult] = []
    for score, _, emb in top_k_heap:
        # Look up node by full_id
        node = db.get_node_by_full_id(emb.full_id)
        if node is None:
            continue

        # Apply scope filtering
        if scope and not node_matches_scope(
            db,
            node,
            scope_members,
            scope_topics,
            exclude_topic_ids,
            shared_topic_id,
        ):
            continue

        results.append(
            SemanticResult(
                short_id=node.short_id,
                full_id=emb.full_id,
                score=score,
                doc_id=node.doc_id,
                kind=node.kind,
                title=node.title,
            )
        )

    return results


def embed_node(
    db: Database,
    embedder: Embedder,
    full_id: str,
    text: str,
) -> bool:
    """Embed a node and store the result.

    Args:
        db: Database instance.
        embedder: Embedder to use.
        full_id: Node full_id.
        text: Text content to embed.

    Returns:
        True if embedding was stored, False if embedding failed.
    """
    if not text.strip():
        return False

    try:
        vectors = embedder.embed([text])
        if not vectors:
            return False

        vector = vectors[0]
        db.store_embedding(full_id, embedder.model, vector)
        return True
    except Exception:
        return False


def embed_nodes_batch(
    db: Database,
    embedder: Embedder,
    nodes: list[tuple[str, str]],  # List of (full_id, text) tuples
) -> int:
    """Embed multiple nodes in a batch.

    Args:
        db: Database instance.
        embedder: Embedder to use.
        nodes: List of (full_id, text) tuples.

    Returns:
        Number of nodes successfully embedded.
    """
    if not nodes:
        return 0

    # Filter out empty texts and check for existing embeddings
    model = embedder.model
    to_embed: list[tuple[str, str]] = []

    for full_id, text in nodes:
        if not text.strip():
            continue
        # Check if already embedded
        existing = db.get_embedding(full_id, model)
        if existing is None:
            to_embed.append((full_id, text))

    if not to_embed:
        return 0

    # Batch embed
    texts = [text for _, text in to_embed]
    try:
        vectors = embedder.embed(texts)
    except Exception:
        return 0

    # Store results
    stored = 0
    for (full_id, _), vector in zip(to_embed, vectors, strict=True):
        try:
            db.store_embedding(full_id, model, vector)
            stored += 1
        except Exception:
            continue

    return stored
