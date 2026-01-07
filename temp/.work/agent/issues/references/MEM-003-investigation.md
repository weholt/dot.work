# MEM-003 Investigation: Embedding vectors stored as Python lists

**Issue:** MEM-003@a7b8c9
**Started:** 2024-12-27T00:35:00Z
**Status:** In Progress

---

## Problem Analysis

**Root Cause:** Embedding vectors stored as Python `list[float]` instead of `np.ndarray`, causing 4-6x memory overhead.

### Location 1: `db.py` - Embedding class (line 91)

```python
@dataclass
class Embedding:
    vector: list[float]  # Python list has ~24 bytes/float vs 4 bytes for numpy
```

### Location 2: `db.py` - `_row_to_embedding()` (line 1133)

```python
vector = list(struct.unpack(f"<{dimensions}f", vector_blob))
```

This creates a Python list from the binary blob.

### Location 3: `search_semantic.py` - `cosine_similarity()` (line 57)

```python
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    # Pure Python loop over floats - slow and memory-heavy
```

---

## Memory Impact

| Embeddings | Dims | Numpy | Python List | Overhead |
|-----------|------|-------|-------------|----------|
| 1,000 | 384 | 1.5MB | 9MB | 6x |
| 10,000 | 768 | 30MB | 180MB | 6x |
| 100,000 | 1536 | 300MB | 3.6GB | 12x |

---

## Proposed Solution

### 1. Add numpy to dependencies

Check if numpy is already in `pyproject.toml`, if not add it.

### 2. Change Embedding.vector type

```python
import numpy as np
from typing import Any

@dataclass
class Embedding:
    vector: np.ndarray | Any  # Use numpy array
```

### 3. Update `_row_to_embedding()`

```python
def _row_to_embedding(self, row: sqlite3.Row) -> Embedding:
    import numpy as np

    dimensions = row["dimensions"]
    vector_blob = row["vector"]
    vector = np.frombuffer(vector_blob, dtype=np.float32)

    return Embedding(
        embedding_pk=row["embedding_pk"],
        full_id=row["full_id"],
        model=row["model"],
        dimensions=dimensions,
        vector=vector,
        created_at=row["created_at"],
    )
```

### 4. Update `cosine_similarity()`

```python
def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if vec_a.shape != vec_b.shape:
        raise ValueError(f"Vector dimensions must match: {vec_a.shape} != {vec_b.shape}")

    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))
```

### 5. Update query vector generation

Check where query vectors are created and ensure they use numpy arrays.

---

## Affected Files
- `pyproject.toml` (add numpy dependency)
- `src/dot_work/knowledge_graph/db.py` (Embedding class, _row_to_embedding)
- `src/dot_work/knowledge_graph/search_semantic.py` (cosine_similarity)

---

## Acceptance Criteria
- [ ] numpy added to dependencies
- [ ] Embedding.vector uses np.ndarray
- [ ] _row_to_embedding() uses np.frombuffer()
- [ ] cosine_similarity() uses numpy operations
- [ ] Memory usage per embedding reduced to ~4x file size
- [ ] All knowledge_graph tests still pass

---

## Next Steps
1. Add numpy to pyproject.toml
2. Update Embedding class
3. Update _row_to_embedding()
4. Update cosine_similarity()
5. Run validation
