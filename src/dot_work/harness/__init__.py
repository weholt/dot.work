"""
Claude Agent SDK harness integration for dot-work.

This module provides autonomous agent task processing using the Claude Agent SDK,
with file-backed state tracking and iterative task completion.
"""

import typer

# Harness subcommand app
harness_app = typer.Typer(
    help="Claude Agent SDK autonomous agent harness for iterative task processing.",
    no_args_is_help=True,
)

__all__ = ["harness_app"]
