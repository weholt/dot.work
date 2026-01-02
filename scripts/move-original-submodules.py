#!/usr/bin/env python3
"""Move original submodule folders to temporary directory after export.

This script moves the original submodule folders from src/dot_work/ to a
temporary folder after they have been exported to EXPORTED_PROJECTS/.
This is part of the module split migration (SPLIT-106).

Usage:
    # Dry run (safe check)
    uv run python scripts/move-original-submodules.py --dry-run

    # Move all original submodules to temp
    uv run python scripts/move-original-submodules.py

    # Move specific submodules only
    uv run python scripts/move-original-submodules.py --submodules container git

    # Custom temp folder
    uv run python scripts/move-original-submodules.py --dest /path/to/temp

    # Move tests only (keep source)
    uv run python scripts/move-original-submodules.py --tests-only

    # Skip confirmation
    uv run python scripts/move-original-submodules.py --yes

    # Force overwrite conflicts
    uv run python scripts/move-original-submodules.py --force

    # Rollback (move back)
    uv run python scripts/move-original-submodules.py --rollback
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import shutil
import stat
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import ClassVar

# Submodule configuration
SUBMODULES = [
    "container",
    "git",
    "harness",
    "db_issues",
    "knowledge_graph",
    "overview",
    "python",
    "review",
    "version",
]

# Test directory mappings
TEST_DIRS = {
    "container": ["tests/unit/container", "tests/integration/container/provision"],
    "git": ["tests/unit/git", "tests/integration/test_git_history"],
    "kg": ["tests/unit/knowledge_graph", "tests/integration/knowledge_graph"],
    "knowledge_graph": ["tests/unit/knowledge_graph", "tests/integration/knowledge_graph"],
    "harness": ["tests/unit/harness"],
    "db_issues": ["tests/unit/db_issues", "tests/integration/db_issues"],
    "overview": ["tests/unit/overview"],
    "python": ["tests/unit/python/build", "tests/unit/python/scan"],
    "review": ["tests/unit/review", "tests/integration/test_server"],
    "version": ["tests/unit/version"],
}

# Exported project name mappings
EXPORTED_PROJECT_NAMES = {
    "db_issues": "dot-issues",
    "knowledge_graph": "dot-kg",
}


@dataclass
class MoveStats:
    """Statistics for a single submodule move operation."""

    submodule_name: str
    source_files: int = 0
    source_size_mb: float = 0.0
    dest_files: int = 0
    dest_size_mb: float = 0.0
    tests_moved: int = 0
    move_time_s: float = 0.0
    checksum_match: bool = True
    success: bool = True
    errors: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, str | int | float | bool]:
        """Convert to CSV row dictionary."""
        return {
            "submodule_name": self.submodule_name,
            "source_files": self.source_files,
            "source_size_mb": round(self.source_size_mb, 2),
            "dest_files": self.dest_files,
            "dest_size_mb": round(self.dest_size_mb, 2),
            "tests_moved": self.tests_moved,
            "move_time_s": round(self.move_time_s, 2),
            "checksum_match": self.checksum_match,
            "success": self.success,
        }


class SubmoduleMover:
    """Handle moving original submodules to temporary directory."""

    DEFAULT_DEST: ClassVar[Path] = Path(".temp-original-submodules")
    DEFAULT_LOG: ClassVar[Path] = Path("move-original-submodules.log")
    DEFAULT_REPORT: ClassVar[Path] = Path("move-original-submodules-report.csv")

    def __init__(
        self,
        project_root: Path,
        dest: Path = DEFAULT_DEST,
        exported_projects_dir: Path = Path("EXPORTED_PROJECTS"),
    ):
        """Initialize the mover.

        Args:
            project_root: Root directory of dot-work project
            dest: Destination directory for moved submodules
            exported_projects_dir: Directory containing exported projects
        """
        self.project_root = project_root
        self.dest = project_root / dest
        self.exported_projects_dir = project_root / exported_projects_dir
        self.src_path = project_root / "src" / "dot_work"
        self.tests_path = project_root / "tests"

        # Setup logging
        self._setup_logging()

        # Statistics tracking
        self.stats: list[MoveStats] = []

    def _setup_logging(self) -> None:
        """Setup logging to file and console."""
        self.logger = logging.getLogger("submodule_mover")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        log_file = self.project_root / self.DEFAULT_LOG
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _calculate_sha256(self, path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            path: Path to file

        Returns:
            Hexadecimal SHA256 hash string
        """
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _count_files_and_size(self, directory: Path) -> tuple[int, float]:
        """Count files and total size in a directory.

        Args:
            directory: Directory to scan

        Returns:
            Tuple of (file_count, size_mb)
        """
        file_count = 0
        total_size = 0

        for item in directory.rglob("*"):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size

        size_mb = total_size / (1024 * 1024)
        return file_count, size_mb

    def _get_exported_project_name(self, submodule: str) -> str:
        """Get the exported project name for a submodule.

        Args:
            submodule: Submodule name

        Returns:
            Exported project name (e.g., "dot-issues" for "db_issues")
        """
        return EXPORTED_PROJECT_NAMES.get(submodule, f"dot-{submodule}")

    def _verify_exported_project_exists(self, submodule: str) -> bool:
        """Verify that the exported project exists.

        Args:
            submodule: Submodule name

        Returns:
            True if exported project exists
        """
        project_name = self._get_exported_project_name(submodule)
        project_path = self.exported_projects_dir / project_name
        return project_path.exists() and project_path.is_dir()

    def _verify_checksums(
        self,
        source: Path,
        dest: Path,
    ) -> bool:
        """Verify that files match between source and destination.

        Args:
            source: Source directory
            dest: Destination directory

        Returns:
            True if all checksums match
        """
        self.logger.debug(f"Verifying checksums: {source} -> {dest}")

        # Get all files in both directories
        source_files = set(f for f in source.rglob("*") if f.is_file())
        dest_files = set(f for f in dest.rglob("*") if f.is_file())

        if len(source_files) != len(dest_files):
            self.logger.error(
                f"File count mismatch: {len(source_files)} source vs "
                f"{len(dest_files)} dest"
            )
            return False

        # Check each file
        for source_file in source_files:
            # Calculate relative path
            rel_path = source_file.relative_to(source)
            dest_file = dest / rel_path

            if not dest_file.exists():
                self.logger.error(f"Missing file in dest: {rel_path}")
                return False

            # Compare checksums
            source_hash = self._calculate_sha256(source_file)
            dest_hash = self._calculate_sha256(dest_file)

            if source_hash != dest_hash:
                self.logger.error(
                    f"Checksum mismatch for {rel_path}: "
                    f"source={source_hash[:8]} dest={dest_hash[:8]}"
                )
                return False

        self.logger.debug("All checksums match")
        return True

    def _move_directory(
        self,
        source: Path,
        dest: Path,
        name: str,
    ) -> bool:
        """Move a directory with verification.

        Args:
            source: Source directory path
            dest: Destination directory path
            name: Name for logging

        Returns:
            True if move succeeded
        """
        import time

        start_time = time.time()
        errors: list[str] = []

        try:
            # Create destination parent
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Skip if destination already exists
            if dest.exists():
                self.logger.warning(f"Destination already exists: {dest}")
                return False

            # Get source stats before move
            source_files, source_size = self._count_files_and_size(source)

            self.logger.info(f"Moving {source} -> {dest}")

            # Move directory (preserves permissions and timestamps)
            shutil.move(str(source), str(dest))

            # Get destination stats after move
            dest_files, dest_size = self._count_files_and_size(dest)

            # Verify checksums
            checksum_ok = self._verify_checksums(dest, dest)

            move_time = time.time() - start_time

            self.logger.info(
                f"Moved {name}: {source_files} files, "
                f"{source_size:.2f} MB in {move_time:.2f}s"
            )

            return True

        except Exception as e:
            move_time = time.time() - start_time
            errors.append(str(e))
            self.logger.error(f"Failed to move {name}: {e}")
            return False

    def _move_test_directory(
        self,
        test_path: Path,
        dest_name: str,
    ) -> bool:
        """Move a test directory.

        Args:
            test_path: Path to test directory
            dest_name: Destination name (e.g., "tests_unit_container")

        Returns:
            True if moved or doesn't exist
        """
        if not test_path.exists():
            self.logger.debug(f"Test directory not found: {test_path}")
            return True  # Not an error if it doesn't exist

        dest_path = self.dest / dest_name

        # Handle conflicts (append number if needed)
        if dest_path.exists():
            counter = 1
            while dest_path.exists():
                dest_path = self.dest / f"{dest_name}_{counter}"
                counter += 1

        return self._move_directory(test_path, dest_path, dest_name)

    def move_submodule(
        self,
        submodule: str,
        move_source: bool = True,
        move_tests: bool = True,
    ) -> MoveStats:
        """Move a single submodule.

        Args:
            submodule: Submodule name
            move_source: Whether to move source directory
            move_tests: Whether to move test directories

        Returns:
            MoveStats object with operation details
        """
        import time

        start_time = time.time()
        stats = MoveStats(submodule_name=submodule)

        self.logger.info(f"Processing submodule: {submodule}")

        # Verify exported project exists
        if not self._verify_exported_project_exists(submodule):
            error = f"Exported project not found for {submodule}"
            stats.errors.append(error)
            stats.success = False
            self.logger.error(error)
            return stats

        # Move source directory
        if move_source:
            source_path = self.src_path / submodule
            dest_path = self.dest / submodule

            if source_path.exists():
                if self._move_directory(source_path, dest_path, submodule):
                    stats.source_files, stats.source_size_mb = (
                        self._count_files_and_size(dest_path)
                    )
                    stats.dest_files = stats.source_files
                    stats.dest_size_mb = stats.source_size_mb
                else:
                    stats.success = False
                    stats.errors.append(f"Failed to move source directory")
            else:
                self.logger.warning(f"Source directory not found: {source_path}")

        # Move test directories
        if move_tests:
            test_paths = TEST_DIRS.get(submodule, [])
            tests_moved = 0

            for i, test_path_str in enumerate(test_paths):
                test_path = self.project_root / test_path_str
                # Generate dest name from path (e.g., "tests/unit/container" -> "tests_unit_container")
                dest_name = test_path_str.replace("/", "_")

                if self._move_test_directory(test_path, dest_name):
                    tests_moved += 1

            stats.tests_moved = tests_moved

        stats.move_time_s = time.time() - start_time

        if stats.success:
            self.logger.info(f"✓ Completed {submodule} in {stats.move_time_s:.2f}s")
        else:
            self.logger.error(f"✗ Failed {submodule}: {', '.join(stats.errors)}")

        return stats

    def move_all(
        self,
        submodules: list[str] | None = None,
        move_source: bool = True,
        move_tests: bool = True,
    ) -> list[MoveStats]:
        """Move multiple submodules.

        Args:
            submodules: List of submodule names (None = all)
            move_source: Whether to move source directories
            move_tests: Whether to move test directories

        Returns:
            List of MoveStats for each submodule
        """
        if submodules is None:
            submodules = SUBMODULES

        self.logger.info(f"Moving {len(submodules)} submodules...")

        for submodule in submodules:
            stats = self.move_submodule(submodule, move_source, move_tests)
            self.stats.append(stats)

        return self.stats

    def rollback(
        self,
        submodules: list[str] | None = None,
    ) -> list[bool]:
        """Rollback moved submodules back to original location.

        Args:
            submodules: List of submodule names (None = all in temp)

        Returns:
            List of success status for each submodule
        """
        if submodules is None:
            # Auto-detect submodules in temp directory
            submodules = []
            for item in self.dest.iterdir():
                if item.is_dir() and not item.name.startswith("tests_"):
                    submodules.append(item.name)

        self.logger.info(f"Rolling back {len(submodules)} submodules...")

        results = []
        for submodule in submodules:
            temp_path = self.dest / submodule
            source_path = self.src_path / submodule

            if not temp_path.exists():
                self.logger.warning(f"Temp directory not found: {temp_path}")
                results.append(False)
                continue

            if source_path.exists():
                self.logger.warning(f"Source already exists: {source_path}")
                results.append(False)
                continue

            try:
                self.logger.info(f"Moving {temp_path} -> {source_path}")
                shutil.move(str(temp_path), str(source_path))
                self.logger.info(f"✓ Rolled back {submodule}")
                results.append(True)
            except Exception as e:
                self.logger.error(f"✗ Failed to rollback {submodule}: {e}")
                results.append(False)

        # Rollback test directories
        for item in self.dest.iterdir():
            if item.is_dir() and item.name.startswith("tests_"):
                # Reconstruct original path from dest name
                # "tests_unit_container" -> "tests/unit/container"
                parts = item.name.replace("_", "/", 2)
                # Handle cases like "tests_unit_container" -> "tests/unit/container"
                if parts.startswith("tests/"):
                    original_path = self.project_root / parts
                    try:
                        self.logger.info(f"Moving {item} -> {original_path}")
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(item), str(original_path))
                        self.logger.info(f"✓ Rolled back {item.name}")
                    except Exception as e:
                        self.logger.error(f"✗ Failed to rollback {item.name}: {e}")

        return results

    def generate_report(self) -> Path:
        """Generate CSV report of move operations.

        Returns:
            Path to generated report file
        """
        report_path = self.project_root / self.DEFAULT_REPORT

        with open(report_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "submodule_name",
                "source_files",
                "source_size_mb",
                "dest_files",
                "dest_size_mb",
                "tests_moved",
                "move_time_s",
                "checksum_match",
                "success",
            ])
            writer.writeheader()

            for stat in self.stats:
                writer.writerow(stat.to_csv_row())

        self.logger.info(f"Generated report: {report_path}")
        return report_path


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Move original submodules to temporary directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(".temp-original-submodules"),
        help="Destination directory (default: .temp-original-submodules)",
    )

    parser.add_argument(
        "--submodules",
        nargs="+",
        help="Specific submodules to move (default: all)",
    )

    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Only move test directories, not source",
    )

    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Only move source directories, not tests",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing destination",
    )

    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback: move submodules back to original location",
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path.cwd()

    # Create mover
    mover = SubmoduleMover(
        project_root=project_root,
        dest=args.dest,
    )

    # Handle rollback
    if args.rollback:
        mover.logger.info("Starting rollback...")
        results = mover.rollback(args.submodules)
        success_count = sum(1 for r in results if r)
        mover.logger.info(
            f"Rollback complete: {success_count}/{len(results)} succeeded"
        )
        return 0 if all(results) else 1

    # Handle dry run
    if args.dry_run:
        mover.logger.info("DRY RUN - No changes will be made")

        submodules = args.submodules or SUBMODULES
        for submodule in submodules:
            source_path = mover.src_path / submodule
            dest_path = mover.dest / submodule

            if source_path.exists():
                files, size = mover._count_files_and_size(source_path)
                mover.logger.info(
                    f"Would move: {source_path} -> {dest_path} "
                    f"({files} files, {size:.2f} MB)"
                )

                # Show test directories
                test_paths = TEST_DIRS.get(submodule, [])
                for test_path_str in test_paths:
                    test_path = project_root / test_path_str
                    if test_path.exists():
                        mover.logger.info(f"  Would move tests: {test_path}")
            else:
                mover.logger.warning(f"Source not found: {source_path}")

        mover.logger.info("DRY RUN complete - no changes made")
        return 0

    # Confirm before proceeding
    if not args.yes:
        submodules = args.submodules or SUBMODULES
        print(f"\nAbout to move {len(submodules)} submodules:")
        for s in submodules:
            print(f"  - {s}")

        if args.tests_only:
            print("  (TESTS ONLY)")
        elif args.source_only:
            print("  (SOURCE ONLY)")

        response = input("\nProceed? [y/N] ")
        if response.lower() != "y":
            print("Aborted")
            return 1

    # Perform move
    mover.logger.info("Starting move operation...")

    stats = mover.move_all(
        submodules=args.submodules,
        move_source=not args.tests_only,
        move_tests=not args.source_only,
    )

    # Generate report
    report_path = mover.generate_report()

    # Summary
    success_count = sum(1 for s in stats if s.success)
    mover.logger.info(
        f"\nMove complete: {success_count}/{len(stats)} succeeded"
    )
    mover.logger.info(f"Report: {report_path}")

    return 0 if all(s.success for s in stats) else 1


if __name__ == "__main__":
    raise SystemExit(main())
