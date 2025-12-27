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

    def __post_init__(self) -> None:
        """Validate environment configuration after initialization.

        Raises:
            ValueError: If prompt_dir contains invalid values.
        """
        # Validate prompt_dir if provided
        if self.prompt_dir is not None:
            # Check for empty string
            if not self.prompt_dir or not self.prompt_dir.strip():
                raise ValueError(
                    f"Environment '{self.name}' (key: {self.key}): "
                    f"prompt_dir cannot be empty, got: {self.prompt_dir!r}"
                )

            # Check for path traversal attempts
            if self.prompt_dir.startswith(".."):
                raise ValueError(
                    f"Environment '{self.name}' (key: {self.key}): "
                    f"path traversal not allowed in prompt_dir, got: {self.prompt_dir}"
                )

            # Check for absolute paths (relative paths expected)
            # Allow absolute paths for some environments but warn about them
            # This is intentionally lenient for flexibility but logged
            import logging

            logger = logging.getLogger(__name__)
            if self.prompt_dir.startswith("/"):
                logger.warning(
                    f"Environment '{self.name}' has absolute prompt_dir: {self.prompt_dir}. "
                    f"Relative paths are recommended."
                )


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
    "cline": Environment(
        key="cline",
        name="Cline",
        prompt_dir=".clinerules",
        prompt_extension=".md",
        instructions_file=None,
        rules_file=None,
        detection=[".clinerules"],
        notes="Folder-based system: all .md files in .clinerules/ are processed. Numeric prefixes optional for ordering.",
    ),
    "cody": Environment(
        key="cody",
        name="Sourcegraph Cody",
        prompt_dir=".cody",
        prompt_extension=".md",
        instructions_file=None,
        rules_file=None,
        detection=[".cody"],
        notes="Prompts in .cody/ directory. Cody uses Prompt Library server-side; local files for project-specific context.",
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
