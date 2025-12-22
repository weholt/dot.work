"""Tests for container provision core module."""

from __future__ import annotations

import pytest

from dot_work.container.provision.core import RepoAgentError


class TestRepoAgentError:
    """Test the RepoAgentError exception class."""

    def test_repo_agent_error_creation(self) -> None:
        """Test that RepoAgentError can be created."""
        error = RepoAgentError("Test error message")
        assert str(error) == "Test error message"

    def test_repo_agent_error_inheritance(self) -> None:
        """Test that RepoAgentError inherits from Exception."""
        error = RepoAgentError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, RepoAgentError)

    def test_repo_agent_error_with_context(self) -> None:
        """Test RepoAgentError with context manager chaining."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            # Test that we can chain exceptions and catch the chained error
            try:
                raise RepoAgentError("Wrapper error") from e
            except RepoAgentError as chained_error:
                assert chained_error.__cause__ is e
                assert str(chained_error) == "Wrapper error"
                return  # Success - exception was properly chained

        # If we get here, the test failed
        pytest.fail("Exception chaining did not work as expected")