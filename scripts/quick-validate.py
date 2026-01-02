#!/usr/bin/env python3
"""Quick validation of exported projects - check code quality only."""

import subprocess
import sys
import time
from pathlib import Path

PROJECTS = [
    ("dot-container", "dot_container"),
    ("dot-git", "dot_git"),
    ("dot-harness", "dot_harness"),
    ("dot-issues", "dot_issues"),
    ("dot-kg", "dot_kg"),
    ("dot-overview", "dot_overview"),
    ("dot-python", "dot_python"),
    ("dot-review", "dot_review"),
    ("dot-version", "dot_version"),
]

EXPORTED_DIR = Path("EXPORTED_PROJECTS")


def run_cmd(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    """Run command and return success."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=120
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def validate_project(project_name: str) -> dict:
    """Validate a single project's code quality checks."""
    project_dir = EXPORTED_DIR / project_name
    result = {
        "project": project_name,
        "uv_sync": False,
        "ruff_format": False,
        "ruff_check": False,
        "mypy": False,
    }

    # uv sync
    success, _ = run_cmd(["uv", "sync"], project_dir)
    result["uv_sync"] = success
    if not success:
        return result

    # ruff format
    success, _ = run_cmd(["uv", "run", "ruff", "format", "--check"], project_dir)
    result["ruff_format"] = success

    # ruff check
    success, _ = run_cmd(["uv", "run", "ruff", "check"], project_dir)
    result["ruff_check"] = success

    # mypy
    success, _ = run_cmd(
        ["uv", "run", "mypy", f"src/{result.get('package', project_name.replace('-', '_'))}"],
        project_dir,
    )
    result["mypy"] = success

    return result


def main():
    """Validate all projects."""
    print("Validating code quality for all exported projects...\n")

    results = []
    for project_name, _ in PROJECTS:
        print(f"=== {project_name} ===")
        result = validate_project(project_name)
        results.append(result)

        status = "OK" if all(result.values()) else "FAIL"
        print(f"uv_sync: {'OK' if result['uv_sync'] else 'FAIL'}")
        print(f"ruff format: {'OK' if result['ruff_format'] else 'FAIL'}")
        print(f"ruff check: {'OK' if result['ruff_check'] else 'FAIL'}")
        print(f"mypy: {'OK' if result['mypy'] else 'FAIL'}")
        print(f"Status: {status}\n")

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        status = "OK" if all(r.values()) else "FAIL"
        print(f"{r['project']}: {status}")

    all_pass = all(all(r.values()) for r in results)
    print(f"\nCode Quality: {'ALL PASS' if all_pass else 'SOME FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
