"""CLI commands for Subagents management."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dot_work.subagents import (
    SUBAGENT_GENERATOR,
    SUBAGENT_PARSER,
    SUBAGENT_VALIDATOR,
    SubagentDiscovery,
)
from dot_work.subagents.environments import get_supported_environments
from dot_work.utils.sanitization import sanitize_error_message

logger = logging.getLogger(__name__)

subagents_app = typer.Typer(help="Subagents management commands.")
console = Console()


@subagents_app.command("list")
def list_subagents(
    environment: Annotated[
        str,
        typer.Option(
            "--env",
            "-e",
            help="Environment to query (claude, opencode, copilot)",
        ),
    ] = "claude",
    search_paths: Annotated[
        list[Path] | None,
        typer.Option(
            "--path",
            "-p",
            help="Additional search paths for canonical subagents",
        ),
    ] = None,
) -> None:
    """List all discovered subagents.

    Searches for native subagents in the environment-specific directory
    and any additional canonical paths specified via --path.

    Example:
        dot-work subagents list
        dot-work subagents list --env opencode
        dot-work subagents list --env copilot --path ./custom-subagents
    """
    try:
        # Build discovery
        discovery = SubagentDiscovery(
            project_root=".",
            environment=environment,
            canonical_paths=search_paths,
        )

        # Discover native subagents
        native_subagents = discovery.discover_native()

        if not native_subagents:
            console.print(f"[yellow]No subagents found for environment '{environment}'.[/yellow]")
            console.print(
                f"\n[dim]Create a {discovery.adapter.get_target_path(Path('.'))} directory "
                f"and add subagent .md files.[/dim]"
            )
            raise typer.Exit(0)

        # Display subagents in a table
        table = Table(title=f"Discovered Subagents ({environment})")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Model", style="dim")
        table.add_column("Tools", style="dim")

        for subagent in native_subagents:
            model_str = subagent.model or "inherit"
            tools_str = f"{len(subagent.tools)} tool(s)" if subagent.tools else "all"
            # Truncate description for table
            desc = (
                subagent.description[:60] + "..."
                if len(subagent.description) > 60
                else subagent.description
            )
            table.add_row(subagent.name, desc, model_str, tools_str)

        console.print()
        console.print(table)
        console.print()
        console.print(f"Found {len(native_subagents)} subagent(s)")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error listing subagents: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("validate")
def validate_subagent(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to subagent file or directory",
        ),
    ],
) -> None:
    """Validate a subagent file or directory.

    Performs comprehensive validation including:
    - Required fields (name, description)
    - Name format (lowercase, hyphens, length)
    - Description length and content
    - File format and structure

    Example:
        dot-work subagents validate .work/subagents/code-reviewer.md
        dot-work subagents validate .claude/agents/code-reviewer.md
    """
    try:
        # Run validation
        result = SUBAGENT_VALIDATOR.validate(path)

        # Display results
        if result.valid:
            if result.warnings:
                console.print(
                    Panel(
                        f"[green]✓[/green] Subagent is valid with {len(result.warnings)} warning(s)\n\n"
                        + "\n".join(f"[yellow]⚠[/yellow] {w}" for w in result.warnings),
                        title="✓ Valid",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        "[green]✓[/green] Subagent is valid (no warnings)",
                        title="✓ Valid",
                        border_style="green",
                    )
                )
        else:
            error_list = "\n".join(f"[red]✗[/red] {e}" for e in result.errors)
            warning_list = "\n".join(f"[yellow]⚠[/yellow] {w}" for w in result.warnings)

            console.print(
                Panel(
                    f"{error_list}\n\n{warning_list}" if result.warnings else error_list,
                    title="✗ Invalid",
                    border_style="red",
                )
                if result.errors or result.warnings
                else Panel("Unknown error", border_style="red")
            )
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error validating subagent: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("show")
def show_subagent(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the subagent to display",
        ),
    ],
    environment: Annotated[
        str,
        typer.Option(
            "--env",
            "-e",
            help="Environment to query (claude, opencode, copilot)",
        ),
    ] = "claude",
) -> None:
    """Display full subagent details including metadata and prompt.

    Example:
        dot-work subagents show code-reviewer
        dot-work subagents show code-reviewer --env opencode
    """
    try:
        discovery = SubagentDiscovery(project_root=".", environment=environment)

        # Load subagent
        config = discovery.load_native(name)

        # Display subagent
        console.print()
        console.print(Panel(f"[cyan]{config.name}[/cyan]", border_style="cyan"))

        # Metadata
        console.print()
        console.print("[bold]Metadata:[/bold]")
        console.print(f"  Description: {config.description}")
        if config.model:
            console.print(f"  Model: {config.model}")
        if config.permission_mode:
            console.print(f"  Permission Mode: {config.permission_mode}")

        # Tools
        if config.tools:
            console.print()
            console.print("[bold]Tools:[/bold]")
            for tool in config.tools:
                console.print(f"  - {tool}")

        # Skills (Claude Code)
        if config.skills:
            console.print()
            console.print("[bold]Skills:[/bold]")
            for skill in config.skills:
                console.print(f"  - {skill}")

        # Content
        console.print()
        console.print("[bold]Prompt:[/bold]")
        console.print(config.prompt)

    except FileNotFoundError:
        console.print(
            f"[red]Error:[/red] Subagent {name!r} not found in environment '{environment}'"
        )
        console.print(
            f"\n[dim]Available subagents: {', '.join(discovery.list_available_names())}[/dim]"
        )
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error showing subagent: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("generate")
def generate_native(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to canonical subagent file",
        ),
    ],
    environment: Annotated[
        str,
        typer.Option(
            "--env",
            "-e",
            help="Target environment (claude, opencode, copilot)",
        ),
    ] = "claude",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: stdout)",
        ),
    ] = None,
) -> None:
    """Generate native subagent file from canonical definition.

    This generates the environment-specific subagent file content
    from a canonical subagent definition.

    Example:
        dot-work subagents generate .work/subagents/code-reviewer.md --env claude
        dot-work subagents generate .work/subagents/code-reviewer.md --env opencode -o .opencode/agent/code-reviewer.md
    """
    try:
        # Parse canonical subagent
        canonical = SUBAGENT_PARSER.parse(path)

        # Generate native content
        content = SUBAGENT_GENERATOR.generate_native(canonical, environment)

        # Output to file or stdout
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]✓[/green] Generated: {output}")
        else:
            console.print()
            console.print(
                Panel(
                    content,
                    title=f"<{environment} subagent>",
                    border_style="cyan",
                )
            )

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Canonical subagent file not found: {path}")
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error generating native file: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("sync")
def sync_subagents(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to canonical subagent file",
        ),
    ],
) -> None:
    """Sync canonical subagent to all configured environments.

    Generates and writes native subagent files for all environments
    defined in the canonical subagent.

    Example:
        dot-work subagents sync .work/subagents/code-reviewer.md
    """
    try:
        # Parse canonical subagent
        canonical = SUBAGENT_PARSER.parse(path)

        if not canonical.environments:
            console.print("[yellow]Warning:[/yellow] No environments defined in canonical subagent")
            raise typer.Exit(0)

        # Generate for all environments
        generated = SUBAGENT_GENERATOR.generate_all(canonical, Path("."))

        if not generated:
            console.print("[yellow]No subagent files generated.[/yellow]")
            raise typer.Exit(0)

        # Display results
        console.print()
        console.print(
            Panel(
                "\n".join(f"[green]✓[/green] {env}: {path}" for env, path in generated.items()),
                title=f"✨ Synced {canonical.meta.name}",
                border_style="green",
            )
        )

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Canonical subagent file not found: {path}")
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error syncing subagents: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("init")
def init_subagent(
    name: Annotated[
        str,
        typer.Argument(
            help="Subagent name (lowercase, hyphens)",
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Subagent description",
        ),
    ],
    environments: Annotated[
        list[str] | None,
        typer.Option(
            "--env",
            "-e",
            help="Environments to include (claude, opencode, copilot)",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: .work/subagents/<name>.md)",
        ),
    ] = None,
) -> None:
    """Initialize a new canonical subagent template.

    Creates a template file for a new canonical subagent with
    the specified name and environments.

    Example:
        dot-work subagents init code-reviewer --description "Expert code reviewer"
        dot-work subagents init debugger --description "Root cause analysis" --env claude opencode
    """
    try:
        # Generate template
        template = SUBAGENT_GENERATOR.generate_canonical_template(
            name=name,
            description=description,
            environments=environments,
        )

        # Determine output path
        if output is None:
            output_dir = Path(".work/subagents")
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / f"{name}.md"

        # Write template
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(template, encoding="utf-8")

        console.print()
        console.print(
            Panel(
                f"[green]✓[/green] Created canonical subagent template\n\n"
                f"[cyan]Name:[/cyan] {name}\n"
                f"[cyan]Description:[/cyan] {description}\n"
                f"[cyan]Output:[/cyan] {output}\n"
                f"[cyan]Environments:[/cyan] {', '.join(environments or ['claude', 'opencode', 'copilot'])}\n\n"
                f"[dim]Edit the file to customize the subagent, then run:[/dim]\n"
                f"[dim]  dot-work subagents sync {output}[/dim]",
                title="✨ Subagent Initialized",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error initializing subagent: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@subagents_app.command("envs")
def list_environments() -> None:
    """List supported environments for subagent deployment.

    Example:
        dot-work subagents envs
    """
    try:
        envs = get_supported_environments()

        console.print()
        console.print("[bold]Supported Environments:[/bold]")
        console.print()

        for env in envs:
            adapter = SubagentDiscovery(project_root=".", environment=env).adapter
            console.print(f"  [cyan]{env}[/cyan]")
            console.print(f"    Target: {adapter.DEFAULT_TARGET}")

        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error listing environments: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


app = subagents_app
