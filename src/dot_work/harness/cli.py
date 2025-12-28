"""
CLI interface for the harness command.

Provides command-line interface for running autonomous agents with Claude Agent SDK.
"""

from pathlib import Path

import typer
from rich.console import Console

from .client import CLAUDE_AGENT_SDK_AVAILABLE, run_harness

console = Console()
app = typer.Typer(help="Claude Agent SDK autonomous agent harness.")


@app.command()
def run(
    context_files: list[str] = typer.Argument(
        None,
        help="Context files to process (can be task files or other context)",
        metavar="CONTEXT",
    ),
    cwd: Path = typer.Option(
        Path("."),
        "--cwd",
        "--working-directory",
        help="Working directory for the agent",
        exists=True,
        resolve_path=True,
    ),
    max_iterations: int = typer.Option(
        50,
        "--max-iterations",
        "-i",
        help="Maximum iterations to run (default: 50)",
    ),
    max_turns: int = typer.Option(
        25,
        "--max-turns",
        "-t",
        help="Max agent/tool turns per iteration (default: 25)",
    ),
    permission_mode: str = typer.Option(
        "acceptEdits",
        "--permission-mode",
        "-p",
        help="Permission mode for file operations (default: acceptEdits)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Run autonomous agent harness on context files.

    Processes each context file with the Claude Agent SDK, executing tasks
    iteratively until complete or blocked.

    Example:
        dot-work harness run tasks.md context.md
        dot-work harness run --cwd /path/to/project --max-iterations 10 tasks.md
    """
    if not CLAUDE_AGENT_SDK_AVAILABLE:
        console.print(
            "[red]Error: claude-agent-sdk is not installed.[/red]\n"
            "[yellow]Install with:[/yellow] pip install claude-agent-sdk anyio"
        )
        raise typer.Exit(1)
    if not context_files:
        console.print("[red]Error: At least one context file is required.[/red]")
        console.print("\n[yellow]Usage:[/yellow] dot-work harness run CONTEXT_FILE...")
        raise typer.Exit(1)

    for context_file in context_files:
        context_path = Path(context_file)

        if not context_path.exists():
            console.print(f"[red]Error: Context file not found: {context_file}[/red]")
            continue

        if verbose:
            console.print(f"\n[cyan]Processing:[/cyan] {context_file}")
            console.print(f"[cyan]Working directory:[/cyan] {cwd}")
            console.print(f"[cyan]Max iterations:[/cyan] {max_iterations}")
            console.print(f"[cyan]Max turns per iteration:[/cyan] {max_turns}")

        try:
            run_harness(
                cwd=cwd,
                tasks_path=context_path,
                max_iterations=max_iterations,
                max_turns=max_turns,
                permission_mode=permission_mode,  # type: ignore[arg-type]
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user.[/yellow]")
            raise typer.Exit(130) from None
        except Exception as e:
            console.print(f"[red]Error processing {context_file}: {e}[/red]")
            raise typer.Exit(1) from None


@app.command()
def validate(
    context_files: list[str] = typer.Argument(
        None,
        help="Context files to validate",
        metavar="CONTEXT",
    ),
) -> None:
    """Validate context/task files for correct format.

    Checks that:
    - Files exist
    - Files contain valid markdown checkbox tasks
    - Tasks are properly formatted

    Example:
        dot-work harness validate tasks.md
    """
    if not context_files:
        console.print("[red]Error: At least one context file is required.[/red]")
        raise typer.Exit(1)

    from .tasks import load_tasks, validate_task_file

    all_valid = True

    for context_file in context_files:
        context_path = Path(context_file)
        console.print(f"\n[cyan]Validating:[/cyan] {context_file}")

        try:
            validate_task_file(context_path)
            _, tasks = load_tasks(context_path)

            done_count = sum(1 for t in tasks if t.done)
            total_count = len(tasks)

            console.print("  [green]✓[/green] File exists")
            console.print(f"  [green]✓[/green] Found {total_count} task(s)")
            console.print(f"  [blue]Info:[/blue] {done_count}/{total_count} completed")

        except SystemExit as e:
            console.print(f"  [red]✗[/red] {e}")
            all_valid = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Unexpected error: {e}")
            all_valid = False

    if all_valid:
        console.print("\n[green]All files are valid![/green]")
    else:
        console.print("\n[red]Some files have errors.[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    output: str = typer.Option(
        "tasks.md",
        "--output",
        "-o",
        help="Output file name",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing file",
    ),
) -> None:
    """Initialize a new task file with example tasks.

    Creates a markdown file with example checkbox tasks that can be used
    with the harness command.

    Example:
        dot-work harness init
        dot-work harness init --output my-tasks.md --force
    """
    output_path = Path(output)

    if output_path.exists() and not force:
        console.print(f"[red]Error: File already exists: {output}[/red]")
        console.print("[yellow]Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)

    example_content = """# Tasks

Example task file for the dot-work harness.

## Core Tasks
- [ ] T-001: Create a python module `src/app.py` that exposes `add(a,b)` and `mul(a,b)` with type hints.
- [ ] T-002: Add unit tests for `add` and `mul` using pytest.
- [ ] T-003: Add `pyproject.toml` with minimal config to run `pytest -q`.

## Documentation
- [ ] D-001: Write README.md with usage examples.
- [ ] D-002: Add docstrings to all public functions.

## Notes
- Tasks are processed in order (first unchecked task is selected)
- When a task is complete, change `[ ]` to `[x]`
- Add evidence as indented sub-bullet: `  - Evidence: pytest -q passed`
- If blocked, add: `  - BLOCKED: reason` (don't mark as done)
"""

    output_path.write_text(example_content)
    console.print(f"[green]Created:[/green] {output}")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Edit tasks: {output}")
    console.print(f"  2. Run harness: dot-work harness run {output}")


__all__ = ["app"]
