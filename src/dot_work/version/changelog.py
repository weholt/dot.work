"""Changelog generator with template rendering."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template

from dot_work.version.commit_parser import CommitInfo, ConventionalCommitParser


@dataclass
class ChangelogEntry:
    """Changelog entry information."""

    version: str
    date: str
    summary: str
    highlights: list[str]
    commits_by_type: dict[str, list[CommitInfo]]
    statistics: dict
    contributors: list[tuple[str, int]]
    project_name: str = "Project"  # Project name from pyproject.toml


class ChangelogGenerator:
    """Generate changelog entries from commits."""

    DEFAULT_TEMPLATE = """# {{ project_name }} - Version {{ version }} ({{ date }})

## Summary
{{ summary }}

{% if highlights %}
## Highlights
{% for highlight in highlights %}
- {{ highlight }}
{% endfor %}
{% endif %}

## Changes

{% for type_name, commits in commits_by_type.items() %}
### {{ type_name }}
{% for commit in commits %}
- [{{ commit.commit_type }}] {{ commit.subject }} ({{ commit.short_hash }}) @{{ commit.author }}
{% endfor %}

{% endfor %}

## Statistics
- Total commits: {{ statistics.commit_count }}
- Contributors: {{ statistics.contributor_count }}

## Contributors
{% for author, count in contributors %}
- {{ author }} ({{ count }} commits)
{% endfor %}

---

"""

    def __init__(self, template_path: Path | None = None):
        """Initialize changelog generator.
        
        Args:
            template_path: Optional custom template file
        """
        if template_path and template_path.exists():
            self.template = Template(template_path.read_text(encoding='utf-8'))
        else:
            self.template = Template(self.DEFAULT_TEMPLATE)

    def generate_entry(
        self,
        version: str,
        commits: list[CommitInfo],
        repo_stats: dict,
        use_llm: bool = False,
        project_name: str = "Project"
    ) -> str:
        """Generate a changelog entry for a version.
        
        Args:
            version: Version string
            commits: List of commits
            repo_stats: Repository statistics
            use_llm: Whether to use LLM for summaries
            project_name: Name of the project from pyproject.toml
            
        Returns:
            Formatted changelog entry
        """
        parser = ConventionalCommitParser()
        commits_by_type = parser.group_commits_by_type(commits)

        # Map internal types to display names
        display_commits = {}
        for commit_type, commit_list in commits_by_type.items():
            display_name = parser.COMMIT_TYPES.get(commit_type, commit_type.title())
            display_commits[display_name] = commit_list

        highlights = self.extract_highlights(commits)
        summary = self.generate_summary(commits, use_llm)
        contributors = self._count_contributors(commits)

        entry = ChangelogEntry(
            version=version,
            date=self._get_current_date(),
            summary=summary,
            highlights=highlights,
            commits_by_type=display_commits,
            statistics=repo_stats,
            contributors=contributors,
            project_name=project_name
        )

        return self.template.render(
            version=entry.version,
            date=entry.date,
            summary=entry.summary,
            highlights=entry.highlights,
            commits_by_type=entry.commits_by_type,
            statistics=entry.statistics,
            contributors=entry.contributors,
            project_name=entry.project_name
        )

    def extract_highlights(self, commits: list[CommitInfo]) -> list[str]:
        """Extract notable changes from commits.
        
        Args:
            commits: List of commits
            
        Returns:
            List of highlight strings
        """
        highlights = []
        keywords = ['breaking', 'security', 'performance', 'major', 'important']

        for commit in commits:
            message_lower = (commit.subject + ' ' + commit.body).lower()
            if any(kw in message_lower for kw in keywords):
                highlights.append(commit.subject)

        return highlights[:5]  # Limit to 5 highlights

    def generate_summary(self, commits: list[CommitInfo], use_llm: bool) -> str:
        """Generate version summary.
        
        Args:
            commits: List of commits
            use_llm: Whether to use LLM
            
        Returns:
            Summary string
        """
        if use_llm:
            # TODO: Implement LLM integration
            return self._generate_conventional_summary(commits)
        else:
            return self._generate_conventional_summary(commits)

    def _generate_conventional_summary(self, commits: list[CommitInfo]) -> str:
        """Generate summary from commit types.
        
        Args:
            commits: List of commits
            
        Returns:
            Summary string
        """
        parser = ConventionalCommitParser()
        grouped = parser.group_commits_by_type(commits)

        feat_count = len(grouped.get('feat', []))
        fix_count = len(grouped.get('fix', []))

        parts = []
        if feat_count > 0:
            parts.append(f"{feat_count} new feature{'s' if feat_count != 1 else ''}")
        if fix_count > 0:
            parts.append(f"{fix_count} bug fix{'es' if fix_count != 1 else ''}")

        if parts:
            return f"This release includes {' and '.join(parts)}."
        else:
            return f"This release includes {len(commits)} commit{'s' if len(commits) != 1 else ''}."

    def append_to_changelog(self, entry: str, changelog_path: Path) -> None:
        """Append new entry to CHANGELOG.md.
        
        Args:
            entry: Changelog entry text
            changelog_path: Path to CHANGELOG.md file
        """
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding='utf-8')
            # Prepend new entry
            new_content = entry + '\n' + existing
        else:
            # Create new file
            new_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{entry}"

        changelog_path.write_text(new_content, encoding='utf-8')

    def _count_contributors(self, commits: list[CommitInfo]) -> list[tuple[str, int]]:
        """Count commits per contributor.
        
        Args:
            commits: List of commits
            
        Returns:
            List of (author, count) tuples sorted by count
        """
        counts: dict[str, int] = {}
        for commit in commits:
            counts[commit.author] = counts.get(commit.author, 0) + 1

        return sorted(counts.items(), key=lambda x: x[1], reverse=True)

    def _get_current_date(self) -> str:
        """Get current date string.
        
        Returns:
            Date string in YYYY-MM-DD format
        """
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
