"""Shared fixtures for birdseye tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    project = tmp_path / "demo_project"
    project.mkdir()

    (project / "api.py").write_text(
        dedent(
            '''
            from fastapi import APIRouter

            router = APIRouter()


            @router.get("/greet")
            def read_greeting(name: str) -> dict[str, str]:
                """Return a JSON greeting so clients know what to expect."""
                return {"message": f"Hello {name}"}
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project / "cli.py").write_text(
        dedent(
            '''
            import typer

            app = typer.Typer()


            @app.command()
            def greet(name: str) -> None:
                """Print the greeting for terminal users."""
                typer.echo(f"Hello {name}")
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project / "models.py").write_text(
        dedent(
            '''
            from pydantic import BaseModel


            class Profile(BaseModel):
                """Profile model exposed via API responses."""

                username: str
                bio: str | None = None
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project / "services.py").write_text(
        dedent(
            '''
            class GreetingService:
                """Co-ordinates greetings for any caller."""

                def greet(self, name: str) -> str:
                    """Return a friendly greeting for dashboards or logs."""
                    return f"Hello {name}"
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project / "README.md").write_text(
        dedent(
            """
            # GreetingService greet

            Use this feature to confirm that users receive the right greeting.
            Provide a name and expect the friendly message back to the caller.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    docs_dir = project / "docs"
    docs_dir.mkdir()
    (docs_dir / "feature-guide.md").write_text(
        dedent(
            """
            ## greet

            - Provide a name to the CLI or API.
            - Confirm the message includes the same name.
            - Record any formatting issues for regression tests.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    return project
