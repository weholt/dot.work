"""CLI commands for zip functionality.

This module provides Typer CLI commands for creating and uploading zip archives
respecting .gitignore patterns.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from dot_work.zip.config import ZipConfig

console = Console()

app = typer.Typer(help="Zip folders respecting .gitignore.")


@app.callback(invoke_without_command=True)
def zip_callback(
    ctx: typer.Context,
    folder: Annotated[
        Path | None,
        typer.Argument(
            help="Folder to zip",
            show_default=False,
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output zip file path (default: <folder>.zip in current directory)",
        ),
    ] = None,
    upload_to_api: Annotated[
        bool,
        typer.Option(
            "--upload",
            "-u",
            help="Upload to configured API endpoint after creating zip",
        ),
    ] = False,
) -> None:
    """Create a zip archive of a folder, respecting .gitignore patterns.

    If no subcommand is specified, creates a zip file. Otherwise, invokes the subcommand.

    Examples:
        dot-work zip my-folder
        dot-work zip my-folder --output custom.zip
        dot-work zip my-folder --upload
        dot-work zip upload my-file.zip
    """
    # If a subcommand was specified, let it handle execution
    if ctx.invoked_subcommand is not None:
        return

    # Otherwise, handle default behavior (create)
    if folder is None:
        console.print("[yellow]WARNING: No folder specified[/yellow]")
        raise typer.Exit(1)

    _create_zip_internal(
        folder=folder,
        output=output,
        upload=upload_to_api,
    )


@app.command("create")
def create(
    folder: Annotated[
        Path,
        typer.Argument(help="Folder to zip"),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output zip file path (default: <folder>.zip in current directory)",
        ),
    ] = None,
    upload_file: Annotated[
        bool,
        typer.Option(
            "--upload",
            "-u",
            help="Upload to configured API endpoint after creating zip",
        ),
    ] = False,
) -> None:
    """Create a zip archive of a folder, respecting .gitignore patterns."""
    try:
        _create_zip_internal(folder=folder, output=output, upload=upload_file)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1) from e


def _create_zip_internal(folder: Path, output: Path | None, upload: bool) -> None:
    """Internal implementation of zip create functionality."""
    # Lazy import to defer dependency errors
    from dot_work.zip import zip_folder

    folder = folder.resolve()

    # Determine output path
    if output is None:
        output_path = Path.cwd() / f"{folder.name}.zip"
    else:
        output_path = output.resolve()

    # Validate folder
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    # Create zip archive
    try:
        console.print(f"[cyan]Creating zip archive:[/cyan] {folder} -> {output_path}")
        zip_folder(folder, output_path)
        console.print("[green]SUCCESS: Zip created[/green]")
        console.print(f"[dim]   Location: {output_path}[/dim]")
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        console.print(f"[dim]   Size: {file_size_mb:.2f} MB[/dim]")
    except ImportError as e:
        console.print(f"[red]ERROR: Missing dependency:[/red] {e}")
        raise typer.Exit(1) from e

    # Upload if requested
    if upload:
        _upload_zip_internal(output_path)


@app.command("upload")
def upload(
    file: Annotated[
        Path,
        typer.Argument(help="Zip file to upload"),
    ],
) -> None:
    """Upload a zip file to the configured API endpoint."""
    try:
        _upload_zip_internal(file)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1) from e


def _upload_zip_internal(file: Path) -> None:
    """Internal implementation of zip upload functionality."""
    # Lazy import to defer dependency errors
    from dot_work.zip import upload_zip

    file = file.resolve()

    # Validate file
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")

    if not file.is_file():
        raise ValueError(f"Not a file: {file}")

    if file.suffix != ".zip":
        raise ValueError(f"File is not a zip archive: {file}")

    # Load config
    config = ZipConfig.from_env()

    if not config.upload_url:
        raise ValueError(
            "No upload URL configured. Set the DOT_WORK_ZIP_UPLOAD_URL environment variable."
        )

    # Upload
    try:
        console.print(f"[cyan]Uploading zip:[/cyan] {file}")
        console.print(f"[dim]   To: {config.upload_url}[/dim]")

        upload_zip(file, config.upload_url)

        console.print("[green]SUCCESS: Upload complete[/green]")
    except ImportError as e:
        console.print(f"[red]ERROR: Missing dependency:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]ERROR: Upload failed:[/red] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
