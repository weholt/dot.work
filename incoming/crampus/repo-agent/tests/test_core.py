from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from repo_agent.core import (
    RepoAgentError,
    RunConfig,
    _bool_meta,
    _build_docker_run_cmd,
    _docker_build_if_needed,
    _load_frontmatter,
    _resolve_config,
    run_from_markdown,
)


class TestBoolMeta:
    """Test _bool_meta function for parsing boolean values from metadata."""

    def test_returns_default_when_key_missing(self):
        assert _bool_meta({}, "missing_key", True) is True
        assert _bool_meta({}, "missing_key", False) is False

    def test_returns_bool_value_directly(self):
        assert _bool_meta({"key": True}, "key", False) is True
        assert _bool_meta({"key": False}, "key", True) is False

    def test_parses_string_true_values(self):
        for value in ["1", "true", "True", "TRUE", "yes", "YES", "on", "ON"]:
            assert _bool_meta({"key": value}, "key", False) is True

    def test_parses_string_false_values(self):
        for value in ["0", "false", "False", "FALSE", "no", "NO", "off", "OFF"]:
            assert _bool_meta({"key": value}, "key", True) is False

    def test_converts_other_types_to_bool(self):
        assert _bool_meta({"key": 1}, "key", False) is True
        assert _bool_meta({"key": 0}, "key", True) is False
        # Non-empty strings that aren't recognized true/false values return default
        # This is the actual behavior of the function
        assert _bool_meta({"key": "something"}, "key", False) is False


class TestLoadFrontmatter:
    """Test _load_frontmatter function."""

    @patch("repo_agent.core.frontmatter.load")
    def test_loads_frontmatter_successfully(self, mock_load):
        mock_post = Mock()
        mock_post.metadata = {"key": "value"}
        mock_post.content = "Test content"
        mock_load.return_value = mock_post

        meta, content = _load_frontmatter(Path("test.md"))

        assert meta == {"key": "value"}
        assert content == "Test content"

    @patch("repo_agent.core.frontmatter.load")
    def test_handles_empty_metadata(self, mock_load):
        mock_post = Mock()
        mock_post.metadata = None
        mock_post.content = "Content only"
        mock_load.return_value = mock_post

        meta, content = _load_frontmatter(Path("test.md"))

        assert meta == {}
        assert content == "Content only"

    @patch("repo_agent.core.frontmatter.load")
    def test_strips_content_whitespace(self, mock_load):
        mock_post = Mock()
        mock_post.metadata = {}
        mock_post.content = "  \n  Test content  \n  "
        mock_load.return_value = mock_post

        meta, content = _load_frontmatter(Path("test.md"))

        assert content == "Test content"


