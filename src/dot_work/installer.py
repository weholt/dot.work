"""Installer functions for different AI environments."""

import importlib.resources
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


def install_prompts(
    env_key: str,
    target: Path,
    prompts_dir: Path,
    console: Console,
) -> None:
    """Install prompts for the specified environment."""
    installer = INSTALLERS.get(env_key)
    if not installer:
        raise ValueError(f"Unknown environment: {env_key}")

    installer(target, prompts_dir, console)


def install_for_copilot(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for GitHub Copilot (VS Code)."""
    dest_dir = target / ".github" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["copilot"]

    for prompt_file in prompts_dir.glob("*.md"):
        if prompt_file.name.endswith(".prompt.md"):
            dest_name = prompt_file.name
        else:
            dest_name = prompt_file.stem + ".prompt.md"

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = dest_dir / dest_name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {dest_name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")
    console.print("[dim]💡 Use with: /project-from-discussion or /issue-tracker-setup[/dim]")


def install_for_claude(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Claude Code."""
    claude_md = target / "CLAUDE.md"
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


def install_for_cursor(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Cursor."""
    rules_dir = target / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["cursor"]

    for prompt_file in prompts_dir.glob("*.md"):
        dest_name = prompt_file.stem + ".mdc"

        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = rules_dir / dest_name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {dest_name}")

    cursorrules = target / ".cursorrules"
    if not cursorrules.exists():
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

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {rules_dir}")
    console.print("[dim]💡 Rules available in Cursor's @ menu[/dim]")


def install_for_windsurf(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Windsurf."""
    rules_dir = target / ".windsurf" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["windsurf"]

    for prompt_file in prompts_dir.glob("*.md"):
        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = rules_dir / prompt_file.name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    windsurfrules = target / ".windsurfrules"
    if not windsurfrules.exists():
        windsurfrules.write_text(
            "# Windsurf Rules\n\nSee .windsurf/rules/ for detailed prompts.\n", encoding="utf-8"
        )
        console.print(f"  [green]✓[/green] Created {windsurfrules.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {rules_dir}")


def install_for_aider(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Aider."""
    conventions_md = target / "CONVENTIONS.md"
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


def install_for_continue(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Continue.dev."""
    dest_dir = target / ".continue" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["continue"]

    for prompt_file in prompts_dir.glob("*.md"):
        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = dest_dir / prompt_file.name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")
    console.print("[dim]💡 Access prompts via Continue's slash commands[/dim]")


def install_for_amazon_q(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Amazon Q Developer."""
    amazonq_dir = target / ".amazonq"
    amazonq_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["amazon-q"]

    rules_md = amazonq_dir / "rules.md"
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


def install_for_zed(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for Zed AI."""
    dest_dir = target / ".zed" / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["zed"]

    for prompt_file in prompts_dir.glob("*.md"):
        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = dest_dir / prompt_file.name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {dest_dir}")


def install_for_opencode(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for OpenCode."""
    opencode_prompts_dir = target / ".opencode" / "prompts"
    opencode_prompts_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["opencode"]

    for prompt_file in prompts_dir.glob("*.md"):
        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = opencode_prompts_dir / prompt_file.name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    agents_md = target / "AGENTS.md"
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

    console.print(f"\n[cyan]📁 Prompts installed to:[/cyan] {opencode_prompts_dir}")
    console.print(f"[cyan]📄 Instructions in:[/cyan] {agents_md}")
    console.print("[dim]💡 Reference prompts with: 'Read .opencode/prompts/<name>.prompt.md'[/dim]")


def install_for_generic(target: Path, prompts_dir: Path, console: Console) -> None:
    """Install prompts for generic/manual use."""
    dest_dir = target / "prompts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    env_config = ENVIRONMENTS["generic"]

    for prompt_file in prompts_dir.glob("*.md"):
        # Render template with environment-specific values
        rendered_content = render_prompt(prompts_dir, prompt_file, env_config)

        dest_path = dest_dir / prompt_file.name
        dest_path.write_text(rendered_content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Installed {prompt_file.name}")

    agents_md = target / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text(
            "# AI Agent Instructions\n\n"
            "See the `prompts/` directory for detailed instructions:\n\n"
            "- `project-from-discussion.prompt.md` - Convert discussions to projects\n"
            "- `issue-tracker-setup.prompt.md` - Set up file-based issue tracking\n\n"
            "When starting a new project, ask the AI to read and follow these prompts.\n",
            encoding="utf-8",
        )
        console.print(f"  [green]✓[/green] Created {agents_md.name}")

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
