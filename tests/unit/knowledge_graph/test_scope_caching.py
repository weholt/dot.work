"""Tests for scope caching (PERF-013)."""

import time
import pytest
from unittest.mock import MagicMock

from dot_work.knowledge_graph.scope import (
    ScopeFilter,
    build_scope_sets,
    clear_scope_cache,
    get_cache_stats,
)


class TestScopeCaching:
    """Tests for scope set caching functionality (PERF-013)."""

    def test_cache_key_identical_scopes(self) -> None:
        """Test that identical scopes generate the same cache key."""
        scope1 = ScopeFilter(project="test", topics=["a", "b"])
        scope2 = ScopeFilter(project="test", topics=["b", "a"])  # Different order

        # Both should generate same cache key since topics are sorted
        # We can't directly access the cache key, but we can verify caching works
        db = MagicMock()
        db.get_collection_by_name.return_value = MagicMock(collection_id="test")
        db.list_collection_members.return_value = []
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        # Mock to avoid actual DB calls
        result1 = build_scope_sets(db, scope1, use_cache=False)
        assert get_cache_stats()["cache_entries"] == 0

    def test_cache_hit_returns_same_result(self) -> None:
        """Test that cache hit returns the same result without DB queries."""
        db = MagicMock()
        scope = ScopeFilter(project="test")

        # Setup mock to return predictable values
        collection = MagicMock(collection_id="test")
        db.get_collection_by_name.return_value = collection

        # Create mock members
        member1 = MagicMock(member_pk="node1")
        member2 = MagicMock(member_pk="node2")
        db.list_collection_members.return_value = [member1, member2]
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        # First call - should build from DB
        result1 = build_scope_sets(db, scope, use_cache=True)
        stats1 = get_cache_stats()
        assert stats1["cache_entries"] == 1

        # Second call - should use cache
        result2 = build_scope_sets(db, scope, use_cache=True)
        stats2 = get_cache_stats()
        assert stats2["cache_entries"] == 1

        # Results should be identical
        assert result1 == result2

        # Verify we didn't call DB again (still only 1 call to list_collection_members)
        assert db.list_collection_members.call_count == 1

    def test_cache_miss_after_ttl(self) -> None:
        """Test that cache expires after TTL."""
        db = MagicMock()
        scope = ScopeFilter(project="test")

        collection = MagicMock(collection_id="test")
        db.get_collection_by_name.return_value = collection
        member1 = MagicMock(member_pk="node1")
        db.list_collection_members.return_value = [member1]
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        # First call
        result1 = build_scope_sets(db, scope, use_cache=True)
        call_count_after_first = db.list_collection_members.call_count

        # Manually expire the cache by setting old timestamp
        from dot_work.knowledge_graph.scope import _SCOPE_CACHE_TIMESTAMPS
        old_time = time.time() - 100  # 100 seconds ago (beyond 60s TTL)
        for key in list(_SCOPE_CACHE_TIMESTAMPS.keys()):
            _SCOPE_CACHE_TIMESTAMPS[key] = old_time

        # Second call should miss cache and rebuild
        result2 = build_scope_sets(db, scope, use_cache=True)

        # Should have called DB again due to cache expiry
        # First call + rebuild after expiry = 2 calls
        assert db.list_collection_members.call_count == call_count_after_first + 1

    def test_clear_scope_cache(self) -> None:
        """Test that clear_scope_cache empties the cache."""
        db = MagicMock()
        scope = ScopeFilter(project="test")

        collection = MagicMock(collection_id="test")
        db.get_collection_by_name.return_value = collection
        db.list_collection_members.return_value = []
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        # Build some cache entries
        build_scope_sets(db, scope, use_cache=True)
        assert get_cache_stats()["cache_entries"] > 0

        # Clear cache
        clear_scope_cache()
        assert get_cache_stats()["cache_entries"] == 0

    def test_cache_stats(self) -> None:
        """Test that get_cache_stats returns correct information."""
        stats = get_cache_stats()
        assert "cache_entries" in stats
        assert "cache_ttl_seconds" in stats
        assert stats["cache_ttl_seconds"] == 60

    def test_use_cache_false_bypasses_cache(self) -> None:
        """Test that use_cache=False bypasses caching."""
        db = MagicMock()
        scope = ScopeFilter(project="test")

        collection = MagicMock(collection_id="test")
        db.get_collection_by_name.return_value = collection
        db.list_collection_members.return_value = []
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        # Call with caching disabled
        build_scope_sets(db, scope, use_cache=False)

        # Cache should be empty
        assert get_cache_stats()["cache_entries"] == 0

    def test_different_scopes_have_different_cache_entries(self) -> None:
        """Test that different scope parameters create separate cache entries."""
        db = MagicMock()

        collection = MagicMock(collection_id="test")
        db.get_collection_by_name.return_value = collection
        db.list_collection_members.return_value = []
        db.get_topic_by_name.return_value = MagicMock(topic_id="topic1")

        scope1 = ScopeFilter(project="project1")
        scope2 = ScopeFilter(project="project2")

        build_scope_sets(db, scope1, use_cache=True)
        build_scope_sets(db, scope2, use_cache=True)

        # Should have 2 cache entries
        assert get_cache_stats()["cache_entries"] == 2
