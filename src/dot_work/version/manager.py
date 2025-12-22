"""Version manager for date-based versioning."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from git import Repo

from dot_work.version.project_parser import PyProjectParser


@dataclass
class VersionInfo:
    """Version information container."""

    version: str
    build_date: str
    git_commit: str
    git_tag: str
    previous_version: str | None = None
    changelog_generated: bool = False


class VersionManager:
    """Manages version information and calculations."""

    def __init__(self, project_root: Path):
        """Initialize version manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.version_file = self.project_root / "version.json"

        # Try to initialize git repo, but allow non-git directories
        self.repo: Repo | None = None
        try:
            self.repo = Repo(self.project_root)
        except Exception:
            pass

        # Load project information from pyproject.toml
        parser = PyProjectParser()
        self.project_info = parser.read_project_info(self.project_root)

    def read_version(self) -> VersionInfo | None:
        """Read current version from version.json.

        Returns:
            VersionInfo object or None if file doesn't exist
        """
        if not self.version_file.exists():
            return None

        with open(self.version_file, encoding="utf-8") as f:
            data = json.load(f)

        return VersionInfo(**data)

    def calculate_next_version(self, current: VersionInfo | None = None) -> str:
        """Calculate next version based on current date and build number.

        Args:
            current: Current version info, or None for first version

        Returns:
            Next version string in format YYYY.MM.NNNNN
        """
        now = datetime.now()
        year = now.year
        month = now.month

        if current is None:
            # First version
            return f"{year}.{month:02d}.00001"

        # Parse current version
        parts = current.version.split(".")
        curr_year = int(parts[0])
        curr_month = int(parts[1])
        curr_build = int(parts[2])

        if year == curr_year and month == curr_month:
            # Same month, increment build number
            return f"{year}.{month:02d}.{curr_build + 1:05d}"
        else:
            # New month, reset to 1
            return f"{year}.{month:02d}.00001"

    def write_version(self, version_info: VersionInfo) -> None:
        """Write version info to version.json.

        Args:
            version_info: Version information to write
        """
        data = {
            "version": version_info.version,
            "build_date": version_info.build_date,
            "git_commit": version_info.git_commit,
            "git_tag": version_info.git_tag,
            "previous_version": version_info.previous_version,
            "changelog_generated": version_info.changelog_generated,
        }

        with open(self.version_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def init_version(self, version: str | None = None) -> VersionInfo:
        """Initialize version file with first version.

        Args:
            version: Optional specific version, otherwise calculated

        Returns:
            Created VersionInfo
        """
        if self.version_file.exists():
            raise ValueError("Version file already exists")

        if version is None:
            version = self.calculate_next_version(None)

        # Get git commit if available
        git_commit = self.repo.head.commit.hexsha if self.repo else "unknown"

        version_info = VersionInfo(
            version=version,
            build_date=datetime.now().isoformat(),
            git_commit=git_commit,
            git_tag=f"version-{version}",
            previous_version=None,
            changelog_generated=False,
        )

        self.write_version(version_info)
        return version_info

    def freeze_version(self, use_llm: bool = False, dry_run: bool = False) -> VersionInfo:
        """Freeze a new version with changelog generation.

        Args:
            use_llm: Whether to use LLM for summaries
            dry_run: If True, preview without making changes

        Returns:
            New VersionInfo
        """
        # Import here to avoid circular dependency
        from dot_work.version.changelog import ChangelogGenerator
        from dot_work.version.commit_parser import ConventionalCommitParser

        current = self.read_version()
        next_version = self.calculate_next_version(current)

        # Get commits since last tag (only if repo exists)
        commits = []
        if self.repo:
            parser = ConventionalCommitParser()
            last_tag = current.git_tag if current else None
            commits = parser.get_commits_since_tag(self.repo, last_tag)

        # Generate changelog
        generator = ChangelogGenerator()
        changelog_entry = generator.generate_entry(
            version=next_version,
            commits=commits,
            repo_stats=self._get_repo_statistics(current.git_tag if current else None),
            use_llm=use_llm,
            project_name=self.project_info.name,
        )

        # Get git commit if available
        git_commit = self.repo.head.commit.hexsha if self.repo else "unknown"

        if not dry_run and self.repo:
            # Create git tag
            tag_name = f"version-{next_version}"
            self.repo.create_tag(tag_name, message=f"Release {next_version}")

            # Update version.json
            version_info = VersionInfo(
                version=next_version,
                build_date=datetime.now().isoformat(),
                git_commit=git_commit,
                git_tag=tag_name,
                previous_version=current.version if current else None,
                changelog_generated=True,
            )
            self.write_version(version_info)

            # Append to CHANGELOG.md
            changelog_path = self.project_root / "CHANGELOG.md"
            generator.append_to_changelog(changelog_entry, changelog_path)

            # Commit changes
            self.repo.index.add(["version.json", "CHANGELOG.md"])
            self.repo.index.commit(f"chore: release version {next_version}")

        else:
            # Dry run - return preview version info
            version_info = VersionInfo(
                version=next_version,
                build_date=datetime.now().isoformat(),
                git_commit=git_commit,
                git_tag=f"version-{next_version}",
                previous_version=current.version if current else None,
                changelog_generated=False,
            )

        return version_info

    def _get_repo_statistics(self, from_tag: str | None) -> dict:
        """Get repository statistics between tags.

        Args:
            from_tag: Starting tag, or None for all history

        Returns:
            Statistics dictionary
        """
        if not self.repo:
            return {"commit_count": 0, "contributor_count": 0, "contributors": []}

        # Simplified statistics
        if from_tag:
            commits = list(self.repo.iter_commits(f"{from_tag}..HEAD"))
        else:
            commits = list(self.repo.iter_commits())

        authors = {c.author.name for c in commits}

        return {
            "commit_count": len(commits),
            "contributor_count": len(authors),
            "contributors": sorted(authors),
        }

    def get_latest_tag(self) -> str | None:
        """Get the most recent version tag.

        Returns:
            Tag name or None
        """
        if not self.repo:
            return None

        tags = sorted(
            [t for t in self.repo.tags if t.name.startswith("version-")],
            key=lambda t: t.commit.committed_datetime,
            reverse=True,
        )
        return tags[0].name if tags else None

    def get_version_history(self, limit: int = 10) -> list[dict]:
        """Get version history from git tags.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of version dicts
        """
        if not self.repo:
            return []

        tags = sorted(
            [t for t in self.repo.tags if t.name.startswith("version-")],
            key=lambda t: t.commit.committed_datetime,
            reverse=True,
        )[:limit]

        return [
            {
                "version": tag.name.replace("version-", ""),
                "date": tag.commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                "commit": tag.commit.hexsha,
                "author": tag.commit.author.name,
            }
            for tag in tags
        ]

    def get_commits_since(self, since_tag: str | None) -> list:
        """Get commits since a specific tag.

        Args:
            since_tag: Starting tag, or None for all

        Returns:
            List of CommitInfo objects
        """
        if not self.repo:
            return []

        from dot_work.version.commit_parser import ConventionalCommitParser

        parser = ConventionalCommitParser()
        return parser.get_commits_since_tag(self.repo, since_tag)

    def push_tags(self) -> None:
        """Push all tags to remote."""
        if self.repo and self.repo.remote():
            self.repo.remote().push(tags=True)

    def load_config(self) -> dict:
        """Load configuration from .version-management.yaml.

        Returns:
            Configuration dictionary
        """
        config_file = self.project_root / ".version-management.yaml"

        if not config_file.exists():
            return self._default_config()

        import yaml

        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        """Get default configuration."""
        return {
            "format": "YYYY.MM.build-number",
            "tag_prefix": "version-",
            "changelog": {"file": "CHANGELOG.md", "include_authors": True, "group_by_type": True},
        }
