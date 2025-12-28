"""CLI entry point for dot-work."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dot_work.container.provision.cli import app as container_provision_app
from dot_work.environments import ENVIRONMENTS
from dot_work.git.cli import history_app
from dot_work.harness.cli import app as harness_app
from dot_work.installer import (
    discover_available_environments,
    get_prompts_dir,
    initialize_work_directory,
    install_prompts,
)
from dot_work.knowledge_graph.cli import app as kg_app
from dot_work.overview.pipeline import analyze_project, write_outputs
from dot_work.python import python_app
from dot_work.version.cli import app as version_app
from dot_work.zip.cli import app as zip_app

app = typer.Typer(
    name="dot-work",
    help="Install AI coding prompts for your development environment.",
    no_args_is_help=True,
)
console = Console()

# Create subcommand group for validate
validate_app = typer.Typer(help="Validate files for syntax and schema errors.")

# Create subcommand group for review
review_app = typer.Typer(help="Interactive code review with AI-friendly export.")

# Create subcommand group for canonical prompts
canonical_app = typer.Typer(help="Validate and install canonical prompt files.")

# Create subcommand group for prompt management
prompt_app = typer.Typer(help="Create and manage canonical prompt files.")

# Create subcommand group for container operations
container_app = typer.Typer(help="Container-based operations.")

# Create subcommand group for git operations
git_app = typer.Typer(help="Git analysis tools.")


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

    install_prompts(env_key, target, prompts_dir, console, force=force, dry_run=dry_run)

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
            help="AI environment to use",
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
    """Initialize a new project with prompts and issue tracking structure."""
    # This is an alias for install that's more intuitive
    install(env=env, target=target, force=False)


@app.command("init-work")
def init_work(
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
    """Initialize the .work/ issue tracking directory structure.

    Creates the complete .work/ directory structure for file-based issue tracking,
    including priority files, focus tracking, and project memory.
    """
    target = target.resolve()

    if not target.exists():
        console.print(f"[red]❌ Target directory does not exist:[/red] {target}")
        raise typer.Exit(1)

    console.print("\n[bold blue]📋 Initializing work directory...[/bold blue]\n")

    initialize_work_directory(target, console, force=force)

    console.print("\n[bold green]✅ Work directory initialized![/bold green]")
    console.print("[dim]Next: Run 'generate-baseline' before making code changes[/dim]")


@app.command("overview")
def overview(
    input_dir: Annotated[
        Path,
        typer.Argument(
            ...,
            exists=True,
            resolve_path=True,
            help="Folder containing the project to scan.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Argument(
            ...,
            exists=False,
            resolve_path=False,
            help="Where to store the generated markdown and JSON files.",
        ),
    ],
) -> None:
    """Generate a bird's-eye overview of a codebase.

    Scans the project for Python files and markdown documentation, then generates:
    - birdseye_overview.md: Human-readable project guide
    - features.json: Structured feature data for LLMs
    - documents.json: Cross-referenceable documentation sections
    """
    console.print(f"[cyan]🔍 Scanning project:[/cyan] {input_dir}\n")

    bundle = analyze_project(input_dir)
    destinations = write_outputs(bundle, output_dir)

    console.print("[green]✓ Scan complete. Deliverables:[/green]")
    for label, path in destinations.items():
        console.print(f"  [dim]{label}:[/dim] {path}")

    console.print("\n[bold green]✅ Overview generated![/bold green]")
    console.print(
        f"[dim]Found {len(bundle.features)} features, {len(bundle.models)} models, {len(bundle.documents)} document sections[/dim]"
    )


def prompt_for_environment(discovered_envs: dict[str, set[str]] | None = None) -> str:
    """Interactively ask the user which environment to use.

    Args:
        discovered_envs: Optional dict of environments discovered from prompt frontmatter.
            If provided, only show environments that have at least one prompt.
            Keys are environment names, values are sets of prompt names.
    """
    console.print("\n[bold]🤖 Which AI coding environment are you using?[/bold]\n")

    # Determine which environments to show
    if discovered_envs:
        # Show only environments that prompts support
        options = sorted(discovered_envs.keys())
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
        # Show all registered environments
        options = list(ENVIRONMENTS.keys())
        for i, key in enumerate(options, 1):
            env = ENVIRONMENTS[key]
            console.print(f"  [cyan][{i}][/cyan] {env.name}")
            if env.notes:
                console.print(f"      [dim]└─ {env.notes}[/dim]")

    console.print()

    while True:
        choice = typer.prompt("Enter number (or environment key)")

        # Check if it's a number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            console.print("[red]Invalid choice. Please try again.[/red]")
        except ValueError:
            # Check if they typed the environment key
            choice_lower = choice.lower()
            # Check against options first (discovered), then all ENVIRONMENTS
            if choice_lower in options:
                return choice_lower
            if choice_lower in ENVIRONMENTS:
                # If not in discovered but in ENVIRONMENTS, warn but allow
                if discovered_envs and choice_lower not in discovered_envs:
                    console.print(
                        f"[yellow]⚠ No prompts found for '{choice_lower}'. "
                        f"Available: {', '.join(sorted(discovered_envs.keys()))}[/yellow]"
                    )
                    if typer.confirm("Continue anyway?", default=False):
                        return choice_lower
                    console.print("[red]Please enter a number or environment key.[/red]")
                else:
                    return choice_lower
            console.print("[red]Please enter a number or environment key.[/red]")


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


# =============================================================================
# Review Subcommands
# =============================================================================


@review_app.command("start")
def review_start(
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Port to run the review server on",
        ),
    ] = 8765,
    base: Annotated[
        str | None,
        typer.Option(
            "--base",
            "-b",
            help="Base commit/branch to diff against (default: HEAD~1)",
        ),
    ] = None,
    head: Annotated[
        str | None,
        typer.Option(
            "--head",
            help="Head commit/branch to diff (default: working tree)",
        ),
    ] = None,
) -> None:
    """Start the interactive code review server.

    Opens a local web interface for reviewing changes in your git repository.
    Add comments and suggestions, then export them for AI agents.
    """
    try:
        from dot_work.review.server import run_server
    except ImportError as e:
        console.print(f"[red]❌ Review module dependencies missing:[/red] {e}")
        console.print("[dim]Install with: pip install fastapi uvicorn[/dim]")
        raise typer.Exit(1) from None

    console.print(f"\n[bold blue]🔍 Starting code review server on port {port}...[/bold blue]\n")
    console.print(f"[dim]Base: {base or 'HEAD~1'}, Head: {head or 'working tree'}[/dim]")
    console.print(f"\n[green]→[/green] Open http://localhost:{port} in your browser\n")

    run_server(host="127.0.0.1", port=port, base=base, head=head)


@review_app.command("export")
def review_export(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: .work/reviews/review.md)",
        ),
    ] = None,
    review_id: Annotated[
        str | None,
        typer.Option(
            "--review-id",
            "-r",
            help="Specific review ID to export (default: latest)",
        ),
    ] = None,
) -> None:
    """Export review comments as agent-friendly markdown.

    Generates a markdown file with all comments and suggestions that can
    be used as context for AI coding agents.
    """
    try:
        from dot_work.review.exporter import export_agent_md
        from dot_work.review.git import repo_root
        from dot_work.review.storage import latest_review_id, load_comments
    except ImportError as e:
        console.print(f"[red]❌ Review module dependencies missing:[/red] {e}")
        raise typer.Exit(1) from None

    # Get repository root
    try:
        root = repo_root(".")
    except Exception as e:
        console.print(f"[red]❌ Not in a git repository:[/red] {e}")
        raise typer.Exit(1) from None

    # Determine review ID
    rid = review_id or latest_review_id(root)
    if not rid:
        console.print("[yellow]⚠ No reviews found[/yellow]")
        console.print("[dim]Start a review with: dot-work review start[/dim]")
        raise typer.Exit(1)

    # Load comments
    comments = load_comments(root, rid)
    if not comments:
        console.print(f"[yellow]⚠ No comments in review {rid}[/yellow]")
        raise typer.Exit(1)

    # Export
    output_path = export_agent_md(root, rid)
    if output:
        # Copy to user-specified path
        import shutil

        shutil.copy(output_path, output)
        output_path = output.resolve()

    console.print(f"[green]✅ Exported {len(comments)} comments to:[/green] {output_path}")
    console.print("[dim]Tip: Reference this file in your AI agent prompt[/dim]")


@review_app.command("clear")
def review_clear(
    review_id: Annotated[
        str | None,
        typer.Option(
            "--review-id",
            "-r",
            help="Specific review ID to clear (default: all reviews)",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Clear without confirmation",
        ),
    ] = False,
) -> None:
    """Clear review comments from storage.

    Removes stored comments for a specific review or all reviews.
    """
    try:
        from dot_work.review.config import settings
        from dot_work.review.git import repo_root
    except ImportError as e:
        console.print(f"[red]❌ Review module dependencies missing:[/red] {e}")
        raise typer.Exit(1) from None

    # Get repository root
    try:
        root = repo_root(".")
    except Exception as e:
        console.print(f"[red]❌ Not in a git repository:[/red] {e}")
        raise typer.Exit(1) from None

    storage_dir = Path(root) / settings.storage_dir / "reviews"

    if not storage_dir.exists():
        console.print("[yellow]⚠ No reviews directory found[/yellow]")
        return

    if review_id:
        # Clear specific review
        review_file = storage_dir / f"{review_id}.jsonl"
        if not review_file.exists():
            console.print(f"[yellow]⚠ Review not found:[/yellow] {review_id}")
            raise typer.Exit(1)

        if not force:
            if not typer.confirm(f"Clear review {review_id}?"):
                raise typer.Abort()

        review_file.unlink()
        console.print(f"[green]✅ Cleared review:[/green] {review_id}")
    else:
        # Clear all reviews
        jsonl_files = list(storage_dir.glob("*.jsonl"))
        if not jsonl_files:
            console.print("[yellow]⚠ No reviews to clear[/yellow]")
            return

        if not force:
            if not typer.confirm(f"Clear all {len(jsonl_files)} reviews?"):
                raise typer.Abort()

        for f in jsonl_files:
            f.unlink()
        console.print(f"[green]✅ Cleared {len(jsonl_files)} reviews[/green]")


# Register the review subcommand group
app.add_typer(review_app, name="review")


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
        console.print(f"[red]❌[/red] Validation failed: {e}")
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
        console.print(f"[red]❌[/red] Installation failed: {e}")
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
        console.print(f"[red]❌[/red] Extraction failed: {e}")
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
        raise typer.Exit(0)

    except Exception as e:
        console.print(f"\n[red]Error creating prompt:[/red] {e}")
        raise typer.Exit(1) from e


# Register the canonical subcommand group
app.add_typer(canonical_app, name="canonical")

# Register the prompt management subcommand group (also as 'prompts' alias)
app.add_typer(prompt_app, name="prompt")
app.add_typer(prompt_app, name="prompts")

# Register the review subcommand group
app.add_typer(review_app, name="review")

# Register the knowledge graph subcommand group
app.add_typer(kg_app, name="kg")

# Register the version subcommand group
app.add_typer(version_app, name="version")

# Register the zip subcommand group
app.add_typer(zip_app, name="zip")

# Register the container subcommand group
app.add_typer(container_app, name="container")

# Register the python subcommand group
app.add_typer(python_app, name="python")

# Register the git subcommand group
app.add_typer(git_app, name="git")

# Register the harness subcommand group
app.add_typer(harness_app, name="harness")

# Register the history subcommand under git
git_app.add_typer(history_app, name="history")

# Register the provision subcommand under container
container_app.add_typer(container_provision_app, name="provision")


if __name__ == "__main__":
    app()
