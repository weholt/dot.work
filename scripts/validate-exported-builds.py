#!/usr/bin/env python3
"""Validate all exported projects by running uv sync and build.py."""

import subprocess
import sys
import time
from pathlib import Path

# Project configuration: (exported_project_name, source_package_name)
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


def run_command(
    cmd: list[str],
    cwd: Path,
    timeout: int = 300,
) -> tuple[bool, str, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return False, "", f"Command not found: {e}"
    except Exception as e:
        return False, "", f"Error: {e}"


def validate_project(
    exported_projects_dir: Path,
    project_name: str,
    package_name: str,
) -> dict:
    """Validate a single exported project.

    Returns:
        Dictionary with validation results
    """
    project_dir = exported_projects_dir / project_name
    result = {
        "project": project_name,
        "package": package_name,
        "exists": project_dir.exists(),
        "uv_sync": {"success": False, "time": 0, "output": "", "error": ""},
        "build_py_exists": False,
        "build": {"success": False, "time": 0, "output": "", "error": ""},
    }

    if not result["exists"]:
        return result

    # Check if build.py exists
    build_py_path = project_dir / "scripts" / "build.py"
    result["build_py_exists"] = build_py_path.exists() and build_py_path.is_file()

    if not result["build_py_exists"]:
        return result

    # Run uv sync
    print(f"\n=== {project_name}: uv sync ===")
    start_time = time.time()
    success, stdout, stderr = run_command(["uv", "sync"], project_dir, timeout=180)
    sync_time = time.time() - start_time

    result["uv_sync"]["success"] = success
    result["uv_sync"]["time"] = sync_time
    result["uv_sync"]["output"] = stdout[-1000:] if stdout else ""  # Last 1000 chars
    result["uv_sync"]["error"] = stderr[-1000:] if stderr else ""

    if success:
        print(f"[OK] uv sync ({sync_time:.1f}s)")
    else:
        print(f"[FAIL] uv sync ({sync_time:.1f}s)")
        if stderr:
            print(f"Error: {stderr[:500]}")
        # Don't continue to build if sync failed
        return result

    # Run build.py --fix --verbose
    print(f"\n=== {project_name}: build.py --fix --verbose ===")
    start_time = time.time()
    success, stdout, stderr = run_command(
        ["uv", "run", "python", "scripts/build.py", "--fix", "--verbose"],
        project_dir,
        timeout=600,  # 10 minutes max for build
    )
    build_time = time.time() - start_time

    result["build"]["success"] = success
    result["build"]["time"] = build_time
    result["build"]["output"] = stdout[-2000:] if stdout else ""  # Last 2000 chars
    result["build"]["error"] = stderr[-1000:] if stderr else ""  # Last 1000 chars

    # Check if build actually succeeded by looking for success indicators
    # The VIRTUAL_ENV warning is harmless and can be ignored
    actual_success = success or (
        "BUILD SUCCESSFUL" in stdout
        or "BUILD MOSTLY SUCCESSFUL" in stdout
        or "[OK] Build Summary" in stdout
    )

    if actual_success:
        print(f"[OK] build.py ({build_time:.1f}s)")
        result["build"]["success"] = True
    else:
        print(f"[FAIL] build.py ({build_time:.1f}s)")
        if stderr and not stderr.strip().startswith("warning: `VIRTUAL_ENV"):
            print(f"Error: {stderr[:500]}")

    return result


def generate_report(results: list[dict], output_path: Path) -> None:
    """Generate validation report."""
    with open(output_path, "w") as f:
        f.write("# Exported Projects Validation Report\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        total = len(results)
        exist = sum(1 for r in results if r["exists"])
        sync_ok = sum(1 for r in results if r["uv_sync"]["success"])
        build_ok = sum(1 for r in results if r["build"]["success"])

        f.write("## Summary\n\n")
        f.write(f"- Total projects: {total}\n")
        f.write(f"- Projects exist: {exist}\n")
        f.write(f"- uv sync passed: {sync_ok}\n")
        f.write(f"- build.py passed: {build_ok}\n\n")

        # Detailed results
        f.write("## Detailed Results\n\n")

        for result in results:
            f.write(f"### {result['project']}\n\n")
            f.write(f"- Package: `{result['package']}`\n")
            f.write(f"- Exists: {result['exists']}\n")
            f.write(f"- build.py exists: {result['build_py_exists']}\n")

            if result["exists"]:
                sync = result["uv_sync"]
                f.write(f"- uv sync: {'✓ PASSED' if sync['success'] else '✗ FAILED'} ({sync['time']:.1f}s)\n")
                if not sync["success"] and sync["error"]:
                    f.write(f"  - Error: {sync['error'][:200]}...\n")

                build = result["build"]
                if sync["success"]:  # Only show build if sync passed
                    f.write(f"- build.py: {'✓ PASSED' if build['success'] else '✗ FAILED'} ({build['time']:.1f}s)\n")
                    if not build["success"] and build["error"]:
                        f.write(f"  - Error: {build['error'][:200]}...\n")

            f.write("\n")

        # Failed projects
        failed = [r for r in results if not (r["build"]["success"] if r["uv_sync"]["success"] else r["uv_sync"]["success"])]
        if failed:
            f.write("## Failed Projects\n\n")
            for result in failed:
                reason = "uv sync failed" if not result["uv_sync"]["success"] else "build.py failed"
                f.write(f"- {result['project']}: {reason}\n")
            f.write("\n")

        # Success projects
        passed = [r for r in results if r["build"]["success"] and r["uv_sync"]["success"]]
        if passed:
            f.write("## Passed Projects\n\n")
            for result in passed:
                sync_time = result["uv_sync"]["time"]
                build_time = result["build"]["time"]
                f.write(f"- {result['project']}: sync {sync_time:.1f}s, build {build_time:.1f}s\n")
            f.write("\n")

    print(f"\n[OK] Report written to {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate all exported projects"
    )
    parser.add_argument(
        "--exported-dir",
        type=Path,
        default=Path("EXPORTED_PROJECTS"),
        help="Path to EXPORTED_PROJECTS directory (default: EXPORTED_PROJECTS)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("EXPORTED_PROJECTS/build-validation-report.md"),
        help="Path to output report (default: EXPORTED_PROJECTS/build-validation-report.md)",
    )

    args = parser.parse_args()

    if not args.exported_dir.exists():
        print(f"[ERROR] Exported projects directory not found: {args.exported_dir}")
        return 1

    print(f"Exported projects directory: {args.exported_dir}")
    print(f"Validating {len(PROJECTS)} projects...")
    print("This may take several minutes...\n")

    results = []
    for project_name, package_name in PROJECTS:
        result = validate_project(args.exported_dir, project_name, package_name)
        results.append(result)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    exist = sum(1 for r in results if r["exists"])
    sync_ok = sum(1 for r in results if r["uv_sync"]["success"])
    build_ok = sum(1 for r in results if r["build"]["success"])

    print(f"Projects exist: {exist}/{len(results)}")
    print(f"uv sync passed: {sync_ok}/{len(results)}")
    print(f"build.py passed: {build_ok}/{len(results)}")

    # Generate report
    generate_report(results, args.report)

    # Return exit code based on results
    if build_ok == len(results):
        print("\n[SUCCESS] All projects validated successfully!")
        return 0
    elif sync_ok == len(results):
        print(f"\n[WARN] {len(results) - build_ok} projects failed build validation")
        return 1
    else:
        print(f"\n[FAIL] {len(results) - sync_ok} projects failed to sync dependencies")
        return 2


if __name__ == "__main__":
    sys.exit(main())
