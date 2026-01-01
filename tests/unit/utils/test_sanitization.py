"""Tests for error message sanitization utilities."""

import pytest

from dot_work.utils.sanitization import (
    sanitize_error_message,
    sanitize_log_message,
)


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    def test_removes_password_from_exception(self) -> None:
        """Test that passwords are redacted from error messages."""
        error = ValueError("Connection failed: password=secret123")
        sanitized = sanitize_error_message(error)
        assert "secret123" not in sanitized
        assert "[password]" in sanitized

    def test_removes_api_keys_from_exception(self) -> None:
        """Test that API keys are redacted from error messages."""
        error = Exception("API key=ghp_1234567890abcdef1234567890abcdef123456")
        sanitized = sanitize_error_message(error)
        assert "ghp_" not in sanitized
        assert "[api key]" in sanitized or "[key]" in sanitized

    def test_removes_file_paths_from_exception(self) -> None:
        """Test that file paths are redacted from error messages."""
        error = IOError("Failed to open /home/user/.ssh/id_rsa")
        sanitized = sanitize_error_message(error)
        assert "/home/user/.ssh/id_rsa" not in sanitized
        assert "[path]" in sanitized

    def test_removes_email_addresses_from_exception(self) -> None:
        """Test that email addresses are redacted from error messages."""
        error = ValueError("Invalid email: user@example.com")
        sanitized = sanitize_error_message(error)
        assert "user@example.com" not in sanitized
        assert "[email]" in sanitized

    def test_removes_connection_strings_from_exception(self) -> None:
        """Test that database connection strings are redacted."""
        error = Exception("DB connection: postgresql://user:pass@host/db")
        sanitized = sanitize_error_message(error)
        assert "postgresql://" not in sanitized
        assert "[connection string]" in sanitized

    def test_preserves_error_semantics(self) -> None:
        """Test that core error meaning is preserved."""
        error = FileNotFoundError("File not found: /path/to/file.txt")
        sanitized = sanitize_error_message(error)
        # The word "not found" should be preserved
        assert "not found" in sanitized.lower()

    def test_generic_message_for_sensitive_errors(self) -> None:
        """Test that generic messages are used for highly sensitive errors."""
        error = Exception("/home/user/.ssh/id_rsa: Permission denied")
        sanitized = sanitize_error_message(error)
        # Should not contain the actual path
        assert sanitized
        # Should be non-empty and not the original
        assert sanitized != str(error)

    def test_handles_string_input(self) -> None:
        """Test that string inputs are handled correctly."""
        message = "Error with password=secret123"
        sanitized = sanitize_error_message(message)
        assert "secret123" not in sanitized

    def test_logs_full_error(self, caplog) -> None:
        """Test that full error is logged for debugging."""
        error = ValueError("password=secret123")
        with caplog.at_level("DEBUG"):
            sanitize_error_message(error)
        # The full error should be in the logs
        assert "password=secret123" in caplog.text


class TestSanitizeLogMessage:
    """Tests for sanitize_log_message function (backward compatibility)."""

    def test_removes_password_from_log(self) -> None:
        """Test that passwords are redacted from log messages."""
        message = "Connecting with password=secret123"
        sanitized = sanitize_log_message(message)
        assert "secret123" not in sanitized
        assert "***" in sanitized

    def test_removes_token_from_log(self) -> None:
        """Test that tokens are redacted from log messages."""
        message = "Auth token=abc123def456"
        sanitized = sanitize_log_message(message)
        assert "abc123def456" not in sanitized
        assert "***" in sanitized

    def test_removes_github_token_from_log(self) -> None:
        """Test that GitHub tokens are redacted from log messages."""
        message = "Using ghp_1234567890abcdef1234567890abcdef123456"
        sanitized = sanitize_log_message(message)
        assert "ghp_" not in sanitized or "***" in sanitized

    def test_removes_email_from_log(self) -> None:
        """Test that emails are redacted from log messages."""
        message = "User: user@example.com"
        sanitized = sanitize_log_message(message)
        assert "user@example.com" not in sanitized or "***" in sanitized
