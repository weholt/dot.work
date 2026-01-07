"""CLI commands for Agent Skills management."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dot_work.skills import (
    DEFAULT_DISCOVERY,
    SKILL_VALIDATOR,
    SkillDiscovery,
    generate_skills_prompt,
)
from dot_work.utils.sanitization import sanitize_error_message

logger = logging.getLogger(__name__)

skills_app = typer.Typer(help="Agent Skills management commands.")
console = Console()


@skills_app.command("list")
def list_skills(
    search_paths: Annotated[
        list[Path] | None,
        typer.Option(
            "--path",
            "-p",
            help="Additional search paths for skills",
        ),
    ] = None,
) -> None:
    """List all discovered Agent Skills.

    Searches for skills in default locations (.skills/, ~/.config/dot-work/skills/)
    and any additional paths specified via --path.

    Example:
        dot-work skills list
        dot-work skills list --path ./custom-skills --path ~/more-skills
    """
    try:
        # Build search paths
        paths: list[Path] = []
        if search_paths:
            paths.extend(search_paths)

        discovery = SkillDiscovery(search_paths=paths) if paths else DEFAULT_DISCOVERY

        # Discover skills
        skills = discovery.discover()

        if not skills:
            console.print("[yellow]No skills found.[/yellow]")
            console.print(
                "\n[dim]Create a .skills/ directory and add SKILL.md files to define skills.[/dim]"
            )
            raise typer.Exit(0)

        # Display skills in a table
        table = Table(title="Discovered Agent Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("License", style="dim")

        for skill in skills:
            license_str = skill.license or "Unspecified"
            # Truncate description for table
            desc = (
                skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
            )
            table.add_row(skill.name, desc, license_str)

        console.print()
        console.print(table)
        console.print()
        console.print(f"Found {len(skills)} skill(s)")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error listing skills: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@skills_app.command("validate")
def validate_skill(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to skill directory or SKILL.md file",
        ),
    ],
) -> None:
    """Validate a skill directory or SKILL.md file.

    Performs comprehensive validation including:
    - Required fields (name, description)
    - Name format (lowercase, hyphens, length)
    - Description length and content
    - Directory structure
    - SKILL.md presence and format

    Example:
        dot-work skills validate .skills/my-skill
        dot-work skills validate .skills/my-skill/SKILL.md
    """
    try:
        # Resolve path
        skill_dir = path
        if path.name == "SKILL.md":
            skill_dir = path.parent

        # Run validation
        result = SKILL_VALIDATOR.validate_directory(skill_dir)

        # Display results
        if result.valid:
            if result.warnings:
                console.print(
                    Panel(
                        f"[green]✓[/green] Skill is valid with {len(result.warnings)} warning(s)\n\n"
                        + "\n".join(f"[yellow]⚠[/yellow] {w}" for w in result.warnings),
                        title="✓ Valid",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        "[green]✓[/green] Skill is valid (no warnings)",
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
        logger.error(f"Error validating skill: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@skills_app.command("show")
def show_skill(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the skill to display",
        ),
    ],
) -> None:
    """Display full skill content including metadata and body.

    Example:
        dot-work skills show pdf-processing
    """
    try:
        discovery = DEFAULT_DISCOVERY

        # Load skill
        skill = discovery.load_skill(name)

        # Display skill
        console.print()
        console.print(Panel(f"[cyan]{skill.meta.name}[/cyan]", border_style="cyan"))

        # Metadata
        console.print()
        console.print("[bold]Metadata:[/bold]")
        console.print(f"  Description: {skill.meta.description}")
        if skill.meta.license:
            console.print(f"  License: {skill.meta.license}")
        if skill.meta.compatibility:
            console.print(f"  Compatibility: {skill.meta.compatibility}")
        if skill.meta.metadata:
            console.print("  Additional Metadata:")
            for key, value in skill.meta.metadata.items():
                console.print(f"    {key}: {value}")

        # Resources
        if skill.scripts or skill.references or skill.assets:
            console.print()
            console.print("[bold]Resources:[/bold]")
            if skill.scripts:
                console.print(f"  Scripts: {len(skill.scripts)} file(s)")
            if skill.references:
                console.print(f"  References: {len(skill.references)} file(s)")
            if skill.assets:
                console.print(f"  Assets: {len(skill.assets)} file(s)")

        # Content
        console.print()
        console.print("[bold]Content:[/bold]")
        console.print(skill.content)

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Skill {name!r} not found")
        console.print(
            f"\n[dim]Available skills: {', '.join(s.name for s in DEFAULT_DISCOVERY.discover())}[/dim]"
        )
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error showing skill: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@skills_app.command("prompt")
def generate_prompt(
    include_paths: Annotated[
        bool,
        typer.Option(
            "--paths/--no-paths",
            help="Include file paths in output",
        ),
    ] = True,
) -> None:
    """Generate available_skills XML prompt for all discovered skills.

    This generates the XML that can be injected into agent system prompts
    to inform them about available skills.

    Example:
        dot-work skills prompt
        dot-work skills prompt --no-paths
    """
    try:
        discovery = DEFAULT_DISCOVERY
        skills = discovery.discover()

        if not skills:
            console.print("[yellow]No skills found.[/yellow]")
            raise typer.Exit(0)

        # Generate XML prompt
        xml_prompt = generate_skills_prompt(skills, include_paths=include_paths)

        # Display XML
        console.print()
        console.print(Panel(xml_prompt, title="<available_skills>", border_style="cyan"))

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        logger.error(f"Error generating prompt: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


@skills_app.command("install")
def install_skill(
    source: Annotated[
        Path,
        typer.Argument(
            help="Path to skill directory or SKILL.md file to install",
        ),
    ],
    target: Annotated[
        Path,
        typer.Option(
            "--target",
            "-t",
            help="Target installation directory (default: .skills/)",
        ),
    ] = Path(".skills"),
) -> None:
    """Install a skill to the project .skills/ directory.

    Copies the skill directory to .skills/<skill-name>/.

    Example:
        dot-work skills install ~/my-skills/pdf-processing
        dot-work skills install ~/my-skills/pdf-processing/SKILL.md
    """
    import shutil

    try:
        # Resolve source path
        source_dir = source
        if source.name == "SKILL.md":
            source_dir = source.parent

        if not source_dir.exists():
            console.print(f"[red]Error:[/red] Source path does not exist: {source}")
            raise typer.Exit(1)

        # Validate source skill
        result = SKILL_VALIDATOR.validate_directory(source_dir)
        if not result.valid:
            console.print("[red]Error:[/red] Source skill is invalid")
            for error in result.errors:
                console.print(f"  [red]✗[/red] {error}")
            raise typer.Exit(1)

        # Get skill name from source directory
        skill_name = source_dir.name

        # Create target directory
        target.mkdir(parents=True, exist_ok=True)
        target_dir = target / skill_name

        # Copy skill directory
        if target_dir.exists():
            console.print(f"[yellow]Warning:[/yellow] Target already exists: {target_dir}")
            if not typer.confirm(f"Overwrite {target_dir}?"):
                console.print("[dim]Installation cancelled.[/dim]")
                raise typer.Exit(0)
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)

        console.print()
        console.print(
            Panel(
                f"[green]✓[/green] Skill installed successfully!\n\n"
                f"[cyan]Source:[/cyan] {source_dir}\n"
                f"[cyan]Target:[/cyan] {target_dir}\n\n"
                f"[dim]Verify with:[/dim] dot-work skills validate {target_dir}",
                title="✨ Skill Installed",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0) from None
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error installing skill: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] {sanitize_error_message(e)}")
        raise typer.Exit(1) from e


app = skills_app
