"""Subagents module for cross-environment AI agent definitions.

This module provides support for defining and managing subagents/custom agents
that can be deployed across multiple AI coding environments:
- Claude Code (.claude/agents/)
- OpenCode (.opencode/agent/)
- GitHub Copilot (.github/agents/)

Public API:
    SubagentMetadata: Lightweight metadata for discovery/listing
    SubagentConfig: Full subagent configuration
    CanonicalSubagent: Canonical subagent with multi-environment support
    SubagentParser: Parser for markdown + YAML frontmatter files
    SubagentValidator: Validation for subagent definitions
    SubagentDiscovery: Discover subagents in configured paths
    SubagentGenerator: Generate environment-specific files

Example:
    from dot_work.subagents import (
        SubagentDiscovery,
        SubagentGenerator,
        DEFAULT_DISCOVERY,
    )

    # Discover subagents
    discovery = SubagentDiscovery(project_root=".", environment="claude")
    subagents = discovery.discover_native()

    # Generate native file
    generator = SubagentGenerator()
    native_content = generator.generate_native(canonical_subagent, "claude")
"""

from dot_work.subagents.discovery import DEFAULT_DISCOVERY, SubagentDiscovery
from dot_work.subagents.generator import SUBAGENT_GENERATOR, SubagentGenerator
from dot_work.subagents.models import (
    CanonicalSubagent,
    SubagentConfig,
    SubagentEnvironmentConfig,
    SubagentMetadata,
)
from dot_work.subagents.parser import SUBAGENT_PARSER, SubagentParser
from dot_work.subagents.validator import SUBAGENT_VALIDATOR, SubagentValidator

__all__ = [
    # Models
    "SubagentMetadata",
    "SubagentConfig",
    "SubagentEnvironmentConfig",
    "CanonicalSubagent",
    # Parser
    "SubagentParser",
    "SUBAGENT_PARSER",
    # Validator
    "SubagentValidator",
    "SUBAGENT_VALIDATOR",
    # Discovery
    "SubagentDiscovery",
    "DEFAULT_DISCOVERY",
    # Generator
    "SubagentGenerator",
    "SUBAGENT_GENERATOR",
]
