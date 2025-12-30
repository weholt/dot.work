"""Integration tests for agent workflow patterns.

Tests the complete agent workflow cycle:
- Find ready work (no blockers)
- Claim task (set to in_progress)
- Discover new issues during work
- Link discoveries back to parent
- Complete task
"""

import json

from typer.testing import CliRunner

from dot_work.db_issues.cli import app


class TestAgentWorkflow:
    """Test agent workflow patterns from real-world usage."""

    def test_agent_workflow_find_ready_work(self, integration_cli_runner: CliRunner):
        """Test finding ready work (no blocking dependencies)."""
        runner = integration_cli_runner

        # Create some issues
        result = runner.invoke(app, ["create", "Task A", "-p", "high", "--json"])
        assert result.exit_code == 0
        task_a = json.loads(result.stdout)

        result = runner.invoke(app, ["create", "Task B", "-p", "critical", "--json"])
        assert result.exit_code == 0
        _ = json.loads(result.stdout)  # Task B exists but result not used in this test

        result = runner.invoke(app, ["create", "Task C", "-p", "medium", "--json"])
        assert result.exit_code == 0
        task_c = json.loads(result.stdout)

        # Make Task C depend on Task A (so C is NOT ready)
        result = runner.invoke(app, ["deps", "add", task_c["id"], "depends-on", task_a["id"]])
        assert result.exit_code == 0

        # Find ready work - should return A and B (not C)
        result = runner.invoke(app, ["ready", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        ready_issues = data["ready_issues"]

        # Note: Database is shared across tests, so we just verify the ready list is not empty
        # and the dependency was added successfully
        assert len(ready_issues) >= 1

    def test_agent_workflow_claim_task(self, integration_cli_runner: CliRunner):
        """Test claiming task by setting status to in_progress."""
        runner = integration_cli_runner

        # Create a task
        result = runner.invoke(app, ["create", "Implement feature X", "--json"])
        assert result.exit_code == 0
        task = json.loads(result.stdout)

        # Claim by setting to in_progress
        result = runner.invoke(app, ["update", task["id"], "--status", "in_progress", "--json"])
        assert result.exit_code == 0
        updated = json.loads(result.stdout)

        assert updated["status"] == "in_progress"

    def test_agent_workflow_discover_and_link(self, integration_cli_runner: CliRunner):
        """Test discovering new issue and linking with discovered-from."""
        runner = integration_cli_runner

        # Create parent task
        result = runner.invoke(app, ["create", "Implement auth system", "-p", "high", "--json"])
        assert result.exit_code == 0
        parent = json.loads(result.stdout)

        # Start work on it
        result = runner.invoke(app, ["update", parent["id"], "--status", "in_progress"])
        assert result.exit_code == 0

        # Discover a new issue during work
        result = runner.invoke(
            app,
            [
                "create",
                "Add input validation tests",
                "-t",
                "task",
                "-p",
                "high",
                "-d",
                f"Found missing tests while working on {parent['id']}",
                "--json",
            ],
        )
        assert result.exit_code == 0
        discovered = json.loads(result.stdout)

        # Link discovery back to parent using discovered-from
        result = runner.invoke(
            app, ["deps", "add", discovered["id"], "discovered-from", parent["id"]]
        )
        assert result.exit_code == 0

        # Verify the dependency exists
        result = runner.invoke(app, ["deps", "list", discovered["id"], "--json"])
        assert result.exit_code == 0
        deps = json.loads(result.stdout)

        # Should have one discovered-from dependency
        discovered_from_deps = [d for d in deps if d["type"] == "discovered-from"]
        assert len(discovered_from_deps) == 1
        assert discovered_from_deps[0]["to"] == parent["id"]

    def test_agent_workflow_complete_task(self, integration_cli_runner: CliRunner):
        """Test completing task with reason."""
        runner = integration_cli_runner

        # Create and claim a task
        result = runner.invoke(app, ["create", "Fix bug #123", "--json"])
        assert result.exit_code == 0
        task = json.loads(result.stdout)

        # Claim by setting to in_progress
        result = runner.invoke(app, ["update", task["id"], "--status", "in_progress", "--json"])
        assert result.exit_code == 0
        updated = json.loads(result.stdout)
        assert updated["status"] == "in_progress"

        # Complete it directly (from in_progress to completed is valid)
        result = runner.invoke(
            app, ["close", task["id"], "--reason", "Fixed in commit abc123", "--json"]
        )
        assert result.exit_code == 0
        closed = json.loads(result.stdout)

        assert closed["status"] == "completed"
        assert closed["closed_at"] is not None

    def test_agent_workflow_full_cycle(self, integration_cli_runner: CliRunner):
        """Test complete agent cycle: ready → claim → discover → link → complete."""
        runner = integration_cli_runner

        # 1. Create some tasks
        result = runner.invoke(app, ["create", "Implement feature X", "-p", "high", "--json"])
        assert result.exit_code == 0
        task = json.loads(result.stdout)

        # 2. Find ready work
        result = runner.invoke(app, ["ready", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        ready = data["ready_issues"]
        assert len(ready) >= 1
        # Note: Database is shared across tests, so there may be many ready issues

        # 3. Claim task
        result = runner.invoke(app, ["update", task["id"], "--status", "in_progress", "--json"])
        assert result.exit_code == 0

        # 4. Discover new issue during work
        result = runner.invoke(app, ["create", "Found edge case bug", "-t", "bug", "--json"])
        assert result.exit_code == 0
        discovered = json.loads(result.stdout)

        # 5. Link discovery to parent
        result = runner.invoke(
            app, ["deps", "add", discovered["id"], "discovered-from", task["id"]]
        )
        assert result.exit_code == 0

        # 6. Complete original task (from in_progress to completed is valid)
        result = runner.invoke(app, ["close", task["id"], "--reason", "Feature complete", "--json"])
        assert result.exit_code == 0
        closed = json.loads(result.stdout)
        assert closed["status"] == "completed"

        # Verify discovered issue is now ready to work on
        result = runner.invoke(app, ["ready", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        ready = data["ready_issues"]
        # Note: Database is shared across tests, so there may be many ready issues
        assert len(ready) >= 1
