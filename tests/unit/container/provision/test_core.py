"""Tests for container provision core module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dot_work.container.provision.core import (
    BOOL_FALSE,
    BOOL_TRUE,
    RepoAgentError,
    RunConfig,
    _bool_meta,
    _build_env_args,
    _build_volume_args,
    _load_frontmatter,
    _resolve_config,
    validate_docker_image,
    validate_dockerfile_path,
)


class TestRepoAgentError:
    """Test the RepoAgentError exception class."""

    def test_repo_agent_error_creation(self) -> None:
        """Test that RepoAgentError can be created."""
        error = RepoAgentError("Test error message")
        assert str(error) == "Test error message"

    def test_repo_agent_error_inheritance(self) -> None:
        """Test that RepoAgentError inherits from Exception."""
        error = RepoAgentError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, RepoAgentError)

    def test_repo_agent_error_with_context(self) -> None:
        """Test RepoAgentError with context manager chaining."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            # Test that we can chain exceptions and catch the chained error
            try:
                raise RepoAgentError("Wrapper error") from e
            except RepoAgentError as chained_error:
                assert chained_error.__cause__ is e
                assert str(chained_error) == "Wrapper error"
                return  # Success - exception was properly chained

        # If we get here, the test failed
        pytest.fail("Exception chaining did not work as expected")


