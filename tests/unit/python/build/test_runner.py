"""Tests for BuildRunner class."""

from pathlib import Path

import pytest

from dot_work.python.build.runner import BuildRunner, MemoryStats


class TestBuildRunner:
    """Tests for BuildRunner class."""

    def test_runner_initialization(self, project_root: Path) -> None:
        """Test BuildRunner initializes with correct defaults."""
        runner = BuildRunner(
            project_root=project_root,
            verbose=False,
            fix=False,
            source_dirs=["."],
            test_dirs=["tests"],
            coverage_threshold=70,
            use_uv=False,
        )

        assert runner.project_root == project_root
        assert runner.verbose is False
        assert runner.fix is False
        assert runner.source_dirs == ["."]
        assert runner.test_dirs == ["tests"]
        assert runner.coverage_threshold == 70
        assert runner.use_uv is False
        assert runner.failed_steps == []

    def test_runner_with_defaults(self, project_root: Path) -> None:
        """Test BuildRunner with default values."""
        runner = BuildRunner(project_root=project_root)

        assert runner.project_root == project_root
        assert runner.verbose is False
        assert runner.fix is False
        assert runner.use_uv is False
        assert runner.coverage_threshold == 70
        assert runner.test_dirs == ["tests"]

    def test_get_command_prefix_with_uv(self, project_root: Path) -> None:
        """Test command prefix includes 'uv run' when use_uv=True."""
        runner = BuildRunner(project_root=project_root, use_uv=True)
        assert runner._get_command_prefix() == ["uv", "run"]

    def test_get_command_prefix_without_uv(self, project_root: Path) -> None:
        """Test command prefix is empty when use_uv=False."""
        runner = BuildRunner(project_root=project_root, use_uv=False)
        assert runner._get_command_prefix() == []

    def test_detect_source_dirs_with_packages(self, project_root: Path) -> None:
        """Test source directory detection finds packages."""
        # Create a package directory
        pkg_dir = project_root / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").touch()

        runner = BuildRunner(project_root=project_root)
        assert "mypackage" in runner.source_dirs

    def test_detect_source_dirs_with_py_files(self, project_root: Path) -> None:
        """Test source directory detection finds directories with .py files."""
        # Create a directory with Python files
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()

        runner = BuildRunner(project_root=project_root)
        assert "src" in runner.source_dirs

    def test_detect_source_dirs_fallback(self, project_root: Path) -> None:
        """Test source directory detection falls back to '.' when no packages found."""
        runner = BuildRunner(project_root=project_root)
        assert runner.source_dirs == ["."]

    def test_detect_source_dirs_excludes_test_dirs(self, project_root: Path) -> None:
        """Test source directory detection excludes test directories."""
        # Create test directories with __init__.py
        for test_dir in ["tests", "test", "docs", "examples", "scripts"]:
            dir_path = project_root / test_dir
            dir_path.mkdir()
            (dir_path / "__init__.py").touch()

        runner = BuildRunner(project_root=project_root)
        assert "tests" not in runner.source_dirs
        assert "test" not in runner.source_dirs
        assert "docs" not in runner.source_dirs
        assert "examples" not in runner.source_dirs
        assert "scripts" not in runner.source_dirs

    def test_coverage_threshold_check(self, project_root: Path) -> None:
        """Test coverage threshold is stored correctly."""
        runner = BuildRunner(project_root=project_root, coverage_threshold=80)
        assert runner.coverage_threshold == 80

    def test_clean_artifacts_creates_list(self, project_root: Path) -> None:
        """Test clean artifacts includes expected patterns."""
        runner = BuildRunner(project_root=project_root)
        # This test just verifies the method exists and can be called
        # Actual artifact cleaning is tested in integration tests
        assert hasattr(runner, "clean_artifacts")

    def test_build_step_methods_exist(self, project_root: Path) -> None:
        """Test all build step methods exist."""
        runner = BuildRunner(project_root=project_root)

        methods = [
            "check_dependencies",
            "format_code",
            "lint_code",
            "type_check",
            "run_tests",
            "run_security_check",
            "run_static_analysis",
            "build_documentation",
            "generate_reports",
            "clean_artifacts",
            "run_full_build",
        ]

        for method in methods:
            assert hasattr(runner, method), f"BuildRunner missing method: {method}"

    def test_failed_steps_tracking(self, project_root: Path) -> None:
        """Test failed steps are tracked."""
        runner = BuildRunner(project_root=project_root)
        assert runner.failed_steps == []

        runner.failed_steps.append("Test Step")
        assert "Test Step" in runner.failed_steps


class TestMemoryStats:
    """Tests for MemoryStats dataclass."""

    def test_memory_stats_creation(self) -> None:
        """Test creating MemoryStats."""
        stats = MemoryStats(
            peak_rss_mb=100.5,
            peak_vms_mb=200.0,
            duration_seconds=5.25,
            step_name="Test Step",
        )
        assert stats.peak_rss_mb == 100.5
        assert stats.peak_vms_mb == 200.0
        assert stats.duration_seconds == 5.25
        assert stats.step_name == "Test Step"

    def test_memory_stats_string_format(self) -> None:
        """Test MemoryStats string representation."""
        stats = MemoryStats(
            peak_rss_mb=100.5,
            peak_vms_mb=200.0,
            duration_seconds=5.25,
            step_name="Test Step",
        )
        result = str(stats)
        assert "Test Step" in result
        assert "100.5 MB RSS" in result
        assert "200.0 MB VMS" in result
        assert "5.25s" in result


