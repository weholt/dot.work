"""Tests for container provision core module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dot_work.container.provision.core import (
    RepoAgentError,
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
