"""Tests for dot_work.zip.zipper module."""

import zipfile
from pathlib import Path

import pytest

from dot_work.zip.zipper import should_include, zip_folder


class TestZipFolder:
    """Tests for zip_folder function."""

    def test_zip_folder_creates_archive(
        self, test_folder_structure: Path, zip_output_dir: Path
    ) -> None:
        """Test that zip_folder creates a valid zip archive.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "test.zip"

        zip_folder(test_folder_structure, output_path)

        assert output_path.exists()
        assert zipfile.is_zipfile(output_path)

    def test_zip_folder_includes_all_files_by_default(
        self, test_folder_structure: Path, zip_output_dir: Path
    ) -> None:
        """Test that zip_folder includes all files when no .gitignore exists.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "test.zip"

        zip_folder(test_folder_structure, output_path)

        with zipfile.ZipFile(output_path, "r") as zipf:
            names = zipf.namelist()

            # Should include all files
            assert "file1.txt" in names
            assert "file2.py" in names
            assert "subdir/nested_file.txt" in names
            assert "subdir/nested_code.py" in names
            assert "build/output.o" in names

    def test_zip_folder_respects_gitignore_patterns(
        self, gitignore_folder: Path, zip_output_dir: Path
    ) -> None:
        """Test that zip_folder respects .gitignore patterns.

        Args:
            gitignore_folder: Fixture providing folder with .gitignore
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "gitignore.zip"

        zip_folder(gitignore_folder, output_path)

        with zipfile.ZipFile(output_path, "r") as zipf:
            names = zipf.namelist()

            # Should include tracked files
            assert "main.py" in names
            assert ".gitignore" in names
            assert "src/code.py" in names

            # Should exclude ignored files/dirs
            assert not any("debug.log" in name for name in names)
            assert not any("app.log" in name for name in names)
            assert not any("debug/" in name for name in names)
            assert not any("build/" in name for name in names)

    def test_zip_folder_empty_directory(self, empty_folder: Path, zip_output_dir: Path) -> None:
        """Test that zip_folder handles empty directories.

        Args:
            empty_folder: Fixture providing empty folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "empty.zip"

        zip_folder(empty_folder, output_path)

        assert output_path.exists()
        assert zipfile.is_zipfile(output_path)

        with zipfile.ZipFile(output_path, "r") as zipf:
            names = zipf.namelist()
            # Empty directory should result in empty zip
            assert len(names) == 0

    def test_zip_folder_nonexistent_path(self, zip_output_dir: Path) -> None:
        """Test that zip_folder raises FileNotFoundError for nonexistent folder.

        Args:
            zip_output_dir: Fixture providing output directory
        """
        nonexistent = zip_output_dir / "nonexistent"
        output_path = zip_output_dir / "test.zip"

        with pytest.raises(FileNotFoundError):
            zip_folder(nonexistent, output_path)

    def test_zip_folder_not_a_directory(self, temp_dir: Path) -> None:
        """Test that zip_folder raises NotADirectoryError for files.

        Args:
            temp_dir: Fixture providing temp directory
        """
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")
        output_path = temp_dir / "test.zip"

        with pytest.raises(NotADirectoryError):
            zip_folder(file_path, output_path)

    def test_zip_folder_custom_compression(
        self, test_folder_structure: Path, zip_output_dir: Path
    ) -> None:
        """Test zip_folder with custom compression method.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "test.zip"

        # Use ZIP_STORED (no compression)
        zip_folder(test_folder_structure, output_path, compression=zipfile.ZIP_STORED)

        assert output_path.exists()
        assert zipfile.is_zipfile(output_path)

        with zipfile.ZipFile(output_path, "r") as zipf:
            for info in zipf.infolist():
                # ZIP_STORED has compress_type of 0
                assert info.compress_type == zipfile.ZIP_STORED

    def test_zip_folder_with_path_objects(
        self, test_folder_structure: Path, zip_output_dir: Path
    ) -> None:
        """Test that zip_folder works with Path objects.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "test.zip"

        # Should work with Path objects
        zip_folder(test_folder_structure, output_path)

        assert output_path.exists()

    def test_zip_folder_preserves_file_content(
        self, test_folder_structure: Path, zip_output_dir: Path
    ) -> None:
        """Test that zip_folder preserves file content.

        Args:
            test_folder_structure: Fixture providing test folder
            zip_output_dir: Fixture providing output directory
        """
        output_path = zip_output_dir / "test.zip"

        zip_folder(test_folder_structure, output_path)

        with zipfile.ZipFile(output_path, "r") as zipf:
            content = zipf.read("file1.txt").decode("utf-8")
            assert content == "content1"

            content = zipf.read("file2.py").decode("utf-8")
            assert content == "print('hello')"


class TestShouldInclude:
    """Tests for should_include function."""

    def test_should_include_no_matcher(self) -> None:
        """Test should_include returns True when no matcher provided."""
        filepath = Path("file.txt")

        result = should_include(filepath, None)

        assert result is True

    def test_should_include_with_matcher_matching(self) -> None:
        """Test should_include returns False when file matches pattern.

        Uses a mock matcher that simulates gitignore behavior.
        """
        filepath = Path("debug.log")

        # Mock matcher that returns True for files matching *.log
        def mock_matcher(path: str) -> bool:
            return path.endswith(".log")

        result = should_include(filepath, mock_matcher)

        # should_include returns False when matcher returns True (matched by gitignore)
        assert result is False

    def test_should_include_with_matcher_not_matching(self) -> None:
        """Test should_include returns True when file doesn't match pattern.

        Uses a mock matcher that simulates gitignore behavior.
        """
        filepath = Path("code.py")

        # Mock matcher that returns True for files matching *.log
        def mock_matcher(path: str) -> bool:
            return path.endswith(".log")

        result = should_include(filepath, mock_matcher)

        # should_include returns True when matcher returns False (not matched)
        assert result is True

    def test_should_include_matcher_exception_handling(self) -> None:
        """Test should_include handles matcher exceptions gracefully."""
        filepath = Path("file.txt")

        # Mock matcher that raises exception
        def broken_matcher(path: str) -> bool:
            raise ValueError("Matching failed")

        result = should_include(filepath, broken_matcher)

        # Should include file if matcher fails
        assert result is True
