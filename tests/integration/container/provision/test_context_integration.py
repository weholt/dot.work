"""Integration tests for context injection (FEAT-026).

These tests verify the end-to-end integration between CLI arguments,
context resolution, and Docker volume argument generation.
"""

from pathlib import Path

import pytest

from dot_work.container.provision.context import (
    DEFAULT_CONTEXT_MOUNT_POINT,
    build_context_volume_args,
    resolve_context_spec,
)


@pytest.mark.integration
class TestContextResolutionIntegration:
    """Test end-to-end context resolution."""

    def test_auto_detection_from_project_root(self, tmp_path: Path) -> None:
        """Test auto-detection of context files from project root."""
        # Create typical context files
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "config.md").write_text("# Config")
        (tmp_path / ".opencode.json").write_text("{}")

        # Simulate what _build_volume_args does with project_root
        context_spec = resolve_context_spec(
            explicit_paths=None,  # Triggers auto-detection
            allowlist=None,  # Use default allowlist
            denylist=None,  # Use default denylist
            override=False,
            mount_point=DEFAULT_CONTEXT_MOUNT_POINT,
            project_root=tmp_path,
        )

        # Should auto-detect both .claude and .opencode.json
        assert len(context_spec.paths) == 2
        path_names = [p.name for p in context_spec.paths]
        assert ".claude" in path_names
        assert ".opencode.json" in path_names

    def test_explicit_paths_override_auto_detection(self, tmp_path: Path) -> None:
        """Test that explicit paths override auto-detection."""
        # Create both typical files and explicit files
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".opencode.json").write_text("{}")

        explicit_file = tmp_path / "custom.md"
        explicit_file.write_text("# Custom")

        context_spec = resolve_context_spec(
            explicit_paths=[explicit_file],  # Explicit path
            project_root=tmp_path,
        )

        # Should only have explicit file, not auto-detected
        assert len(context_spec.paths) == 1
        assert context_spec.paths[0] == explicit_file

    def test_env_variable_configuration(self, tmp_path: Path, monkeypatch) -> None:
        """Test that environment variables configure context detection."""
        (tmp_path / "test.env").write_text("KEY=value")
        (tmp_path / "test.txt").write_text("Text")

        # Set env var for allowlist
        monkeypatch.setenv("CONTEXT_ALLOWLIST", "*.env")

        context_spec = resolve_context_spec(
            explicit_paths=None,
            project_root=tmp_path,
        )

        # Should only find .env file due to env allowlist
        assert len(context_spec.paths) == 1
        assert context_spec.paths[0].name == "test.env"
        assert context_spec.allowlist is not None
        assert "*.env" in context_spec.allowlist

    def test_custom_allowlist_filters_files(self, tmp_path: Path) -> None:
        """Test custom allowlist filters auto-detected files."""
        (tmp_path / "custom.md").write_text("# Custom")
        (tmp_path / "other.txt").write_text("Text")

        context_spec = resolve_context_spec(
            explicit_paths=None,
            allowlist=["*.md"],  # Only .md files
            project_root=tmp_path,
        )

        # Should only find .md file
        assert len(context_spec.paths) == 1
        assert context_spec.paths[0].name == "custom.md"


