"""Installer functions for different AI environments."""

import importlib.resources
from datetime import UTC
from pathlib import Path

from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader
from rich.console import Console

from dot_work.environments import ENVIRONMENTS, Environment


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


def should_write_file(dest_path: Path, force: bool, console: Console) -> bool:
    """Check if a file should be written, prompting user if it exists.

    Args:
        dest_path: Path to the destination file.
        force: If True, overwrite without prompting.
        console: Rich console for user interaction.

    Returns:
        True if the file should be written, False to skip.
    """
    if not dest_path.exists():
        return True
    if force:
        return True

    # Prompt user for confirmation
    console.print(f"  [yellow]⚠[/yellow] File already exists: {dest_path.name}")
    response = console.input("    Overwrite? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def install_prompts(
    env_key: str,
    target: Path,
    prompts_dir: Path,
    console: Console,
    *,
    force: bool = False,
) -> None:
    """Install prompts for the specified environment.

    Args:
        env_key: The environment key (e.g., 'copilot', 'claude').
        target: Target directory to install prompts to.
        prompts_dir: Source directory containing prompt templates.
        console: Rich console for output.
        force: If True, overwrite existing files without prompting.
    """
    installer = INSTALLERS.get(env_key)
    if not installer:
        raise ValueError(f"Unknown environment: {env_key}")

    installer(target, prompts_dir, console, force=force)


