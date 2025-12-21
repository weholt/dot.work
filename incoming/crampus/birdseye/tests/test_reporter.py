"""Tests for the markdown reporter."""

from __future__ import annotations

from pathlib import Path

from birdseye.pipeline import analyze_project
from birdseye.reporter import build_markdown_report


def test_build_markdown_report_lists_features(sample_project: Path) -> None:
    bundle = analyze_project(sample_project)
    report = build_markdown_report(bundle)

    assert "# Birdseye Project Guide" in report
    assert "## Feature Walkthrough" in report
    assert "```mermaid" in report

    # Ensure a representative feature is documented.
    assert "read_greeting" in report
    assert "GreetingService" in report

    # Confirm model table presence when models exist.
    assert "## Data Models" in report
    assert "Profile" in report
