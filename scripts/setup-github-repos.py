#!/usr/bin/env python3
"""Setup GitHub repositories for all exported projects.

This script automates:
1. Git initialization for each exported project
2. GitHub repository creation via gh CLI
3. Initial commit and push to remote

Prerequisites:
    - gh CLI installed and authenticated: gh auth login
    - Git configured with user.name and user.email

Usage:
    # Dry run (show what would be done)
    uv run python scripts/setup-github-repos.py --dry-run

    # Create all repos
    uv run python scripts/setup-github-repos.py

    # Create specific repos only
    uv run python scripts/setup-github-repos.py --projects dot-container dot-git

    # Use custom GitHub username/org
    uv run python scripts/setup-github-repos.py --org my-org
"""

from __future__ import annotations

import argparse
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EXPORTED_DIR = PROJECT_ROOT / "EXPORTED_PROJECTS"

# All exported projects
ALL_PROJECTS = [
    "dot-container",
    "dot-git",
    "dot-harness",
    "dot-issues",
    "dot-kg",
    "dot-overview",
    "dot-python",
    "dot-review",
    "dot-version",
]

# README templates
README_TEMPLATE = """# {name}

> {description}

Part of the [dot-work](https://github.com/{org}/dot-work) plugin ecosystem.

## Installation

```bash
# Install the plugin
pip install {name}

# Or install with dot-work[all]
pip install "dot-work[all]"
```

## Usage

```bash
# Use via dot-work
dot-work {cli_group} --help

# Or use standalone
{name} --help
```

## Development

```bash
# Clone repository
git clone https://github.com/{org}/{name}.git
cd {name}

# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run mypy src/
```

## License

MIT

## Related

- [dot-work](https://github.com/{org}/dot-work) - Main project
"""

# Project metadata
PROJECT_METADATA = {
    "dot-container": {
        "description": "Docker container provisioning for OpenCode development environments",
        "cli_group": "container",
    },
    "dot-git": {
        "description": "Git history analysis and changelog generation tools",
        "cli_group": "git",
    },
    "dot-harness": {
        "description": "Claude Agent SDK integration and task harness",
        "cli_group": "harness",
    },
    "dot-issues": {
        "description": "SQLite-based issue tracking and dependency management",
        "cli_group": "db-issues",
    },
    "dot-kg": {
        "description": "Knowledge graph with semantic search and code analysis",
        "cli_group": "kg",
    },
    "dot-overview": {
        "description": "Codebase overview generation and analysis tools",
        "cli_group": "overview",
    },
    "dot-python": {
        "description": "Python build and scan utilities for project metrics",
        "cli_group": "python",
    },
    "dot-review": {
        "description": "Interactive code review with AI-friendly export",
        "cli_group": "review",
    },
    "dot-version": {
        "description": "Date-based version management and changelog generation",
        "cli_group": "version",
    },
}


@dataclass
class RepoResult:
    """Result of repository creation."""

    project: str
    success: bool
    url: str = ""
    error: str = ""