def install_for_copilot(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for GitHub Copilot (VS Code)."""
    dest_dir = target / ".github" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["copilot"]

    for prompt_file in prompts_dir.glob("*.md"):
        if prompt_file.name.endswith(".prompt.md"):
            dest_name = prompt_file.name
        else:
            dest_name = prompt_file.stem + ".prompt.md"

        dest_path = dest_dir / dest_name
        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {dest_name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {dest_name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")
    console.print("[dim]💡 Use with: /project-from-discussion or /issue-tracker-setup[/dim]")


def install_for_claude(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Claude Code."""
    claude_md = target / "CLAUDE.md"

    if not should_write_file(claude_md, force, console):
        console.print(f"  [dim]⏭[/dim] Skipped {claude_md.name}")
        return

    env_config = ENVIRONMENTS["claude"]

    sections = [
        "# Claude Code Instructions\n\n",
        "This file contains AI agent instructions for this project.\n\n",
    ]

    for prompt_file in sorted(prompts_dir.glob("*.md")):
        # Render template with environment-specific values
        content = render_prompt(prompts_dir, prompt_file, env_config)
        title = prompt_file.stem.replace("-", " ").replace("_", " ").title()
        sections.append(f"---\n\n## {title}\n\n")
        sections.append(content)
        sections.append("\n\n")

    claude_md.write_text("".join(sections), encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {claude_md.name}")
    console.print(f"\n[cyan]📁 Instructions installed to:[/cyan] {claude_md}")
    console.print("[dim]💡 Claude will automatically read CLAUDE.md[/dim]")


def install_for_cursor(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Cursor."""
    rules_dir = target / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["cursor"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_name = prompt_file.stem + ".mdc"
        dest_path = rules_dir / dest_name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {dest_name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {dest_name}")

    cursorrules = target / ".cursorrules"
    if should_write_file(cursorrules, force, console):
        cursorrules.write_text(
            "# Cursor Rules\n\n"
            "See .cursor/rules/ for detailed prompts.\n\n"
            "## General Guidelines\n"
            "- Follow the project structure defined in prompts\n"
            "- Use type hints on all functions\n"
            "- Write tests for new functionality\n",
            encoding="utf-8",
        )
        console.print(f"  [green]✓[/green] Created {cursorrules.name}")
    elif cursorrules.exists():
        console.print(f"  [dim]⏭[/dim] Skipped {cursorrules.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {rules_dir}")
    console.print("[dim]💡 Rules available in Cursor's @ menu[/dim]")


def install_for_windsurf(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Windsurf."""
    rules_dir = target / ".windsurf" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["windsurf"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_path = rules_dir / prompt_file.name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {prompt_file.name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    windsurfrules = target / ".windsurfrules"
    if should_write_file(windsurfrules, force, console):
        windsurfrules.write_text(
            "# Windsurf Rules\n\nSee .windsurf/rules/ for detailed prompts.\n", encoding="utf-8"
        )
        console.print(f"  [green]✓[/green] Created {windsurfrules.name}")
    elif windsurfrules.exists():
        console.print(f"  [dim]⏭[/dim] Skipped {windsurfrules.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {rules_dir}")


def install_for_aider(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Aider."""
    conventions_md = target / "CONVENTIONS.md"

    if not should_write_file(conventions_md, force, console):
        console.print(f"  [dim]⏭[/dim] Skipped {conventions_md.name}")
        return

    env_config = ENVIRONMENTS["aider"]

    sections = ["# Project Conventions\n\n"]

    for prompt_file in sorted(prompts_dir.glob("*.md")):
        # Render template with environment-specific values
        content = render_prompt(prompts_dir, prompt_file, env_config)
        title = prompt_file.stem.replace("-", " ").replace("_", " ").title()
        sections.append(f"---\n\n## {title}\n\n")
        sections.append(content)
        sections.append("\n\n")

    conventions_md.write_text("".join(sections), encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {conventions_md.name}")
    console.print(f"\n[cyan]📁 Conventions installed to:[/cyan] {conventions_md}")
    console.print("[dim]💡 Aider will read CONVENTIONS.md automatically[/dim]")


def install_for_continue(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Continue.dev."""
    dest_dir = target / ".continue" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["continue"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_path = dest_dir / prompt_file.name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {prompt_file.name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")
    console.print("[dim]💡 Access prompts via Continue's slash commands[/dim]")


def install_for_amazon_q(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Amazon Q Developer."""
    amazonq_dir = target / ".amazonq"
    amazonq_dir.mkdir(parents=True, exist_ok=True)

    rules_md = amazonq_dir / "rules.md"

    if not should_write_file(rules_md, force, console):
        console.print(f"  [dim]⏭[/dim] Skipped {rules_md.name}")
        return

    env_config = ENVIRONMENTS["amazon-q"]
    sections = ["# Amazon Q Project Rules\n\n"]

    for prompt_file in sorted(prompts_dir.glob("*.md")):
        # Render template with environment-specific values
        content = render_prompt(prompts_dir, prompt_file, env_config)
        title = prompt_file.stem.replace("-", " ").replace("_", " ").title()
        sections.append(f"---\n\n## {title}\n\n")
        sections.append(content)
        sections.append("\n\n")

    rules_md.write_text("".join(sections), encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {rules_md.name}")
    console.print(f"\n[cyan]📁 Rules installed to:[/cyan] {rules_md}")


def install_for_zed(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for Zed AI."""
    dest_dir = target / ".zed" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["zed"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_path = dest_dir / prompt_file.name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {prompt_file.name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")


def install_for_opencode(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for OpenCode."""
    opencode_prompts_dir = target / ".opencode" / "prompts"
    opencode_prompts_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["opencode"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_path = opencode_prompts_dir / prompt_file.name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {prompt_file.name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    agents_md = target / "AGENTS.md"
    if should_write_file(agents_md, force, console):
        agents_content = """# AI Agent Instructions

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
"""
        agents_md.write_text(agents_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Created {agents_md.name}")
    elif agents_md.exists():
        console.print(f"  [dim]⏭[/dim] Skipped {agents_md.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {opencode_prompts_dir}")
    console.print(f"[cyan]📄 Instructions in:[/cyan] {agents_md}")
    console.print("[dim]💡 Reference prompts with: 'Read .opencode/prompts/<name>.prompt.md'[/dim]")


def install_for_generic(
    target: Path, prompts_dir: Path, console: Console, *, force: bool = False
) -> None:
    """Install prompts for generic/manual use."""
    dest_dir = target / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["generic"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_path = dest_dir / prompt_file.name

        if not should_write_file(dest_path, force, console):
            console.print(f"  [dim]⏭[/dim] Skipped {prompt_file.name}")
            continue

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    agents_md = target / "AGENTS.md"
    if should_write_file(agents_md, force, console):
        agents_md.write_text(
            "# AI Agent Instructions\n\n"
            "See the `prompts/` directory for detailed instructions:\n\n"
            "- `project-from-discussion.prompt.md` - Convert discussions to projects\n"
            "- `issue-tracker-setup.prompt.md` - Set up file-based issue tracking\n\n"
            "When starting a new project, ask the AI to read and follow these prompts.\n",
            encoding="utf-8",
        )
        console.print(f"  [green]✓[/green] Created {agents_md.name}")
    elif agents_md.exists():
        console.print(f"  [dim]⏭[/dim] Skipped {agents_md.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")
    console.print("[dim]💡 Reference these prompts manually in your AI conversations[/dim]")


# Installer dispatch table
INSTALLERS = {
    "copilot": install_for_copilot,
    "claude": install_for_claude,
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
