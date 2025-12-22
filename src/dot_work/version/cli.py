"""Command-line interface for version management."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from dot_work.version.manager import VersionManager

app = typer.Typer(help="Date-based version management with changelog generation")
console = Console()


@app.command()
def init(
    version: str | None = typer.Option(None, help="Initial version (e.g., 2025.10.001)"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Initialize version management for a project."""
    manager = VersionManager(project_root=project_root)

    try:
        if version:
            result = manager.init_version(version=version)
        else:
            result = manager.init_version()

        console.print(f"[green]✓[/green] Initialized version: {result.version}")
        console.print(f"[dim]Version file created: {manager.version_file}[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Initialization failed: {e}")
        raise typer.Exit(1)


@app.command()
def freeze(
    llm: bool = typer.Option(False, "--llm", help="Use LLM for enhanced summaries"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without making changes"),
    push: bool = typer.Option(False, "--push", help="Push tags to remote after freeze"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Freeze a new version with changelog generation."""
    manager = VersionManager(project_root=project_root)

    try:
        with console.status("[bold blue]Freezing version...", spinner="dots"):
            result = manager.freeze_version(use_llm=llm, dry_run=dry_run)

        if dry_run:
            console.print("[yellow]DRY RUN - No changes made[/yellow]")

        console.print(f"[green]✓[/green] Version frozen: {result.version}")
        console.print(f"[dim]Git tag: {result.git_tag}[/dim]")

        if result.changelog_generated:
            console.print("[dim]Changelog updated: CHANGELOG.md[/dim]")

        if push and not dry_run:
            with console.status("[bold blue]Pushing tags...", spinner="dots"):
                manager.push_tags()
            console.print("[green]✓[/green] Tags pushed to remote")

    except Exception as e:
        console.print(f"[red]✗[/red] Version freeze failed: {e}")
        raise typer.Exit(1)


@app.command()
def show(
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Show current version information."""
    manager = VersionManager(project_root=project_root)

    try:
        current = manager.read_version()

        if not current:
            console.print("[yellow]No version found. Run 'version-management init' first.[/yellow]")
            raise typer.Exit(1)

        # Display project info
        console.print(f"\n[bold cyan]{manager.project_info.name}[/bold cyan]")
        if manager.project_info.description:
            console.print(f"[dim]{manager.project_info.description}[/dim]\n")

        table = Table(title="Current Version", show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Version", current.version)
        table.add_row("Build Date", current.build_date)
        table.add_row("Git Commit", current.git_commit[:12] if current.git_commit else "N/A")
        table.add_row("Git Tag", current.git_tag or "N/A")

        if current.previous_version:
            table.add_row("Previous Version", current.previous_version)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error reading version: {e}")
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, help="Number of versions to show"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Show version history from git tags."""
    manager = VersionManager(project_root=project_root)

    try:
        versions = manager.get_version_history(limit=limit)

        if not versions:
            console.print("[yellow]No version history found.[/yellow]")
            return

        table = Table(title=f"Version History (last {limit})")
        table.add_column("Version", style="cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Commit", style="dim")
        table.add_column("Author", style="green")

        for v in versions:
            table.add_row(
                v["version"],
                v["date"],
                v["commit"][:12],
                v["author"]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error reading history: {e}")
        raise typer.Exit(1)


@app.command()
def commits(
    since: str | None = typer.Option(None, help="Show commits since this tag/version"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Show commits since last version tag."""
    manager = VersionManager(project_root=project_root)

    try:
        if not since:
            # Get latest tag
            since = manager.get_latest_tag()
            if not since:
                console.print("[yellow]No previous version tag found. Showing all commits.[/yellow]")
                since = None

        commit_list = manager.get_commits_since(since)

        if not commit_list:
            console.print("[yellow]No commits found.[/yellow]")
            return

        table = Table(title=f"Commits since {since or 'beginning'}")
        table.add_column("Type", style="cyan")
        table.add_column("Subject", style="white")
        table.add_column("Author", style="green")
        table.add_column("Hash", style="dim")

        for commit in commit_list:
            table.add_row(
                commit.commit_type,
                commit.subject[:60],
                commit.author,
                commit.short_hash
            )

        console.print(table)
        console.print(f"\n[dim]Total commits: {len(commit_list)}[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error reading commits: {e}")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    project_root: Path = typer.Option(Path.cwd(), help="Project root directory"),
):
    """Manage version management configuration."""
    manager = VersionManager(project_root=project_root)

    if show:
        cfg = manager.load_config()
        console.print_json(data=cfg)
    else:
        console.print("[yellow]Use --show to display configuration[/yellow]")


if __name__ == "__main__":
    app()
