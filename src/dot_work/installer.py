"""Installer functions for different AI environments."""

import importlib.resources
from dataclasses import dataclass, field
from datetime import UTC
from enum import Enum, auto
from pathlib import Path
from typing import Callable

from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader
from rich.console import Console
from rich.table import Table
import typer

from dot_work.environments import ENVIRONMENTS, Environment


class BatchChoice(Enum):
    """User's batch overwrite choice."""

    ALL = auto()  # Overwrite all existing files
    SKIP = auto()  # Skip all existing files
    PROMPT = auto()  # Prompt for each file individually
    CANCEL = auto()  # Cancel installation


@dataclass
class InstallState:
    """Tracks state during batch installation."""

    batch_choice: BatchChoice | None = None
    existing_files: list[Path] = field(default_factory=list)
    new_files: list[Path] = field(default_factory=list)

    @property
    def has_existing_files(self) -> bool:
        """Check if any existing files were found."""
        return len(self.existing_files) > 0

    @property
    def total_files(self) -> int:
        """Total files to process."""
        return len(self.existing_files) + len(self.new_files)


@dataclass
class InstallerConfig:
    """Configuration for an environment installer.

    Attributes:
        env_key: Environment key in ENVIRONMENTS dict
        dest_path: Destination directory path pattern (relative to target)
        file_naming: How to name output files ("keep", "prompt-suffix", "mdc-suffix")
        file_extension: File extension for individual files (default: ".md")
        combined: If True, combine all prompts into single file
        combined_path: Path for combined output (relative to target)
        auxiliary_files: List of (path, content_template) tuples for extra files
        sort_files: If True, sort prompt files before processing
        messages: Tuple of (success_msg, location_msg, tip_msg) for console output
    """

    env_key: str
    dest_path: str
    file_naming: str = "keep"  # "keep", "prompt-suffix", "mdc-suffix"
    file_extension: str = ".md"
    combined: bool = False
    combined_path: str = ""
    auxiliary_files: list[tuple[str, str]] = field(default_factory=list)
    sort_files: bool = False
    messages: tuple[str, str, str | None] = (
        "Installed {name}",
        "Prompts installed to: {path}",
        None,
    )


def get_prompts_dir() -> Path:
    """Get the directory containing the bundled prompts."""
    # Use importlib.resources to find prompts bundled with the package
    try:
        pkg_files = importlib.resources.files("dot_work")
        prompts_dir = Path(str(pkg_files)) / "prompts"
        if prompts_dir.exists():
            return prompts_dir
    except (TypeError, FileNotFoundError):
        pass

    # Fallback: look relative to this file (for development)
    module_dir = Path(__file__).parent
    prompts_dir = module_dir / "prompts"
    if prompts_dir.exists():
        return prompts_dir

    # Try project root (for development)
    project_root = module_dir.parent.parent.parent
    prompts_dir = project_root / "prompts"
    if prompts_dir.exists():
        return prompts_dir

    raise FileNotFoundError(
        "Could not find prompts directory. Make sure the package is installed correctly."
    )


def create_jinja_env(prompts_dir: Path) -> JinjaEnvironment:
    """Create a Jinja2 environment for processing prompt templates.

    Args:
        prompts_dir: Path to the directory containing prompt templates.

    Returns:
        Configured Jinja2 environment with FileSystemLoader.

    Note:
        Autoescape is disabled since we generate markdown, not HTML.
        These templates are trusted internal files, not user input.
    """
    return JinjaEnvironment(  # noqa: S701 - autoescape disabled for markdown
        loader=FileSystemLoader(prompts_dir),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
        autoescape=False,  # Markdown templates, not HTML
    )


def build_template_context(env_config: Environment) -> dict[str, str]:
    """Build the template context dictionary from an environment config.

    Args:
        env_config: The environment configuration to extract values from.

    Returns:
        Dictionary of template variables and their values.
    """
    return {
        "prompt_path": env_config.prompt_dir or "prompts",
        "ai_tool": env_config.key,
        "ai_tool_name": env_config.name,
        "prompt_extension": env_config.prompt_extension or ".md",
        "instructions_file": env_config.instructions_file or "",
        "rules_file": env_config.rules_file or "",
    }


def render_prompt(
    prompts_dir: Path,
    prompt_file: Path,
    env_config: Environment,
) -> str:
    """Render a prompt template with environment-specific variables.

    Args:
        prompts_dir: Path to the directory containing prompt templates.
        prompt_file: Path to the specific prompt file to render.
        env_config: Environment configuration with template values.

    Returns:
        Rendered prompt content with all template variables substituted.

    Raises:
        jinja2.TemplateNotFound: If the template file doesn't exist.
        jinja2.TemplateSyntaxError: If the template has invalid syntax.
    """
    jinja_env = create_jinja_env(prompts_dir)
    template = jinja_env.get_template(prompt_file.name)
    context = build_template_context(env_config)
    return template.render(**context)


