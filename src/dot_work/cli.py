"""CLI entry point for dot-work."""

import json
import logging
import re
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dot_work.environments import ENVIRONMENTS
from dot_work.installer import (
    discover_available_environments,
    get_prompts_dir,
    initialize_work_directory,
    install_prompts,
)
from dot_work.plugins import discover_plugins, register_all_plugins
from dot_work.skills.cli import app as skills_app
from dot_work.subagents.cli import app as subagents_app
from dot_work.utils.sanitization import sanitize_error_message
from dot_work.zip.cli import app as zip_app

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="dot-work",
    help="Install AI coding prompts for your development environment.",
    no_args_is_help=True,
)
console = Console()

# Create subcommand group for validate
validate_app = typer.Typer(help="Validate files for syntax and schema errors.")

# Review subcommand group has been exported to dot-review plugin

# Create subcommand group for canonical prompts
canonical_app = typer.Typer(help="Validate and install canonical prompt files.")

# Create subcommand group for prompt management
prompt_app = typer.Typer(help="Create and manage canonical prompt files.")


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
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Preview changes without writing files",
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
        console.print("[dim]💡 Fix: Reinstall dot-work to ensure prompt files are available[/dim]")
        raise typer.Exit(1) from None

    # Discover available environments from prompt frontmatter
    discovered_envs = discover_available_environments(prompts_dir)

    # Determine environment
    env_key = env
    if not env_key:
        # Try to detect
        detected = detect_environment(target)
        if detected and detected in discovered_envs:
            console.print(f"[cyan]🔍 Detected environment:[/cyan] {ENVIRONMENTS[detected].name}")
            if typer.confirm("Use this environment?", default=True):
                env_key = detected

        # Fall back to interactive selection with discovered environments
        if not env_key:
            env_key = prompt_for_environment(discovered_envs)

    # Validate environment
    if env_key not in ENVIRONMENTS:
        console.print(f"[red]❌ Unknown environment:[/red] {env_key}")
        console.print(f"Available in ENVIRONMENTS: {', '.join(ENVIRONMENTS.keys())}")
        raise typer.Exit(1)

    # Check if environment is supported by any prompts
    if env_key not in discovered_envs:
        console.print(
            f"[yellow]⚠ Environment '{env_key}' not found in any prompt frontmatter.[/yellow]"
        )
        console.print(
            f"[dim]Available environments: {', '.join(sorted(discovered_envs.keys()))}[/dim]"
        )
        if not typer.confirm("Continue with legacy installation?", default=False):
            raise typer.Exit(0)

    # Install
    env_config = ENVIRONMENTS[env_key]
    if dry_run:
        console.print(
            f"\n[bold yellow]🔍 Dry run: Previewing installation for {env_config.name}...[/bold yellow]\n"
        )
    else:
        console.print(f"\n[bold blue]📦 Installing prompts for {env_config.name}...[/bold blue]\n")

    try:
        install_prompts(env_key, target, prompts_dir, console, force=force, dry_run=dry_run)
    except ValueError as e:
        console.print(f"\n[red]❌ Installation failed:[/red] {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        # Log full error for debugging
        logger.error(f"Installation error: {e}", exc_info=True)
        console.print("\n[red]❌ Unexpected error during installation:[/red]")
        console.print(f"[dim]{sanitize_error_message(e)}[/dim]")
        console.print("\n[dim]💡 Try running with --dry-run to preview changes[/dim]")
        console.print("[dim]💡 Report this issue if it persists[/dim]")
        raise typer.Exit(1) from None

    if dry_run:
        console.print("\n[bold yellow]⚠️  Dry run complete - no files were written[/bold yellow]")
    else:
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
            help="AI environment to use (anthropic, openai, etc.)",
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
    """Install AI prompts to your project (alias for 'install' command).

    This is an alias for 'dot-work install' that installs AI coding prompts to your
    project. Use this to add AI-powered development capabilities to existing projects.

    For setting up issue tracking (without AI prompts), use 'init-tracking' instead.
    For more control over installation, use the 'install' command directly.
    """
    # This is an alias for install that's more intuitive for new users
    install(env=env, target=target, force=False)


@app.command("init-tracking")
def init_tracking(
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
    """Initialize the .work/ issue tracking directory structure only.

    Creates the .work/ directory for file-based issue tracking without installing
    AI prompts. Use this when you only want issue tracking capabilities.

    For full project setup with AI prompts, use 'init' instead.
    """
    target = target.resolve()

    if not target.exists():
        console.print(f"[red]❌ Target directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    console.print("\n[bold blue]📋 Initializing work directory...[/bold blue]\n")

    initialize_work_directory(target, console, force=force)

    console.print("\n[bold green]✅ Work directory initialized![/bold green]")
    console.print("[dim]Next: Run 'generate-baseline' before making code changes[/dim]")


@app.command("status")
def status(
    format: Annotated[
        Literal["table", "markdown", "json", "simple"],
        typer.Option(
            "--format",
            "-f",
            help="Output format (table, markdown, json, simple)",
        ),
    ] = "table",
) -> None:
    """Show project status including focus and issue counts.

    Displays the current focus (Previous/Current/Next from .work/agent/focus.md)
    and counts issues by priority level.
    """
    # Get work directory
    work_dir = Path(".work")
    issues_dir = work_dir / "agent" / "issues"
    focus_file = work_dir / "agent" / "focus.md"

    # Check if work directory exists
    if not work_dir.exists():
        console.print("[yellow]⚠ No .work/ directory found[/yellow]")
        console.print("[dim]Run 'dot-work init-tracking' to initialize issue tracking[/dim]")
        raise typer.Exit(1)

    # Parse focus.md
    focus_data: dict[str, str] = {"previous": "N/A", "current": "N/A", "next": "N/A"}
    if focus_file.exists():
        content = focus_file.read_text(encoding="utf-8")
        # Extract sections using simple regex patterns
        current_section = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("## Previous"):
                current_section = "previous"
            elif line.startswith("## Current"):
                current_section = "current"
            elif line.startswith("## Next"):
                current_section = "next"
            elif line.startswith("- Issue:") and current_section:
                issue_id = re.search(r"[\w-]+@[\w-]+", line)
                if issue_id:
                    focus_data[current_section] = issue_id.group(0)

    # Count issues in each priority file
    issue_counts: dict[str, int] = {}
    priority_files = {
        "shortlist": issues_dir / "shortlist.md",
        "critical": issues_dir / "critical.md",
        "high": issues_dir / "high.md",
        "medium": issues_dir / "medium.md",
        "low": issues_dir / "low.md",
        "backlog": issues_dir / "backlog.md",
    }

    for priority, file_path in priority_files.items():
        if file_path.exists():
            count = len(re.findall(r'^id: "', file_path.read_text(encoding="utf-8"), re.MULTILINE))
            issue_counts[priority] = count
        else:
            issue_counts[priority] = 0

    # Output based on format
    if format == "table":
        _status_table(console, focus_data, issue_counts)
    elif format == "markdown":
        _status_markdown(console, focus_data, issue_counts)
    elif format == "json":
        _status_json(console, focus_data, issue_counts)
    else:  # simple
        _status_simple(console, focus_data, issue_counts)


def _status_table(
    console: Console, focus_data: dict[str, str], issue_counts: dict[str, int]
) -> None:
    """Output status as Rich table."""
    # Focus table
    focus_table = Table(title="🎯 Current Focus", show_header=True, header_style="bold cyan")
    focus_table.add_column("Section", style="green")
    focus_table.add_column("Issue ID")

    for section, issue_id in [
        ("Previous", focus_data["previous"]),
        ("Current", focus_data["current"]),
        ("Next", focus_data["next"]),
    ]:
        style = "bold yellow" if section == "Current" and issue_id != "N/A" else ""
        focus_table.add_row(section, issue_id if style == "" else f"[{style}]{issue_id}[/]")

    console.print(focus_table)
    console.print()

    # Issue counts table
    counts_table = Table(title="📋 Issue Counts", show_header=True, header_style="bold cyan")
    counts_table.add_column("Priority", style="green")
    counts_table.add_column("Count", justify="right")
    counts_table.add_column("Status", style="dim")

    priority_colors = {
        "shortlist": ("bold red", "User Priority"),
        "critical": ("red", "P0"),
        "high": ("yellow", "P1"),
        "medium": ("blue", "P2"),
        "low": ("cyan", "P3"),
        "backlog": ("dim", "Backlog"),
    }

    total = 0
    for priority, _file_path in [
        ("shortlist", None),
        ("critical", None),
        ("high", None),
        ("medium", None),
        ("low", None),
        ("backlog", None),
    ]:
        count = issue_counts.get(priority, 0)
        total += count
        color, level = priority_colors.get(priority, ("white", ""))
        counts_table.add_row(priority.capitalize(), str(count), f"[{color}]{level}[/{color}]")

    counts_table.add_row("Total", str(total), "")

    console.print(counts_table)


def _status_markdown(
    console: Console, focus_data: dict[str, str], issue_counts: dict[str, int]
) -> None:
    """Output status as markdown."""
    console.print("## 🎯 Current Focus\n")
    for section, issue_id in [
        ("Previous", focus_data["previous"]),
        ("Current", focus_data["current"]),
        ("Next", focus_data["next"]),
    ]:
        marker = "**" if section == "Current" else ""
        console.print(f"- {marker}{section}{marker}: {issue_id}")

    console.print("\n## 📋 Issue Counts\n")
    console.print("| Priority | Count |")
    console.print("|----------|-------|")

    total = 0
    for priority in ["shortlist", "critical", "high", "medium", "low", "backlog"]:
        count = issue_counts.get(priority, 0)
        total += count
        level = {
            "shortlist": "User",
            "critical": "P0",
            "high": "P1",
            "medium": "P2",
            "low": "P3",
            "backlog": "Backlog",
        }.get(priority, "")
        console.print(f"| {priority.capitalize()} ({level}) | {count} |")

    console.print(f"| **Total** | **{total}** |")


def _status_json(
    console: Console, focus_data: dict[str, str], issue_counts: dict[str, int]
) -> None:
    """Output status as JSON."""
    output = {
        "focus": {
            "previous": focus_data["previous"],
            "current": focus_data["current"],
            "next": focus_data["next"],
        },
        "issue_counts": {
            "shortlist": issue_counts.get("shortlist", 0),
            "critical": issue_counts.get("critical", 0),
            "high": issue_counts.get("high", 0),
            "medium": issue_counts.get("medium", 0),
            "low": issue_counts.get("low", 0),
            "backlog": issue_counts.get("backlog", 0),
            "total": sum(issue_counts.values()),
        },
    }
    console.print(json.dumps(output, indent=2))


def _status_simple(
    console: Console, focus_data: dict[str, str], issue_counts: dict[str, int]
) -> None:
    """Output status as simple text."""
    console.print("🎯 Current Focus")
    console.print()
    for section, issue_id in [
        ("Previous", focus_data["previous"]),
        ("Current", focus_data["current"]),
        ("Next", focus_data["next"]),
    ]:
        prefix = "→ " if section == "Current" else "  "
        console.print(f"{prefix}{section}: {issue_id}")

    console.print()
    console.print("📋 Issue Counts")
    console.print()

    total = 0
    for priority in ["shortlist", "critical", "high", "medium", "low", "backlog"]:
        count = issue_counts.get(priority, 0)
        total += count
        console.print(f"  {priority.capitalize()}: {count}")

    console.print(f"  Total: {total}")


@app.command("plugins")
def plugins_cmd() -> None:
    """List installed dot-work plugins."""
    plugins_list = discover_plugins()

    if not plugins_list:
        console.print("[yellow]⚠ No plugins installed[/yellow]")
        console.print("\n[dim]Plugins can be installed with pip:[/dim]")
        console.print("  pip install dot-issues    # Issue tracking")
        console.print("  pip install dot-kg        # Knowledge graph")
        console.print("  pip install dot-review    # Code review")
        console.print("  pip install dot-container  # Docker containers")
        console.print("  pip install dot-git       # Git analysis")
        console.print("  pip install dot-python    # Python build tools")
        console.print("  pip install dot-version   # Version management")
        console.print("\n[dim]Or install all plugins:[/dim]")
        console.print("  pip install 'dot-work[all]'")
        return

    table = Table(title="🔌 Installed Plugins")
    table.add_column("Plugin", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Module", style="dim")

    for plugin in plugins_list:
        command = plugin.cli_group if plugin.cli_group else plugin.name
        version = plugin.version if plugin.version else "-"
        table.add_row(plugin.name, command, version, plugin.module)

    console.print(table)
    console.print(f"\n[green]✓ {len(plugins_list)} plugin(s) installed[/green]")


def _build_environment_options(discovered_envs: dict[str, set[str]] | None) -> list[str]:
    """Build list of environment options to show the user.

    Args:
        discovered_envs: If provided, only include environments with prompts.

    Returns:
        List of environment keys (e.g., ['copilot', 'claude']).
    """
    if discovered_envs:
        return sorted(discovered_envs.keys())
    return list(ENVIRONMENTS.keys())


def _display_environment_menu(
    options: list[str], discovered_envs: dict[str, set[str]] | None
) -> None:
    """Display the environment selection menu.

    Args:
        options: List of environment keys to display.
        discovered_envs: If provided, shows prompt counts.
    """
    console.print("\n[bold]🤖 Which AI coding environment are you using?[/bold]\n")

    if discovered_envs:
        console.print("[dim]Available environments (from prompt frontmatter):[/dim]\n")
        for i, key in enumerate(options, 1):
            env = ENVIRONMENTS.get(key)
            if env:
                prompt_count = len(discovered_envs[key])
                console.print(
                    f"  [cyan][{i}][/cyan] {env.name} [dim]({prompt_count} prompts)[/dim]"
                )
                if env.notes:
                    console.print(f"      [dim]└─ {env.notes}[/dim]")
            else:
                console.print(
                    f"  [cyan][{i}][/cyan] {key} [dim]({len(discovered_envs[key])} prompts)[/dim]"
                )
    else:
        for i, key in enumerate(options, 1):
            env = ENVIRONMENTS[key]
            console.print(f"  [cyan][{i}][/cyan] {env.name}")
            if env.notes:
                console.print(f"      [dim]└─ {env.notes}[/dim]")

    console.print()


def _validate_environment_choice(
    choice: str, options: list[str], discovered_envs: dict[str, set[str]] | None
) -> str | None:
    """Validate and process user's environment choice.

    Args:
        choice: User's input (number or environment key).
        options: List of valid environment keys.
        discovered_envs: If provided, warns when choice not in discovered.

    Returns:
        The validated environment key, or None if invalid/rejected.
    """
    # Try parsing as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
        console.print("[red]Invalid choice. Please try again.[/red]")
        return None
    except ValueError:
        pass

    # Check if environment key
    choice_lower = choice.lower()
    if choice_lower in options:
        return choice_lower

    if choice_lower in ENVIRONMENTS:
        # Not in options but valid environment
        if discovered_envs and choice_lower not in discovered_envs:
            console.print(
                f"[yellow]⚠ No prompts found for '{choice_lower}'. "
                f"Available: {', '.join(sorted(discovered_envs.keys()))}[/yellow]"
            )
            if typer.confirm("Continue anyway?", default=False):
                return choice_lower
            console.print("[red]Please enter a number or environment key.[/red]")
            return None
        return choice_lower

    console.print("[red]Invalid choice. Please try again.[/red]")
    return None


def prompt_for_environment(discovered_envs: dict[str, set[str]] | None = None) -> str:
    """Interactively ask the user which environment to use.

    Args:
        discovered_envs: Optional dict of environments discovered from prompt frontmatter.
            If provided, only show environments that have at least one prompt.
            Keys are environment names, values are sets of prompt names.
    """
    options = _build_environment_options(discovered_envs)
    _display_environment_menu(options, discovered_envs)

    while True:
        choice = typer.prompt("Enter number (or environment key)")
        result = _validate_environment_choice(choice, options, discovered_envs)
        if result:
            return result


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
        from importlib.metadata import version as get_version

        pkg_version = get_version("dot-work")
        console.print(f"dot-work version {pkg_version}")
        raise typer.Exit()

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


# =============================================================================
# Validate Subcommands
# =============================================================================


@validate_app.command("json")
def validate_json_cmd(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the JSON file to validate"),
    ],
    schema: Annotated[
        Path | None,
        typer.Option(
            "--schema",
            "-s",
            help="Optional JSON Schema file to validate against",
        ),
    ] = None,
) -> None:
    """Validate a JSON file for syntax errors and optionally against a schema."""
    from dot_work.tools.json_validator import validate_against_schema, validate_json_file

    file = file.resolve()

    if not file.exists():
        console.print(f"[red]❌ File not found:[/red] {file}")
        raise typer.Exit(1)

    console.print(f"[cyan]📋 Validating:[/cyan] {file.name}\n")

    # Syntax validation
    result = validate_json_file(file)

    if not result.valid:
        console.print("[red]❌ Syntax errors found:[/red]\n")
        for error in result.errors:
            console.print(f"  [red]•[/red] {error}")
            if error.context:
                console.print(f"    [dim]Context: ...{error.context}...[/dim]")
        raise typer.Exit(1)

    console.print("[green]✓[/green] JSON syntax is valid")

    # Schema validation if provided
    if schema:
        if not schema.exists():
            console.print(f"[red]❌ Schema file not found:[/red] {schema}")
            raise typer.Exit(1)

        import json

        try:
            schema_data = json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid schema file:[/red] {e}")
            raise typer.Exit(1) from None

        schema_result = validate_against_schema(result.data, schema_data)
        if not schema_result.valid:
            console.print("\n[red]❌ Schema validation errors:[/red]\n")
            for error in schema_result.errors:
                console.print(f"  [red]•[/red] {error.message}")
            raise typer.Exit(1)

        console.print("[green]✓[/green] Schema validation passed")

    # Show warnings
    if result.warnings:
        console.print(f"\n[yellow]⚠ {len(result.warnings)} warning(s):[/yellow]\n")
        for warning in result.warnings:
            console.print(f"  [yellow]•[/yellow] {warning}")

    console.print("\n[bold green]✅ Validation complete![/bold green]")


@validate_app.command("yaml")
def validate_yaml_cmd(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the YAML file to validate"),
    ],
    frontmatter: Annotated[
        bool,
        typer.Option(
            "--frontmatter",
            "-f",
            help="Treat file as markdown with YAML frontmatter",
        ),
    ] = False,
) -> None:
    """Validate a YAML file for syntax errors."""
    from dot_work.tools.yaml_validator import extract_frontmatter, validate_yaml_file

    file = file.resolve()

    if not file.exists():
        console.print(f"[red]❌ File not found:[/red] {file}")
        raise typer.Exit(1)

    console.print(f"[cyan]📋 Validating:[/cyan] {file.name}\n")

    if frontmatter:
        # Frontmatter mode
        content = file.read_text(encoding="utf-8")
        fm_result = extract_frontmatter(content)

        if not fm_result.valid:
            console.print("[red]❌ Frontmatter errors found:[/red]\n")
            for error in fm_result.errors:
                console.print(f"  [red]•[/red] {error}")
            raise typer.Exit(1)

        console.print("[green]✓[/green] YAML frontmatter is valid")
        if fm_result.frontmatter:
            console.print(f"    [dim]Keys: {', '.join(fm_result.frontmatter.keys())}[/dim]")
    else:
        # Full file mode
        yaml_result = validate_yaml_file(file)

        if not yaml_result.valid:
            console.print("[red]❌ Syntax errors found:[/red]\n")
            for error in yaml_result.errors:
                console.print(f"  [red]•[/red] {error}")
            raise typer.Exit(1)

        console.print("[green]✓[/green] YAML syntax is valid")

        # Show warnings
        if yaml_result.warnings:
            console.print(f"\n[yellow]⚠ {len(yaml_result.warnings)} warning(s):[/yellow]\n")
            for warning in yaml_result.warnings:
                console.print(f"  [yellow]•[/yellow] {warning}")

    console.print("\n[bold green]✅ Validation complete![/bold green]")


# Register the validate subcommand group
app.add_typer(validate_app, name="validate")


# Review subcommands have been exported to dot-review plugin


@canonical_app.command("validate")
def canonical_validate(
    prompt_file: Annotated[
        Path,
        typer.Argument(help="Path to canonical prompt file to validate"),
    ],
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Use strict validation mode"),
    ] = False,
) -> None:
    """Validate a canonical prompt file."""
    from dot_work.installer import validate_canonical_prompt_file

    try:
        validate_canonical_prompt_file(prompt_file, strict=strict)
        console.print(f"[green]✅[/green] {prompt_file} is a valid canonical prompt")
    except Exception as e:
        logger.error(f"Validation error for {prompt_file}: {e}", exc_info=True)
        console.print(f"[red]❌[/red] Validation failed: {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@canonical_app.command("install")
def canonical_install(
    prompt_file: Annotated[
        Path,
        typer.Argument(help="Path to canonical prompt file to install"),
    ],
    env: Annotated[
        str,
        typer.Option("--env", "-e", help="Target environment (copilot, claude, etc.)"),
    ],
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
        typer.Option("--force", "-f", help="Overwrite existing files"),
    ] = False,
) -> None:
    """Install a canonical prompt file to specified environment."""
    from dot_work.installer import install_canonical_prompt

    target = target.resolve()

    if not target.exists():
        console.print(f"[red]❌ Target directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    try:
        install_canonical_prompt(prompt_file, env, target, console, force=force)
        console.print(f"[green]✅[/green] Installed {prompt_file} for {env}")
    except Exception as e:
        logger.error(f"Canonical installation error for {prompt_file}: {e}", exc_info=True)
        console.print(f"[red]❌[/red] Installation failed: {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@canonical_app.command("extract")
def canonical_extract(
    prompt_file: Annotated[
        Path,
        typer.Argument(help="Path to canonical prompt file"),
    ],
    env: Annotated[
        str,
        typer.Option("--env", "-e", help="Environment to extract"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory (default: current directory)"),
    ] = Path("."),
) -> None:
    """Extract environment-specific prompt from canonical prompt."""
    from dot_work.prompts.canonical import extract_environment_file

    try:
        output_path = extract_environment_file(prompt_file, env, output_dir)
        console.print(f"[green]✅[/green] Extracted {env} prompt to {output_path}")
    except Exception as e:
        logger.error(f"Extraction error for {prompt_file}: {e}", exc_info=True)
        console.print(f"[red]❌[/red] Extraction failed: {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


# ============================================================================
# Prompt Management Commands (prompt_app)
# ============================================================================


@prompt_app.command("create")
def prompt_create(
    title: Annotated[
        str | None,
        typer.Option("--title", "-t", help="Prompt title (skip wizard prompt)"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Prompt description (skip wizard prompt)"),
    ] = None,
    type: Annotated[
        str | None,
        typer.Option(
            "--type",
            "-T",
            help="Prompt type (agent, command, review, other) - skip wizard prompt",
        ),
    ] = None,
    environments: Annotated[
        str | None,
        typer.Option(
            "--env",
            "-e",
            help="Comma-separated environment list (skip wizard prompt)",
        ),
    ] = None,
) -> None:
    """Create a new canonical prompt using an interactive wizard.

    This command launches an interactive wizard that guides you through
    creating a new prompt with proper canonical frontmatter.

    Wizard steps:
      1. Enter prompt title (required)
      2. Enter prompt description (required)
      3. Select prompt type (suggests appropriate environments)
      4. Select target environments
      5. Confirm configuration
      6. Create file with frontmatter
      7. Open editor for content

    The wizard generates valid canonical frontmatter and validates
    the created file using CanonicalPromptValidator.

    Examples:
        # Run full interactive wizard
        dot-work prompt create

        # Provide title upfront
        dot-work prompt create --title "My Review Prompt"

        # Provide all options non-interactively
        dot-work prompt create --title "Security Review" \\
            --description "Security-focused code review" \\
            --type review \\
            --env claude,cursor,copilot
    """
    from dot_work.prompts.wizard import create_prompt_interactive

    # Parse environments if provided
    env_list: list[str] | None = None
    if environments:
        env_list = [e.strip() for e in environments.split(",") if e.strip()]

    try:
        prompt_path = create_prompt_interactive(
            title=title,
            description=description,
            prompt_type=type,
            environments=env_list,
            console=console,
        )

        console.print()
        console.print(
            Panel(
                f"[green]✓[/green] Prompt created successfully!\n\n"
                f"[cyan]File:[/cyan] {prompt_path}\n\n"
                f"[dim]Next steps:[/dim]\n"
                f"  1. Edit the prompt content with specific guidelines\n"
                f"  2. Test with: [cyan]dot-work canonical validate {prompt_path}[/cyan]\n"
                f"  3. Install to your project with: [cyan]dot-work install[/cyan]",
                title="✨ Prompt Created",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Wizard cancelled.[/yellow]")
        raise typer.Exit(0) from None

    except Exception as e:
        logger.error(f"Prompt creation error: {e}", exc_info=True)
        console.print(f"\n[red]Error creating prompt:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


# Register the canonical subcommand group
app.add_typer(canonical_app, name="canonical")

# Register the prompt management subcommand group (also as 'prompts' alias)
app.add_typer(prompt_app, name="prompt")
app.add_typer(prompt_app, name="prompts")

# Review subcommand group is registered via dot-review plugin

# Register the zip subcommand group (retained in core)
app.add_typer(zip_app, name="zip")

# Register the skills subcommand group (retained in core)
app.add_typer(skills_app, name="skills")

# Register the subagents subcommand group (retained in core)
app.add_typer(subagents_app, name="subagents")

# Discover and register all plugins
# This registers submodules that have been extracted as plugins:
# - container (dot-container)
# - git (dot-git)
# - harness (dot-harness)
# - knowledge_graph (dot-kg)
# - python (dot-python)
# - version (dot-version)
# - review (dot-review)
# - db_issues (dot-issues)
# - overview (dot-overview)
register_all_plugins(app)


if __name__ == "__main__":
    app()
