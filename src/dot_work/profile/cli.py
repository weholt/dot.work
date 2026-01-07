"""CLI commands for user profile management."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from dot_work.profile.models import (
    PROFILE_PATH,
    UserProfile,
    load_profile,
    save_profile,
    validate_profile,
)
from dot_work.utils.sanitization import sanitize_error_message

logger = logging.getLogger(__name__)

profile_app = typer.Typer(help="Manage user profile information.")


@profile_app.command("init")
def init_profile() -> None:
    """Initialize user profile with an interactive wizard."""
    from rich.console import Console

    console = Console()

    # Check if profile already exists
    if PROFILE_PATH.exists():
        console.print("\n[yellow]Profile already exists at [/yellow]")
        console.print(f"[cyan]{PROFILE_PATH}[/cyan]\n")
        if not Confirm.ask("Overwrite existing profile?", default=False):
            console.print("[yellow]Profile initialization cancelled.[/yellow]")
            return

    # Welcome screen
    console.print(
        Panel.fit(
            "[bold cyan]Welcome to dot-work Profile Setup[/bold cyan]\n\n"
            "Let's configure your developer profile. This information will be "
            "used across all dot-work projects.",
            title=":bust_in_silhouette: Profile Setup",
        )
    )

    # Collect standard fields with rich prompts
    console.print("\n[bold]Basic Information[/bold]")
    first_name = Prompt.ask("First name")
    last_name = Prompt.ask("Last name")
    username = Prompt.ask(
        "Username", default=f"{first_name.lower()}{last_name.lower()}".replace(" ", "")
    )
    github_username = Prompt.ask("GitHub username")
    email = Prompt.ask("Email")

    # License selection with choices
    console.print("\n[bold]Default License[/bold]")
    console.print("Choose a default license for your code files:")
    console.print("  1. MIT")
    console.print("  2. Apache-2.0")
    console.print("  3. GPL-3.0")
    console.print("  4. BSD-3-Clause")
    license_choice = Prompt.ask("Select license", choices=["1", "2", "3", "4"], default="1")
    license_map = {"1": "MIT", "2": "Apache-2.0", "3": "GPL-3.0", "4": "BSD-3-Clause"}
    default_license = license_map[license_choice]

    # Create profile
    now = datetime.now().isoformat()
    profile = UserProfile(
        username=username,
        github_username=github_username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        default_license=default_license,
        created_at=now,
        updated_at=now,
        _exported_fields=["username", "email", "github_username"],
    )

    # Custom fields option
    if Confirm.ask("\nWould you like to add custom fields?", default=False):
        console.print("\n[bold]Custom Fields[/bold]")
        console.print("You can add any custom fields (e.g., company, timezone).")
        console.print("Press Enter with empty name to finish.\n")

        while True:
            field_name = Prompt.ask("Field name", default="")
            if not field_name:
                break
            field_value = Prompt.ask(f"Value for '{field_name}'")
            profile.set(field_name, field_value)

            if Confirm.ask(f"Export '{field_name}' to agents/CLI?", default=False):
                profile.add_export(field_name)

    # Summary table
    table = Table(title=":memo: Profile Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    for key in ["username", "email", "github_username", "default_license"]:
        value = getattr(profile, key, "")
        table.add_row(key, str(value))

    for key, value in profile._custom_fields.items():
        exported = ":heavy_check_mark:" if profile.is_exported(key) else ""
        table.add_row(f"{key} {exported}", str(value))

    console.print("\n")
    console.print(table)

    if Confirm.ask("\n[bold]Save this profile?[/bold]", default=True):
        # Validate before saving
        errors = validate_profile(profile)
        if errors:
            console.print("\n[red]Profile validation errors:[/red]")
            for error in errors:
                console.print(f"  :x: {error}")
            if not Confirm.ask("\nSave anyway?", default=False):
                console.print("[yellow]Profile not saved.[/yellow]")
                return

        save_profile(profile)
        console.print(f"[green]:check_mark:[/green] Profile saved to {PROFILE_PATH}")
    else:
        console.print("[yellow]Profile not saved.[/yellow]")


@profile_app.command("show")
def show_profile() -> None:
    """Display current profile information."""
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    # Create table
    table = Table(title=":bust_in_silhouette: User Profile")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Exported", style="yellow")

    # Standard fields
    for key in [
        "username",
        "github_username",
        "first_name",
        "last_name",
        "email",
        "default_license",
        "created_at",
        "updated_at",
    ]:
        value = getattr(profile, key, "")
        if value:
            exported = ":heavy_check_mark:" if profile.is_exported(key) else ""
            table.add_row(key, str(value), exported)

    # Custom fields
    for key, value in profile._custom_fields.items():
        exported = ":heavy_check_mark:" if profile.is_exported(key) else ""
        table.add_row(key, str(value), exported)

    console.print("\n")
    console.print(table)
    console.print()


@profile_app.command("set")
def set_profile_field(
    field: Annotated[str, typer.Argument(help="Field name to set")],
    value: Annotated[str, typer.Argument(help="Value to set")],
) -> None:
    """Set a profile field value.

    Can set both standard fields (username, email, etc.) and custom fields.
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    profile.set(field, value)
    save_profile(profile)

    console.print(f"[green]:check_mark:[/green] Set [cyan]{field}[/cyan] = [cyan]{value}[/cyan]")


