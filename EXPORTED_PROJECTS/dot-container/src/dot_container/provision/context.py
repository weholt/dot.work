"""Context resolution and mounting for Docker containers.

This module provides functionality for injecting additional context files,
directories, and configuration into OpenCode containers at runtime.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default context mount point inside container
DEFAULT_CONTEXT_MOUNT_POINT = "/root/.context"

# Default allowlist for auto-detected context files
DEFAULT_ALLOWLIST: list[str] = [
    ".claude/",
    ".opencode.json",
    ".github/copilot-instructions.md",
]

# Default denylist (never mount these)
DEFAULT_DENYLIST: list[str] = [
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "*.pyc",
]


@dataclass
class ContextSpec:
    """Specification for context injection.

    Attributes:
        paths: List of file/directory paths to inject.
        allowlist: Optional list of glob patterns for auto-detection.
        denylist: Optional list of glob patterns to exclude.
        override: Whether to override existing files in container.
        mount_point: Mount point inside container.
    """

    paths: list[Path] = field(default_factory=list)
    allowlist: list[str] | None = None
    denylist: list[str] | None = None
    override: bool = False
    mount_point: str = DEFAULT_CONTEXT_MOUNT_POINT


def resolve_context_spec(
    explicit_paths: list[Path] | None = None,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
    override: bool = False,
    mount_point: str = DEFAULT_CONTEXT_MOUNT_POINT,
    project_root: Path | None = None,
) -> ContextSpec:
    """Resolve context specification from CLI args and environment.

    Args:
        explicit_paths: Explicit paths from --context flags.
        allowlist: Optional allowlist from CLI or env.
        denylist: Optional denylist from CLI or env.
        override: --override flag value.
        mount_point: Mount point inside container.
        project_root: Project root directory for auto-detection.

    Returns:
        Resolved ContextSpec object.
    """
    # Resolve allowlist from env or use default
    if allowlist is None:
        env_allowlist = os.getenv("CONTEXT_ALLOWLIST")
        if env_allowlist:
            allowlist = env_allowlist.split(":")
        else:
            allowlist = DEFAULT_ALLOWLIST.copy()

    # Resolve denylist from env or use default
    if denylist is None:
        env_denylist = os.getenv("CONTEXT_DENYLIST")
        if env_denylist:
            denylist = env_denylist.split(":")
        else:
            denylist = DEFAULT_DENYLIST.copy()

    # Auto-detect context files if no explicit paths
    paths: list[Path] = []
    if explicit_paths:
        paths = explicit_paths
    elif project_root:
        # Auto-detect based on allowlist
        logger.debug(f"Auto-detecting context files in {project_root}")
        for pattern in allowlist:
            matches = list(project_root.glob(pattern))
            for match in matches:
                if match not in paths:
                    paths.append(match)
        logger.debug(f"Auto-detected {len(paths)} context files/directories")

    return ContextSpec(
        paths=paths,
        allowlist=allowlist,
        denylist=denylist,
        override=override,
        mount_point=mount_point,
    )


def build_context_volume_args(spec: ContextSpec) -> list[str]:
    """Build Docker volume arguments for context injection.

    Args:
        spec: ContextSpec with paths and configuration.

    Returns:
        List of Docker volume arguments in format ['-v', 'host:container', ...].
    """
    volume_args: list[str] = []

    for path in spec.paths:
        if not path.exists():
            logger.warning(f"Context path does not exist, skipping: {path}")
            continue

        # Determine mount target inside container
        if path.is_file():
            # Mount single file
            target = f"{spec.mount_point}/{path.name}"
        else:
            # Mount directory
            target = f"{spec.mount_point}/{path.name}/"

        # Check for conflicts if override is False
        if not spec.override:
            # TODO: Check if target exists in container (not possible without running container)
            logger.debug(f"Would mount {path} to {target} (conflict checking not implemented)")
            pass

        volume_args.extend(["-v", f"{path.resolve()}:{target}"])
        logger.debug(f"Added context mount: {path} -> {target}")

    return volume_args
