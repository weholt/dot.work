"""Tests for git operations with security validation."""

from unittest.mock import patch

import pytest

from dot_work.review.git import (
    GitRefValidationError,
    _validate_git_path,
    _validate_git_ref,
    changed_files,
    get_unified_diff,
    parse_unified_diff,
)


class TestValidateGitRef:
    """Tests for _validate_git_ref function."""

    def test_valid_head(self) -> None:
        """HEAD is a valid reference."""
        assert _validate_git_ref("HEAD") == "HEAD"

    def test_valid_branch_names(self) -> None:
        """Standard branch names are valid."""
        assert _validate_git_ref("main") == "main"
        assert _validate_git_ref("develop") == "develop"
        assert _validate_git_ref("feature/my-feature") == "feature/my-feature"
        assert _validate_git_ref("bugfix/issue-123") == "bugfix/issue-123"

    def test_valid_tag_names(self) -> None:
        """Tag names are valid."""
        assert _validate_git_ref("v1.0.0") == "v1.0.0"
        assert _validate_git_ref("release-2.0") == "release-2.0"

    def test_valid_commit_hashes(self) -> None:
        """Full commit hashes are valid."""
        short_hash = "a" * 40
        assert _validate_git_ref(short_hash) == short_hash
        long_hash = "f" * 64
        assert _validate_git_ref(long_hash) == long_hash

    def test_valid_ref_with_tilde(self) -> None:
        """Refs with tilde (HEAD~n) are valid."""
        assert _validate_git_ref("HEAD~1") == "HEAD~1"
        assert _validate_git_ref("HEAD~10") == "HEAD~10"

    def test_valid_ref_with_caret(self) -> None:
        """Refs with caret (HEAD^n) are valid."""
        assert _validate_git_ref("HEAD^1") == "HEAD^1"
        assert _validate_git_ref("HEAD^2") == "HEAD^2"

    def test_valid_at_annotation(self) -> None:
        """@ annotation syntax is valid."""
        assert _validate_git_ref("@{-1}") == "@{-1}"
        assert _validate_git_ref("@{-10}") == "@{-10}"

    def test_valid_remote_branch(self) -> None:
        """Remote branch references are valid."""
        assert _validate_git_ref("origin/main") == "origin/main"
        assert _validate_git_ref("upstream/develop") == "upstream/develop"


class TestGitRefValidationSecurity:
    """Tests for git ref injection prevention."""

    def test_empty_ref_rejected(self) -> None:
        """Empty references are rejected."""
        with pytest.raises(GitRefValidationError, match="cannot be empty"):
            _validate_git_ref("")

    def test_git_option_double_dash_rejected(self) -> None:
        """Git options starting with -- are rejected."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            _validate_git_ref("--help")

    def test_git_option_upload_pack_rejected(self) -> None:
        """RCE via --upload-pack is blocked."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            _validate_git_ref("--upload-pack=|touch /tmp/pwned|")

    def test_git_option_git_dir_rejected(self) -> None:
        """File access via --git-dir is blocked."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            _validate_git_ref("--git-dir=/etc/passwd")

    def test_git_option_work_tree_rejected(self) -> None:
        """Directory escape via --work-tree is blocked."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            _validate_git_ref("--work-tree=/tmp")

    def test_git_option_config_rejected(self) -> None:
        """Config injection via -c is blocked."""
        with pytest.raises(GitRefValidationError, match="Invalid git reference"):
            _validate_git_ref("-c core.sshCommand=/tmp/evil.sh")

    def test_shell_pipe_character_rejected(self) -> None:
        """Shell pipe injection is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main|rm -rf /")

    def test_shell_command_injection_rejected(self) -> None:
        """Command injection via shell metacharacters is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main;touch /tmp/pwned")

        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main&cat /etc/passwd")

    def test_shell_dollar_sign_rejected(self) -> None:
        """Variable expansion is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main$(rm -rf /)")

    def test_shell_backtick_rejected(self) -> None:
        """Backtick command substitution is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main`whoami`")

    def test_path_traversal_rejected(self) -> None:
        """Path traversal via double dot is blocked."""
        with pytest.raises(GitRefValidationError, match="path traversal"):
            _validate_git_ref("../main")

    def test_newline_rejected(self) -> None:
        """Newline injection is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main\n--exec")

    def test_carriage_return_rejected(self) -> None:
        """Carriage return injection is blocked."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_ref("main\r--exec")

    def test_invalid_characters_rejected(self) -> None:
        """Characters not in whitelist are rejected."""
        # Wildcard character is not allowed
        with pytest.raises(GitRefValidationError, match="Invalid git reference"):
            _validate_git_ref("branch*")  # wildcard not allowed

        # Special characters not in whitelist
        with pytest.raises(GitRefValidationError, match="Invalid git reference"):
            _validate_git_ref("branch!tag")  # exclamation not allowed