def should_write_file(
    dest_path: Path,
    force: bool,
    console: Console,
    *,
    batch_choice: BatchChoice | None = None,
) -> bool:
    """Check if a file should be written, prompting user if it exists.

    Args:
        dest_path: Path to the destination file.
        force: If True, overwrite without prompting.
        console: Rich console for user interaction.
        batch_choice: Optional batch overwrite choice for handling multiple existing files.

    Returns:
        True if the file should be written, False to skip.
    """
    if not dest_path.exists():
        return True
    if force:
        return True

    # Handle batch choice if provided
    if batch_choice is not None:
        if batch_choice == BatchChoice.ALL:
            return True
        elif batch_choice == BatchChoice.SKIP:
            return False
        elif batch_choice == BatchChoice.CANCEL:
            return False
        # PROMPT falls through to individual prompt below

    # Prompt user for confirmation
    console.print(f"  [yellow]⚠[/yellow] File already exists: {dest_path.name}")
    response = console.input("    Overwrite? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def _prompt_batch_choice(console: Console, state: InstallState) -> BatchChoice:
    """Prompt user for batch overwrite choice.

    Args:
        console: Rich console for output.
        state: Current installation state with file lists.

    Returns:
        The user's batch choice.
    """
    # Summary table
    table = Table(title="File Status Summary", show_header=True)
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("[yellow]Existing[/yellow]", str(len(state.existing_files)))
    table.add_row("[green]New[/green]", str(len(state.new_files)))
    console.print(table)

    # Menu
    console.print("\n[yellow]⚠ Existing files found.[/yellow]")
    console.print("How should I proceed?\n")
    console.print("  [bold cyan][a][/bold cyan] Overwrite [bold]ALL[/bold] existing files")
    console.print("  [bold cyan][s][/bold cyan] [bold]SKIP[/bold] all existing files")
    console.print("  [bold cyan][p][/bold cyan] [bold]PROMPT[/bold] for each file individually")
    console.print("  [bold cyan][c][/bold cyan] [bold]CANCEL[/bold] installation\n")

    while True:
        response = console.input("Choice [a/s/p/c]: ").strip().lower()
        if response in ("a", "all"):
            return BatchChoice.ALL
        elif response in ("s", "skip"):
            return BatchChoice.SKIP
        elif response in ("p", "prompt"):
            return BatchChoice.PROMPT
        elif response in ("c", "cancel"):
            return BatchChoice.CANCEL
        console.print("[red]Invalid choice. Please enter a, s, p, or c.[/red]")


def install_prompts(
    env_key: str,
    target: Path,
    prompts_dir: Path,
    console: Console,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Install prompts for the specified environment using canonical frontmatter.

    Reads prompt frontmatter to discover supported environments and installs
    using the paths specified in each prompt's environment configuration.

    Args:
        env_key: The environment key (e.g., 'copilot', 'claude').
        target: Target directory to install prompts to.
        prompts_dir: Source directory containing prompt templates.
        console: Rich console for output.
        force: If True, overwrite existing files without prompting.
        dry_run: If True, preview changes without writing files.

    Raises:
        ValueError: If environment not found in any prompt prompts.
    """
    # First try to use canonical prompt installation
    try:
        install_canonical_prompts_by_environment(
            env_key, target, prompts_dir, console, force=force, dry_run=dry_run
        )
        return
    except ValueError as e:
        # If no canonical prompts found, fall back to legacy installer
        if "not found in any prompt files" in str(e):
            console.print("[dim]⚠ No canonical prompts found, trying legacy installation...[/dim]\n")
        else:
            raise

    # Legacy fallback for non-canonical prompts
    installer = INSTALLERS.get(env_key)
    if not installer:
        raise ValueError(f"Unknown environment: {env_key}")

    installer(target, prompts_dir, console, force=force, dry_run=dry_run)


def install_prompts_generic(
    config: InstallerConfig,
    target: Path,
    prompts_dir: Path,
    console: Console,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Generic installer function that handles all environment patterns.

    Args:
        config: Installer configuration defining behavior.
        target: Target directory to install prompts to.
        prompts_dir: Source directory containing prompt templates.
        console: Rich console for output.
        force: If True, overwrite existing files without prompting.
        dry_run: If True, preview changes without writing files.
    """
    env_config = ENVIRONMENTS[config.env_key]

    # Combined file mode (claude, aider, amazon-q)
    if config.combined:
        combined_path = target / config.combined_path

        # Create parent directory if needed (skip in dry-run)
        if not dry_run:
            combined_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if we should write (in dry-run, always show what would happen)
        if not dry_run and not should_write_file(combined_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {combined_path.name}")
            return

        sections = [_build_combined_header(config)]

        # Get prompt files
        prompt_files = sorted(prompts_dir.glob("*.md")) if config.sort_files else prompts_dir.glob("*.md")

        for prompt_file in prompt_files:
            content = render_prompt(prompts_dir, prompt_file, env_config)
            title = prompt_file.stem.replace("-", " ").replace("_", " ").title()
            sections.append(f"---\n\n## {title}\n\n")
            sections.append(content)
            sections.append("\n\n")

        if dry_run:
            action = "Would create" if not combined_path.exists() else "Would overwrite"
            console.print(f"  [yellow][DRY-RUN][/yellow] [dim]{action}[/dim] {combined_path}")
        else:
            combined_path.write_text("".join(sections), encoding="utf-8")
            console.print(f"  [green]✓[/green] Created {combined_path.name}")
        console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {combined_path}")
        if config.messages[2]:
            console.print(f"[dim]💡 {config.messages[2]}[/dim]")
        return

    # Directory mode (copilot, cursor, windsurf, continue, zed, opencode, generic, cline, cody)
    dest_dir = target / config.dest_path
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    # Scan phase: collect all destination paths and categorize
    state = InstallState()
    prompt_files = list(prompts_dir.glob("*.md"))

    for prompt_file in prompt_files:
        dest_name = _get_dest_filename(prompt_file, config)
        dest_path = dest_dir / dest_name
        if dest_path.exists():
            state.existing_files.append(dest_path)
        else:
            state.new_files.append(dest_path)

    # Add auxiliary files to scan
    for aux_path, _aux_content in config.auxiliary_files:
        aux_full_path = target / aux_path
        if aux_full_path.exists():
            state.existing_files.append(aux_full_path)
        else:
            state.new_files.append(aux_full_path)

    # Show batch menu if there are existing files and not in force/dry-run mode
    batch_choice: BatchChoice | None = None
    if state.has_existing_files and not force and not dry_run:
        batch_choice = _prompt_batch_choice(console, state)
        if batch_choice == BatchChoice.CANCEL:
            console.print("[yellow]Installation cancelled.[/yellow]")
            return

    # Process each file
    for prompt_file in prompt_files:
        # Determine destination filename
        dest_name = _get_dest_filename(prompt_file, config)
        dest_path = dest_dir / dest_name

        # Check if we should write (pass batch_choice)
        if not dry_run and not should_write_file(
            dest_path, force, console, batch_choice=batch_choice
        ):
            console.print(f"  [dim]⏭[/dim] Skipped {dest_name}")
            continue

        if dry_run:
            action = "[CREATE]" if not dest_path.exists() else "[OVERWRITE]"
            console.print(f"  [yellow][DRY-RUN][/yellow] [dim]{action}[/dim] {dest_path}")
        else:
            # Render and write
            rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
            dest_path.write_text(rendered_content, encoding="utf-8")
            console.print(f"  [green]✓[/green] {config.messages[0].format(name=dest_name)}")

    # Create auxiliary files
    for aux_path, aux_content in config.auxiliary_files:
        aux_full_path = target / aux_path
        if dry_run:
            action = "[CREATE]" if not aux_full_path.exists() else "[OVERWRITE]"
            console.print(f"  [yellow][DRY-RUN][/yellow] [dim]{action}[/dim] {aux_full_path}")
        elif should_write_file(aux_full_path, force, console, batch_choice=batch_choice):
            aux_full_path.write_text(aux_content, encoding="utf-8")
            console.print(f"  [green]✓[/green] Created {aux_full_path.name}")
        elif aux_full_path.exists():
            console.print(f"  [dim]⏭[/dim] Skipped {aux_full_path.name}")

    console.print(f"\n[cyan]📁 {config.messages[1].format(path=dest_dir)}")
    if config.messages[2]:
        console.print(f"[dim]💡 {config.messages[2]}[/dim]")


def _build_combined_header(config: InstallerConfig) -> str:
    """Build the header for a combined file.

    Args:
        config: Installer configuration.

    Returns:
        Header string for the combined file.
    """
    if config.env_key == "claude":
        return "# Claude Code Instructions\n\nThis file contains AI agent instructions for this project.\n\n"
    elif config.env_key == "aider":
        return "# Project Conventions\n\n"
    elif config.env_key == "amazon-q":
        return "# Amazon Q Project Rules\n\n"
    else:
        return "# AI Agent Instructions\n\n"


def _get_dest_filename(prompt_file: Path, config: InstallerConfig) -> str:
    """Get the destination filename for a prompt file.

    Args:
        prompt_file: The source prompt file.
        config: Installer configuration.

    Returns:
        Destination filename.
    """
    if config.file_naming == "prompt-suffix":
        # copilot: use .prompt.md extension for all
        if prompt_file.name.endswith(".prompt.md"):
            return prompt_file.name
        return f"{prompt_file.stem}.prompt.md"
    elif config.file_naming == "mdc-suffix":
        # cursor: use .mdc extension
        return f"{prompt_file.stem}.mdc"
    else:
        # keep: use original name or configured extension
        if config.file_extension != ".md":
            return f"{prompt_file.stem}{config.file_extension}"
        return prompt_file.name


def install_for_copilot(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for GitHub Copilot (VS Code)."""
    config = InstallerConfig(
        env_key="copilot",
        dest_path=".github/prompts",
        file_naming="prompt-suffix",
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Use with: /project-from-discussion or /issue-tracker-setup",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_claude(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Claude Code."""
    config = InstallerConfig(
        env_key="claude",
        dest_path="",
        combined=True,
        combined_path="CLAUDE.md",
        sort_files=True,
        messages=(
            "Created {name}",
            "Instructions installed to: {path}",
            "Claude will automatically read CLAUDE.md",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_cursor(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Cursor."""
    config = InstallerConfig(
        env_key="cursor",
        dest_path=".cursor/rules",
        file_naming="mdc-suffix",
        auxiliary_files=[
            (
                ".cursorrules",
                "# Cursor Rules\n\n"
                "See .cursor/rules/ for detailed prompts.\n\n"
                "## General Guidelines\n"
                "- Follow the project structure defined in prompts\n"
                "- Use type hints on all functions\n"
                "- Write tests for new functionality\n",
            )
        ],
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Rules available in Cursor's @ menu",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_windsurf(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Windsurf."""
    config = InstallerConfig(
        env_key="windsurf",
        dest_path=".windsurf/rules",
        auxiliary_files=[
            (".windsurfrules", "# Windsurf Rules\n\nSee .windsurf/rules/ for detailed prompts.\n")
        ],
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            None,
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_aider(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Aider."""
    config = InstallerConfig(
        env_key="aider",
        dest_path="",
        combined=True,
        combined_path="CONVENTIONS.md",
        sort_files=True,
        messages=(
            "Created {name}",
            "Conventions installed to: {path}",
            "Aider will read CONVENTIONS.md automatically",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_continue(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Continue.dev."""
    config = InstallerConfig(
        env_key="continue",
        dest_path=".continue/prompts",
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Access prompts via Continue's slash commands",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_amazon_q(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Amazon Q Developer."""
    config = InstallerConfig(
        env_key="amazon-q",
        dest_path="",
        combined=True,
        combined_path=".amazonq/rules.md",
        sort_files=True,
        messages=(
            "Created {name}",
            "Rules installed to: {path}",
            None,
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_zed(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Zed AI."""
    config = InstallerConfig(
        env_key="zed",
        dest_path=".zed/prompts",
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            None,
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_opencode(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for OpenCode."""
    config = InstallerConfig(
        env_key="opencode",
        dest_path=".opencode/prompts",
        auxiliary_files=[
            (
                "AGENTS.md",
                """# AI Agent Instructions

This file provides instructions for AI agents working on this codebase.

## Available Prompts

The following prompts are available in `.opencode/prompts/`:

- **project-from-discussion** - Transform a project discussion into a production-ready Python project
- **issue-tracker-setup** - Set up file-based issue tracking for AI agents

## Usage

Reference these prompts in your conversation:
- "Read and follow .opencode/prompts/project-from-discussion.prompt.md"
- "Initialize issue tracking per .opencode/prompts/issue-tracker-setup.prompt.md"

Or use the slash command syntax if supported:
- `/project-from-discussion`
- `/issue-tracker-setup`

## Code Quality Standards

- Type annotations on all functions
- Google-style docstrings on public APIs
- Use `pathlib.Path` for file operations
- Run `python scripts/build.py` before committing
- Maintain test coverage ≥75%
""",
            )
        ],
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Reference prompts with: 'Read .opencode/prompts/<name>.prompt.md'",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_cline(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Cline.

    Cline uses a folder-based system: all .md files in .clinerules/ are processed.
    Files can have numeric prefixes for ordering (e.g., 01-coding.md, 02-docs.md).
    """
    config = InstallerConfig(
        env_key="cline",
        dest_path=".clinerules",
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Cline will automatically process all .md files in .clinerules/",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_cody(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for Sourcegraph Cody.

    Cody uses a Prompt Library for shared prompts, but local .cody/ directory
    can be used for project-specific context and instructions.
    """
    config = InstallerConfig(
        env_key="cody",
        dest_path=".cody",
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Use Cody @-mentions to reference these files in chat",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


def install_for_generic(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False, dry_run: bool = False
) -> None:
    """Install prompts for generic/manual use."""
    config = InstallerConfig(
        env_key="generic",
        dest_path="prompts",
        auxiliary_files=[
            (
                "AGENTS.md",
                "# AI Agent Instructions\n\n"
                "See the `prompts/` directory for detailed instructions:\n\n"
                "- `project-from-discussion.prompt.md` - Convert discussions to projects\n"
                "- `issue-tracker-setup.prompt.md` - Set up file-based issue tracking\n\n"
                "When starting a new project, ask the AI to read and follow these prompts.\n",
            )
        ],
        messages=(
            "Installed {name}",
            "Prompts installed to: {path}",
            "Reference these prompts manually in your AI conversations",
        ),
    )
    install_prompts_generic(config, target, prompts_dir, console, force=force, dry_run=dry_run)


# Installer dispatch table
INSTALLERS = {
    "copilot": install_for_copilot,
    "claude": install_for_claude,
    "cline": install_for_cline,
    "cody": install_for_cody,
    "cursor": install_for_cursor,
    "windsurf": install_for_windsurf,
    "aider": install_for_aider,
    "continue": install_for_continue,
    "amazon-q": install_for_amazon_q,
    "zed": install_for_zed,
    "opencode": install_for_opencode,
    "generic": install_for_generic,
}


# =============================================================================
# Work Directory Initialization
# =============================================================================

# Template content for .work/ files
_FOCUS_TEMPLATE = """# Agent Focus
Last updated: {timestamp}

## Previous
None

## Current
None

## Next
None
"""

_MEMORY_TEMPLATE = """# Agent Memory

## Project Context
- Primary language: {language}
- Framework: {framework}
- Package manager: {package_manager}
- Test framework: {test_framework}

## User Preferences
(To be populated as preferences are discovered)

## Architectural Decisions
(To be populated as decisions are made)

## Patterns & Conventions
(To be populated as patterns are identified)

## Known Constraints
(To be populated as constraints are discovered)

## Lessons Learned
(To be populated after completing issues)
"""

_SHORTLIST_TEMPLATE = """# Shortlist (User-Directed Priority)

This file represents **explicit user intent**. Agent may only modify when explicitly instructed.

---

(No issues yet)
"""

_CRITICAL_TEMPLATE = """# Critical Issues (P0)

Blockers, security issues, data loss risks.

---

(No issues)
"""

_HIGH_TEMPLATE = """# High Priority Issues (P1)

Core functionality broken or missing documented features.

---

(No issues)
"""

_MEDIUM_TEMPLATE = """# Medium Priority Issues (P2)

Enhancements, technical debt.

---

(No issues)
"""

_LOW_TEMPLATE = """# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

(No issues)
"""

_BACKLOG_TEMPLATE = """# Backlog

Untriaged ideas and future work.

---

(No issues)
"""

_HISTORY_TEMPLATE = """# Issue History (Append-Only)

Completed and closed issues are archived here.

---

(No completed issues yet)
"""

_BASELINE_TEMPLATE = """# Project Baseline

**Captured:** Not yet generated
**Commit:** N/A
**Branch:** N/A

---

Run `generate-baseline` to populate this file with quality metrics.
"""


def detect_project_context(target: Path) -> dict[str, str]:
    """Detect project context from files in the target directory.

    Args:
        target: Path to the project directory.

    Returns:
        Dictionary with detected project context values.
    """
    context = {
        "language": "unknown",
        "framework": "unknown",
        "package_manager": "unknown",
        "test_framework": "unknown",
    }

    # Detect Python
    if (target / "pyproject.toml").exists():
        context["language"] = "Python"
        context["package_manager"] = "uv or pip"

        pyproject_content = (target / "pyproject.toml").read_text(encoding="utf-8")
        if "pytest" in pyproject_content:
            context["test_framework"] = "pytest"
        if "typer" in pyproject_content:
            context["framework"] = "Typer (CLI)"
        elif "fastapi" in pyproject_content:
            context["framework"] = "FastAPI"
        elif "django" in pyproject_content:
            context["framework"] = "Django"
        elif "flask" in pyproject_content:
            context["framework"] = "Flask"

    elif (target / "requirements.txt").exists():
        context["language"] = "Python"
        context["package_manager"] = "pip"

    # Detect Node.js
    elif (target / "package.json").exists():
        context["language"] = "JavaScript/TypeScript"
        context["package_manager"] = "npm or yarn"

        pkg_content = (target / "package.json").read_text(encoding="utf-8")
        if "jest" in pkg_content:
            context["test_framework"] = "Jest"
        elif "mocha" in pkg_content:
            context["test_framework"] = "Mocha"
        if "next" in pkg_content:
            context["framework"] = "Next.js"
        elif "react" in pkg_content:
            context["framework"] = "React"
        elif "vue" in pkg_content:
            context["framework"] = "Vue"
        elif "express" in pkg_content:
            context["framework"] = "Express"

    # Detect Rust
    elif (target / "Cargo.toml").exists():
        context["language"] = "Rust"
        context["package_manager"] = "cargo"
        context["test_framework"] = "cargo test"

    # Detect Go
    elif (target / "go.mod").exists():
        context["language"] = "Go"
        context["package_manager"] = "go modules"
        context["test_framework"] = "go test"

    return context


def initialize_work_directory(
    target: Path,
    console: Console,
    *,
    force: bool = False,
) -> None:
    """Initialize the .work/ directory structure for issue tracking.

    Args:
        target: Path to the project directory.
        console: Rich console for output.
        force: Whether to overwrite existing files without prompting.
    """
    from datetime import datetime

    work_dir = target / ".work"
    agent_dir = work_dir / "agent"
    issues_dir = agent_dir / "issues"
    notes_dir = agent_dir / "notes"
    refs_dir = issues_dir / "references"

    # Create directories
    for dir_path in [work_dir, agent_dir, issues_dir, notes_dir, refs_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Detect project context
    context = detect_project_context(target)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Define files to create
    files_to_create: list[tuple[Path, str]] = [
        (work_dir / "baseline.md", _BASELINE_TEMPLATE),
        (agent_dir / "focus.md", _FOCUS_TEMPLATE.format(timestamp=timestamp)),
        (
            agent_dir / "memory.md",
            _MEMORY_TEMPLATE.format(
                language=context["language"],
                framework=context["framework"],
                package_manager=context["package_manager"],
                test_framework=context["test_framework"],
            ),
        ),
        (issues_dir / "shortlist.md", _SHORTLIST_TEMPLATE),
        (issues_dir / "critical.md", _CRITICAL_TEMPLATE),
        (issues_dir / "high.md", _HIGH_TEMPLATE),
        (issues_dir / "medium.md", _MEDIUM_TEMPLATE),
        (issues_dir / "low.md", _LOW_TEMPLATE),
        (issues_dir / "backlog.md", _BACKLOG_TEMPLATE),
        (issues_dir / "history.md", _HISTORY_TEMPLATE),
        (notes_dir / ".gitkeep", ""),
        (refs_dir / ".gitkeep", ""),
    ]

    # Create files
    for file_path, content in files_to_create:
        if should_write_file(file_path, force, console):
            file_path.write_text(content, encoding="utf-8")
            console.print(f"  [green]✓[/green] Created {file_path.relative_to(target)}")
        else:
            console.print(f"  [dim]⏭[/dim] Skipped {file_path.relative_to(target)}")

    console.print(f"\n[cyan]📁 Work directory initialized at:[/cyan] {work_dir}")
    console.print("[dim]💡 Run 'generate-baseline' before making code changes[/dim]")


def validate_canonical_prompt_file(prompt_file: Path, strict: bool = False) -> None:
    """Validate a canonical prompt file and raise exception if invalid.

    Args:
        prompt_file: Path to canonical prompt file (.canon.md or similar).
        strict: Whether to use strict validation mode.

    Raises:
        ValueError: If the file is not a valid canonical prompt.
    """
    from dot_work.prompts.canonical import CanonicalPromptParser, CanonicalPromptValidator

    if not prompt_file.exists():
        raise FileNotFoundError(f"Canonical prompt file not found: {prompt_file}")

    try:
        parser = CanonicalPromptParser()
        prompt = parser.parse(prompt_file)

        validator = CanonicalPromptValidator()
        errors = validator.validate(prompt, strict=strict)

        # Filter errors by severity
        error_messages = [e.message for e in errors if e.severity == "error"]
        warning_messages = [e.message for e in errors if e.severity == "warning"]

        # In strict mode, treat errors starting with "Strict mode:" differently
        strict_mode_errors = [msg for msg in error_messages if msg.startswith("Strict mode:")]
        regular_errors = [msg for msg in error_messages if not msg.startswith("Strict mode:")]

        if regular_errors:
            error_text = "\n  ".join(regular_errors)
            raise ValueError(f"Canonical prompt validation failed:\n  {error_text}")

        if strict_mode_errors or (warning_messages and strict):
            all_strict_issues = strict_mode_errors + (warning_messages if strict else [])
            error_text = "\n  ".join(all_strict_issues)
            raise ValueError(f"Canonical prompt strict validation failed:\n  {error_text}")

    except ValueError as e:
        # For strict validation failures, wrap them appropriately
        if "Canonical prompt strict validation failed" in str(e):
            raise
        # For validation errors from parse/validate, wrap them
        if "Canonical prompt validation failed" in str(e):
            raise
        # For other ValueError exceptions from parsing, wrap them
        error_msg = str(e)
        raise ValueError(f"Canonical prompt validation failed:\n  {error_msg}") from e
    except Exception as e:
        raise ValueError(f"Canonical prompt validation failed:\n  {e}") from e


def install_canonical_prompt(
    prompt_file: Path,
    env_key: str,
    target: Path,
    console: Console,
    *,
    force: bool = False,
) -> None:
    """Install a canonical prompt file to the specified environment.

    Args:
        prompt_file: Path to canonical prompt file.
        env_key: Environment key to install for (e.g., 'copilot', 'claude').
        target: Target directory to install in.
        console: Rich console for output.
        force: Whether to overwrite existing files.

    Raises:
        ValueError: If the environment is not supported or prompt is invalid.
        FileNotFoundError: If the prompt file doesn't exist.
    """
    from dot_work.prompts.canonical import CanonicalPromptError, CanonicalPromptParser

    # First validate canonical prompt
    validate_canonical_prompt_file(prompt_file, strict=False)

    # Parse canonical prompt
    parser = CanonicalPromptParser()
    prompt = parser.parse(prompt_file)

    # Get environment configuration (will raise CanonicalPromptError if not found)
    try:
        env_config = prompt.get_environment(env_key)
    except CanonicalPromptError as e:
        # Convert CanonicalPromptError to ValueError for consistent API
        raise ValueError(str(e)) from e

    # Validate target path is not empty
    if not env_config.target or not env_config.target.strip():
        raise ValueError(
            f"Environment '{env_key}' has an empty or missing 'target' path. "
            f"The target path must be specified and non-empty."
        )

    # Determine output path
    if env_config.target.startswith("/"):
        # Absolute path
        output_dir = Path(env_config.target.lstrip("/"))
    elif env_config.target.startswith("./"):
        # Relative to current directory
        output_dir = target / env_config.target[2:]
    else:
        # Relative to target
        output_dir = target / env_config.target

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename
    if env_config.filename:
        # Validate filename is not empty
        if not env_config.filename or not env_config.filename.strip():
            raise ValueError(
                f"Environment '{env_key}' has an empty 'filename'. The filename must be non-empty."
            )
        output_filename = env_config.filename
    elif env_config.filename_suffix:
        # Validate filename_suffix is not empty
        if not env_config.filename_suffix or not env_config.filename_suffix.strip():
            raise ValueError(
                f"Environment '{env_key}' has an empty 'filename_suffix'. "
                f"The filename_suffix must be non-empty."
            )
        # Use prompt file stem with suffix, stripping .canon/.canonical prefix
        base_name = prompt_file.stem
        # Remove .canon or .canonical suffix if present
        if base_name.endswith(".canon"):
            base_name = base_name[:-6]  # Remove ".canon"
        elif base_name.endswith(".canonical"):
            base_name = base_name[:-10]  # Remove ".canonical"
        output_filename = base_name + env_config.filename_suffix
    else:
        raise ValueError(
            f"Environment '{env_key}' must specify either 'filename' or 'filename_suffix'. "
            f"Both are missing or None."
        )

    output_path = output_dir / output_filename

    # Check if we should write the file
    if not should_write_file(output_path, force, console):
        console.print(f"  [dim]⏭[/dim] Skipped {output_filename}")
        return

    # Build environment-specific frontmatter
    env_config_dict = {k: v for k, v in vars(env_config).items() if k != "target" and v is not None}
    frontmatter = {
        "meta": prompt.meta,
        "filename": output_filename,
        **env_config_dict,
    }

    # Write the prompt with environment-specific frontmatter
    import yaml

    output_content = f"""---
{yaml.safe_dump(frontmatter, default_flow_style=False)}---

{prompt.content}"""

    output_path.write_text(output_content, encoding="utf-8")
    console.print(f"  [green]✓[/green] Installed {output_filename}")


def install_canonical_prompt_directory(
    prompts_dir: Path,
    env_key: str,
    target: Path,
    console: Console,
    *,
    force: bool = False,
) -> None:
    """Install all canonical prompt files from a directory to the specified environment.

    Args:
        prompts_dir: Directory containing canonical prompt files.
        env_key: Environment key to install for.
        target: Target directory to install in.
        console: Rich console for output.
        force: Whether to overwrite existing files.

    Raises:
        ValueError: If no canonical prompts found or invalid.
    """
    from dot_work.prompts.canonical import CanonicalPromptParser

    # Find canonical prompt files
    canonical_files = list(prompts_dir.glob("*.canon.md"))
    canonical_files.extend(prompts_dir.glob("*.canonical.md"))

    if not canonical_files:
        raise ValueError(f"No canonical prompt files found in {prompts_dir}")

    parser = CanonicalPromptParser()
    installed_count = 0

    console.print(f"Installing {len(canonical_files)} canonical prompt(s) for {env_key}...")

    for prompt_file in canonical_files:
        try:
            # Check if this file has the target environment before installing
            prompt = parser.parse(prompt_file)
            if env_key not in prompt.environments:
                available = ", ".join(prompt.list_environments())
                console.print(
                    f"  [dim]⏭[/dim] Skipped {prompt_file.name} (no '{env_key}' environment, available: {available})"
                )
                continue

            install_canonical_prompt(prompt_file, env_key, target, console, force=force)
            installed_count += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to install {prompt_file.name}: {e}")

    if installed_count == 0:
        raise ValueError(
            f"Environment '{env_key}' not found in any canonical prompt. "
            f"Processed {len(canonical_files)} canonical prompt file(s), but none contained "
            f"the '{env_key}' environment."
        )

    console.print(f"[green]✓[/green] Completed installation of {installed_count} canonical prompts")


# =============================================================================
# Canonical Prompt Frontmatter Discovery
# =============================================================================

def discover_available_environments(prompts_dir: Path) -> dict[str, set[str]]:
    """Discover available environments from prompt file frontmatter.

    Scans all *.prompt.md files, parses their canonical frontmatter,
    and returns which environments each prompt supports.

    Args:
        prompts_dir: Directory containing prompt files with canonical frontmatter.

    Returns:
        Dictionary mapping environment names to sets of prompt file names that support them.
        Example: {"claude": {"do-work", "new-issue"}, "copilot": {"do-work"}}
    """
    from dot_work.prompts.canonical import CanonicalPromptParser

    parser = CanonicalPromptParser()
    environments: dict[str, set[str]] = {}

    # Find all prompt files with canonical frontmatter
    for prompt_file in prompts_dir.glob("*.prompt.md"):
        try:
            prompt = parser.parse(prompt_file)
            prompt_name = prompt_file.stem

            # Add this prompt to each environment it supports
            for env_name in prompt.environments:
                if env_name not in environments:
                    environments[env_name] = set()
                environments[env_name].add(prompt_name)
        except Exception:
            # Skip files that can't be parsed (not canonical format)
            continue

    return environments


def install_canonical_prompts_by_environment(
    env_name: str,
    target: Path,
    prompts_dir: Path,
    console: Console,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Install canonical prompts for a specific environment using frontmatter paths.

    For each prompt file that supports the specified environment, reads the
    environment configuration from its frontmatter and installs it to the
    target path specified in the frontmatter.

    Args:
        env_name: Name of the environment to install for (e.g., 'claude', 'copilot').
        target: Target project directory to install in.
        prompts_dir: Source directory containing canonical prompt files.
        console: Rich console for output.
        force: If True, overwrite existing files without prompting.
        dry_run: If True, preview changes without writing files.

    Raises:
        ValueError: If environment not found in any prompts or installation fails.
    """
    from dot_work.prompts.canonical import CanonicalPromptParser

    parser = CanonicalPromptParser()
    prompt_files = list(prompts_dir.glob("*.prompt.md"))
    installed_count = 0
    skipped_count = 0

    if not prompt_files:
        raise ValueError(f"No prompt files found in {prompts_dir}")

    console.print(f"Installing prompts for environment: [bold cyan]{env_name}[/bold cyan]")
    console.print(f"Source: {prompts_dir}")
    console.print(f"Target: {target}\n")

    # Scan phase: categorize files
    state = InstallState()
    install_plan: list[tuple[Path, Path, Path]] = []  # (prompt_file, output_dir, output_path)

    for prompt_file in prompt_files:
        try:
            prompt = parser.parse(prompt_file)

            # Skip if prompt doesn't support this environment
            if env_name not in prompt.environments:
                continue

            # Get environment config from frontmatter
            env_config = prompt.get_environment(env_name)

            # Determine output directory from frontmatter target
            if env_config.target.startswith("/"):
                # Absolute path (relative to target root)
                output_dir = target / env_config.target.lstrip("/")
            elif env_config.target.startswith("./"):
                # Relative path
                output_dir = target / env_config.target[2:]
            else:
                # Relative path
                output_dir = target / env_config.target

            # Determine filename from frontmatter
            if env_config.filename:
                output_filename = env_config.filename
            elif env_config.filename_suffix:
                # Use prompt file stem with suffix
                output_filename = prompt_file.stem + env_config.filename_suffix
            else:
                # Default to original filename
                output_filename = prompt_file.name

            output_path = output_dir / output_filename
            install_plan.append((prompt_file, output_dir, output_path))

            # Track for batch prompting
            if output_path.exists():
                state.existing_files.append(output_path)
            else:
                state.new_files.append(output_path)

        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Skipping {prompt_file.name}: {e}")
            skipped_count += 1

    if not install_plan:
        raise ValueError(
            f"Environment '{env_name}' not found in any prompt files. "
            f"Checked {len(prompt_files)} file(s)."
        )

    # Show batch menu if there are existing files and not in force/dry-run mode
    batch_choice: BatchChoice | None = None
    if state.has_existing_files and not force and not dry_run:
        batch_choice = _prompt_batch_choice(console, state)
        if batch_choice == BatchChoice.CANCEL:
            console.print("[yellow]Installation cancelled.[/yellow]")
            return

    # Installation phase
    if not dry_run:
        console.print(f"Installing {len(install_plan)} prompt(s)...\n")
    else:
        console.print(f"[yellow][DRY-RUN] Would install {len(install_plan)} prompt(s):[/yellow]\n")

    for prompt_file, output_dir, output_path in install_plan:
        # Check if we should write
        if not dry_run and not should_write_file(
            output_path, force, console, batch_choice=batch_choice
        ):
            console.print(f"  [dim]⏭[/dim] Skipped {output_path.name}")
            continue

        # Create directory if needed
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        # Read prompt content
        prompt = parser.parse(prompt_file)

        # Write output (without extra frontmatter - prompts already have it)
        if dry_run:
            action = "[CREATE]" if not output_path.exists() else "[OVERWRITE]"
            console.print(f"  [yellow][DRY-RUN][/yellow] [dim]{action}[/dim] {output_path}")
        else:
            # Write the prompt file as-is (it already has proper frontmatter)
            output_path.write_text(prompt_file.read_text(encoding="utf-8"), encoding="utf-8")
            console.print(f"  [green]✓[/green] Installed {output_path.name}")
            installed_count += 1

    if dry_run:
        console.print(f"\n[cyan]📁 Dry-run complete: {len(install_plan)} file(s) would be installed[/cyan]")
    else:
        console.print(f"\n[cyan]📁 Installed {installed_count} prompt(s) for {env_name}[/cyan]")

    if skipped_count > 0:
        console.print(f"[dim]⚠ {skipped_count} file(s) skipped due to errors[/dim]")