class GitHubRepoSetup:
    """Setup GitHub repositories for exported projects."""

    def __init__(
        self,
        org: str | None = None,
        exported_dir: Path = EXPORTED_DIR,
        dry_run: bool = False,
    ):
        """Initialize the setup.

        Args:
            org: GitHub organization or username (None = detect from gh)
            exported_dir: Directory containing exported projects
            dry_run: Show what would be done without making changes
        """
        self.org = org
        self.exported_dir = exported_dir
        self.dry_run = dry_run

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger("github_setup")

        # Results
        self.results: list[RepoResult] = []

    def _get_github_username(self) -> str:
        """Get GitHub username/org from gh CLI."""
        if self.org:
            return self.org

        try:
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            if self.dry_run:
                # Use placeholder in dry-run mode
                return "<username>"
            self.logger.warning(
                "Could not detect GitHub username from gh CLI. "
                "Use --org to specify or run: gh auth login"
            )
            raise

    def _check_gh_auth(self) -> bool:
        """Check if gh CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.error("gh CLI not found. Install with: pacman -S github-cli")
            return False

    def _run(self, cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run a command, respecting dry_run mode.

        Args:
            cmd: Command to run
            cwd: Working directory

        Returns:
            Completed process result
        """
        cmd_str = " ".join(cmd)
        if cwd:
            cmd_str = f"(cd {cwd} && {cmd_str})"

        if self.dry_run:
            self.logger.info(f"DRY RUN: {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, b"", b"")

        self.logger.debug(f"Running: {cmd_str}")
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    def _init_git(self, project_path: Path) -> bool:
        """Initialize git repository.

        Args:
            project_path: Path to project directory

        Returns:
            True if successful
        """
        # Check if already initialized
        if (project_path / ".git").exists():
            self.logger.debug(f"Git already initialized in {project_path.name}")
            return True

        result = self._run(["git", "init"], cwd=project_path)
        if result.returncode != 0:
            self.logger.error(f"git init failed: {result.stderr}")
            return False

        return True

    def _create_readme(self, project_path: Path, project_name: str) -> None:
        """Create README.md if it doesn't exist.

        Args:
            project_path: Path to project directory
            project_name: Name of the project
        """
        readme_path = project_path / "README.md"

        if readme_path.exists():
            return

        metadata = PROJECT_METADATA.get(project_name, {})
        readme_content = README_TEMPLATE.format(
            name=project_name,
            description=metadata.get("description", f"dot-work plugin: {project_name}"),
            cli_group=metadata.get("cli_group", project_name),
            org=self.org or "<username>",
        )

        readme_path.write_text(readme_content)
        self.logger.debug(f"Created README.md for {project_name}")

    def _git_commit(self, project_path: Path) -> bool:
        """Create initial commit.

        Args:
            project_path: Path to project directory

        Returns:
            True if successful
        """
        # Add all files
        result = self._run(["git", "add", "."], cwd=project_path)
        if result.returncode != 0:
            self.logger.error(f"git add failed: {result.stderr}")
            return False

        # Check if there's anything to commit
        result = self._run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=project_path,
        )
        if result.returncode == 0:
            self.logger.debug("Nothing to commit")
            return True

        # Create commit
        result = self._run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_path,
        )
        if result.returncode != 0:
            self.logger.error(f"git commit failed: {result.stderr}")
            return False

        return True

    def _create_github_repo(
        self,
        project_name: str,
        project_path: Path,
    ) -> tuple[bool, str, str]:
        """Create GitHub repository and push.

        Args:
            project_name: Name of the project
            project_path: Path to project directory

        Returns:
            Tuple of (success, url, error_message)
        """
        org = self._get_github_username()
        repo_name = project_name

        # Create README if missing
        self._create_readme(project_path, project_name)

        # Initialize git
        if not self._init_git(project_path):
            return False, "", "git init failed"

        # Create initial commit
        if not self._git_commit(project_path):
            return False, "", "git commit failed"

        # Create GitHub repo and push
        # gh repo will create the repo, set remote, and push in one command
        result = self._run(
            [
                "gh",
                "repo",
                "create",
                f"{org}/{repo_name}",
                "--private",
                "--source=.",
                "--remote=origin",
                "--push",
            ],
            cwd=project_path,
        )

        if result.returncode != 0:
            return False, "", f"gh repo create failed: {result.stderr}"

        url = f"https://github.com/{org}/{repo_name}"
        return True, url, ""

    def setup_project(self, project_name: str) -> RepoResult:
        """Setup a single project.

        Args:
            project_name: Name of the project

        Returns:
            RepoResult with outcome
        """
        self.logger.info(f"Setting up {project_name}...")

        project_path = self.exported_dir / project_name

        # Check project exists
        if not project_path.exists():
            return RepoResult(
                project=project_name,
                success=False,
                error=f"Project directory not found: {project_path}",
            )

        # Create repo and push
        success, url, error = self._create_github_repo(project_name, project_path)

        return RepoResult(
            project=project_name,
            success=success,
            url=url,
            error=error,
        )

    def setup_all(self, projects: list[str] | None = None) -> list[RepoResult]:
        """Setup all projects.

        Args:
            projects: List of project names (None = all)

        Returns:
            List of RepoResult for each project
        """
        if projects is None:
            projects = ALL_PROJECTS

        # Check gh CLI is authenticated
        if not self.dry_run and not self._check_gh_auth():
            self.logger.error(
                "gh CLI not authenticated. Run: gh auth login"
            )
            return []

        self.logger.info(f"Setting up {len(projects)} repositories...")

        for project in projects:
            result = self.setup_project(project)
            self.results.append(result)

            if result.success:
                self.logger.info(f"✓ {result.project}: {result.url}")
            else:
                self.logger.error(f"✗ {result.project}: {result.error}")

        return self.results


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup GitHub repos for exported projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--projects",
        nargs="+",
        help="Specific projects to setup (default: all)",
    )

    parser.add_argument(
        "--org",
        help="GitHub organization or username (default: detect from gh)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Create setup
    setup = GitHubRepoSetup(
        org=args.org,
        dry_run=args.dry_run,
    )

    # Setup repos
    results = setup.setup_all(args.projects)

    # Summary
    success_count = sum(1 for r in results if r.success)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"Setup Summary: {success_count}/{total} repos created")
    print(f"{'=' * 60}")

    if success_count == total and total > 0:
        print("✓ All repositories created successfully!")
        return 0
    elif success_count > 0:
        print(f"✗ {total - success_count} repo(s) failed")
        return 1
    else:
        print("No repositories created")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