@profile_app.command("get")
def get_profile_field(
    field: Annotated[str, typer.Argument(help="Field name to get")],
) -> None:
    """Get a profile field value.

    Outputs only the field value to stdout, useful for scripting:
        dot-work profile get email
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    value = profile.get(field, "")
    if value == "":
        console.print(f"\n[yellow]Field '{field}' not found or is empty[/yellow]\n")
        raise typer.Exit(1)

    console.print(value)


@profile_app.command("add-field")
def add_custom_field(
    name: Annotated[str, typer.Argument(help="Custom field name")],
    value: Annotated[str, typer.Argument(help="Custom field value")],
    export: Annotated[
        bool,
        typer.Option("--export", "-e", help="Add field to export list"),
    ] = False,
) -> None:
    """Add a custom field to the profile.

    Example:
        dot-work profile add-field company "Acme Corp" --export
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    profile.add_custom_field(name, value, export=export)
    save_profile(profile)

    export_msg = " (exported)" if export else ""
    console.print(
        f"[green]:check_mark:[/green] Added field [cyan]{name}[/cyan]"
        f" = [cyan]{value}[/cyan]{export_msg}"
    )


@profile_app.command("remove-field")
def remove_custom_field(
    name: Annotated[str, typer.Argument(help="Custom field name to remove")],
) -> None:
    """Remove a custom field from the profile.

    Cannot remove standard fields (username, email, etc.).

    Example:
        dot-work profile remove-field company
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    if name in {
        "username",
        "github_username",
        "first_name",
        "last_name",
        "email",
        "default_license",
    }:
        console.print(f"\n[red]Cannot remove standard field '{name}'[/red]")
        console.print("Use [cyan]dot-work profile set[/cyan] to update standard fields.\n")
        raise typer.Exit(1)

    if profile.remove_custom_field(name):
        save_profile(profile)
        console.print(f"[green]:check_mark:[/green] Removed field [cyan]{name}[/cyan]")
    else:
        console.print(f"\n[yellow]Custom field '{name}' not found[/yellow]\n")
        raise typer.Exit(1)


# Export subcommand group
export_app = typer.Typer(help="Manage profile field exports.")


@export_app.command("add")
def add_export(
    field: Annotated[str, typer.Argument(help="Field name to export")],
) -> None:
    """Add a field to the export list.

    Exported fields are available to agents and CLI auto-population.

    Example:
        dot-work profile export add company
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    # Check if field exists
    if field not in profile.to_dict() or field.startswith("_"):
        console.print(f"\n[red]Field '{field}' does not exist[/red]\n")
        raise typer.Exit(1)

    if profile.add_export(field):
        save_profile(profile)
        console.print(f"[green]:check_mark:[/green] Exporting field [cyan]{field}[/cyan]")
    else:
        console.print(f"\n[yellow]Field '{field}' is already exported[/yellow]\n")


@export_app.command("remove")
def remove_export(
    field: Annotated[str, typer.Argument(help="Field name to stop exporting")],
) -> None:
    """Remove a field from the export list.

    Example:
        dot-work profile export remove company
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    if profile.remove_export(field):
        save_profile(profile)
        console.print(f"[green]:check_mark:[/green] Stopped exporting [cyan]{field}[/cyan]")
    else:
        console.print(f"\n[yellow]Field '{field}' is not exported[/yellow]\n")


@export_app.command("list")
def list_exports() -> None:
    """List all exported fields.

    Example:
        dot-work profile export list
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    if not profile._exported_fields:
        console.print("\n[yellow]No exported fields[/yellow]\n")
        return

    table = Table(title="Exported Fields")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    for key in profile._exported_fields:
        value = profile.get(key, "")
        table.add_row(key, str(value))

    console.print("\n")
    console.print(table)
    console.print()


