#!/usr/bin/env python3
"""Generate complete, correct pyproject.toml files for exported projects."""

from pathlib import Path

# Project configuration - based on original dot-work pyproject.toml
PROJECT_CONFIGS = {
    "dot-container": {
        "name": "dot-container",
        "description": "Docker container provisioning for OpenCode",
        "package": "dot_container",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'python-frontmatter>=1.1.0',
        ],
        "optional_deps": None,
        "scripts": {"dot-container": "dot_container.cli:app"},
        "per_file_ignores": {
            "src/dot_container/provision/core.py": ["S108", "S603", "S607"],
            "src/dot_container/provision/fetch.py": ["S310"],
        },
    },
    "dot-git": {
        "name": "dot-git",
        "description": "Git history analysis and complexity metrics",
        "package": "dot_git",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'GitPython>=3.1.0',
            'radon>=6.0.0',
            'tqdm>=4.66.0',
        ],
        "optional_deps": {
            "llm": ['openai>=1.0.0', 'anthropic>=0.3.0'],
        },
        "dev_deps_extra": ['types-PyYAML>=6.0.0'],
        "scripts": {"dot-git": "dot_git.cli:app"},
    },
    "dot-harness": {
        "name": "dot-harness",
        "description": "Claude Agent SDK integration for dot-work",
        "package": "dot_harness",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
        ],
        "optional_deps": {
            "sdk": ['claude-agent-sdk>=0.1.0', 'anyio>=4.0.0'],
        },
        "scripts": {"dot-harness": "dot_harness.cli:app"},
    },
    "dot-issues": {
        "name": "dot-issues",
        "description": "SQLite-based issue tracking for autonomous agents",
        "package": "dot_issues",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'sqlmodel>=0.0.22',
            'jinja2>=3.1.0',
            'pyyaml>=6.0.0',
        ],
        "optional_deps": None,
        "scripts": {"dot-issues": "dot_issues.cli:app"},
    },
    "dot-kg": {
        "name": "dot-kg",
        "description": "Knowledge graph and semantic code search",
        "package": "dot_kg",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'numpy>=1.24.0',
        ],
        "optional_deps": {
            "http": ['httpx>=0.27.0'],
            "ann": ['hnswlib>=0.8.0'],
            "vec": ['sqlite-vec>=0.1.0'],
        },
        "scripts": {"dot-kg": "dot_kg.cli:app"},
    },
    "dot-overview": {
        "name": "dot-overview",
        "description": "Codebase overview generation and analysis",
        "package": "dot_overview",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'libcst>=1.1.0',
        ],
        "optional_deps": None,
        "scripts": {"dot-overview": "dot_overview.cli:app"},
    },
    "dot-python": {
        "name": "dot-python",
        "description": "Python build and scan utilities",
        "package": "dot_python",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
        ],
        "optional_deps": {
            "scan-graph": ['networkx>=3.0', 'pyvis>=0.3.0'],
        },
        "scripts": {
            "dot-python": "dot_python.cli:app",
            "pybuilder": "dot_python.build.cli:main",
        },
    },
    "dot-review": {
        "name": "dot-review",
        "description": "Code review server and tools",
        "package": "dot_review",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'fastapi>=0.115.0',
            'uvicorn>=0.32.0',
            'pydantic>=2.6.0',
        ],
        "optional_deps": None,
        "scripts": {"dot-review": "dot_review.cli:app"},
    },
    "dot-version": {
        "name": "dot-version",
        "description": "Date-based version management",
        "package": "dot_version",
        "base_deps": [
            'typer>=0.12.0',
            'rich>=13.0.0',
            'GitPython>=3.1.0',
            'python-dotenv>=1.0.0',
        ],
        "optional_deps": {
            "llm": ['httpx>=0.24.0'],
        },
        "scripts": {"dot-version": "dot_version.cli:app"},
    },
}

DEV_DEPS = [
    'pytest>=8.0.0',
    'pytest-cov>=4.1.0',
    'pytest-mock>=3.12.0',
    'ruff>=0.6.0',
    'mypy>=1.11.0',
]


