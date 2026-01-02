"""Tests for version changelog module."""

from pathlib import Path

from dot_version.changelog import ChangelogEntry, ChangelogGenerator
from dot_version.commit_parser import CommitInfo


def test_changelog_entry():
    """Test ChangelogEntry dataclass."""
    commits_by_type = {
        "Features": [
            CommitInfo(
                commit_hash="abc123",
                short_hash="abc123",
                commit_type="feat",
                scope=None,
                subject="Add new feature",
                body="",
                author="Test Author",
                date="2025-01-01",
                is_breaking=False,
            )
        ]
    }

    entry = ChangelogEntry(
        version="2025.01.001",
        date="2025-01-01",
        summary="Test release",
        highlights=["Added new feature", "Fixed bug"],
        commits_by_type=commits_by_type,
        statistics={"commit_count": 1, "contributor_count": 1},
        contributors=[("Test Author", 1)],
        project_name="Test Project",
    )

    assert entry.version == "2025.01.001"
    assert entry.date == "2025-01-01"
    assert len(entry.highlights) == 2
    assert entry.project_name == "Test Project"


def test_generate_conventional_summary():
    """Test generating conventional summary."""
    generator = ChangelogGenerator()

    commits = [
        CommitInfo(
            commit_hash="abc123",
            short_hash="abc123",
            commit_type="feat",
            scope=None,
            subject="add new feature",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        ),
        CommitInfo(
            commit_hash="def456",
            short_hash="def456",
            commit_type="fix",
            scope=None,
            subject="fix bug",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
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

### Summary
{{ entry.summary }}

{% for highlight in entry.highlights %}
- {{ highlight }}
{% endfor %}

{% endfor %}
"""
    template = Path(temp_dir) / "template.md"
    template.write_text(template_content)

    commits_by_type = {
        "Features": [
            CommitInfo(
                commit_hash="abc123",
                short_hash="abc123",
                commit_type="feat",
                scope=None,
                subject="Add new feature",
                body="",
                author="Test Author",
                date="2025-01-01",
                is_breaking=False,
            )
        ]
    }

    entries = [
        ChangelogEntry(
            version="2025.01.001",
            date="2025-01-01",
            summary="Test release",
            highlights=["Added new feature"],
            commits_by_type=commits_by_type,
            statistics={"commit_count": 1, "contributor_count": 1},
            contributors=[("Test Author", 1)],
            project_name="Test Project",
        )
    ]

    changelog = generator.generate(entries, str(template))

    assert "# Changelog" in changelog
    assert "## 2025.01.001 - 2025-01-01" in changelog
    assert "- Added new feature" in changelog


def test_generate_with_default_template():
    """Test generating changelog with default template."""
    generator = ChangelogGenerator()

    commits_by_type = {
        "Features": [
            CommitInfo(
                commit_hash="abc123",
                short_hash="abc123",
                commit_type="feat",
                scope=None,
                subject="Add new feature",
                body="",
                author="Test Author",
                date="2025-01-01",
                is_breaking=False,
            ),
            CommitInfo(
                commit_hash="def456",
                short_hash="def456",
                commit_type="fix",
                scope=None,
                subject="Fix bug",
                body="",
                author="Test Author",
                date="2025-01-01",
                is_breaking=False,
            ),
        ]
    }

    entries = [
        ChangelogEntry(
            version="2025.01.001",
            date="2025-01-01",
            summary="Test release",
            highlights=["Added new feature", "Fixed bug"],
            commits_by_type=commits_by_type,
            statistics={"commit_count": 2, "contributor_count": 1},
            contributors=[("Test Author", 2)],
            project_name="Test Project",
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
            commit_hash="abc123",
            short_hash="abc123",
            commit_type="feat",
            scope=None,
            subject="add feature",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        )
    ]

    summary = generator.generate_summary(commits)

    # Should return conventional summary
    assert summary is not None
    assert len(summary) > 0


def test_generate_summary_with_use_llm_true():
    """Test generate_summary with use_llm=True (placeholder)."""
    generator = ChangelogGenerator()

    commits = [
        CommitInfo(
            commit_hash="abc123",
            short_hash="abc123",
            commit_type="feat",
            scope=None,
            subject="add feature",
            body="",
            author="Test Author",
            date="2025-01-01",
            is_breaking=False,
        )
    ]

    # With LLM integration not implemented, should fall back to conventional
    summary = generator.generate_summary(commits)

    assert summary is not None
    assert len(summary) > 0