class TestBuildRunnerMemory:
    """Tests for BuildRunner memory-related features."""

    def test_default_memory_limit(self, project_root: Path) -> None:
        """Test that default memory limit is 4GB (4096 MB)."""
        runner = BuildRunner(project_root=project_root)
        assert runner.memory_limit_mb == 4096
        assert runner.enforce_memory_limit is True

    def test_custom_memory_limit(self, project_root: Path) -> None:
        """Test setting custom memory limit."""
        runner = BuildRunner(project_root=project_root, memory_limit_mb=8192)
        assert runner.memory_limit_mb == 8192

    def test_memory_enforcement_disabled(self, project_root: Path) -> None:
        """Test disabling memory enforcement."""
        runner = BuildRunner(project_root=project_root, enforce_memory_limit=False)
        assert runner.enforce_memory_limit is False

    def test_memory_stats_list_initialized(self, project_root: Path) -> None:
        """Test that memory_stats list is initialized."""
        runner = BuildRunner(project_root=project_root)
        assert runner.memory_stats == []

    def test_get_memory_mb_returns_tuple(self, project_root: Path) -> None:
        """Test _get_memory_mb returns tuple of floats."""
        runner = BuildRunner(project_root=project_root)
        rss, vms = runner._get_memory_mb()
        assert isinstance(rss, float)
        assert isinstance(vms, float)

    def test_get_memory_mb_linux(self, project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _get_memory_mb reads from /proc/self/status on Linux."""

        def mock_open(filename: str, *args: object, **kwargs: object):
            if filename == "/proc/self/status":
                content = """VmRSS: 262144 kB
VmSize: 524288 kB
"""
                import io

                return io.StringIO(content)
            return open(filename, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr("builtins.open", mock_open)
        runner = BuildRunner(project_root=project_root)
        rss, vms = runner._get_memory_mb()
        assert rss == 256.0  # 262144 KB / 1024
        assert vms == 512.0  # 524288 KB / 1024

    def test_wrap_with_cgroup(self, project_root: Path) -> None:
        """Test _wrap_with_cgroup produces correct systemd-run command."""
        runner = BuildRunner(project_root=project_root)
        cmd = ["pytest", "tests/"]
        wrapped = runner._wrap_with_cgroup(cmd, 4096)
        assert wrapped[0] == "systemd-run"
        assert "--scope" in wrapped
        assert f"--property=MemoryMax=4096M" in wrapped
        assert "pytest" in wrapped

    def test_wrap_with_ulimit(self, project_root: Path) -> None:
        """Test _wrap_with_ulimit produces correct shell wrapper."""
        runner = BuildRunner(project_root=project_root)
        cmd = ["pytest", "tests/"]
        wrapped = runner._wrap_with_ulimit(cmd, 2048)
        assert wrapped[0] == "sh"
        assert wrapped[1] == "-c"
        assert "ulimit -v 2097152" in wrapped[2]  # 2048 * 1024
        assert "pytest" in wrapped[2]

    def test_wrap_with_memory_limit_uses_cgroup_when_available(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _wrap_with_memory_limit prefers cgroup when systemd-run exists."""

        def mock_which(cmd: str) -> str | None:
            return "/usr/bin/systemd-run" if cmd == "systemd-run" else None

        monkeypatch.setattr("shutil.which", mock_which)
        runner = BuildRunner(project_root=project_root, verbose=False)
        cmd = ["pytest", "tests/"]
        wrapped = runner._wrap_with_memory_limit(cmd, 4096)
        assert wrapped[0] == "systemd-run"

    def test_wrap_with_memory_limit_falls_back_to_ulimit(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _wrap_with_memory_limit falls back to ulimit when systemd-run missing."""

        def mock_which(cmd: str) -> str | None:
            return None  # systemd-run not found

        monkeypatch.setattr("shutil.which", mock_which)
        runner = BuildRunner(project_root=project_root, verbose=False)
        cmd = ["pytest", "tests/"]
        wrapped = runner._wrap_with_memory_limit(cmd, 4096)
        assert wrapped[0] == "sh"  # ulimit wrapper

    def test_runner_initialization_with_memory_params(
        self, project_root: Path,
    ) -> None:
        """Test BuildRunner initialization with memory parameters."""
        runner = BuildRunner(
            project_root=project_root,
            memory_limit_mb=8192,
            enforce_memory_limit=False,
        )
        assert runner.memory_limit_mb == 8192
        assert runner.enforce_memory_limit is False

    def test_default_memory_limit_constant(self) -> None:
        """Test DEFAULT_MEMORY_LIMIT_MB constant is 4096."""
        assert BuildRunner.DEFAULT_MEMORY_LIMIT_MB == 4096