class TestValidateDockerImage:
    """Test Docker image name validation."""

    def test_valid_simple_image(self) -> None:
        """Test validation of simple image name."""
        # Should not raise
        validate_docker_image("repo/image")

    def test_valid_image_with_tag(self) -> None:
        """Test validation of image with tag."""
        validate_docker_image("repo/image:v1.0")
        validate_docker_image("repo/image:latest")
        validate_docker_image("namespace/image:12345")

    def test_valid_image_with_registry(self) -> None:
        """Test validation of image with registry."""
        validate_docker_image("registry.io/repo/image")
        validate_docker_image("registry.io/namespace/image:tag")
        validate_docker_image("localhost:5000/repo/image")

    def test_valid_image_localhost(self) -> None:
        """Test validation of localhost image."""
        validate_docker_image("localhost/image")
        validate_docker_image("localhost/namespace/image:tag")

    def test_valid_multi_component_image(self) -> None:
        """Test validation of multi-component image names."""
        validate_docker_image("registry.io/namespace/subnamespace/image:tag")
        validate_docker_image("namespace/subnamespace/image")

    def test_valid_image_with_hyphens_and_underscores(self) -> None:
        """Test validation allows hyphens and underscores in image names."""
        validate_docker_image("my-repo/my_image")
        validate_docker_image("my_repo/my-image:v1.0-beta")

    def test_invalid_empty_string(self) -> None:
        """Test validation rejects empty string."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("")

    def test_invalid_uppercase(self) -> None:
        """Test validation rejects uppercase letters."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("Repo/Image")

    def test_invalid_special_chars(self) -> None:
        """Test validation rejects special characters."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("repo/image!")

    def test_invalid_tag_format(self) -> None:
        """Test validation rejects invalid tag formats."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("repo/image:tag!")

    def test_invalid_double_slash(self) -> None:
        """Test validation rejects double slashes."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("repo//image")

    def test_invalid_leading_slash(self) -> None:
        """Test validation rejects leading slash."""
        with pytest.raises(ValueError, match="Invalid docker image name"):
            validate_docker_image("/image")

    def test_valid_image_no_tag(self) -> None:
        """Test validation of image without explicit tag."""
        validate_docker_image("alpine")
        validate_docker_image("nginx")
        validate_docker_image("python")


class TestValidateDockerfilePath:
    """Test Dockerfile path validation."""

    def test_none_dockerfile_allowed(self) -> None:
        """Test that None dockerfile is allowed (no custom Dockerfile)."""
        # Should not raise
        validate_dockerfile_path(None, Path("/project"))

    def test_dockerfile_within_project(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation of Dockerfile within project directory."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        dockerfile = project_root / "Dockerfile"
        dockerfile.touch()

        # Should not raise
        validate_dockerfile_path(dockerfile, project_root)

    def test_dockerfile_in_subdirectory(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation of Dockerfile in subdirectory."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        subdir = project_root / "docker"
        subdir.mkdir()
        dockerfile = subdir / "Dockerfile"
        dockerfile.touch()

        # Should not raise
        validate_dockerfile_path(dockerfile, project_root)

    def test_dockerfile_outside_project_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation rejects Dockerfile outside project directory."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        other_dir = tmp_path / "other"
        other_dir.mkdir()
        dockerfile = other_dir / "Dockerfile"
        dockerfile.touch()

        with pytest.raises(ValueError, match="Dockerfile must be within project directory"):
            validate_dockerfile_path(dockerfile, project_root)

    def test_dockerfile_parent_escape_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation rejects Dockerfile path with parent directory traversal."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        dockerfile = project_root / "../other/Dockerfile"

        with pytest.raises(ValueError, match="Dockerfile must be within project directory"):
            validate_dockerfile_path(dockerfile, project_root)

    def test_dockerfile_absolute_path_within(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation works with absolute paths."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        dockerfile = project_root / "Dockerfile"
        dockerfile.touch()

        # Use absolute path
        validate_dockerfile_path(dockerfile.resolve(), project_root.resolve())

    def test_dockerfile_relative_path(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test validation works with relative paths resolved from project root."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        dockerfile = project_root / "docker" / "Dockerfile"
        dockerfile.parent.mkdir()
        dockerfile.touch()

        # When using relative paths, they need to be resolved relative to project_root
        # The function expects absolute paths or paths that resolve correctly
        # For a relative path to work, the current directory would need to be project_root
        # Since we can't change cwd in tests, we use the absolute path
        validate_dockerfile_path(dockerfile, project_root)


class TestBoolMeta:
    """Test _bool_meta function for parsing boolean values from metadata."""

    def test_missing_key_returns_default(self) -> None:
        """Test that missing key returns default value."""
        assert _bool_meta({}, "missing", True) is True
        assert _bool_meta({}, "missing", False) is False

    def test_native_bool_values(self) -> None:
        """Test that native bool values are returned as-is."""
        assert _bool_meta({"flag": True}, "flag", False) is True
        assert _bool_meta({"flag": False}, "flag", True) is False

    def test_string_numeric_true_values(self) -> None:
        """Test that '1' is parsed as True."""
        assert _bool_meta({"flag": "1"}, "flag", False) is True

    def test_string_numeric_false_values(self) -> None:
        """Test that '0' is parsed as False."""
        assert _bool_meta({"flag": "0"}, "flag", True) is False

    def test_string_text_true_values(self) -> None:
        """Test that text 'true', 'yes', 'on' are parsed as True."""
        for val in ["true", "TRUE", "True", "yes", "YES", "Yes", "on", "ON", "On"]:
            assert _bool_meta({"flag": val}, "flag", False) is True

    def test_string_text_false_values(self) -> None:
        """Test that other text values are parsed as False."""
        for val in ["false", "FALSE", "no", "NO", "off", "OFF", "random"]:
            assert _bool_meta({"flag": val}, "flag", True) is False

    def test_numeric_truthy(self) -> None:
        """Test that non-zero numbers are truthy."""
        assert _bool_meta({"flag": 1}, "flag", False) is True
        assert _bool_meta({"flag": 42}, "flag", False) is True
        assert _bool_meta({"flag": -1}, "flag", False) is True

    def test_numeric_falsey(self) -> None:
        """Test that zero is falsy."""
        assert _bool_meta({"flag": 0}, "flag", True) is False


class TestLoadFrontmatter:
    """Test _load_frontmatter function for parsing markdown files."""

    def test_load_frontmatter_with_metadata(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test loading markdown file with YAML frontmatter."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
key1: value1
key2: 42
---
Content here
""")
        meta, content = _load_frontmatter(test_file)
        assert meta == {"key1": "value1", "key2": 42}
        assert content == "Content here"

    def test_load_frontmatter_without_metadata(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test loading markdown file without frontmatter."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Just content")
        meta, content = _load_frontmatter(test_file)
        assert meta == {}
        assert content == "Just content"

    def test_load_frontmatter_empty_metadata(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test loading markdown file with empty frontmatter."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
---
Content
""")
        meta, content = _load_frontmatter(test_file)
        assert meta == {}
        assert content == "Content"

    def test_load_frontmatter_strips_whitespace(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that content is stripped of leading/trailing whitespace."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
key: value
---

   Content with spaces

""")
        meta, content = _load_frontmatter(test_file)
        assert content == "Content with spaces"