class TestValidateGitPath:
    """Tests for _validate_git_path function."""

    def test_valid_paths(self) -> None:
        """Valid file paths are accepted."""
        assert _validate_git_path("README.md") == "README.md"
        assert _validate_git_path("src/main.py") == "src/main.py"
        assert _validate_git_path("tests/unit/test_git.py") == "tests/unit/test_git.py"

    def test_path_with_hyphens_and_underscores(self) -> None:
        """Paths with hyphens and underscores are valid."""
        assert _validate_git_path("my-file.py") == "my-file.py"
        assert _validate_git_path("my_file.py") == "my_file.py"

    def test_empty_path_rejected(self) -> None:
        """Empty paths are rejected."""
        with pytest.raises(GitRefValidationError, match="cannot be empty"):
            _validate_git_path("")

    def test_git_option_in_path_rejected(self) -> None:
        """Git options in paths are rejected."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            _validate_git_path("--help")

    def test_shell_chars_in_path_rejected(self) -> None:
        """Shell metacharacters in paths are rejected."""
        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_path("file|rm -rf /")

        with pytest.raises(GitRefValidationError, match="dangerous characters"):
            _validate_git_path("file;cat /etc/passwd")


class TestChangedFilesSecurity:
    """Tests for changed_files security."""

    @patch("dot_work.review.git._run_git")
    def test_changed_files_validates_base(self, mock_run_git):
        """changed_files validates the base parameter."""
        mock_run_git.return_value = "file1.py\nfile2.py"

        # Valid ref should work
        result = changed_files("/tmp/repo", base="main")
        assert result == {"file1.py", "file2.py"}

    @patch("dot_work.review.git._run_git")
    def test_changed_files_rejects_injection(self, mock_run_git):
        """changed_files rejects git option injection."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            changed_files("/tmp/repo", base="--upload-pack=|evil|")

        # Should not call git with malicious input
        mock_run_git.assert_not_called()


class TestGetUnifiedDiffSecurity:
    """Tests for get_unified_diff security."""

    @patch("dot_work.review.git._run_git")
    def test_get_unified_diff_validates_parameters(self, mock_run_git):
        """get_unified_diff validates both base and path."""
        mock_run_git.return_value = "diff content"

        # Valid parameters should work
        result = get_unified_diff("/tmp/repo", "main.py", base="HEAD")
        assert result == "diff content"

    @patch("dot_work.review.git._run_git")
    def test_get_unified_diff_rejects_base_injection(self, mock_run_git):
        """get_unified_diff rejects injection via base parameter."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            get_unified_diff("/tmp/repo", "main.py", base="--git-dir=/etc")

        # Should not call git with malicious input
        mock_run_git.assert_not_called()

    @patch("dot_work.review.git._run_git")
    def test_get_unified_diff_rejects_path_injection(self, mock_run_git):
        """get_unified_diff rejects injection via path parameter."""
        with pytest.raises(GitRefValidationError, match="Git options are not allowed"):
            get_unified_diff("/tmp/repo", "--help", base="HEAD")

        # Should not call git with malicious input
        mock_run_git.assert_not_called()


class TestParseUnifiedDiff:
    """Tests for parse_unified_diff function."""

    def test_parse_empty_diff(self) -> None:
        """Empty diff returns empty FileDiff."""
        result = parse_unified_diff("test.py", "")
        assert result.path == "test.py"
        assert result.hunks == []

    def test_parse_binary_diff(self) -> None:
        """Binary diff is detected."""
        diff_text = "Binary files a/test.py and b/test.py differ"
        result = parse_unified_diff("test.py", diff_text)
        assert result.is_binary
        assert result.hunks == []

    def test_parse_simple_hunk(self) -> None:
        """Simple diff hunk is parsed correctly."""
        diff_text = """@@ -1,3 +1,4 @@
 line1
-line2
+line2-modified
 line3
+line4
"""
        result = parse_unified_diff("test.py", diff_text)
        assert len(result.hunks) == 1
        assert result.hunks[0].old_start == 1
        assert result.hunks[0].new_start == 1
        # 5 lines total: context, deleted, added, context, added
        assert len(result.hunks[0].lines) == 5
