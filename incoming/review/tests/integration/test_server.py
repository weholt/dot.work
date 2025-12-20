"""Integration tests for agent_review.server module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_review.server import AddCommentIn, create_app, pick_port


@pytest.fixture
def git_repo_with_changes(temp_dir: Path) -> Path:
    """Create a git repo with uncommitted changes."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    # Create initial file and commit
    test_file = temp_dir / "test.py"
    test_file.write_text("# Initial content\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    # Make changes
    test_file.write_text("# Modified content\nprint('hello world')\n")

    return temp_dir


class TestPickPort:
    """Tests for pick_port function."""

    def test_returns_provided_port(self) -> None:
        """Test that provided port is returned."""
        assert pick_port(8080) == 8080
        assert pick_port(3000) == 3000

    def test_picks_free_port_on_zero(self) -> None:
        """Test that a free port is picked when 0 is provided."""
        port = pick_port(0)
        assert port > 0
        assert port < 65536

    def test_picks_free_port_on_none(self) -> None:
        """Test that a free port is picked when None is provided."""
        port = pick_port(None)
        assert port > 0
        assert port < 65536


class TestAddCommentIn:
    """Tests for AddCommentIn model."""

    def test_create_comment_input(self) -> None:
        """Test creating comment input model."""
        inp = AddCommentIn(
            path="test.py",
            line=10,
            message="Fix this",
        )
        assert inp.path == "test.py"
        assert inp.side == "new"  # default
        assert inp.line == 10
        assert inp.message == "Fix this"
        assert inp.suggestion is None

    def test_comment_input_with_suggestion(self) -> None:
        """Test comment input with suggestion."""
        inp = AddCommentIn(
            path="test.py",
            side="old",
            line=5,
            message="Change this",
            suggestion="new code",
        )
        assert inp.side == "old"
        assert inp.suggestion == "new code"


@pytest.mark.integration
class TestCreateApp:
    """Integration tests for create_app function."""

    def test_creates_app_and_review_id(self, git_repo_with_changes: Path) -> None:
        """Test that create_app returns app and review ID."""
        app, review_id = create_app(str(git_repo_with_changes))
        assert app is not None
        assert review_id is not None
        assert len(review_id) == 15  # YYYYMMDD-HHMMSS

    def test_index_returns_html(self, git_repo_with_changes: Path) -> None:
        """Test that index endpoint returns HTML."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "agent-review" in response.text

    def test_state_endpoint(self, git_repo_with_changes: Path) -> None:
        """Test the state API endpoint."""
        app, review_id = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.get("/api/state")
        assert response.status_code == 200
        data = response.json()
        assert data["review_id"] == review_id
        assert data["base_ref"] == "HEAD"
        assert "tracked_files" in data
        assert "changed_files" in data

    def test_add_comment_endpoint(self, git_repo_with_changes: Path) -> None:
        """Test adding a comment via API."""
        app, review_id = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.post(
            "/api/comment",
            json={
                "path": "test.py",
                "side": "new",
                "line": 1,
                "message": "Test comment",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "id" in data

    def test_index_with_file_path(self, git_repo_with_changes: Path) -> None:
        """Test index with specific file path."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.get("/?path=test.py")
        assert response.status_code == 200
        assert "test.py" in response.text
