"""Parser for subagent definition files with YAML frontmatter.

This module implements the SubagentParser class which extracts and parses
subagent files following the subagent specification format.

The parser mirrors the pattern of SkillParser and CanonicalPromptParser
for consistency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentEnvironmentConfig,
    SubagentMetadata,
)


class SubagentParserError(Exception):
    """Error in subagent file parsing or validation."""


@dataclass
class ValidationError:
    """Represents a validation error in a subagent file."""

    field: str
    message: str
    severity: str = "error"  # error, warning

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class SubagentParser:
    """Parser for subagent definition files with YAML frontmatter.

    This class has no state - all methods are pure functions.
    Use the SUBAGENT_PARSER singleton for efficiency.

    The canonical frontmatter format:
    ---
    meta:
      name: code-reviewer
      description: Expert code reviewer for quality and security

    environments:
      claude:
        target: ".claude/agents/"
        model: sonnet
        permission_mode: default

      opencode:
        target: ".opencode/agent/"
        mode: subagent
        temperature: 0.1

    tools:
      - Read
      - Grep
      - Glob
      - Bash
    ---

    You are a senior code reviewer ensuring high standards...
    """

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

    def parse(self, file_path: str | Path) -> CanonicalSubagent:
        """Parse a canonical subagent file.

        Args:
            file_path: Path to the subagent .md file.

        Returns:
            CanonicalSubagent object with metadata, config, and environments.

        Raises:
            FileNotFoundError: If file not found.
            SubagentParserError: If parsing or validation fails.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Subagent file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8").strip()
        return self._parse_content(content, source_file=file_path)

    def parse_native(self, file_path: str | Path, environment: str) -> SubagentConfig:
        """Parse a native environment-specific subagent file.

        Args:
            file_path: Path to the native subagent file.
            environment: Environment name (claude, opencode, copilot).

        Returns:
            SubagentConfig object.

        Raises:
            FileNotFoundError: If file not found.
            SubagentParserError: If parsing or validation fails.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Subagent file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8").strip()
        return self._parse_native_content(content, environment, source_file=file_path)

    def _parse_content(self, content: str, source_file: Path) -> CanonicalSubagent:
        """Parse content string into CanonicalSubagent object.

        Args:
            content: Full subagent file content.
            source_file: Path to the source file.

        Returns:
            CanonicalSubagent object.

        Raises:
            ValueError: If frontmatter format is invalid.
            SubagentParserError: If YAML parsing fails or validation fails.
        """
        # Extract frontmatter and content
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Invalid subagent format: missing frontmatter markers")

        frontmatter_text, prompt_body = match.groups()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a dictionary")
        except yaml.YAMLError as e:
            raise SubagentParserError(f"Invalid YAML in frontmatter: {e}") from e

        # Extract metadata and config
        meta = self._extract_metadata(frontmatter, source_file)
        config = self._extract_config(frontmatter, prompt_body, source_file)
        environments = self._extract_environments(frontmatter, source_file)

        return CanonicalSubagent(
            meta=meta,
            config=config,
            environments=environments,
            source_file=source_file,
        )

    def _parse_native_content(
        self, content: str, environment: str, source_file: Path
    ) -> SubagentConfig:
        """Parse native environment-specific content into SubagentConfig.

        Args:
            content: Full native subagent file content.
            environment: Environment name (claude, opencode, copilot).
            source_file: Path to the source file.

        Returns:
            SubagentConfig object.

        Raises:
            ValueError: If frontmatter format is invalid.
            SubagentParserError: If YAML parsing fails or validation fails.
        """
        # Extract frontmatter and content
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Invalid subagent format: missing frontmatter markers")

        frontmatter_text, prompt_body = match.groups()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter must be a dictionary")
        except yaml.YAMLError as e:
            raise SubagentParserError(f"Invalid YAML in frontmatter: {e}") from e

        return self._extract_config(frontmatter, prompt_body, source_file)

    def _extract_metadata(
        self, frontmatter: dict[str, Any], source_file: Path
    ) -> SubagentMetadata:
        """Extract and validate metadata from frontmatter.

        Args:
            frontmatter: Parsed YAML frontmatter dictionary.
            source_file: Path to the source file (for error messages).

        Returns:
            SubagentMetadata object.

        Raises:
            SubagentParserError: If required fields are missing.
        """
        # Check for meta section
        meta_section = frontmatter.get("meta")
        if not isinstance(meta_section, dict):
            raise SubagentParserError(
                f"Missing or invalid 'meta' section in {source_file}"
            )

        # Check for required fields
        if "name" not in meta_section:
            raise SubagentParserError(
                f"Missing required field 'meta.name' in {source_file}"
            )

        if "description" not in meta_section:
            raise SubagentParserError(
                f"Missing required field 'meta.description' in {source_file}"
            )

        name = meta_section["name"]
        description = meta_section["description"]

        return SubagentMetadata(name=name, description=description)

    def _extract_config(
        self, frontmatter: dict[str, Any], prompt_body: str, source_file: Path
    ) -> SubagentConfig:
        """Extract configuration from frontmatter.

        Args:
            frontmatter: Parsed YAML frontmatter dictionary.
            prompt_body: Prompt body content.
            source_file: Path to the source file (for error messages).

        Returns:
            SubagentConfig object.
        """
        # Get name from meta or frontmatter root
        meta_section = frontmatter.get("meta", {})
        name = meta_section.get("name") or frontmatter.get("name")
        if name is None:
            raise SubagentParserError(f"Missing required field 'name' in {source_file}")
        description = meta_section.get("description") or frontmatter.get("description", "")

        # Extract optional fields
        tools = frontmatter.get("tools")
        model = frontmatter.get("model")
        permission_mode = frontmatter.get("permissionMode") or frontmatter.get("permission_mode")
        permissions = frontmatter.get("permissions")

        # OpenCode-specific
        mode = frontmatter.get("mode")
        temperature = frontmatter.get("temperature")
        max_steps = frontmatter.get("maxSteps") or frontmatter.get("max_steps")

        # Claude Code-specific
        skills = frontmatter.get("skills")

        # GitHub Copilot-specific
        target = frontmatter.get("target")
        infer = frontmatter.get("infer")
        mcp_servers = frontmatter.get("mcpServers") or frontmatter.get("mcp_servers")

        return SubagentConfig(
            name=name,
            description=description,
            prompt=prompt_body,
            tools=tools,
            model=model,
            permission_mode=permission_mode,
            permissions=permissions,
            mode=mode,
            temperature=temperature,
            max_steps=max_steps,
            skills=skills,
            target=target,
            infer=infer,
            mcp_servers=mcp_servers,
            source_file=source_file,
        )

    def _extract_environments(
        self, frontmatter: dict[str, Any], source_file: Path
    ) -> dict[str, SubagentEnvironmentConfig]:
        """Extract environment-specific configurations.

        Args:
            frontmatter: Parsed YAML frontmatter dictionary.
            source_file: Path to the source file (for error messages).

        Returns:
            Dict of environment name to SubagentEnvironmentConfig.
        """
        env_section = frontmatter.get("environments")
        if not isinstance(env_section, dict):
            return {}

        environments: dict[str, SubagentEnvironmentConfig] = {}

        for env_name, env_config in env_section.items():
            if not isinstance(env_config, dict):
                continue

            # Extract environment config
            target = env_config.get("target")
            if not target:
                continue

            environments[env_name] = SubagentEnvironmentConfig(
                target=target,
                model=env_config.get("model"),
                permission_mode=env_config.get("permissionMode") or env_config.get("permission_mode"),
                tools=env_config.get("tools"),
                mode=env_config.get("mode"),
                temperature=env_config.get("temperature"),
                max_steps=env_config.get("maxSteps") or env_config.get("max_steps"),
                skills=env_config.get("skills"),
                infer=env_config.get("infer"),
            )

        return environments


# Singleton instance for efficiency
SUBAGENT_PARSER = SubagentParser()