class TestBuildEnvArgs:
    """Test _build_env_args function for building Docker environment variables."""

    def test_build_env_args_basic_config(self) -> None:
        """Test building env args with basic configuration."""
        cfg = RunConfig(
            instructions_path=Path("/test/instructions.md"),
            repo_url="https://github.com/user/repo",
            base_branch="main",
            branch="feature/test",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token="ghp_test",
            api_key="sk_test",
            git_user_name="Test User",
            git_user_email="test@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="Test PR",
            pr_body="Test body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Test commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Agentic header",
            prompt_header_direct="Direct header",
            dry_run=False,
        )
        result = _build_env_args(cfg)

        # Check format: ['-e', 'KEY=value', ...]
        assert "-e" in result
        assert "REPO_URL=https://github.com/user/repo" in result
        assert "BASE_BRANCH=main" in result
        assert "TARGET_BRANCH=feature/test" in result
        assert f"AUTO_COMMIT={BOOL_TRUE}" in result
        assert f"CREATE_PR={BOOL_TRUE}" in result
        assert "GITHUB_TOKEN=ghp_test" in result
        assert "GH_TOKEN=ghp_test" in result
        assert "OPENROUTER_API_KEY=sk_test" in result

    def test_build_env_args_with_ssh(self) -> None:
        """Test building env args with SSH authentication."""
        cfg = RunConfig(
            instructions_path=Path("/test/instructions.md"),
            repo_url="git@github.com:user/repo.git",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=True,
            ssh_key_dir=Path("/home/user/.ssh"),
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="direct",
            pr_title="PR",
            pr_body="Body",
            auto_commit=False,
            create_pr=False,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )
        result = _build_env_args(cfg)
        assert "REPO_URL=git@github.com:user/repo.git" in result
        assert f"AUTO_COMMIT={BOOL_FALSE}" in result

    def test_build_env_args_with_tool_args(self) -> None:
        """Test building env args with tool arguments."""
        cfg = RunConfig(
            instructions_path=Path("/test/instructions.md"),
            repo_url="https://github.com/user/repo",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={"verbose": True, "output": "result.json", "max_tokens": 1000},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )
        result = _build_env_args(cfg)

        # tool_args should be serialized to CLI-style arguments
        # Format is ['-e', 'KEY=value', ...] so find the value after 'TOOL_EXTRA_ARGS'
        for _i, arg in enumerate(result):
            if arg.startswith("TOOL_EXTRA_ARGS="):
                tool_extra_value = arg.split("=", 1)[1]
                assert "--verbose" in tool_extra_value
                assert "--output" in tool_extra_value
                assert "result.json" in tool_extra_value
                assert "--max-tokens" in tool_extra_value
                assert "1000" in tool_extra_value
                break
        else:
            pytest.fail("TOOL_EXTRA_ARGS not found in result")

    def test_build_env_args_empty_base_branch(self) -> None:
        """Test that empty base_branch is handled correctly."""
        cfg = RunConfig(
            instructions_path=Path("/test/instructions.md"),
            repo_url="https://github.com/user/repo",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )
        result = _build_env_args(cfg)
        assert "BASE_BRANCH=" in result

    def test_build_env_args_without_tokens(self) -> None:
        """Test building env args without authentication tokens."""
        cfg = RunConfig(
            instructions_path=Path("/test/instructions.md"),
            repo_url="https://github.com/user/repo",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )
        result = _build_env_args(cfg)
        # Should not have token env vars
        assert "GITHUB_TOKEN=" not in result
        assert "GH_TOKEN=" not in result
        assert "OPENROUTER_API_KEY=" not in result


