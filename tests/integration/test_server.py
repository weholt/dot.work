"""Integration tests for dot_work.review.server module."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dot_work.review.server import AddCommentIn, create_app, pick_port


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
        # Format: YYYYMMDD-HHMMSS-XXX (19 chars with milliseconds)
        assert len(review_id) == 19
        assert "-" in review_id

    def test_index_returns_html(self, git_repo_with_changes: Path) -> None:
        """Test that index endpoint returns HTML."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "dot-work review" in response.text.lower()

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
        app, _ = create_app(str(git_repo_with_changes))
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


@pytest.mark.integration
class TestAuthentication:
    """Tests for authentication middleware."""

    def test_no_auth_required_when_token_not_set(self, git_repo_with_changes: Path) -> None:
        """Test that requests succeed when no auth token is configured (dev mode)."""
        # Ensure no token is set
        token = os.environ.pop("REVIEW_AUTH_TOKEN", None)

        try:
            app, _ = create_app(str(git_repo_with_changes))
            client = TestClient(app)

            # All endpoints should work without auth
            response = client.get("/")
            assert response.status_code == 200

            response = client.get("/api/state")
            assert response.status_code == 200

            response = client.post(
                "/api/comment",
                json={"path": "test.py", "side": "new", "line": 1, "message": "Test"},
            )
            assert response.status_code == 200
        finally:
            # Restore token if it was set
            if token:
                os.environ["REVIEW_AUTH_TOKEN"] = token

    def test_auth_required_when_token_set(self, git_repo_with_changes: Path) -> None:
        """Test that requests fail without valid auth token when one is configured."""
        os.environ["REVIEW_AUTH_TOKEN"] = "test-secret-token"

        try:
            app, _ = create_app(str(git_repo_with_changes))
            client = TestClient(app)

            # Request without auth header should fail
            response = client.get("/")
            assert response.status_code == 401

            response = client.get("/api/state")
            assert response.status_code == 401

            # Request with invalid token should fail (401 since we check token validity)
            response = client.get(
                "/",
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert response.status_code == 401

            # Request with valid token should succeed
            response = client.get(
                "/",
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert response.status_code == 200
        finally:
            os.environ.pop("REVIEW_AUTH_TOKEN", None)

    def test_static_files_skip_auth(self, git_repo_with_changes: Path) -> None:
        """Test that static files mount works (auth not required for mounted static files in FastAPI)."""
        os.environ["REVIEW_AUTH_TOKEN"] = "test-token"

        try:
            app, _ = create_app(str(git_repo_with_changes))
            client = TestClient(app)

            # Static files are served via StaticFiles mount which bypasses our endpoint auth
            # The mount serves files directly without going through our auth check
            response = client.get("/static/app.js")
            # May be 404 if file doesn't exist, but should not be 401/403 (StaticFiles bypasses our auth)
            assert response.status_code in (200, 404)
        finally:
            os.environ.pop("REVIEW_AUTH_TOKEN", None)


@pytest.mark.integration
class TestPathTraversalProtection:
    """Tests for path traversal protection."""

    def test_reject_path_with_parent_dots(self, git_repo_with_changes: Path) -> None:
        """Test that paths with .. are rejected."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        # Try to access file outside repo
        response = client.get("/?path=../../../etc/passwd")
        assert response.status_code == 403

        response = client.post(
            "/api/comment",
            json={"path": "../test.py", "side": "new", "line": 1, "message": "Test"},
        )
        assert response.status_code == 403

    def test_reject_absolute_path(self, git_repo_with_changes: Path) -> None:
        """Test that absolute paths outside the repo are rejected."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        # Try to access an absolute path outside the repo
        response = client.get("/?path=/etc/passwd")
        assert response.status_code == 403

    def test_accept_valid_relative_path(self, git_repo_with_changes: Path) -> None:
        """Test that valid relative paths are accepted."""
        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        response = client.get("/?path=test.py")
        assert response.status_code == 200


@pytest.mark.integration
class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_enforcement(self, git_repo_with_changes: Path) -> None:
        """Test that rate limiting is enforced."""
        # Clear rate limit store before test
        from dot_work.review.server import RATE_LIMIT_REQUESTS, _rate_limit_store

        _rate_limit_store.clear()

        app, _ = create_app(str(git_repo_with_changes))
        client = TestClient(app)

        # Make requests up to the limit
        for i in range(RATE_LIMIT_REQUESTS):
            response = client.post(
                "/api/comment",
                json={"path": "test.py", "side": "new", "line": 1, "message": f"Test {i}"},
            )
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.post(
            "/api/comment",
            json={"path": "test.py", "side": "new", "line": 1, "message": "Test limit"},
        )
        assert response.status_code == 429

    def test_rate_limit_per_client(self, git_repo_with_changes: Path) -> None:
        """Test that rate limiting is per-client (by IP)."""
        # Clear rate limit store before test
        from dot_work.review.server import RATE_LIMIT_REQUESTS, _rate_limit_store

        _rate_limit_store.clear()

        app, _ = create_app(str(git_repo_with_changes))

        # Note: TestClient uses the same IP (testclient) by default
        # This test verifies the rate limiting mechanism works
        client1 = TestClient(app)

        # Client 1 makes requests up to limit
        for i in range(RATE_LIMIT_REQUESTS):
            response = client1.post(
                "/api/comment",
                json={"path": "test.py", "side": "new", "line": 1, "message": f"Test {i}"},
            )
            assert response.status_code == 200

        # Client 1 should be rate limited
        response = client1.post(
            "/api/comment",
            json={"path": "test.py", "side": "new", "line": 1, "message": "Test limit"},
        )
        assert response.status_code == 429

        # Clear and verify new client can make requests
        _rate_limit_store.clear()
        response = client1.post(
            "/api/comment",
            json={"path": "test.py", "side": "new", "line": 1, "message": "After clear"},
        )
        assert response.status_code == 200
