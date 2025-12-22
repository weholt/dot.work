"""Tests for version changelog module."""

from pathlib import Path
from unittest.mock import Mock, patch

from dot_work.version.changelog import ChangelogEntry, ChangelogGenerator
from dot_work.version.commit_parser import CommitInfo


def test_changelog_entry():
    """Test ChangelogEntry dataclass."""
    entry = ChangelogEntry(
        version="2025.01.001",
        date="2025-01-01",
        changes=[
            "feat: Add new feature",
            "fix: Fix bug",
        ],
        author="Test Author"
    )

    assert entry.version == "2025.01.001"
    assert entry.date == "2025-01-01"
    assert len(entry.changes) == 2
    assert entry.author == "Test Author"


def test_generate_conventional_summary():
    """Test generating conventional summary."""
    generator = ChangelogGenerator()

    commits = [
        CommitInfo(
            hash="abc123",
            short_hash="abc123",
            message="feat: add new feature",
            subject="add new feature",
            commit_type="feat",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        ),
        CommitInfo(
            hash="def456",
            short_hash="def456",
            message="fix: fix bug",
            subject="fix bug",
            commit_type="fix",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        ),
    ]

    summary = generator._generate_conventional_summary(commits)

    assert "1 new feature" in summary or "features" in summary
    assert "1 bug fix" in summary or "bug fixes" in summary


def test_generate_with_template(temp_dir: Path):
    """Test generating changelog with template."""
    generator = ChangelogGenerator()

    # Create a custom template
    template_content = """# Changelog

{% for entry in entries %}
## {{ entry.version }} - {{ entry.date }}

### Changes
{% for change in entry.changes %}
- {{ change }}
{% endfor %}

{% endfor %}
"""
    template = Path(temp_dir) / "template.md"
    template.write_text(template_content)

    entries = [
        ChangelogEntry(
            version="2025.01.001",
            date="2025-01-01",
            changes=["feat: Add new feature"],
            author="Test Author"
        )
    ]

    changelog = generator.generate(entries, str(template))

    assert "# Changelog" in changelog
    assert "## 2025.01.001 - 2025-01-01" in changelog
    assert "- feat: Add new feature" in changelog


def test_generate_with_default_template():
    """Test generating changelog with default template."""
    generator = ChangelogGenerator()

    entries = [
        ChangelogEntry(
            version="2025.01.001",
            date="2025-01-01",
            changes=["feat: Add new feature", "fix: Fix bug"],
            author="Test Author"
        )
    ]

    # Should not raise exception with default template
    changelog = generator.generate(entries)

    assert "2025.01.001" in changelog
    assert "2025-01-01" in changelog


def test_generate_summary_with_use_llm_false():
    """Test generate_summary with use_llm=False."""
    generator = ChangelogGenerator()

    commits = [
        CommitInfo(
            hash="abc123",
            short_hash="abc123",
            message="feat: add feature",
            subject="add feature",
            commit_type="feat",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        )
    ]

    summary = generator.generate_summary(commits, use_llm=False)

    # Should return conventional summary
    assert summary is not None
    assert len(summary) > 0


def test_generate_summary_with_use_llm_true():
    """Test generate_summary with use_llm=True (placeholder)."""
    generator = ChangelogGenerator()

    commits = [
        CommitInfo(
            hash="abc123",
            short_hash="abc123",
            message="feat: add feature",
            subject="add feature",
            commit_type="feat",
            scope=None,
            breaking=False,
            author="Test Author",
            date="2025-01-01"
        )
    ]

    # With LLM integration not implemented, should fall back to conventional
    summary = generator.generate_summary(commits, use_llm=True)

    assert summary is not None
    assert len(summary) > 0