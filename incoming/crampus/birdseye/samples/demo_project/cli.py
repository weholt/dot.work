"""CLI interface for the sample project."""

import typer

app = typer.Typer()


@app.command()
def greet(name: str) -> None:
    """Print a greeting for command line users."""
    typer.echo(f"Hello {name}")
