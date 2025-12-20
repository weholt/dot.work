"""CLI entry point for dot-work."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import get_prompts_dir, install_prompts

app = typer.Typer(
    name="dot-work",
    help="Install AI coding prompts for your development environment.",
    no_args_is_help=True,
)
console = Console()


def detect_environment(target: Path) -> str | None:
    """Try to detect which AI environment is configured in the target project."""
    for key, env in ENVIRONMENTS.items():
        for marker in env.detection:
            if (target / marker).exists():
                return key
    return None


@app.command("install")
def install(
    env: Annotated[
        str | None,
        typer.Option(
            "--env",
            "-e",
            help="AI environment to install for (copilot, claude, cursor, opencode, etc.)",
        ),
    ] = None,
    target: Annotated[
        Path,
        typer.Option(
            "--target",
            "-t",
            help="Target project directory (default: current directory)",
        ),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing files without asking",
        ),
    ] = False,
) -> None:
    """Install AI prompts to your project directory."""
    target = target.resolve()

    if not target.exists():
        console.print(f"[red]❌ Target directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    # Get prompts directory
    try:
        prompts_dir = get_prompts_dir()
    except FileNotFoundError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1) from None

    # Determine environment
    env_key = env
    if not env_key:
        # Try to detect
        detected = detect_environment(target)
        if detected:
            console.print(f"[cyan]🔍 Detected environment:[/cyan] {ENVIRONMENTS[detected].name}")
            if typer.confirm("Use this environment?", default=True):
                env_key = detected

        # Fall back to interactive selection
        if not env_key:
            env_key = prompt_for_environment()

    # Validate environment
    if env_key not in ENVIRONMENTS:
        console.print(f"[red]❌ Unknown environment:[/red] {env_key}")
        console.print(f"Available: {', '.join(ENVIRONMENTS.keys())}")
        raise typer.Exit(1)

    # Install
    env_config = ENVIRONMENTS[env_key]
    console.print(f"\n[bold blue]📦 Installing prompts for {env_config.name}...[/bold blue]\n")

    install_prompts(env_key, target, prompts_dir, console)

    console.print("\n[bold green]✅ Installation complete![/bold green]")


@app.command("list")
def list_envs() -> None:
    """List all supported AI coding environments."""
    table = Table(title="🤖 Supported AI Environments")
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Prompt Location", style="yellow")
    table.add_column("Notes", style="dim")

    for key, env in ENVIRONMENTS.items():
        location = env.prompt_dir or env.instructions_file or "-"
        table.add_row(key, env.name, location, env.notes)

    console.print(table)


@app.command("detect")
def detect(
    target: Annotated[
        Path,
        typer.Option(
            "--target",
            "-t",
            help="Target project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Detect the AI environment in a project directory."""
    target = target.resolve()

    if not target.exists():
        console.print(f"[red]❌ Directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    detected = detect_environment(target)
    if detected:
        env = ENVIRONMENTS[detected]
        console.print(f"[green]🔍 Detected:[/green] {env.name}")
        console.print(f"   Key: [cyan]{detected}[/cyan]")
        if env.notes:
            console.print(f"   Note: {env.notes}")
    else:
        console.print("[yellow]🔍 No AI environment detected[/yellow]")
        console.print("Run [cyan]dot-work list[/cyan] to see available environments")


@app.command("init")
def init_project(
    env: Annotated[
        str | None,
        typer.Option(
            "--env",
            "-e",
            help="AI environment to use",
        ),
    ] = None,
    target: Annotated[
        Path,
        typer.Option(
            "--target",
            "-t",
            help="Target project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Initialize a new project with prompts and issue tracking structure."""
    # This is an alias for install that's more intuitive
    install(env=env, target=target, force=False)


def prompt_for_environment() -> str:
    """Interactively ask the user which environment to use."""
    console.print("\n[bold]🤖 Which AI coding environment are you using?[/bold]\n")

    options = list(ENVIRONMENTS.keys())
    for i, key in enumerate(options, 1):
        env = ENVIRONMENTS[key]
        console.print(f"  [cyan][{i}][/cyan] {env.name}")
        if env.notes:
            console.print(f"      [dim]└─ {env.notes}[/dim]")

    console.print()

    while True:
        choice = typer.prompt("Enter number (or environment key)")

        # Check if it's a number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            console.print("[red]Invalid choice. Please try again.[/red]")
        except ValueError:
            # Check if they typed the environment key
            if choice.lower() in ENVIRONMENTS:
                return choice.lower()
            console.print("[red]Please enter a number or environment key.[/red]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show version and exit"),
    ] = False,
) -> None:
    """dot-work: Install AI coding prompts for your environment."""
    if version:
        from dot_work import __version__

        console.print(f"dot-work version {__version__}")
        raise typer.Exit()

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
