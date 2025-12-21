"""Conventional commit parser for extracting commit information."""

import re
from dataclasses import dataclass

from git import Repo


@dataclass
class CommitInfo:
    """Parsed commit information."""

    commit_hash: str
    short_hash: str
    commit_type: str
    scope: str | None
    subject: str
    body: str
    author: str
    date: str
    is_breaking: bool


class ConventionalCommitParser:
    """Parser for conventional commit messages."""

    # Pattern: type(scope): subject
    COMMIT_PATTERN = re.compile(
        r'^(?P<type>\w+)(?:\((?P<scope>[\w-]+)\))?: (?P<subject>.+)$'
    )

    COMMIT_TYPES = {
        'feat': 'Features',
        'fix': 'Bug Fixes',
        'docs': 'Documentation',
        'chore': 'Internal Changes',
        'test': 'Tests',
        'refactor': 'Refactoring',
        'perf': 'Performance',
        'ci': 'CI/CD',
        'build': 'Build System',
        'style': 'Code Style',
    }

    def parse_commit(self, commit) -> CommitInfo:
        """Parse a git commit into structured data.
        
        Args:
            commit: GitPython commit object
            
        Returns:
            CommitInfo object
        """
        message = commit.message.strip()
        lines = message.split('\n')
        first_line = lines[0]
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

        # Try to parse conventional commit format
        match = self.COMMIT_PATTERN.match(first_line)

        if match:
            commit_type = match.group('type')
            scope = match.group('scope')
            subject = match.group('subject')
        else:
            # Fallback for non-conventional commits
            commit_type = 'other'
            scope = None
            subject = first_line

        # Check for breaking changes
        is_breaking = ('BREAKING CHANGE' in message or
                      'BREAKING-CHANGE' in message or
                      first_line.endswith('!'))

        return CommitInfo(
            commit_hash=commit.hexsha,
            short_hash=commit.hexsha[:12],
            commit_type=commit_type,
            scope=scope,
            subject=subject,
            body=body,
            author=commit.author.name,
            date=commit.committed_datetime.strftime('%Y-%m-%d'),
            is_breaking=is_breaking
        )

    def get_commits_since_tag(self, repo: Repo, tag: str | None) -> list[CommitInfo]:
        """Get all commits since a specific tag.
        
        Args:
            repo: Git repository
            tag: Starting tag, or None for all commits
            
        Returns:
            List of CommitInfo objects
        """
        if tag:
            commits = list(repo.iter_commits(f"{tag}..HEAD"))
        else:
            commits = list(repo.iter_commits())

        return [self.parse_commit(c) for c in commits]

    def group_commits_by_type(self, commits: list[CommitInfo]) -> dict[str, list[CommitInfo]]:
        """Group commits by their type.
        
        Args:
            commits: List of CommitInfo objects
            
        Returns:
            Dictionary mapping commit type to list of commits
        """
        grouped: dict[str, list[CommitInfo]] = {}

        for commit in commits:
            commit_type = commit.commit_type
            if commit_type not in grouped:
                grouped[commit_type] = []
            grouped[commit_type].append(commit)

        return grouped
