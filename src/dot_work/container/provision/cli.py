"""CLI interface for repo-agent.

This module provides the Typer-based command-line interface for repo-agent,
including commands for running agents, initializing instruction templates,
and validating configuration files.

Example:
    $ repo-agent run instructions.md
    $ repo-agent init my-instructions.md
    $ repo-agent validate instructions.md
"""

from __future__ import annotations

from pathlib import Path

import typer

from .core import RepoAgentError, run_from_markdown

# Exit code constants
EXIT_CODE_ERROR = 1
EXIT_CODE_KEYBOARD_INTERRUPT = 130

app = typer.Typer(
    help="Run a configurable LLM-powered code tool in Docker using markdown instructions."
)


@app.command()
def run(
    instructions: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Markdown file with frontmatter + instructions.",
    ),
    repo_url: str | None = typer.Option(
        None,
        "--repo-url",
        help="Git repo URL (overrides frontmatter repo_url).",
    ),
    branch: str | None = typer.Option(
        None,
        "--branch",
        help="Target branch to use/create for changes.",
    ),
    base_branch: str | None = typer.Option(
        None,
        "--base-branch",
        help="Base branch to branch from (e.g. main).",
    ),
    docker_image: str | None = typer.Option(
        None,
        "--docker-image",
        help="Docker image to use (defaults to frontmatter or repo-agent:latest).",
    ),
    dockerfile: Path | None = typer.Option(
        None,
        "--dockerfile",
        exists=True,
        readable=True,
        help="Dockerfile to build before running (overrides frontmatter dockerfile).",
    ),
    use_ssh: bool = typer.Option(
        False,
        "--ssh",
        help="Use SSH auth and mount ~/.ssh (overrides frontmatter use_ssh).",
    ),
    ssh_key_dir: Path | None = typer.Option(
        None,
        "--ssh-key-dir",
        help="Directory with SSH keys to mount into the container (defaults to ~/.ssh).",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Model id for the tool (provider/model), overrides frontmatter model.",
    ),
    strategy: str | None = typer.Option(
        None,
        "--strategy",
        help="Strategy: agentic or direct (overrides frontmatter strategy/opencode_strategy).",
    ),
    pr_title: str | None = typer.Option(
        None,
        "--pr-title",
        help="Title of the pull request.",
    ),
    pr_body: str | None = typer.Option(
        None,
        "--pr-body",
        help="Body/description of the pull request.",
    ),
    github_token: str | None = typer.Option(
        None,
        "--github-token",
        envvar=["GITHUB_TOKEN", "GH_TOKEN"],
        help="GitHub token to use (or set via env / frontmatter).",
    ),
    auto_commit: bool | None = typer.Option(
        None,
        "--auto-commit/--no-auto-commit",
        help="Enable/disable auto commit & push (overrides frontmatter).",
    ),
    create_pr: bool | None = typer.Option(
        None,
        "--create-pr/--no-create-pr",
        help="Enable/disable PR creation (overrides frontmatter).",
    ),
    create_repo_if_missing: bool | None = typer.Option(
        None,
        "--create-repo/--no-create-repo",
        help="Create the GitHub repository if it doesn't exist (overrides frontmatter).",
    ),
    commit_message: str | None = typer.Option(
        None,
        "--commit-message",
        help="Commit message for auto commits.",
    ),
    git_user_name: str | None = typer.Option(
        None,
        "--git-user-name",
        help="Git user.name configured inside the container.",
    ),
    git_user_email: str | None = typer.Option(
        None,
        "--git-user-email",
        help="Git user.email configured inside the container.",
    ),
    tool_entrypoint: str | None = typer.Option(
        None,
        "--tool-entrypoint",
        help="Override the tool entrypoint (e.g. 'opencode run', 'my-tool exec').",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the docker command instead of executing it.",
    ),
) -> None:
    """Run the agent with an instruction file."""
    try:
        run_from_markdown(
            instructions_path=instructions,
            repo_url=repo_url,
            branch=branch,
            base_branch=base_branch,
            docker_image=docker_image,
            dockerfile=dockerfile,
            use_ssh=use_ssh,
            ssh_key_dir=ssh_key_dir,
            model=model,
            strategy=strategy,
            pr_title=pr_title,
            pr_body=pr_body,
            github_token=github_token,
            auto_commit=auto_commit,
            create_pr=create_pr,
            create_repo_if_missing=create_repo_if_missing,
            commit_message=commit_message,
            git_user_name=git_user_name,
            git_user_email=git_user_email,
            tool_entrypoint=tool_entrypoint,
            dry_run=dry_run,
        )
    except RepoAgentError as exc:
        typer.echo(f"repo-agent error: {exc}", err=True)
        raise typer.Exit(code=EXIT_CODE_ERROR)
    except KeyboardInterrupt:
        raise typer.Exit(code=EXIT_CODE_KEYBOARD_INTERRUPT)


@app.command()
def init(
    output: Path = typer.Argument(
        "instructions.md",
        help="Where to write the generated instructions markdown.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing file.",
    ),
) -> None:
    """Generate a valid instructions markdown template with frontmatter."""
    from .templates import DEFAULT_INSTRUCTIONS_TEMPLATE

    if output.exists() and not force:
        typer.echo(f"{output} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(code=EXIT_CODE_ERROR)

    output.write_text(DEFAULT_INSTRUCTIONS_TEMPLATE, encoding="utf-8")
    typer.echo(f"Created template: {output}")


@app.command()
def validate(
    instructions: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Markdown instructions file to validate.",
    ),
) -> None:
    """Validate frontmatter fields, tool configuration, and required metadata."""
    from .validation import validate_instructions

    try:
        validate_instructions(instructions)
        typer.echo("✓ Instructions file is valid.")
    except RepoAgentError as exc:
        typer.echo(f"✗ Invalid instructions file: {exc}", err=True)
        raise typer.Exit(code=EXIT_CODE_ERROR)


if __name__ == "__main__":
    app()