def generate_pyproject_toml(project_name: str) -> str:
    """Generate complete pyproject.toml content for a project."""
    config = PROJECT_CONFIGS.get(project_name)
    if not config:
        raise ValueError(f"Unknown project: {project_name}")

    lines = [
        '[build-system]',
        'requires = ["hatchling"]',
        'build-backend = "hatchling.build"',
        '',
        '[project]',
        f'name = "{config["name"]}"',
        'version = "0.1.0"',
        f'description = "{config["description"]}"',
        'readme = "README.md"',
        'requires-python = ">=3.11"',
        'license = {text = "MIT"}',
        'dependencies = [',
    ]

    for dep in config["base_deps"]:
        lines.append(f'    "{dep}",')

    lines.append(']')

    # Optional dependencies
    lines.append('')
    lines.append('[project.optional-dependencies]')

    if config["optional_deps"]:
        for opt_name, opt_deps in config["optional_deps"].items():
            lines.append(f'{opt_name} = [')
            for dep in opt_deps:
                lines.append(f'    "{dep}",')
            lines.append(']')
    else:
        lines.append('# No optional dependencies')

    # Dev dependencies
    lines.append('')
    lines.append('dev = [')
    for dep in DEV_DEPS:
        lines.append(f'    "{dep}",')
    # Add extra dev dependencies if configured
    if config.get("dev_deps_extra"):
        for dep in config["dev_deps_extra"]:
            lines.append(f'    "{dep}",')
    lines.append(']')

    # Scripts
    lines.append('')
    lines.append('[project.scripts]')
    for script_name, script_entry in config["scripts"].items():
        lines.append(f'{script_name} = "{script_entry}"')

    # Plugin entry point
    lines.append('')
    lines.append('[project.entry-points."dot_work.plugins"]')
    plugin_name = config["package"].replace("_", "")  # dot_issues -> issues
    lines.append(f'{plugin_name} = "{config["package"]}"')

    # Hatch build config
    lines.append('')
    lines.append('[tool.hatch.build.targets.wheel]')
    lines.append(f'packages = ["src/{config["package"]}"]')
    lines.append('artifacts = [')
    lines.append('    # No static assets')
    lines.append(']')

    # Ruff config
    lines.append('')
    lines.append('[tool.ruff]')
    lines.append('line-length = 100')
    lines.append('target-version = "py311"')
    lines.append('')
    lines.append('[tool.ruff.lint]')
    lines.append('select = ["E", "F", "W", "I", "N", "B"]')
    lines.append('ignore = ["B008", "B009", "B904", "E402", "E501"]')

    # Per-file ignores if configured
    if config.get("per_file_ignores"):
        lines.append('')
        lines.append('[tool.ruff.lint.per-file-ignores]')
        for file_path, ignores in config["per_file_ignores"].items():
            ignores_str = '", "'.join(ignores)
            lines.append(f'"{file_path}" = ["{ignores_str}"]')

    # MyPy config
    lines.append('')
    lines.append('[tool.mypy]')
    lines.append('python_version = "3.11"')
    lines.append('warn_unused_ignores = true')

    return '\n'.join(lines)


def fix_pyproject_toml(project_dir: Path, project_name: str) -> bool:
    """Generate complete pyproject.toml for a project.

    Returns:
        True if successful, False otherwise
    """
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"[SKIP] {project_name}: pyproject.toml not found")
        return False

    # Generate complete new content
    content = generate_pyproject_toml(project_name)
    pyproject_path.write_text(content)

    print(f"[OK] {project_name}: Generated pyproject.toml")
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate complete pyproject.toml files for exported projects"
    )
    parser.add_argument(
        "--exported-dir",
        type=Path,
        default=Path("EXPORTED_PROJECTS"),
        help="Path to EXPORTED_PROJECTS directory (default: EXPORTED_PROJECTS)",
    )

    args = parser.parse_args()

    if not args.exported_dir.exists():
        print(f"[ERROR] Exported projects directory not found: {args.exported_dir}")
        return 1

    print(f"Generating pyproject.toml files in: {args.exported_dir}\n")

    success_count = 0
    for project_name in PROJECT_CONFIGS.keys():
        project_dir = args.exported_dir / project_name
        if fix_pyproject_toml(project_dir, project_name):
            success_count += 1

    print(f"\n{'=' * 60}")
    print(f"Generated: {success_count}/{len(PROJECT_CONFIGS)} projects")

    return 0 if success_count == len(PROJECT_CONFIGS) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
