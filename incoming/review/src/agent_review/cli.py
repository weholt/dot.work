"""CLI entry point for agent-review."""

from __future__ import annotations

import webbrowser

import typer
import uvicorn

from agent_review.exporter import export_agent_md
from agent_review.git import ensure_git_repo
from agent_review.server import create_app, pick_port
from agent_review.storage import latest_review_id

app = typer.Typer(
    name="agent-review",
    help="Local Git diff review UI with inline comments and agent export.",
    add_completion=False,
)


@app.command()
def review(
    base: str = typer.Option("HEAD", "--base", help="Base ref to diff against"),
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    port: int = typer.Option(0, "--port", help="Server port (0 = auto-pick)"),
) -> None:
    """Launch local web UI for reviewing git diffs and adding inline comments."""
    ensure_git_repo(".")
    fastapi_app, review_id = create_app(".", base_ref=base)
    p = pick_port(port)
    url = f"http://{host}:{p}/"
    typer.echo(f"Starting review session: {review_id}")
    typer.echo(f"Opening browser: {url}")
    webbrowser.open(url)
    uvicorn.run(fastapi_app, host=host, port=p, log_level="warning")


@app.command()
def export(
    latest: bool = typer.Option(True, "--latest", help="Export latest review"),
    review_id: str = typer.Option("", "--review-id", help="Explicit review id"),
    format: str = typer.Option("agent-md", "--format", help="Export format"),
) -> None:
    """Export review comments to a bundle suitable for agentic coders."""
    if format != "agent-md":
        typer.echo("Error: only --format agent-md is supported", err=True)
        raise typer.Exit(code=1)

    rid: str = review_id.strip()
    if not rid and latest:
        found = latest_review_id(".")
        rid = found if found else ""

    if not rid:
        typer.echo("Error: no reviews found", err=True)
        raise typer.Exit(code=2)

    out = export_agent_md(".", rid)
    typer.echo(f"Exported to: {out}")


if __name__ == "__main__":
    app()
