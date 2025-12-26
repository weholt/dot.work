"""
Claude Agent SDK client wrapper for the harness.

Provides async interface to Claude Agent SDK with proper configuration.
"""

from pathlib import Path

try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        TextBlock,
    )
    CLAUDE_AGENT_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_AGENT_SDK_AVAILABLE = False
    ClaudeSDKClient = None  # type: ignore
    ClaudeAgentOptions = None  # type: ignore


class HarnessClient:
    """Client wrapper for Claude Agent SDK autonomous agent execution."""

    def __init__(
        self,
        cwd: Path,
        permission_mode: str = "acceptEdits",
        allowed_tools: list[str] | None = None,
        max_turns: int = 25,
        system_prompt: str | None = None,
    ):
        """Initialize the harness client.

        Args:
            cwd: Working directory for the agent
            permission_mode: Permission mode for file operations
            allowed_tools: List of allowed tool names
            max_turns: Maximum tool turns per iteration
            system_prompt: Optional system prompt for the agent

        Raises:
            ImportError: If claude-agent-sdk is not installed
        """
        if not CLAUDE_AGENT_SDK_AVAILABLE:
            raise ImportError(
                "claude-agent-sdk is required for harness functionality. "
                "Install with: pip install claude-agent-sdk"
            )

        self.cwd = cwd
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools or ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
        self.max_turns = max_turns
        self.system_prompt = system_prompt or (
            "Follow the task-file workflow strictly. "
            "Never mark a task done without updating the repo and adding Evidence."
        )

    def create_options(self, tasks_path: Path) -> ClaudeAgentOptions:
        """Create ClaudeAgentOptions for the SDK client.

        Args:
            tasks_path: Path to the tasks markdown file

        Returns:
            ClaudeAgentOptions configured for the harness
        """
        return ClaudeAgentOptions(
            cwd=str(self.cwd),
            permission_mode=self.permission_mode,
            allowed_tools=self.allowed_tools,
            max_turns=self.max_turns,
            system_prompt=self.system_prompt,
        )

    async def run_iteration(
        self,
        client: ClaudeSDKClient,
        tasks_path: Path,
    ) -> str:
        """Run a single iteration of the harness.

        Args:
            client: ClaudeSDKClient instance
            tasks_path: Path to the tasks markdown file

        Returns:
            Status message from the agent
        """
        prompt = (
            "You are an autonomous coding agent working in this repository.\n"
            f"- Working directory: {self.cwd}\n"
            f"- Task file: {tasks_path}\n\n"
            "Loop goal: complete tasks in the task file until none remain.\n\n"
            "For THIS iteration:\n"
            "1) Read the task file.\n"
            "2) Select the FIRST unchecked task.\n"
            "3) Implement it in the repo (edit/create files as needed).\n"
            "4) Run verification commands appropriate for the repo (at least: `pytest -q` if tests exist).\n"
            "5) Mark that task as done by changing `[ ]` to `[x]` in the task file, and add one indented sub-bullet under it: `  - Evidence: <commands run>`.\n"
            "6) If blocked, add an indented sub-bullet: `  - BLOCKED: <exact reason>` and DO NOT mark it done.\n\n"
            "Return a short status message (1-3 lines)."
        )

        await client.query(prompt)

        out_text_parts: list[str] = []
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        out_text_parts.append(block.text)

        return "\n".join(s.strip() for s in out_text_parts if s.strip())


async def run_harness_async(
    cwd: Path,
    tasks_path: Path,
    max_iterations: int = 50,
    max_turns: int = 25,
    permission_mode: str = "acceptEdits",
) -> None:
    """Run the harness asynchronously.

    Args:
        cwd: Working directory for the agent
        tasks_path: Path to the tasks markdown file
        max_iterations: Maximum iterations to run
        max_turns: Maximum tool turns per iteration
        permission_mode: Permission mode for file operations
    """
    from .tasks import count_done, load_tasks, next_open_task, validate_task_file

    # Validate task file
    tasks_path = tasks_path.resolve()
    validate_task_file(tasks_path)

    # Create client wrapper
    harness = HarnessClient(
        cwd=cwd,
        permission_mode=permission_mode,
        max_turns=max_turns,
    )

    options = harness.create_options(tasks_path)

    async with ClaudeSDKClient(options=options) as client:
        for iteration in range(1, max_iterations + 1):
            _, before_tasks = load_tasks(tasks_path)
            open_task = next_open_task(before_tasks)

            if open_task is None:
                print("DONE: no unchecked tasks remain.")
                return

            before_done = count_done(before_tasks)

            status = await harness.run_iteration(client, tasks_path)

            _, after_tasks = load_tasks(tasks_path)
            after_done = count_done(after_tasks)

            print(f"\n--- Iteration {iteration} ---")
            print(f"Next task: {open_task.text}")
            if status:
                print(status)

            if after_done > before_done:
                continue

            print("STOP: no task was marked done in this iteration. Check tasks.md for a BLOCKED note.")
            return

        print("STOP: reached --max-iterations without completing all tasks.")


def run_harness(
    cwd: Path,
    tasks_path: Path,
    max_iterations: int = 50,
    max_turns: int = 25,
    permission_mode: str = "acceptEdits",
) -> None:
    """Run the harness (synchronous wrapper).

    Args:
        cwd: Working directory for the agent
        tasks_path: Path to the tasks markdown file
        max_iterations: Maximum iterations to run
        max_turns: Maximum tool turns per iteration
        permission_mode: Permission mode for file operations
    """
    try:
        import anyio
    except ImportError:
        raise ImportError(
            "anyio is required for harness functionality. "
            "Install with: pip install anyio"
        ) from None

    anyio.run(run_harness_async, cwd, tasks_path, max_iterations, max_turns, permission_mode)


__all__ = [
    "HarnessClient",
    "run_harness",
    "run_harness_async",
    "CLAUDE_AGENT_SDK_AVAILABLE",
]
