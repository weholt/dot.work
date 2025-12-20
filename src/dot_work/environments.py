"""Environment configurations for different AI coding tools."""

from dataclasses import dataclass, field


@dataclass
class Environment:
    """Represents an AI coding environment configuration."""

    key: str
    name: str
    prompt_dir: str | None
    prompt_extension: str | None
    instructions_file: str | None
    rules_file: str | None
    detection: list[str] = field(default_factory=list)
    notes: str = ""


# Environment configurations
ENVIRONMENTS: dict[str, Environment] = {
    "copilot": Environment(
        key="copilot",
        name="GitHub Copilot (VS Code)",
        prompt_dir=".github/prompts",
        prompt_extension=".prompt.md",
        instructions_file=None,
        rules_file=".github/copilot-instructions.md",
        detection=[".github/prompts", ".vscode"],
        notes="Prompts invoked with /prompt-name",
    ),
    "claude": Environment(
        key="claude",
        name="Claude Code",
        prompt_dir=None,
        prompt_extension=None,
        instructions_file="CLAUDE.md",
        rules_file="CLAUDE.md",
        detection=["CLAUDE.md"],
        notes="All instructions in CLAUDE.md at project root",
    ),
    "cursor": Environment(
        key="cursor",
        name="Cursor",
        prompt_dir=".cursor/rules",
        prompt_extension=".mdc",
        instructions_file=None,
        rules_file=".cursorrules",
        detection=[".cursorrules", ".cursor"],
        notes="Rules in .cursorrules, prompts in .cursor/rules/",
    ),
    "windsurf": Environment(
        key="windsurf",
        name="Windsurf (Codeium)",
        prompt_dir=".windsurf/rules",
        prompt_extension=".md",
        instructions_file=None,
        rules_file=".windsurfrules",
        detection=[".windsurfrules", ".windsurf"],
        notes="Similar to Cursor structure",
    ),
    "aider": Environment(
        key="aider",
        name="Aider",
        prompt_dir=None,
        prompt_extension=None,
        instructions_file=".aider.conf.yml",
        rules_file="CONVENTIONS.md",
        detection=[".aider.conf.yml", ".aider"],
        notes="Uses CONVENTIONS.md for coding standards",
    ),
    "continue": Environment(
        key="continue",
        name="Continue.dev",
        prompt_dir=".continue/prompts",
        prompt_extension=".md",
        instructions_file=None,
        rules_file=".continue/config.json",
        detection=[".continue"],
        notes="Prompts in .continue/prompts/",
    ),
    "amazon-q": Environment(
        key="amazon-q",
        name="Amazon Q Developer",
        prompt_dir=None,
        prompt_extension=None,
        instructions_file=None,
        rules_file=".amazonq/rules.md",
        detection=[".amazonq"],
        notes="Uses .amazonq/rules.md for project context",
    ),
    "zed": Environment(
        key="zed",
        name="Zed AI",
        prompt_dir=".zed/prompts",
        prompt_extension=".md",
        instructions_file=None,
        rules_file=None,
        detection=[".zed"],
        notes="Prompts stored in .zed/prompts/",
    ),
    "opencode": Environment(
        key="opencode",
        name="OpenCode",
        prompt_dir=".opencode/prompts",
        prompt_extension=".md",
        instructions_file="AGENTS.md",
        rules_file="AGENTS.md",
        detection=[".opencode", "opencode.json"],
        notes="Uses AGENTS.md + .opencode/prompts/ for commands",
    ),
    "generic": Environment(
        key="generic",
        name="Generic / Manual",
        prompt_dir="prompts",
        prompt_extension=".md",
        instructions_file="AGENTS.md",
        rules_file="AGENTS.md",
        detection=[],
        notes="Prompts in prompts/ folder, manually referenced",
    ),
}
