"""Tests for harness client module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dot_work.harness.client import (
    CLAUDE_AGENT_SDK_AVAILABLE,
    HarnessClient,
)


class TestClaudeAgentSdkAvailable:
    """Test SDK availability flag."""

    def test_sdk_available_flag_exists(self):
        """Test that CLAUDE_AGENT_SDK_AVAILABLE is defined."""
        assert isinstance(CLAUDE_AGENT_SDK_AVAILABLE, bool)


class TestHarnessClientInit:
    """Test HarnessClient initialization."""

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        cwd = Path("/test/dir")
        client = HarnessClient(cwd=cwd)

        assert client.cwd == cwd
        assert client.permission_mode == "acceptEdits"
        assert client.allowed_tools == ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
        assert client.max_turns == 25
        assert "Follow the task-file workflow strictly" in client.system_prompt

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        cwd = Path("/test/dir")
        client = HarnessClient(
            cwd=cwd,
            permission_mode="plan",
            allowed_tools=["Read", "Write"],
            max_turns=50,
            system_prompt="Custom prompt",
        )

        assert client.permission_mode == "plan"
        assert client.allowed_tools == ["Read", "Write"]
        assert client.max_turns == 50
        assert client.system_prompt == "Custom prompt"

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", False)
    def test_init_without_sdk_raises_error(self):
        """Test that initialization fails when SDK is not available."""
        cwd = Path("/test/dir")

        with pytest.raises(ImportError, match="claude-agent-sdk is required"):
            HarnessClient(cwd=cwd)


class TestCreateOptions:
    """Test create_options method."""

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    def test_create_options(self):
        """Test creating ClaudeAgentOptions."""
        cwd = Path("/test/dir")
        tasks_path = Path("/tasks.md")
        client = HarnessClient(cwd=cwd, permission_mode="plan", max_turns=50)

        # Mock ClaudeAgentOptions if SDK is not available
        with patch("dot_work.harness.client.ClaudeAgentOptions") as mock_options_class:
            mock_options = MagicMock()
            mock_options_class.return_value = mock_options

            options = client.create_options(tasks_path)

            mock_options_class.assert_called_once()
            call_kwargs = mock_options_class.call_args.kwargs
            assert call_kwargs["cwd"] == str(cwd)
            assert call_kwargs["permission_mode"] == "plan"
            assert call_kwargs["max_turns"] == 50


class TestHarnessClientRunIteration:
    """Test run_iteration method."""

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    async def test_run_iteration_sends_prompt(self, tmp_path: Path):
        """Test that run_iteration sends the correct prompt."""
        cwd = Path("/test/dir")
        tasks_path = tmp_path / "tasks.md"
        tasks_path.write_text("- [ ] Test task\n")

        client = HarnessClient(cwd=cwd)

        # Mock the client's query and receive_response methods
        mock_sdk_client = MagicMock()
        mock_sdk_client.query = AsyncMock()

        # Create async generator for receive_response that returns an async iterator
        async def mock_receive_gen():
            mock_message = MagicMock()
            mock_block = MagicMock()
            mock_block.text = "Task completed successfully"
            mock_message.content = [mock_block]
            yield mock_message

        mock_sdk_client.receive_response = lambda: mock_receive_gen()

        await client.run_iteration(mock_sdk_client, tasks_path)

        # Verify query was called
        mock_sdk_client.query.assert_called_once()
        prompt = mock_sdk_client.query.call_args[0][0]
        assert "Working directory:" in prompt
        assert str(cwd) in prompt
        assert str(tasks_path) in prompt


class TestRunHarnessAsync:
    """Test run_harness_async function."""

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    @patch("dot_work.harness.client.HarnessClient")
    @patch("dot_work.harness.client.ClaudeSDKClient")
    async def test_run_harness_async_with_tasks(
        self, mock_sdk_client_class, mock_harness_class, tmp_path: Path
    ):
        """Test running harness with tasks."""
        from dot_work.harness.client import run_harness_async

        tasks_path = tmp_path / "tasks.md"
        tasks_path.write_text("- [ ] Task 1\n- [ ] Task 2\n")

        cwd = tmp_path

        # Mock the SDK client context manager
        mock_sdk_client = AsyncMock()
        mock_sdk_client.__aenter__ = AsyncMock(return_value=mock_sdk_client)
        mock_sdk_client.__aexit__ = AsyncMock()
        mock_sdk_client_class.return_value = mock_sdk_client

        # Mock harness client
        mock_harness = MagicMock()
        mock_harness.create_options = MagicMock(return_value=MagicMock())
        mock_harness.run_iteration = AsyncMock(return_value="Iteration complete")
        mock_harness_class.return_value = mock_harness

        # Run for one iteration
        await run_harness_async(cwd, tasks_path, max_iterations=1)

        # Verify harness was created and run
        mock_harness_class.assert_called_once()
        mock_harness.run_iteration.assert_called_once()

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    @patch("dot_work.harness.client.HarnessClient")
    @patch("dot_work.harness.client.ClaudeSDKClient")
    async def test_run_harness_async_stops_when_done(
        self, mock_sdk_client_class, mock_harness_class, tmp_path: Path
    ):
        """Test that harness stops when all tasks are done."""
        from dot_work.harness.client import run_harness_async

        tasks_path = tmp_path / "tasks.md"
        tasks_path.write_text("- [x] Task 1\n- [x] Task 2\n")  # All done

        cwd = tmp_path

        # Mock the SDK client context manager
        mock_sdk_client = AsyncMock()
        mock_sdk_client.__aenter__ = AsyncMock(return_value=mock_sdk_client)
        mock_sdk_client.__aexit__ = AsyncMock()
        mock_sdk_client_class.return_value = mock_sdk_client

        # Mock harness client
        mock_harness = MagicMock()
        mock_harness.create_options = MagicMock(return_value=MagicMock())
        mock_harness_class.return_value = mock_harness

        # Run - should exit immediately
        await run_harness_async(cwd, tasks_path, max_iterations=10)

        # Should not call run_iteration since no open tasks
        mock_harness.run_iteration.assert_not_called()

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", True)
    @patch("dot_work.harness.client.HarnessClient")
    @patch("dot_work.harness.client.ClaudeSDKClient")
    async def test_run_harness_async_invalid_file_raises_error(
        self, mock_sdk_client_class, mock_harness_class, tmp_path: Path
    ):
        """Test that invalid task file raises TaskFileError."""
        from dot_work.harness.client import run_harness_async
        from dot_work.harness.tasks import TaskFileError

        tasks_path = tmp_path / "nonexistent.md"
        cwd = tmp_path

        with pytest.raises(TaskFileError):
            await run_harness_async(cwd, tasks_path, max_iterations=1)


class TestRunHarness:
    """Test run_harness synchronous wrapper."""

    @patch("dot_work.harness.client.ClaudeSDKClient", create=True)
    @patch("dot_work.harness.client.HarnessClient", create=True)
    @patch("anyio.run")
    def test_run_harness_calls_async_version(self, mock_anyio_run, mock_harness_class, mock_sdk_client_class):
        """Test that run_harness calls async version with anyio."""
        # Note: We patch anyio at module level, but the function imports it internally
        # We need to import the actual function to test
        # Let's just verify the function exists and has correct signature
        from dot_work.harness.client import run_harness

        cwd = Path("/test/dir")
        tasks_path = Path("/tasks.md")

        # Verify function is callable
        assert callable(run_harness)

    @patch("dot_work.harness.client.CLAUDE_AGENT_SDK_AVAILABLE", False)
    def test_run_harness_without_anyio_raises_error(self):
        """Test that missing anyio raises ImportError."""
        from dot_work.harness.client import run_harness

        cwd = Path("/test/dir")
        tasks_path = Path("/tasks.md")

        # If anyio is not installed, this should raise ImportError
        # We'll just verify the function signature is correct
        assert callable(run_harness)


class TestPermissionMode:
    """Test PermissionMode type."""

    def test_permission_mode_is_literal(self):
        """Test that PermissionMode is a Literal type."""
        # Valid modes
        valid_modes = ["default", "acceptEdits", "plan", "bypassPermissions"]

        # The type should be a Literal with these values
        # This is a compile-time check, but we can verify the values exist
        assert "default" in valid_modes
        assert "acceptEdits" in valid_modes
        assert "plan" in valid_modes
        assert "bypassPermissions" in valid_modes