@pytest.mark.integration
class TestVolumeArgsIntegration:
    """Test Docker volume argument generation from context."""

    def test_volume_args_format(self, tmp_path: Path) -> None:
        """Test that volume args are correctly formatted for Docker."""
        test_file = tmp_path / "config.yml"
        test_file.write_text("key: value")

        context_spec = resolve_context_spec(
            explicit_paths=[test_file],
            mount_point="/root/.context",
        )

        volume_args = build_context_volume_args(context_spec)

        # Should produce ['-v', 'host_path:container_path']
        assert len(volume_args) == 2
        assert volume_args[0] == "-v"
        assert str(test_file.resolve()) in volume_args[1]
        assert "/root/.context/config.yml" in volume_args[1]

    def test_volume_args_multiple_paths(self, tmp_path: Path) -> None:
        """Test volume args for multiple context paths."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")

        context_spec = resolve_context_spec(
            explicit_paths=[file1, file2],
            mount_point="/context",
        )

        volume_args = build_context_volume_args(context_spec)

        # Should have 2 pairs of args
        assert len(volume_args) == 4
        assert volume_args.count("-v") == 2
        assert any("file1.txt" in arg for arg in volume_args)
        assert any("file2.txt" in arg for arg in volume_args)

    def test_volume_args_directory_vs_file(self, tmp_path: Path) -> None:
        """Test that directories and files mount correctly."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        test_dir = tmp_path / "directory"
        test_dir.mkdir()
        (test_dir / "inner.txt").write_text("inner")

        context_spec = resolve_context_spec(
            explicit_paths=[test_file, test_dir],
            mount_point="/root/.context",
        )

        volume_args = build_context_volume_args(context_spec)

        # File should mount to /root/.context/file.txt
        assert any("/root/.context/file.txt" in arg for arg in volume_args)
        # Directory should mount to /root/.context/directory/
        assert any("/root/.context/directory/" in arg for arg in volume_args)

    def test_volume_args_custom_mount_point(self, tmp_path: Path) -> None:
        """Test volume args with custom mount point."""
        test_file = tmp_path / "README.md"
        test_file.write_text("# README")

        context_spec = resolve_context_spec(
            explicit_paths=[test_file],
            mount_point="/custom/mount/point",
        )

        volume_args = build_context_volume_args(context_spec)

        assert any("/custom/mount/point/README.md" in arg for arg in volume_args)

    def test_volume_args_skip_nonexistent(self, tmp_path: Path, caplog) -> None:
        """Test that non-existent paths are skipped."""
        nonexistent = tmp_path / "does_not_exist.txt"

        context_spec = resolve_context_spec(
            explicit_paths=[nonexistent],
            mount_point="/context",
        )

        volume_args = build_context_volume_args(context_spec)

        # Should return empty list (path skipped)
        assert len(volume_args) == 0

    def test_volume_args_override_flag(self, tmp_path: Path) -> None:
        """Test that override flag affects behavior."""
        test_file = tmp_path / "config.json"
        test_file.write_text("{}")

        # With override=False
        spec_no_override = resolve_context_spec(
            explicit_paths=[test_file],
            mount_point="/context",
            override=False,
        )
        args_no_override = build_context_volume_args(spec_no_override)
        assert len(args_no_override) == 2  # Should still create args

        # With override=True
        spec_override = resolve_context_spec(
            explicit_paths=[test_file],
            mount_point="/context",
            override=True,
        )
        args_override = build_context_volume_args(spec_override)
        assert len(args_override) == 2  # Same result (conflict check not impl)


@pytest.mark.integration
class TestDefaultAllowlistIntegration:
    """Test default allowlist for context detection."""

    def test_default_allowlist_includes_common_configs(self) -> None:
        """Test that default allowlist includes common config patterns."""
        from dot_work.container.provision.context import DEFAULT_ALLOWLIST

        # Verify expected defaults are present
        assert ".claude/" in DEFAULT_ALLOWLIST
        assert ".opencode.json" in DEFAULT_ALLOWLIST
        assert ".github/copilot-instructions.md" in DEFAULT_ALLOWLIST

    def test_default_denylist_excludes_common_junk(self) -> None:
        """Test that default denylist excludes common junk."""
        from dot_work.container.provision.context import DEFAULT_DENYLIST

        # Verify expected exclusions
        assert ".git/" in DEFAULT_DENYLIST
        assert "node_modules/" in DEFAULT_DENYLIST
        assert "__pycache__/" in DEFAULT_DENYLIST
        assert ".venv/" in DEFAULT_DENYLIST or "venv/" in DEFAULT_DENYLIST
