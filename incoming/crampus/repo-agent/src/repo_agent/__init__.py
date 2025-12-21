"""repo-agent: A configurable tool for running LLM-powered code agents in Docker.

This package provides tools to automatically modify GitHub repositories using
LLM-based code agents like OpenCode, Claude Code, or GitHub Copilot CLI.

Main features:
- Fully configurable through markdown frontmatter
- Docker-based isolated execution
- Automatic branch creation and PR management
- Support for multiple LLM providers
"""

from .core import run_from_markdown, RepoAgentError

__all__ = ["run_from_markdown", "RepoAgentError"]
