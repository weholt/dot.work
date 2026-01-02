#!/usr/bin/env python3
"""Fix __init__.py files that have malformed docstrings.

The extraction script created __init__.py files where the docstring
is missing the opening \"\"\" on line 1.
"""

import re
from pathlib import Path


def fix_init_file(file_path: Path) -> bool:
    """Fix a single __init__.py file.

    Returns:
        True if the file was fixed, False if it didn't need fixing.
    """
    content = file_path.read_text()

    # Check if the file starts with a non-quoted line (malformed docstring)
    lines = content.split('\n')

    if not lines:
        return False

    # Check if first line is not a comment, import, or docstring start
    first_line = lines[0].strip()

    # Skip if already correct (starts with """, import, comment, or blank)
    if first_line.startswith('"""') or first_line.startswith("'''") or \
       first_line.startswith('import') or first_line.startswith('from') or \
       first_line.startswith('#') or not first_line:
        return False

    # Fix by adding """ at the start
    # The file should have format:
    # Line 1-N: docstring content
    # Line N+1: """
    # Rest of file

    # Find where the docstring ends (first line that is just """")
    docstring_end_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '"""':
            docstring_end_idx = i
            break

    if docstring_end_idx is None:
        # No closing """, just add opening at start
        new_content = '"""\n' + content
    else:
        # Found closing, add opening at start
        new_content = '"""\n' + content

    file_path.write_text(new_content)
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix __init__.py files with malformed docstrings"
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

    # Find all __init__.py files in src/ directories
    init_files = []
    for project_dir in args.exported_dir.glob("dot-*"):
        src_dir = project_dir / "src"
        if src_dir.exists():
            init_files.extend(src_dir.rglob("__init__.py"))

    print(f"Found {len(init_files)} __init__.py files\n")

    fixed_count = 0
    for init_file in init_files:
        rel_path = init_file.relative_to(args.exported_dir)
        if fix_init_file(init_file):
            print(f"[FIXED] {rel_path}")
            fixed_count += 1
        else:
            print(f"[OK]    {rel_path}")

    print(f"\n{'=' * 60}")
    print(f"Fixed: {fixed_count}/{len(init_files)} files")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
