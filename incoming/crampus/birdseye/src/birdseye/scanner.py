"""Project file discovery utilities."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib

DEFAULT_INCLUDE_EXT = {".py", ".md"}
DEFAULT_EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "build", "dist", "node_modules", ".mypy_cache"}


def _normalize_extension(ext: str) -> str:
    ext = ext.lower()
    return ext if ext.startswith(".") else f".{ext}"


@dataclass(frozen=True)
class ProjectFile:
    """Represents a candidate project file for analysis."""

    path: Path

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()

    def read_text(self) -> str:
        return self.path.read_text(encoding="utf-8", errors="ignore")


@dataclass(frozen=True)
class ScannerConfig:
    """Scanner include/exclude configuration."""

    include_ext: set[str]
    exclude_dirs: set[str]


def iter_project_files(
    root: Path,
    include_ext: Sequence[str] | None = None,
    exclude_dirs: Iterable[str] | None = None,
) -> Iterator[ProjectFile]:
    """Yield project files that match the configured filters."""

    include: set[str] = {_normalize_extension(ext) for ext in (include_ext or DEFAULT_INCLUDE_EXT)}
    exclude: set[str] = set(exclude_dirs or DEFAULT_EXCLUDE_DIRS)
    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() in include:
                yield ProjectFile(path=path)


def load_scanner_config(root: Path) -> ScannerConfig:
    include = {_normalize_extension(ext) for ext in DEFAULT_INCLUDE_EXT}
    exclude = set(DEFAULT_EXCLUDE_DIRS)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        tool_cfg = data.get("tool", {}).get("birdseye", {}) if isinstance(data, dict) else {}
        scanner_cfg = tool_cfg.get("scanner", {}) if isinstance(tool_cfg, dict) else {}
        if isinstance(scanner_cfg, dict):
            include.update(_normalize_extension(ext) for ext in scanner_cfg.get("include_ext", []))
            exclude.update(scanner_cfg.get("exclude_dirs", []))
    return ScannerConfig(include_ext=include, exclude_dirs=exclude)
