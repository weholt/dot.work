"""Unit tests for db-issues CLI editor validation.

Tests the _validate_editor function to prevent command injection
via unvalidated editor commands (SEC-001@94eb69).
"""

from __future__ import annotations

import pytest

from dot_work.db_issues.cli import _ALLOWED_EDITORS, _validate_editor


class TestValidateEditor:
    """Tests for _validate_editor function."""

    def test_allowed_editor_simple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Allowed editors should pass validation with simple names."""
        # Ensure EDITOR is not set for this test
        monkeypatch.delenv("EDITOR", raising=False)

        for editor in ["vi", "vim", "nano"]:
            name, args = _validate_editor(editor)
            assert name == editor
            assert args == []

    def test_allowed_editor_with_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Allowed editors with arguments should be parsed correctly."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("code --wait")
        assert name == "code"
        assert args == ["--wait"]

    def test_code_gets_wait_flag_added(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """VS Code should automatically get --wait flag if not present."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("code")
        assert name == "code"
        assert args == ["--wait"]

    def test_code_wait_flag_not_duplicated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """VS Code with --wait should not get it added again."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("code --wait")
        assert name == "code"
        assert args == ["--wait"]
        assert args.count("--wait") == 1

    def test_vim_with_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Vim with arguments should preserve args."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("vim +10")
        assert name == "vim"
        assert args == ["+10"]

    def test_none_editor_defaults_to_vi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """None should default to vi via environment variable."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor(None)
        assert name == "vi"
        assert args == []

    def test_empty_string_defaults_to_vi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string should default to vi."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("")
        assert name == "vi"
        assert args == []

    def test_whitespace_only_defaults_to_vi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Whitespace-only string should default to vi."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("   ")
        assert name == "vi"
        assert args == []

    def test_path_components_are_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Path components should be stripped, leaving only base name."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("/usr/bin/vim")
        assert name == "vim"
        assert args == []

    def test_allowed_editor_full_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full path to allowed editor should work."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("/usr/bin/code --wait")
        assert name == "code"
        assert args == ["--wait"]

    def test_disallowed_editor_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Disallowed editor should raise ValueError with helpful message."""
        monkeypatch.delenv("EDITOR", raising=False)

        with pytest.raises(ValueError) as exc_info:
            _validate_editor("malicious-editor")

        error_msg = str(exc_info.value)
        assert "not allowed" in error_msg
        assert "Allowed editors" in error_msg
        assert "vi" in error_msg  # Should list some allowed editors

    def test_disallowed_editor_with_args_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Disallowed editor with args should also raise ValueError."""
        monkeypatch.delenv("EDITOR", raising=False)

        with pytest.raises(ValueError) as exc_info:
            _validate_editor("rm -rf /")

        error_msg = str(exc_info.value)
        assert "not allowed" in error_msg
        assert "rm" in error_msg

    def test_command_injection_attempts_are_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Command injection patterns should be blocked."""
        monkeypatch.delenv("EDITOR", raising=False)

        # All of these should raise ValueError (either for shell metacharacters
        # or for disallowed editor names)
        malicious_inputs = [
            "vi; rm -rf /",
            "code && exploit",
            "vim| cat /etc/passwd",
            "nano`whoami`",
            "emacs$(touch /tmp/pwned)",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(ValueError):
                _validate_editor(malicious_input)

    def test_all_whitelisted_editors_are_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Every editor in the whitelist should be valid."""
        monkeypatch.delenv("EDITOR", raising=False)

        # Only test editors that don't auto-get --wait flag
        non_code_editors = [
            e for e in _ALLOWED_EDITORS if e not in ("code", "code-server", "codium")
        ]

        for editor in non_code_editors:
            name, args = _validate_editor(editor)
            assert name == editor
            assert args == []

    def test_codium_gets_wait_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """VSCodium should also get --wait flag."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("codium")
        assert name == "codium"
        assert args == ["--wait"]

    def test_code_server_gets_wait_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """code-server should also get --wait flag."""
        monkeypatch.delenv("EDITOR", raising=False)

        name, args = _validate_editor("code-server")
        assert name == "code-server"
        assert args == ["--wait"]

    def test_editor_env_var_is_used_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """EDITOR environment variable should be used when no explicit editor is given."""
        monkeypatch.setenv("EDITOR", "nvim")

        name, args = _validate_editor(None)
        assert name == "nvim"
        assert args == []

    def test_editor_env_var_with_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """EDITOR environment variable with args should be parsed."""
        monkeypatch.setenv("EDITOR", "nvim +10")

        name, args = _validate_editor(None)
        assert name == "nvim"
        assert args == ["+10"]
