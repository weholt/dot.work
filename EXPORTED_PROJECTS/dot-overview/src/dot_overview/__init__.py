Overview module for generating project summaries."""

CLI_GROUP = "overview"

from dot_overview.pipeline import analyze_project
from dot_overview.reporter import build_markdown_report

__all__ = [
    "analyze_project",
    "build_markdown_report",
]
