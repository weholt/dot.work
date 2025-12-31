"""Version manager for date-based versioning."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from git import Repo

from dot_work.version.project_parser import PyProjectParser

logger = logging.getLogger(__name__)


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
        except Exception:  # noqa: S110 (non-git directories are allowed)
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

        # Parse current version with validation
        parts = current.version.split(".")

        if len(parts) != 3:
            raise ValueError(
                f"Invalid version format: '{current.version}'. "
                f"Expected format: YYYY.MM.NNNNN (e.g., '2025.01.00001'). "
                f"Got {len(parts)} parts instead of 3."
            )

        try:
            curr_year = int(parts[0])
            curr_month = int(parts[1])
            curr_build = int(parts[2])
        except ValueError as e:
            raise ValueError(
                f"Invalid version format: '{current.version}'. "
                f"Expected format: YYYY.MM.NNNNN where all parts are integers. "
                f"Error: {e}"
            ) from None

        # Validate reasonable ranges
        if not (2000 <= curr_year <= 2100):
            raise ValueError(
                f"Invalid year in version: '{current.version}'. "
                f"Year must be between 2000 and 2100, got {curr_year}."
            )
        if not (1 <= curr_month <= 12):
            raise ValueError(
                f"Invalid month in version: '{current.version}'. "
                f"Month must be between 1 and 12, got {curr_month}."
            )
        if not (1 <= curr_build <= 99999):
            raise ValueError(
                f"Invalid build number in version: '{current.version}'. "
                f"Build number must be between 1 and 99999, got {curr_build}."
            )

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
        current = self.read_version()
        next_version = self.calculate_next_version(current)

        # Get commits and generate changelog
        commits = self._get_commits_since_last_tag(current)
        changelog_entry = self._generate_changelog_entry(next_version, commits, current, use_llm)

        # Get current git commit
        git_commit = self.repo.head.commit.hexsha if self.repo else "unknown"

        if not dry_run and self.repo:
            return self._finalize_version_release(
                next_version, git_commit, current, changelog_entry
            )
        else:
            # Dry run - return preview version info
            return VersionInfo(
                version=next_version,
                build_date=datetime.now().isoformat(),
                git_commit=git_commit,
                git_tag=f"version-{next_version}",
                previous_version=current.version if current else None,
                changelog_generated=False,
            )

    def _get_commits_since_last_tag(self, current: VersionInfo | None) -> list:
        """Get commits since the last version tag.

        Args:
            current: Current version info

        Returns:
            List of commits since last tag
        """
        from dot_work.version.commit_parser import ConventionalCommitParser

        if not self.repo:
            return []

        parser = ConventionalCommitParser()
        last_tag = current.git_tag if current else None
        return parser.get_commits_since_tag(self.repo, last_tag)

    def _generate_changelog_entry(
        self, next_version: str, commits: list, current: VersionInfo | None, use_llm: bool
    ) -> str:
        """Generate changelog entry for the new version.

        Args:
            next_version: New version string
            commits: List of commits to include
            current: Current version info
            use_llm: Whether to use LLM for summaries

        Returns:
            Changelog entry markdown string
        """
        from dot_work.version.changelog import ChangelogGenerator

        generator = ChangelogGenerator()
        return generator.generate_entry(
            version=next_version,
            commits=commits,
            repo_stats=self._get_repo_statistics(current.git_tag if current else None),
            use_llm=use_llm,
            project_name=self.project_info.name,
        )

    def _create_git_tag(self, version: str) -> None:
        """Create a git tag for the version.

        Args:
            version: Version string to tag

        Raises:
            RuntimeError: If git repository is not available
        """
        if not self.repo:
            raise RuntimeError("Cannot create git tag: no repository available")

        tag_name = f"version-{version}"
        self.repo.create_tag(tag_name, message=f"Release {version}")

    def _write_version_files(
        self, version: str, git_commit: str, current: VersionInfo | None, tag_name: str
    ) -> VersionInfo:
        """Write version.json and append to CHANGELOG.md.

        Args:
            version: New version string
            git_commit: Current git commit hash
            current: Current version info
            tag_name: Git tag name

        Returns:
            Created VersionInfo
        """
        from dot_work.version.changelog import ChangelogGenerator

        version_info = VersionInfo(
            version=version,
            build_date=datetime.now().isoformat(),
            git_commit=git_commit,
            git_tag=tag_name,
            previous_version=current.version if current else None,
            changelog_generated=True,
        )
        self.write_version(version_info)

        # Append to CHANGELOG.md
        changelog_entry = self._generate_changelog_entry(
            version, self._get_commits_since_last_tag(current), current, use_llm=False
        )
        changelog_path = self.project_root / "CHANGELOG.md"
        ChangelogGenerator().append_to_changelog(changelog_entry, changelog_path)

        return version_info

    def _commit_version_changes(self, version: str) -> None:
        """Commit version file changes to git.

        Args:
            version: Version string for commit message

        Raises:
            RuntimeError: If git repository is not available
        """
        if not self.repo:
            raise RuntimeError("Cannot commit changes: no repository available")

        self.repo.index.add(["version.json", "CHANGELOG.md"])
        self.repo.index.commit(f"chore: release version {version}")

    def _finalize_version_release(
        self, next_version: str, git_commit: str, current: VersionInfo | None, changelog_entry: str
    ) -> VersionInfo:
        """Finalize the version release with git operations.

        Uses transaction-like semantics: if any operation fails after tag creation,
        the tag is deleted to maintain consistent state.

        Args:
            next_version: New version string
            git_commit: Current git commit hash
            current: Current version info
            changelog_entry: Changelog entry to append

        Returns:
            Created VersionInfo

        Raises:
            RuntimeError: If git operations fail with rollback attempted
        """
        from dot_work.version.changelog import ChangelogGenerator

        tag_name = f"version-{next_version}"
        created_tag = False
        wrote_version = False
        appended_changelog = False

        try:
            # Create git tag first (cheapest operation, easy to roll back)
            self._create_git_tag(next_version)
            created_tag = True

            # Write version.json
            version_info = VersionInfo(
                version=next_version,
                build_date=datetime.now().isoformat(),
                git_commit=git_commit,
                git_tag=tag_name,
                previous_version=current.version if current else None,
                changelog_generated=True,
            )
            self.write_version(version_info)
            wrote_version = True

            # Append to CHANGELOG.md
            changelog_path = self.project_root / "CHANGELOG.md"
            ChangelogGenerator().append_to_changelog(changelog_entry, changelog_path)
            appended_changelog = True

            # Commit changes (final step, most expensive to roll back)
            self._commit_version_changes(next_version)

            return version_info

        except Exception as e:
            # Rollback: clean up any partial state
            logger.error("Failed to finalize version release: %s. Rolling back...", e)

            if created_tag and self.repo:
                try:
                    # Delete the tag if it was created
                    # Convert tag name string to TagReference
                    tags = [t for t in self.repo.tags if t.name == tag_name or t.path == tag_name]
                    if tags:
                        self.repo.delete_tag(tags[0])
                        logger.info("Rolled back: deleted tag %s", tag_name)
                except Exception as tag_error:
                    logger.error("Failed to rollback tag %s: %s", tag_name, tag_error)

            if wrote_version:
                try:
                    # Restore previous version if it existed
                    if current:
                        self.write_version(current)
                        logger.info("Rolled back: restored previous version %s", current.version)
                    else:
                        # Delete version.json if this was the first version
                        if self.version_file.exists():
                            self.version_file.unlink()
                            logger.info("Rolled back: deleted version.json")
                except Exception as file_error:
                    logger.error("Failed to rollback version file: %s", file_error)

            if appended_changelog:
                try:
                    # Remove the last entry from CHANGELOG.md
                    # This is tricky - best we can do is log the issue
                    logger.warning(
                        "CHANGELOG.md was partially updated. Manual cleanup may be required."
                    )
                except Exception:  # noqa: S110
                    # If logging fails during rollback, just proceed with the error
                    pass

            raise RuntimeError(f"Version release failed and was rolled back: {e}") from e

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
