"""
Main AST scanner for Python codebases.

Provides high-level scanning API for Python projects.
"""

import fnmatch
import logging
import os
import re
from pathlib import Path
from re import Pattern

from dot_work.python.scan.ast_extractor import extract_entities
from dot_work.python.scan.cache import ScanCache
from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.models import CodeIndex, FileEntity
from dot_work.python.scan.utils import is_python_file, should_ignore

logger = logging.getLogger(__name__)


class ASTScanner:
    """Scanner for Python codebases using AST analysis."""

    def __init__(
        self,
        root_path: Path,
        ignore_patterns: list[str] | None = None,
        include_patterns: list[str] | None = None,
        config: ScanConfig | None = None,
    ) -> None:
        """Initialize the scanner.

        Args:
            root_path: Root directory to scan.
            ignore_patterns: Glob patterns to ignore.
            include_patterns: Glob patterns to include (default: all .py files).
            config: Scan configuration for cache.
        """
        self.root_path = root_path.resolve()
        self.ignore_patterns = ignore_patterns
        self.include_patterns = include_patterns or ["*.py"]
        self.config = config or ScanConfig()
        self.cache = ScanCache(self.config)
        # Pre-compile patterns into regex objects for O(1) pattern matching
        self._compiled_patterns: list[Pattern] = [
            re.compile(fnmatch.translate(pattern)) for pattern in self.include_patterns
        ]

    def scan(self, incremental: bool = False) -> CodeIndex:
        """Scan the codebase and build an index.

        Args:
            incremental: If True, use incremental scanning with cache.

        Returns:
            CodeIndex containing all scanned entities.
        """
        index = CodeIndex(root_path=self.root_path)

        # Load cache for incremental mode
        if incremental:
            self.cache.load()
            logger.debug(
                "Incremental scan: cache loaded with %d entries",
                self.cache.size,
            )

        scanned = 0
        skipped = 0

        for file_path in self._find_python_files():
            # Check cache if incremental mode
            if incremental and self.cache.is_cached(file_path):
                skipped += 1
                continue

            # Scan the file
            file_entity = self._scan_file(file_path)
            index.add_file(file_entity)
            scanned += 1

            # Update cache after scanning
            if incremental:
                self.cache.update(file_path)

        # Save cache after scan
        if incremental:
            self.cache.save()
            logger.debug(
                "Incremental scan: %d files scanned, %d cached files skipped",
                scanned,
                skipped,
            )

        return index

    def _find_python_files(self) -> list[Path]:
        """Find all Python files in the codebase.

        Returns:
            List of Python file paths.
        """
        python_files: list[Path] = []

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not should_ignore(root_path / d, self.ignore_patterns)]

            for file in files:
                file_path = root_path / file

                if not is_python_file(file_path):
                    continue

                if should_ignore(file_path, self.ignore_patterns):
                    continue

                if self._compiled_patterns:
                    if not any(pattern.match(file) for pattern in self._compiled_patterns):
                        continue

                python_files.append(file_path)

        return python_files

    def _scan_file(self, file_path: Path) -> FileEntity:
        """Scan a single Python file.

        Args:
            file_path: Path to the file.

        Returns:
            FileEntity with extracted information.
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            return extract_entities(source, file_path)
        except (OSError, UnicodeDecodeError) as e:
            return FileEntity(
                path=file_path,
                functions=[],
                classes=[],
                imports=[],
                line_count=0,
                has_syntax_error=True,
                error_message=f"Failed to read file: {e}",
            )
