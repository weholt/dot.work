import pytest
from repo_agent.core import RepoAgentError
from repo_agent.validation import validate_instructions


class TestValidateInstructions:
    """Test validate_instructions function."""

    @pytest.fixture
    def valid_frontmatter(self):
        return {
            "repo_url": "https://github.com/user/repo.git",
            "model": "gpt-4",
            "github_token_env": "GITHUB_TOKEN",
            "tool": {"name": "opencode", "entrypoint": "opencode run"},
        }

    @pytest.fixture
    def valid_instructions_file(self, tmp_path, valid_frontmatter):
        file = tmp_path / "valid.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Valid instructions
""")
        return file

    def test_validates_correct_file(self, valid_instructions_file):
        # Should not raise any exception
        validate_instructions(valid_instructions_file)

    def test_detects_missing_repo_url(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        with pytest.raises(RepoAgentError, match="repo_url"):
            validate_instructions(file)

    def test_detects_missing_model(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        with pytest.raises(RepoAgentError, match="model"):
            validate_instructions(file)

    def test_detects_missing_tool_section(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
---
Content
""")

        with pytest.raises(RepoAgentError, match="tool"):
            validate_instructions(file)

    def test_detects_missing_tool_name(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  entrypoint: "opencode run"
---
Content
""")

        with pytest.raises(RepoAgentError, match="name"):
            validate_instructions(file)

    def test_detects_missing_tool_entrypoint(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
---
Content
""")

        with pytest.raises(RepoAgentError, match="entrypoint"):
            validate_instructions(file)

    def test_validates_strategy_values(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
strategy: "invalid_strategy"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        with pytest.raises(RepoAgentError, match="strategy"):
            validate_instructions(file)

    def test_accepts_valid_agentic_strategy(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
strategy: "agentic"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        # Should not raise
        validate_instructions(file)

    def test_accepts_valid_direct_strategy(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
strategy: "direct"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        # Should not raise
        validate_instructions(file)

    def test_validates_authentication_configuration(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
use_ssh: true
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        # Should not raise
        validate_instructions(file)

    def test_validates_dockerfile_path(self, tmp_path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM ubuntu")

        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
dockerfile: "Dockerfile"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        # Should not raise
        validate_instructions(file)

    def test_detects_missing_dockerfile(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
dockerfile: "NonexistentDockerfile"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
---
Content
""")

        with pytest.raises(RepoAgentError, match="Dockerfile"):
            validate_instructions(file)

    def test_handles_nonexistent_file(self, tmp_path):
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises((RepoAgentError, FileNotFoundError)):
            validate_instructions(nonexistent)

    def test_accumulates_multiple_errors(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
strategy: "invalid"
---
Content
""")

        # Will raise on first error (repo_url missing)
        with pytest.raises(RepoAgentError):
            validate_instructions(file)

    def test_validates_tool_args_structure(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("""---
repo_url: "https://github.com/user/repo.git"
model: "gpt-4"
github_token_env: "GITHUB_TOKEN"
tool:
  name: "opencode"
  entrypoint: "opencode run"
  args:
    temperature: "0.7"
    max_tokens: "1000"
---
Content
""")

        # Should not raise
        validate_instructions(file)
