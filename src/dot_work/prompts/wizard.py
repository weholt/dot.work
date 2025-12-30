"""Interactive wizard for creating new canonical prompts.

This module provides an interactive CLI wizard that guides users through
creating new prompts with proper canonical frontmatter.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from dot_work.prompts.canonical import (
    CANONICAL_VALIDATOR,
)


@dataclass
class PromptType:
    """Prompt type configuration with suggested environments."""

    name: str
    description: str
    suggested_environments: list[str]


# Prompt type definitions
PROMPT_TYPES: dict[str, PromptType] = {
    "agent": PromptType(
        name="Agent workflow prompt",
        description="Autonomous agent workflow with multi-step processes",
        suggested_environments=["claude", "opencode"],
    ),
    "command": PromptType(
        name="Slash command",
        description="Single command invoked via slash syntax (e.g., /review)",
        suggested_environments=["claude", "copilot"],
    ),
    "review": PromptType(
        name="Code review prompt",
        description="Guidelines for reviewing code quality and security",
        suggested_environments=[
            "claude",
            "copilot",
            "cursor",
            "windsurf",
            "cline",
            "kilo",
            "aider",
            "continue",
            "opencode",
        ],
    ),
    "other": PromptType(
        name="Other",
        description="Custom prompt type (select environments manually)",
        suggested_environments=[],
    ),
}

# Environment target configurations
ENVIRONMENT_TARGETS: dict[str, tuple[str, str]] = {
    "claude": (".claude/commands/", ".md"),
    "copilot": (".github/prompts/", ".prompt.md"),
    "cursor": (".cursor/rules/", ".mdc"),
    "windsurf": (".windsurf/rules/", ".md"),
    "cline": (".clinerules/", ".md"),
    "kilo": (".kilocode/rules/", ".md"),
    "aider": (".aider/", ".md"),
    "continue": (".continue/prompts/", ".md"),
    "opencode": (".opencode/prompts/", ".md"),
}


class PromptWizard:
    """Interactive wizard for creating canonical prompts."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the wizard.

        Args:
            console: Optional Rich console instance. If None, creates a new one.
        """
        self.console = console or Console()
        self.prompt = Prompt(console=self.console)
        self.validator = CANONICAL_VALIDATOR

    def run(
        self,
        title: str | None = None,
        description: str | None = None,
        prompt_type: str | None = None,
        environments: list[str] | None = None,
    ) -> Path:
        """Run the interactive wizard.

        Args:
            title: Optional pre-provided title.
            description: Optional pre-provided description.
            prompt_type: Optional pre-provided prompt type.
            environments: Optional pre-provided environment list.

        Returns:
            Path to the created prompt file.
        """
        self._show_welcome()

        # Step 1: Title
        if title is None:
            title = self._prompt_title()
        else:
            self.console.print(f"[cyan]Title:[/cyan] {title}")

        # Step 2: Description
        if description is None:
            description = self._prompt_description()
        else:
            self.console.print(f"[cyan]Description:[/cyan] {description}")

        # Step 3: Version (default suggestion)
        version = "0.1.0"
        self.console.print(
            f"[cyan]Version:[/cyan] {version} (use [dim]--version[/dim] to override)"
        )

        # Step 4: Prompt type
        if prompt_type is None:
            prompt_type = self._prompt_type()
        else:
            self.console.print(f"[cyan]Type:[/cyan] {PROMPT_TYPES[prompt_type].name}")

        # Step 5: Environments
        if environments is None:
            environments = self._prompt_environments(prompt_type)
        else:
            self.console.print(f"[cyan]Environments:[/cyan] {', '.join(environments)}")

        # Step 6: Show configuration summary
        self._show_summary(title, description, version, prompt_type, environments)

        # Step 7: Confirm and create
        if not Confirm.ask("[cyan]Create prompt with this configuration?[/cyan]", default=True):
            self.console.print("[yellow]Wizard cancelled.[/yellow]")
            raise KeyboardInterrupt("Wizard cancelled by user")

        # Create the prompt file
        prompt_path = self._create_prompt_file(title, description, version, environments)

        # Step 8: Open editor
        self._open_editor(prompt_path)

        # Step 9: Validate created file
        self._validate_created_file(prompt_path)

        return prompt_path

    def _show_welcome(self) -> None:
        """Display welcome message."""
        self.console.print()
        self.console.print(
            Panel(
                "[bold cyan]Canonical Prompt Wizard[/bold cyan]\n\n"
                "This wizard will guide you through creating a new prompt\n"
                "with proper canonical frontmatter for AI coding environments.",
                title="Welcome",
                border_style="cyan",
            )
        )
        self.console.print()

    def _prompt_title(self) -> str:
        """Prompt for prompt title."""
        while True:
            title = self.prompt.ask("[cyan]Prompt title[/cyan]", default="My Custom Prompt")
            if title and title.strip():
                return title.strip()
            self.console.print("[red]Title cannot be empty.[/red]")

    def _prompt_description(self) -> str:
        """Prompt for prompt description."""
        while True:
            description = self.prompt.ask(
                "[cyan]Prompt description[/cyan]",
                default="A helpful prompt for my specific use case",
            )
            if description and description.strip():
                return description.strip()
            self.console.print("[red]Description cannot be empty.[/red]")

    def _prompt_type(self) -> str:
        """Prompt for prompt type selection."""
        self.console.print()
        self.console.print("[cyan]What type of prompt is this?[/cyan]")

        options = list(PROMPT_TYPES.keys())
        for i, (_key, ptype) in enumerate(PROMPT_TYPES.items(), 1):
            self.console.print(f"  [{i}] [cyan]{ptype.name}[/cyan] - {ptype.description}")

        while True:
            choice = self.prompt.ask(
                "[cyan]Select type[/cyan]",
                choices=[str(i) for i in range(1, len(options) + 1)],
                default="1",
            )
            return options[int(choice) - 1]

    def _prompt_environments(self, prompt_type: str) -> list[str]:
        """Prompt for environment selection.

        Args:
            prompt_type: Selected prompt type key.

        Returns:
            List of selected environment keys.
        """
        ptype = PROMPT_TYPES[prompt_type]
        suggested = ptype.suggested_environments

        self.console.print()
        self.console.print(f"[cyan]Suggested environments for {ptype.name}:[/cyan]")
        for env in suggested:
            self.console.print(f"  - [green]{env}[/green]")

        self.console.print()
        self.console.print("[cyan]Available environments:[/cyan]")
        all_envs = list(ENVIRONMENT_TARGETS.keys())
        for i, env in enumerate(all_envs, 1):
            suffix = " [dim](suggested)[/dim]" if env in suggested else ""
            self.console.print(f"  [{i}] {env}{suffix}")

        # Prompt for selection
        self.console.print()
        self.console.print("[dim]Enter environment numbers separated by commas (e.g., 1,3,5)[/dim]")
        self.console.print("[dim]Press Enter to accept all suggested environments[/dim]")

        while True:
            selection = self.prompt.ask("[cyan]Select environments[/cyan]", default="")

            if not selection:
                # Use suggested environments
                if suggested:
                    return suggested
                else:
                    self.console.print("[red]No suggested environments for this type.[/red]")
                    self.console.print("[red]Please select at least one environment.[/red]")
                    continue

            # Parse selection
            try:
                indices = [int(x.strip()) for x in selection.split(",")]
                selected = [all_envs[i - 1] for i in indices if 1 <= i <= len(all_envs)]

                if not selected:
                    self.console.print("[red]Please select at least one environment.[/red]")
                    continue

                return selected

            except (ValueError, IndexError):
                self.console.print(
                    "[red]Invalid selection. Please enter numbers separated by commas.[/red]"
                )

    def _show_summary(
        self,
        title: str,
        description: str,
        version: str,
        prompt_type: str,
        environments: list[str],
    ) -> None:
        """Show configuration summary.

        Args:
            title: Prompt title.
            description: Prompt description.
            version: Prompt version.
            prompt_type: Prompt type key.
            environments: Selected environments.
        """
        self.console.print()
        self.console.print(
            Panel(
                f"[bold]Title:[/bold] {title}\n"
                f"[bold]Description:[/bold] {description}\n"
                f"[bold]Version:[/bold] {version}\n"
                f"[bold]Type:[/bold] {PROMPT_TYPES[prompt_type].name}\n"
                f"[bold]Environments:[/bold] {', '.join(environments)}\n\n"
                f"[dim]Target paths:[/dim]",
                title="Configuration Summary",
                border_style="green",
            )
        )

        # Show target paths for each environment
        for env in environments:
            target, suffix = ENVIRONMENT_TARGETS.get(env, (".unknown/", ".md"))
            filename = self._generate_filename(title, suffix)
            self.console.print(f"  [cyan]{env}:[/cyan] {target}{filename}")

    def _generate_filename(self, title: str, suffix: str) -> str:
        """Generate filename from title.

        Args:
            title: Prompt title.
            suffix: File suffix (e.g., ".prompt.md").

        Returns:
            Generated filename.
        """
        import re

        # Convert title to lowercase, replace spaces and special chars with hyphens
        base = title.lower()
        base = re.sub(r"[^a-z0-9]+", "-", base)
        base = base.strip("-")

        return base + suffix

    def _create_prompt_file(
        self,
        title: str,
        description: str,
        version: str,
        environments: list[str],
    ) -> Path:
        """Create the prompt file with frontmatter.

        Args:
            title: Prompt title.
            description: Prompt description.
            version: Prompt version.
            environments: Selected environment keys.

        Returns:
            Path to the created prompt file.
        """
        # Get prompts directory
        from dot_work.installer import get_prompts_dir

        prompts_dir = get_prompts_dir()

        # Generate filename
        filename = self._generate_filename(title, ".prompt.md")
        prompt_path = prompts_dir / filename

        # Check if file already exists
        if prompt_path.exists():
            if not Confirm.ask(
                f"[yellow]File {filename} already exists. Overwrite?[/yellow]",
                default=False,
            ):
                self.console.print("[red]Wizard cancelled.[/red]")
                raise KeyboardInterrupt("File already exists and user chose not to overwrite")

        # Build frontmatter
        import io

        output = io.StringIO()
        output.write("---\n")
        output.write("meta:\n")
        output.write(f'  title: "{title}"\n')
        output.write(f'  description: "{description}"\n')
        output.write(f'  version: "{version}"\n')
        output.write("\nenvironments:\n")

        for env in environments:
            target, suffix = ENVIRONMENT_TARGETS.get(env, (f".{env}/", ".md"))
            output.write(f"  {env}:\n")
            output.write(f'    target: "{target}"\n')
            output.write(f'    filename_suffix: "{suffix}"\n')

        output.write("---\n")
        output.write("\n# ")
        output.write(title)
        output.write("\n\n")
        output.write("<!-- Prompt content goes here -->\n")
        output.write("\n")
        output.write("## Purpose\n\n")
        output.write(f"{description}\n")
        output.write("\n")
        output.write("## Usage\n\n")
        output.write("Describe how and when to use this prompt.\n")
        output.write("\n")
        output.write("## Guidelines\n\n")
        output.write("Provide specific guidelines for the AI agent.\n")

        # Write file
        prompt_path.write_text(output.getvalue())

        self.console.print()
        self.console.print(f"[green]✓[/green] Created: [cyan]{prompt_path}[/cyan]")

        return prompt_path

    def _open_editor(self, prompt_path: Path) -> None:
        """Open editor for prompt content editing.

        Args:
            prompt_path: Path to the prompt file.
        """
        editor = os.environ.get("EDITOR", "vim")

        if not Confirm.ask(
            f"[cyan]Open {editor} to edit the prompt content?[/cyan]",
            default=True,
        ):
            self.console.print("[dim]Skipping editor. You can edit the file manually later.[/dim]")
            return

        self.console.print(f"[dim]Opening {editor}...[/dim]")

        try:
            subprocess.call([editor, str(prompt_path)])
        except OSError as e:
            self.console.print(f"[yellow]Warning: Could not open editor: {e}[/yellow]")
            self.console.print("[yellow]Please edit the file manually.[/yellow]")

    def _validate_created_file(self, prompt_path: Path) -> None:
        """Validate the created prompt file.

        Args:
            prompt_path: Path to the prompt file.
        """
        self.console.print()

        try:
            from dot_work.prompts.canonical import CANONICAL_PARSER

            prompt = CANONICAL_PARSER.parse(prompt_path)

            errors = self.validator.validate(prompt, strict=False)

            if errors:
                self.console.print("[yellow]⚠ Validation warnings:[/yellow]")
                for error in errors:
                    if error.severity == "error":
                        self.console.print(f"  [red]✗[/red] {error}")
                    else:
                        self.console.print(f"  [yellow]⚠[/yellow] {error} [dim](warning)[/dim]")
            else:
                self.console.print("[green]✓[/green] Prompt validation [green]PASSED[/green]")

        except Exception as e:
            self.console.print(f"[yellow]⚠ Could not validate prompt: {e}[/yellow]")
            self.console.print("[yellow]Please review the file manually.[/yellow]")


def create_prompt_interactive(
    title: str | None = None,
    description: str | None = None,
    prompt_type: str | None = None,
    environments: list[str] | None = None,
    console: Console | None = None,
) -> Path:
    """Run the interactive prompt creation wizard.

    Args:
        title: Optional pre-provided title.
        description: Optional pre-provided description.
        prompt_type: Optional pre-provided prompt type (agent, command, review, other).
        environments: Optional pre-provided environment list.
        console: Optional Rich console instance.

    Returns:
        Path to the created prompt file.

    Raises:
        KeyboardInterrupt: If user cancels the wizard.
    """
    wizard = PromptWizard(console=console)
    return wizard.run(title, description, prompt_type, environments)


__all__ = [
    "PromptWizard",
    "create_prompt_interactive",
    "PROMPT_TYPES",
    "ENVIRONMENT_TARGETS",
]