@profile_app.command("delete")
def delete_profile(
    confirm: Annotated[
        bool,
        typer.Option(
            "--confirm",
            "-y",
            help="Confirm deletion without prompt",
        ),
    ] = False,
) -> None:
    """Delete the profile file.

    Example:
        dot-work profile delete --confirm
    """
    from rich.console import Console

    console = Console()

    if not PROFILE_PATH.exists():
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]\n")
        raise typer.Exit(1)

    if not confirm:
        if not Confirm.ask(
            "\n[red]Are you sure you want to delete your profile?[/red] This cannot be undone.",
            default=False,
        ):
            console.print("[yellow]Profile deletion cancelled.[/yellow]")
            return

    try:
        PROFILE_PATH.unlink()
        console.print(f"[green]:check_mark:[/green] Profile deleted from {PROFILE_PATH}")
    except OSError as e:
        console.print(f"\n[red]Error deleting profile:[/red] {sanitize_error_message(e)}\n")
        raise typer.Exit(1) from e


@profile_app.command("edit")
def edit_profile() -> None:
    """Edit profile interactively.

    Launches the profile wizard with current values pre-filled.

    Example:
        dot-work profile edit
    """
    from rich.console import Console

    console = Console()

    profile = load_profile()
    if not profile:
        console.print(f"\n[yellow]No profile found at {PROFILE_PATH}[/yellow]")
        console.print("Run [cyan]dot-work profile init[/cyan] to create one.\n")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            "[bold cyan]Edit Your Profile[/bold cyan]\n\nPress Enter to keep existing values.",
            title=":bust_in_silhouette: Profile Editor",
        )
    )

    # Edit standard fields
    console.print("\n[bold]Basic Information[/bold]")
    first_name = Prompt.ask("First name", default=profile.first_name)
    last_name = Prompt.ask("Last name", default=profile.last_name)
    username = Prompt.ask("Username", default=profile.username)
    github_username = Prompt.ask("GitHub username", default=profile.github_username)
    email = Prompt.ask("Email", default=profile.email)

    # License selection
    console.print("\n[bold]Default License[/bold]")
    console.print("Choose a default license for your code files:")
    console.print("  1. MIT")
    console.print("  2. Apache-2.0")
    console.print("  3. GPL-3.0")
    console.print("  4. BSD-3-Clause")

    license_to_num = {
        "MIT": "1",
        "Apache-2.0": "2",
        "GPL-3.0": "3",
        "BSD-3-Clause": "4",
    }
    default_choice = license_to_num.get(profile.default_license, "1")

    license_choice = Prompt.ask(
        "Select license", choices=["1", "2", "3", "4"], default=default_choice
    )
    license_map = {"1": "MIT", "2": "Apache-2.0", "3": "GPL-3.0", "4": "BSD-3-Clause"}
    default_license = license_map[license_choice]

    # Update profile
    profile.first_name = first_name
    profile.last_name = last_name
    profile.username = username
    profile.github_username = github_username
    profile.email = email
    profile.default_license = default_license

    # Summary table
    table = Table(title=":memo: Updated Profile")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    for key in ["username", "email", "github_username", "default_license"]:
        value = getattr(profile, key, "")
        table.add_row(key, str(value))

    for key, value in profile._custom_fields.items():
        exported = ":heavy_check_mark:" if profile.is_exported(key) else ""
        table.add_row(f"{key} {exported}", str(value))

    console.print("\n")
    console.print(table)

    if Confirm.ask("\n[bold]Save these changes?[/bold]", default=True):
        # Validate before saving
        errors = validate_profile(profile)
        if errors:
            console.print("\n[red]Profile validation errors:[/red]")
            for error in errors:
                console.print(f"  :x: {error}")
            if not Confirm.ask("\nSave anyway?", default=False):
                console.print("[yellow]Changes not saved.[/yellow]")
                return

        save_profile(profile)
        console.print(f"[green]:check_mark:[/green] Profile saved to {PROFILE_PATH}")
    else:
        console.print("[yellow]Changes not saved.[/yellow]")


# Register export subcommand group
profile_app.add_typer(export_app, name="export")
