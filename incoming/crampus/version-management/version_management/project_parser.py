"""Parser for extracting project information from pyproject.toml."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Python 3.11+ has tomllib in stdlib, older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


@dataclass
class ProjectInfo:
    """Project metadata extracted from pyproject.toml."""

    name: str
    description: str | None
    version: str | None

    def __repr__(self) -> str:
        """Return string representation."""
        parts = [f"name='{self.name}'"]
        if self.description:
            parts.append(f"description='{self.description[:50]}...'")
        if self.version:
            parts.append(f"version='{self.version}'")
        return f"ProjectInfo({', '.join(parts)})"


class PyProjectParser:
    """Parser for pyproject.toml files."""

    def read_project_info(self, project_root: Path) -> ProjectInfo:
        """
        Read project information from pyproject.toml.

        Args:
            project_root: Root directory of the project

        Returns:
            ProjectInfo with extracted metadata

        Raises:
            RuntimeError: If tomli/tomllib is not available
        """
        if tomllib is None:
            raise RuntimeError(
                "TOML parsing library not available. "
                "Install 'tomli' for Python <3.11 or upgrade to Python 3.11+"
            )

        pyproject_path = project_root / "pyproject.toml"

        # Fallback to directory name if no pyproject.toml
        if not pyproject_path.exists():
            fallback_name = project_root.name or "Unknown Project"
            return ProjectInfo(name=fallback_name, description=None, version=None)

        try:
            with open(pyproject_path, "rb") as f:
                data: dict[str, Any] = tomllib.load(f)

            project_data = data.get("project", {})

            name = project_data.get("name", project_root.name or "Unknown Project")
            description = project_data.get("description")
            version = project_data.get("version")

            return ProjectInfo(name=name, description=description, version=version)

        except (OSError, ValueError, KeyError):
            # Fallback to directory name on any error
            fallback_name = project_root.name or "Unknown Project"
            return ProjectInfo(name=fallback_name, description=None, version=None)
