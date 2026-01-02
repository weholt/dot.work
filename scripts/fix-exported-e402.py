#!/usr/bin/env python3
"""Fix E402 errors in exported projects by adding noqa comments."""

from pathlib import Path

EXPORTED_DIR = Path("EXPORTED_PROJECTS")

# Projects that need E402 fixes (based on package structure with imports after docstring)
PROJECTS_TO_FIX = {
    "dot-container": "src/dot_container",
    "dot-git": "src/dot_git",
    "dot-harness": "src/dot_harness",
    "dot-issues": "src/dot_issues",
    "dot-kg": "src/dot_kg",
    "dot-overview": "src/dot_overview",
    "dot-python": "src/dot_python",
    "dot-review": "src/dot_review",
    "dot-version": "src/dot_version",
}


def fix_e402_in_init(init_path: Path) -> bool:
    """Fix E402 errors in __init__.py by adding noqa comments.

    Returns True if file was modified.
    """
    if not init_path.exists():
        return False

    content = init_path.read_text()
    lines = content.splitlines(keepends=True)

    # Find the end of the docstring
    docstring_end = -1
    for i, line in enumerate(lines):
        if '"""' in line and i > 0:  # End of docstring (not opening)
            docstring_end = i
            break

    if docstring_end == -1:
        return False

    # Add noqa: E402 to all import statements after docstring
    modified = False
    for i in range(docstring_end + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()

        # Check if this is an import line
        if stripped.startswith("from ") or stripped.startswith("import "):
            # Check if it doesn't already have noqa
            if "noqa" not in line:
                # Add noqa: E402 at the end of the line
                lines[i] = line.rstrip() + "  # noqa: E402\n"
                modified = True
        elif stripped and not stripped.startswith("#") and stripped != "CLI_GROUP =":
            # Stop at non-import, non-comment, non-assignment lines
            break

    if modified:
        init_path.write_text("".join(lines))
        return True

    return False


def main():
    """Main entry point."""
    print("Fixing E402 errors in exported projects...\n")

    fixed_count = 0
    for project_name, src_path in PROJECTS_TO_FIX.items():
        project_dir = EXPORTED_DIR / project_name
        init_path = project_dir / src_path / "__init__.py"

        if fix_e402_in_init(init_path):
            print(f"[OK] {project_name}: Fixed E402 errors")
            fixed_count += 1
        else:
            print(f"[SKIP] {project_name}: No E402 fixes needed or file not found")

    print(f"\n{'=' * 60}")
    print(f"Fixed E402 errors in {fixed_count}/{len(PROJECTS_TO_FIX)} projects")


if __name__ == "__main__":
    main()
