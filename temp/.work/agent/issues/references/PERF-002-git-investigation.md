# PERF-002 Investigation: O(n²) algorithm in _get_commit_branch()

**Issue:** PERF-002@g2h3i4
**Started:** 2025-12-27T14:00:00Z
**Status:** In Progress

---

## Problem Analysis

**Location:** `src/dot_work/git/services/git_service.py:615-626`

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    """Get the branch name for a commit."""
    if self.repo is None:
        return "unknown"
    try:
        # Try to find the branch containing this commit
        for branch in self.repo.branches:  # N branches
            if commit.hexsha in [c.hexsha for c in self.repo.iter_commits(branch.name)]:
                # For EACH branch, iterate ALL commits in that branch (M commits)
                # Total: N × M operations
                return branch.name
        return "unknown"
    except Exception:
        return "main"  # Default fallback
```

### Root Cause
The nested loop at line 621-622 has O(n²) complexity:
- For every commit check, iterates through all branches (N)
- For each branch, builds list of ALL commits (M commits per branch average)
- Called for EVERY commit in comparison (100-1000+ times)
- Total complexity: O(num_commits × num_branches × avg_commits_per_branch)

### Why This Is Slow
1. **Redundant commit traversals** - Each branch's commits are traversed multiple times
2. **List comprehension overhead** - `[c.hexsha for c in ...]` builds entire list before checking
3. **No caching** - Same branch commits are iterated for each commit being analyzed
4. **Called per commit** - This method is called in `analyze_commit()` at line 192

### Example Impact
- Large repo (100 branches × 500 commits avg) = 50,000 operations per commit
- 100 commits × 50,000 ops/commit = 5,000,000 operations
- 1000 commits = 50,000,000+ operations
- Can cause 10+ second delays for branch-based analysis

---

## Proposed Solution

### Option 1: Pre-build commit-to-branch mapping (Recommended)

Build the mapping once per comparison in `compare_refs()` before the commit loop:

```python
def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
    # Pre-build commit-to-branch mapping once
    self._commit_to_branch_cache = self._build_commit_branch_mapping()

    # Rest of method uses cached mapping
    ...

def _build_commit_branch_mapping(self) -> dict[str, str]:
    """Build a mapping of commit SHAs to branch names."""
    if self.repo is None:
        return {}

    mapping = {}
    for branch in self.repo.branches:
        for commit in self.repo.iter_commits(branch.name):
            mapping[commit.hexsha] = branch.name
    return mapping

def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    """Get the branch name for a commit (cached)."""
    if self.repo is None:
        return "unknown"
    return self._commit_to_branch_cache.get(commit.hexsha, "unknown")
```

### Option 2: Use git's --contains check (Alternative)

Use git's optimized branch checking:

```python
def _get_commit_branch(self, commit: gitpython.Commit) -> str:
    """Get the branch name using git --contains (O(log N) via commit graph)."""
    if self.repo is None:
        return "unknown"
    try:
        # Use git's optimized --contains
        for branch in self.repo.branches:
            try:
                # Check if branch contains commit (O(log N) via commit graph)
                if commit.hexsha in self.repo.git.branch('--contains', commit.hexsha).split():
                    return branch.name
            except Exception:
                continue
        return "unknown"
    except Exception:
        return "main"
```

### Trade-offs
- **Option 1 (Caching):**
  - Pros: O(N×M) build once, O(1) lookup per commit, very predictable
  - Cons: Uses O(N×M) memory for the cache

- **Option 2 (git --contains):**
  - Pros: No memory overhead, uses git's optimized algorithms
  - Cons: Still makes N git calls per commit (though each is O(log N))

**Recommendation:** Option 1 (caching) because:
- Memory overhead is acceptable (commit SHAs + branch names)
- Provides 100-1000x speedup for typical repos
- More predictable performance characteristics
- Cache is built once per comparison, reused for all commits

---

## Affected Code
- `src/dot_work/git/services/git_service.py:615-626` (_get_commit_branch method)
- `src/dot_work/git/services/git_service.py:59-150` (compare_refs - add cache build)
- `src/dot_work/git/services/git_service.py:36-50` (__init__ - add cache attribute)

---

## Acceptance Criteria
- [ ] Commit-to-branch mapping built once per comparison
- [ ] O(1) branch lookup for each commit via cache.get()
- [ ] Cache cleared/updated on each compare_refs call
- [ ] Unit tests for branch mapping correctness
- [ ] Integration test verifies performance improvement
- [ ] Memory usage reasonable for typical repos (<100MB for cache)

---

## Next Steps
1. Implement Option 1 (caching approach)
2. Add cache attribute to __init__
3. Add _build_commit_branch_mapping() method
4. Update compare_refs() to build cache before analyzing commits
5. Update _get_commit_branch() to use cache
6. Add unit tests for branch mapping
7. Run validation tests
8. Benchmark performance improvement
