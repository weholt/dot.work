"""
Container provisioning module for dot-work.

This module provides functionality for running LLM-powered code agents
in Docker containers to modify GitHub repositories and create PRs.

The main entry point is the provision subpackage:
    from dot_work.container import provision
"""

# Export the main provision functionality
from dot_work.container import provision

__all__ = ["provision"]
