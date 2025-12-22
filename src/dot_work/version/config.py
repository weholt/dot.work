"""Configuration for version module.

This module handles configuration for version management using environment
variables and dot-work patterns.
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VersionConfig:
    """Configuration for version management.

    Attributes:
        version_file: Path to version.json (default: .work/version/version.json)
        changelog_file: Path to CHANGELOG.md (default: project root)
        git_tag_prefix: Prefix for git version tags (default: version-)
        include_authors: Include authors in changelog (default: True)
        group_by_type: Group changelog by commit type (default: True)
    """

    version_file: Path | str | None = None
    changelog_file: Path | str | None = None
    git_tag_prefix: str = "version-"
    include_authors: bool = True
    group_by_type: bool = True

    @classmethod
    def from_env(cls) -> "VersionConfig":
        """Load configuration from environment variables.

        Returns:
            VersionConfig instance with settings from environment

        Environment Variables:
            DOT_WORK_VERSION_FILE: Path to version.json
            DOT_WORK_VERSION_CHANGELOG: Path to CHANGELOG.md
            DOT_WORK_VERSION_TAG_PREFIX: Git tag prefix (default: version-)
            DOT_WORK_VERSION_INCLUDE_AUTHORS: Include authors (default: true)
            DOT_WORK_VERSION_GROUP_BY_TYPE: Group by type (default: true)
        """
        version_file = os.getenv("DOT_WORK_VERSION_FILE")
        if version_file:
            version_file = Path(version_file)
        else:
            # Default: .work/version/version.json
            work_dir = Path.home() / ".dot-work"
            if not (Path.cwd() / ".work").exists():
                work_dir = Path.cwd() / ".work"
            else:
                work_dir = Path.cwd() / ".work"
            version_file = work_dir / "version" / "version.json"

        changelog_file = os.getenv("DOT_WORK_VERSION_CHANGELOG")
        if changelog_file:
            changelog_file = Path(changelog_file)

        tag_prefix = os.getenv("DOT_WORK_VERSION_TAG_PREFIX", "version-")
        include_authors = os.getenv("DOT_WORK_VERSION_INCLUDE_AUTHORS", "true").lower() == "true"
        group_by_type = os.getenv("DOT_WORK_VERSION_GROUP_BY_TYPE", "true").lower() == "true"

        return cls(
            version_file=version_file,
            changelog_file=changelog_file,
            git_tag_prefix=tag_prefix,
            include_authors=include_authors,
            group_by_type=group_by_type,
        )

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If required configuration is invalid
        """
        if self.version_file is None:
            raise ValueError("version_file must be specified")

        if isinstance(self.version_file, str):
            self.version_file = Path(self.version_file)

        if self.changelog_file and isinstance(self.changelog_file, str):
            self.changelog_file = Path(self.changelog_file)

        if not self.git_tag_prefix:
            raise ValueError("git_tag_prefix cannot be empty")