class TestResolveConfig:
    """Test _resolve_config function."""

    @pytest.fixture
    def minimal_frontmatter(self):
        return {
            "repo_url": "https://github.com/user/repo.git",
            "model": "openai/gpt-4",
            "tool": {"name": "opencode", "entrypoint": "opencode run"},
        }

    @patch("repo_agent.core._load_frontmatter")
    def test_raises_error_when_repo_url_missing(self, mock_load):
        mock_load.return_value = ({"model": "gpt-4"}, "content")

        with pytest.raises(RepoAgentError, match="repo_url must be provided"):
            _resolve_config(Path("test.md"), {})

    @patch("repo_agent.core._load_frontmatter")
    def test_raises_error_when_model_missing(self, mock_load):
        mock_load.return_value = ({"repo_url": "https://github.com/user/repo.git"}, "content")

        with pytest.raises(RepoAgentError, match="model must be provided"):
            _resolve_config(Path("test.md"), {})

    @patch("repo_agent.core._load_frontmatter")
    def test_creates_config_with_minimal_frontmatter(self, mock_load, minimal_frontmatter):
        mock_load.return_value = (minimal_frontmatter, "test instructions")

        cfg, body = _resolve_config(Path("test.md"), {})

        assert cfg.repo_url == "https://github.com/user/repo.git"
        assert cfg.model == "openai/gpt-4"
        assert cfg.tool_name == "opencode"
        assert cfg.tool_entrypoint == "opencode run"
        assert body == "test instructions"

    @patch("repo_agent.core._load_frontmatter")
    def test_cli_overrides_take_precedence(self, mock_load, minimal_frontmatter):
        mock_load.return_value = (minimal_frontmatter, "content")
        overrides = {
            "repo_url": "https://github.com/override/repo.git",
            "model": "anthropic/claude-3",
            "branch": "custom-branch",
        }

        cfg, _ = _resolve_config(Path("test.md"), overrides)

        assert cfg.repo_url == "https://github.com/override/repo.git"
        assert cfg.model == "anthropic/claude-3"
        assert cfg.branch == "custom-branch"

    @patch("repo_agent.core._load_frontmatter")
    def test_generates_default_branch_name(self, mock_load, minimal_frontmatter):
        mock_load.return_value = (minimal_frontmatter, "content")

        cfg, _ = _resolve_config(Path("test.md"), {})

        assert cfg.branch.startswith("auto/repo-agent-")

    @patch("repo_agent.core._load_frontmatter")
    def test_validates_strategy_values(self, mock_load, minimal_frontmatter):
        minimal_frontmatter["strategy"] = "invalid"
        mock_load.return_value = (minimal_frontmatter, "content")

        with pytest.raises(RepoAgentError, match="strategy must be 'agentic' or 'direct'"):
            _resolve_config(Path("test.md"), {})

    @patch("repo_agent.core._load_frontmatter")
    def test_resolves_github_token_from_env(self, mock_load, minimal_frontmatter, monkeypatch):
        minimal_frontmatter["github_token_env"] = "MY_TOKEN"
        monkeypatch.setenv("MY_TOKEN", "ghp_test_token")
        mock_load.return_value = (minimal_frontmatter, "content")

        cfg, _ = _resolve_config(Path("test.md"), {})

        assert cfg.github_token == "ghp_test_token"

    @patch("repo_agent.core._load_frontmatter")
    def test_resolves_dockerfile_path(self, mock_load, minimal_frontmatter, tmp_path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM ubuntu")
        instructions_file = tmp_path / "instructions.md"
        minimal_frontmatter["dockerfile"] = "Dockerfile"
        mock_load.return_value = (minimal_frontmatter, "content")

        cfg, _ = _resolve_config(instructions_file, {})

        assert cfg.dockerfile == dockerfile

    @patch("repo_agent.core._load_frontmatter")
    def test_parses_all_boolean_flags(self, mock_load, minimal_frontmatter):
        minimal_frontmatter.update(
            {
                "auto_commit": False,
                "create_pr": False,
                "create_repo_if_missing": True,
                "use_ssh": True,
            }
        )
        mock_load.return_value = (minimal_frontmatter, "content")

        cfg, _ = _resolve_config(Path("test.md"), {})

        assert cfg.auto_commit is False
        assert cfg.create_pr is False
        assert cfg.create_repo_if_missing is True
        assert cfg.use_ssh is True


class TestDockerBuildIfNeeded:
    """Test _docker_build_if_needed function."""

    def test_skips_build_when_no_dockerfile(self):
        cfg = Mock()
        cfg.dockerfile = None

        # Should not raise any errors
        _docker_build_if_needed(cfg)

    @patch("repo_agent.core.subprocess.run")
    def test_builds_dockerfile_when_provided(self, mock_run, tmp_path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM ubuntu")

        cfg = Mock()
        cfg.dockerfile = dockerfile
        cfg.docker_image = "test-image"

        _docker_build_if_needed(cfg)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "build" in args
        assert "-t" in args
        assert "test-image" in args


class TestBuildDockerRunCmd:
    """Test _build_docker_run_cmd function."""

    @pytest.fixture
    def minimal_config(self, tmp_path):
        cfg = RunConfig(
            instructions_path=Path("test.md"),
            repo_url="https://github.com/user/repo.git",
            base_branch="main",
            branch="test-branch",
            docker_image="test-image",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token="ghp_test",
            api_key=None,
            git_user_name="Test User",
            git_user_email="test@example.com",
            model="gpt-4",
            strategy="agentic",
            pr_title="Test PR",
            pr_body="Test body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="test commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Test agentic",
            prompt_header_direct="Test direct",
            dry_run=False,
        )
        return cfg

    def test_builds_basic_docker_command(self, minimal_config, tmp_path):
        workdir = tmp_path / "work"
        workdir.mkdir()
        instructions = tmp_path / "instructions.txt"
        instructions.write_text("test")

        cmd = _build_docker_run_cmd(minimal_config, workdir, instructions)

        assert "docker" in cmd
        assert "run" in cmd
        assert "--rm" in cmd
        assert minimal_config.docker_image in cmd
        assert "bash" in cmd

    def test_includes_environment_variables(self, minimal_config, tmp_path):
        workdir = tmp_path / "work"
        workdir.mkdir()
        instructions = tmp_path / "instructions.txt"
        instructions.write_text("test")

        cmd = _build_docker_run_cmd(minimal_config, workdir, instructions)
        cmd_str = " ".join(cmd)

        assert "REPO_URL" in cmd_str
        assert "MODEL" in cmd_str
        assert "GITHUB_TOKEN" in cmd_str
        assert "STRATEGY" in cmd_str

    def test_includes_tool_args_when_provided(self, minimal_config, tmp_path):
        minimal_config.tool_args = {"temperature": "0.7", "max-tokens": "1000"}
        workdir = tmp_path / "work"
        workdir.mkdir()
        instructions = tmp_path / "instructions.txt"
        instructions.write_text("test")

        cmd = _build_docker_run_cmd(minimal_config, workdir, instructions)
        cmd_str = " ".join(cmd)

        assert "TOOL_EXTRA_ARGS" in cmd_str

    def test_mounts_ssh_keys_when_use_ssh_enabled(self, minimal_config, tmp_path):
        minimal_config.use_ssh = True
        minimal_config.ssh_key_dir = tmp_path / ".ssh"
        minimal_config.ssh_key_dir.mkdir()

        workdir = tmp_path / "work"
        workdir.mkdir()
        instructions = tmp_path / "instructions.txt"
        instructions.write_text("test")

        cmd = _build_docker_run_cmd(minimal_config, workdir, instructions)
        cmd_str = " ".join(cmd)

        assert ".ssh" in cmd_str


class TestRunFromMarkdown:
    """Test run_from_markdown function."""

    @pytest.fixture
    def test_instructions_file(self, tmp_path):
        instructions = tmp_path / "test.md"
        instructions.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Test instructions
""")
        return instructions

    def test_raises_error_for_nonexistent_file(self):
        with pytest.raises(RepoAgentError, match="Instructions markdown not found"):
            run_from_markdown(Path("nonexistent.md"))

    @patch("repo_agent.core._resolve_config")
    @patch("repo_agent.core._docker_build_if_needed")
    @patch("repo_agent.core._build_docker_run_cmd")
    def test_dry_run_prints_command(
        self, mock_build_cmd, mock_build, mock_resolve, test_instructions_file, capsys
    ):
        mock_cfg = Mock()
        mock_cfg.dry_run = True
        mock_resolve.return_value = (mock_cfg, "content")
        mock_build_cmd.return_value = ["docker", "run", "test"]

        run_from_markdown(test_instructions_file, dry_run=True)

        captured = capsys.readouterr()
        assert "dry run" in captured.out.lower()
        assert "docker" in captured.out

    @patch("repo_agent.core._resolve_config")
    @patch("repo_agent.core._docker_build_if_needed")
    @patch("repo_agent.core._build_docker_run_cmd")
    @patch("repo_agent.core.subprocess.run")
    def test_executes_docker_command(
        self, mock_run, mock_build_cmd, mock_build, mock_resolve, test_instructions_file
    ):
        mock_cfg = Mock()
        mock_cfg.dry_run = False
        mock_resolve.return_value = (mock_cfg, "content")
        mock_build_cmd.return_value = ["docker", "run", "test"]

        run_from_markdown(test_instructions_file)

        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["docker", "run", "test"]
        assert mock_run.call_args[1]["check"] is True

    @patch("repo_agent.core._build_docker_run_cmd")
    @patch("repo_agent.core._resolve_config")
    @patch("repo_agent.core._docker_build_if_needed")
    def test_creates_temporary_directory(
        self, mock_build, mock_resolve, mock_cmd, test_instructions_file
    ):
        mock_cfg = Mock()
        mock_cfg.dry_run = True
        mock_resolve.return_value = (mock_cfg, "content")
        mock_cmd.return_value = ["docker", "run", "test"]

        run_from_markdown(test_instructions_file, dry_run=True)

        # Verify temporary directory handling (implicitly tested via execution)
        mock_resolve.assert_called_once()
        # Verify docker command was built with temp directory
        assert mock_cmd.called


class TestRunConfig:
    """Test RunConfig dataclass."""

    def test_creates_config_with_all_fields(self):
        cfg = RunConfig(
            instructions_path=Path("test.md"),
            repo_url="https://github.com/user/repo.git",
            base_branch="main",
            branch="feature",
            docker_image="test:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token="token",
            api_key=None,
            git_user_name="user",
            git_user_email="user@example.com",
            model="gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="msg",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="agentic",
            prompt_header_direct="direct",
            dry_run=False,
        )

        assert cfg.repo_url == "https://github.com/user/repo.git"
        assert cfg.model == "gpt-4"
        assert cfg.strategy == "agentic"
        assert cfg.create_repo_if_missing is False