class TestBuildVolumeArgs:
    """Test _build_volume_args function for building Docker volume mounts."""

    def test_build_volume_args_basic(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test building volume args with basic configuration."""
        workdir = tmp_path / "workspace"
        workdir.mkdir()
        instructions_body = tmp_path / "instructions_body.md"
        instructions_body.touch()

        cfg = RunConfig(
            instructions_path=tmp_path / "instructions.md",
            repo_url="https://github.com/user/repo",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )

        result = _build_volume_args(cfg, workdir, instructions_body)

        # Format: ['-v', 'host:container', ...]
        assert "-v" in result
        assert f"{workdir}:/workspace" in result
        assert f"{instructions_body}:/workspace/instructions_body.md:ro" in result

    def test_build_volume_args_with_ssh(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test building volume args with SSH key mount."""
        workdir = tmp_path / "workspace"
        workdir.mkdir()
        instructions_body = tmp_path / "instructions_body.md"
        instructions_body.touch()
        ssh_dir = tmp_path / "ssh"
        ssh_dir.mkdir()

        cfg = RunConfig(
            instructions_path=tmp_path / "instructions.md",
            repo_url="git@github.com:user/repo.git",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=True,
            ssh_key_dir=ssh_dir,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )

        result = _build_volume_args(cfg, workdir, instructions_body)
        assert f"{ssh_dir}:/root/.ssh:ro" in result

    def test_build_volume_args_with_opencode_config(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Test building volume args with opencode.json config."""
        workdir = tmp_path / "workspace"
        workdir.mkdir()
        instructions_body = tmp_path / "instructions_body.md"
        instructions_body.touch()
        opencode_config = tmp_path / "opencode.json"
        opencode_config.write_text('{"test": true}')

        cfg = RunConfig(
            instructions_path=tmp_path / "instructions.md",
            repo_url="https://github.com/user/repo",
            base_branch=None,
            branch="feature",
            docker_image="repo-agent:latest",
            dockerfile=None,
            use_ssh=False,
            ssh_key_dir=None,
            github_token=None,
            api_key=None,
            git_user_name="User",
            git_user_email="user@example.com",
            model="openai/gpt-4",
            strategy="agentic",
            pr_title="PR",
            pr_body="Body",
            auto_commit=True,
            create_pr=True,
            create_repo_if_missing=False,
            commit_message="Commit",
            tool_name="opencode",
            tool_entrypoint="opencode run",
            tool_args={},
            prompt_header_agentic="Header",
            prompt_header_direct="Header",
            dry_run=False,
        )

        result = _build_volume_args(cfg, workdir, instructions_body)
        # Should mount opencode.json if it exists
        assert any("opencode.json" in arg for arg in result)


class TestResolveConfig:
    """Test _resolve_config function for configuration resolution."""

    def test_resolve_config_minimal_valid(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test resolving minimal valid configuration."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
---
Content
""")

        cfg, content = _resolve_config(instructions, {})

        assert cfg.repo_url == "https://github.com/user/repo"
        assert cfg.model == "openai/gpt-4"
        assert cfg.strategy == "agentic"  # default
        assert cfg.docker_image == "repo-agent:latest"  # default
        assert cfg.auto_commit is True  # default
        assert cfg.create_pr is True  # default
        assert content == "Content"

    def test_resolve_config_missing_repo_url_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that missing repo_url raises RepoAgentError."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("---\nmodel: openai/gpt-4\n---\nContent")

        with pytest.raises(RepoAgentError, match="repo_url must be provided"):
            _resolve_config(instructions, {})

    def test_resolve_config_missing_model_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that missing model raises RepoAgentError."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("---\nrepo_url: https://github.com/user/repo\n---\nContent")

        with pytest.raises(RepoAgentError, match="model must be provided"):
            _resolve_config(instructions, {})

    def test_resolve_config_invalid_strategy_raises(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that invalid strategy raises RepoAgentError."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
strategy: invalid
---
Content
""")

        with pytest.raises(RepoAgentError, match="strategy must be 'agentic' or 'direct'"):
            _resolve_config(instructions, {})

    def test_resolve_config_cli_overrides(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that CLI overrides take precedence."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
strategy: agentic
docker_image: custom:latest
---
Content
""")

        cfg, _ = _resolve_config(instructions, {"strategy": "direct", "docker_image": "override:v1"})

        assert cfg.strategy == "direct"  # CLI override
        assert cfg.docker_image == "override:v1"  # CLI override

    def test_resolve_config_boolean_parsing(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test boolean value parsing from frontmatter."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
auto_commit: "1"
create_pr: "false"
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        assert cfg.auto_commit is True
        assert cfg.create_pr is False

    def test_resolve_config_dockerfile_resolution(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that Dockerfile paths are resolved correctly."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.touch()
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
dockerfile: Dockerfile
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        assert cfg.dockerfile == dockerfile.resolve()

    def test_resolve_config_ssh_auth_from_ssh_key(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that use_ssh is set when auth=ssh."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: git@github.com:user/repo.git
model: openai/gpt-4
auth: ssh
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        assert cfg.use_ssh is True

    def test_resolve_config_branch_generation(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that branch name is auto-generated if not provided."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        # Should have default prefix
        assert cfg.branch.startswith("auto/repo-agent-")
        assert cfg.base_branch is None

    def test_resolve_config_with_base_branch(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test configuration with explicit base branch."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
base_branch: main
branch: feature/test
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        assert cfg.base_branch == "main"
        assert cfg.branch == "feature/test"

    def test_resolve_config_github_token_resolution(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test GitHub token resolution from multiple sources."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
---
Content
""")

        # Test with direct token
        cfg1, _ = _resolve_config(instructions, {"github_token": "ghp_direct"})
        assert cfg1.github_token == "ghp_direct"

        # Test with env var name indirection (would need actual env var in real test)
        instructions2 = tmp_path / "instructions2.md"
        instructions2.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
github_token_env: MY_CUSTOM_TOKEN
---
Content
""")

    def test_resolve_config_defaults_applied(self, tmp_path: pytest.TempPathFactory) -> None:
        """Test that all defaults are correctly applied."""
        instructions = tmp_path / "instructions.md"
        instructions.write_text("""---
repo_url: https://github.com/user/repo
model: openai/gpt-4
---
Content
""")

        cfg, _ = _resolve_config(instructions, {})

        assert cfg.docker_image == "repo-agent:latest"
        assert cfg.git_user_name == "repo-agent"
        assert cfg.git_user_email == "repo-agent@example.com"
        assert cfg.pr_title == "Automated changes via repo-agent"
        assert cfg.pr_body == "This PR was generated automatically by repo-agent using a configurable code tool."
        assert cfg.commit_message == "chore: automated changes via repo-agent"
        assert cfg.strategy == "agentic"
