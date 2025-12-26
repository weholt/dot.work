can you create a simple python-based example using claude code sdk to have an iterative loop getting the same prompt to process a list of tasks in a file until all tasks are done?

`claude-code-sdk` is deprecated; use the **Claude Agent SDK** (`claude-agent-sdk`), which embeds Claude Code tooling and provides `query()` / `ClaudeSDKClient`. ([PyPI][1])

```md
# filename: tasks.md
# Tasks
- [ ] T-001: Create a python module `src/app.py` that exposes `add(a,b)` and `mul(a,b)` with type hints.
- [ ] T-002: Add unit tests for `add` and `mul` using pytest.
- [ ] T-003: Add `pyproject.toml` with minimal config to run `pytest -q`.
```

```python
# filename: run_tasks.py
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

TASK_RE = re.compile(r"^\s*-\s*\[\s*(?P<state>[xX ])\s*\]\s*(?P<text>.+?)\s*$")


@dataclass(frozen=True)
class Task:
    line_no: int
    done: bool
    text: str


def load_tasks(md_path: Path) -> Tuple[str, List[Task]]:
    content = md_path.read_text(encoding="utf-8")
    tasks: List[Task] = []
    for i, line in enumerate(content.splitlines()):
        m = TASK_RE.match(line)
        if not m:
            continue
        tasks.append(
            Task(
                line_no=i,
                done=(m.group("state").lower() == "x"),
                text=m.group("text").strip(),
            )
        )
    return content, tasks


def count_done(tasks: List[Task]) -> int:
    return sum(1 for t in tasks if t.done)


def next_open_task(tasks: List[Task]) -> Task | None:
    for t in tasks:
        if not t.done:
            return t
    return None


async def run_one_iteration(
    client: ClaudeSDKClient,
    cwd: Path,
    tasks_path: Path,
    max_tool_turns: int,
) -> str:
    # Same instruction each time; repo state comes from the file Claude reads.
    prompt = (
        "You are an autonomous coding agent working in this repository.\n"
        f"- Working directory: {cwd}\n"
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


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", default=".", help="Repo working directory")
    ap.add_argument("--tasks", default="tasks.md", help="Path to tasks markdown file (relative to cwd)")
    ap.add_argument("--max-iterations", type=int, default=50, help="Hard stop to avoid infinite loops")
    ap.add_argument("--max-turns", type=int, default=25, help="Max agent/tool turns per iteration")
    args = ap.parse_args()

    cwd = Path(args.cwd).resolve()
    tasks_path = (cwd / args.tasks).resolve()

    if not tasks_path.exists():
        raise SystemExit(f"tasks file not found: {tasks_path}")

    options = ClaudeAgentOptions(
        cwd=str(cwd),
        permission_mode="acceptEdits",  # auto-accept file edits
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        max_turns=args.max_turns,
        system_prompt=(
            "Follow the task-file workflow strictly. "
            "Never mark a task done without updating the repo and adding Evidence."
        ),
    )

    async with ClaudeSDKClient(options=options) as client:
        for iteration in range(1, args.max_iterations + 1):
            before_content, before_tasks = load_tasks(tasks_path)
            open_task = next_open_task(before_tasks)
            if open_task is None:
                print("DONE: no unchecked tasks remain.")
                return

            before_done = count_done(before_tasks)

            status = await run_one_iteration(
                client=client,
                cwd=cwd,
                tasks_path=tasks_path,
                max_tool_turns=args.max_turns,
            )

            after_content, after_tasks = load_tasks(tasks_path)
            after_done = count_done(after_tasks)

            print(f"\n--- Iteration {iteration} ---")
            print(f"Next task: {open_task.text}")
            if status:
                print(status)

            if after_done > before_done:
                continue

            # No progress: stop so a human can inspect the BLOCKED reason or fix prompts.
            # (You can change this behavior to skip blocked tasks.)
            print("STOP: no task was marked done in this iteration. Check tasks.md for a BLOCKED note.")
            return

        print("STOP: reached --max-iterations without completing all tasks.")


if __name__ == "__main__":
    anyio.run(main)
```

Run (single-line commands):

* `python -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install claude-agent-sdk anyio` ([Claude Developer Platform][2])
* `python run_tasks.py --cwd . --tasks tasks.md --max-iterations 50 --max-turns 25`

API references for `ClaudeSDKClient`, `ClaudeAgentOptions`, and the async `query()/receive_response()` pattern. ([Claude Developer Platform][2])

[1]: https://pypi.org/project/claude-code-sdk/?utm_source=chatgpt.com "claude-code-sdk"
[2]: https://platform.claude.com/docs/en/agent-sdk/python "Agent SDK reference - Python - Claude Docs"
