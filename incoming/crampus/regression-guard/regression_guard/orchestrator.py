"""
Main orchestrator for the regression prevention workflow.
Coordinates task decomposition, validation, and reporting.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from regression_guard.capture_baseline import BaselineCapture
from regression_guard.decompose import TaskDecomposer
from regression_guard.validate_incremental import IncrementalValidator
from regression_guard.validate_integration import IntegrationValidator


class RegressionOrchestrator:
    """Main orchestrator for regression prevention workflow."""

    def __init__(self, verbose: bool = False, work_dir: str | None = None):
        self.verbose = verbose
        self.project_root = Path.cwd()

        if work_dir:
            self.work_dir = Path(work_dir)
        else:
            self.work_dir = self.project_root / ".work" / "tasks"

        self.work_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        prefix = {
            "INFO": "[*]",
            "SUCCESS": "[+]",
            "ERROR": "[-]",
            "WARN": "[!]",
        }.get(level, "[*]")
        print(f"{prefix} {message}")

    def generate_task_id(self) -> str:
        """Generate unique task ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"task-{timestamp}"

    def start_task(self, description: str) -> str | None:
        """Start new task: decompose and capture baseline."""
        self.log(f"Starting task: {description}")

        task_id = self.generate_task_id()
        task_dir = self.work_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"Task ID: {task_id}", "SUCCESS")
        self.log(f"Task directory: {task_dir}")

        # Step 1: Decompose task into subtasks
        self.log("Step 1: Decomposing task into subtasks...")
        try:
            decomposer = TaskDecomposer(task_id, description, self.verbose)
            decomposer.work_dir = self.work_dir
            manifest = decomposer.decompose()
            self.log("Task decomposed successfully", "SUCCESS")
        except Exception as e:
            self.log(f"Task decomposition failed: {e}", "ERROR")
            return None

        # Step 2: Capture baseline state
        self.log("Step 2: Capturing baseline state...")
        try:
            capturer = BaselineCapture(task_id, self.verbose)
            capturer.work_dir = self.work_dir
            capturer.project_root = self.project_root
            capturer.capture()  # Result stored in task directory for later use
            self.log("Baseline captured successfully", "SUCCESS")
        except Exception as e:
            self.log(f"Baseline capture failed: {e}", "ERROR")
            return None

        # Display task manifest
        self.print_manifest(manifest)

        self.log(f"\nTask {task_id} ready for implementation", "SUCCESS")
        self.log("Next: Implement subtasks and validate with:")
        self.log("  regression-guard validate <subtask-id>")

        return task_id

    def validate_subtask(self, subtask_id: str, task_id: str | None = None) -> bool:
        """Validate specific subtask implementation."""
        # Find task ID if not provided
        if not task_id:
            task_id = self.find_task_for_subtask(subtask_id)
            if not task_id:
                self.log(f"Could not find task for subtask: {subtask_id}", "ERROR")
                return False

        self.log(f"Validating subtask: {subtask_id} (task: {task_id})")

        # Run incremental validation
        try:
            validator = IncrementalValidator(task_id, subtask_id, self.verbose)
            validator.work_dir = self.work_dir
            validator.project_root = self.project_root
            success = validator.validate()
        except Exception as e:
            self.log(f"Validation error: {e}", "ERROR")
            return False

        if success:
            self.log(f"Subtask {subtask_id} validation PASSED", "SUCCESS")
        else:
            self.log(f"Subtask {subtask_id} validation FAILED", "ERROR")

        # Show validation report
        report_path = self.work_dir / task_id / subtask_id / "report.md"
        if report_path.exists():
            print("\n" + "=" * 80)
            print(report_path.read_text(encoding="utf-8"))
            print("=" * 80)

        return success

    def finalize_task(self, task_id: str) -> bool:
        """Run final integration validation."""
        self.log(f"Finalizing task: {task_id}")

        # Run integration validation
        try:
            validator = IntegrationValidator(task_id, self.verbose)
            validator.work_dir = self.work_dir
            validator.project_root = self.project_root
            success = validator.validate()
        except Exception as e:
            self.log(f"Integration validation error: {e}", "ERROR")
            return False

        if success:
            self.log(f"Task {task_id} integration validation PASSED", "SUCCESS")
            self.log("All changes validated successfully!")
        else:
            self.log(f"Task {task_id} integration validation FAILED", "ERROR")

        # Show final report
        report_path = self.work_dir / task_id / "final_report.md"
        if report_path.exists():
            print("\n" + "=" * 80)
            print(report_path.read_text(encoding="utf-8"))
            print("=" * 80)

        return success

    def show_status(self, task_id: str) -> None:
        """Show task status and progress."""
        task_dir = self.work_dir / task_id
        if not task_dir.exists():
            self.log(f"Task not found: {task_id}", "ERROR")
            return

        manifest_path = task_dir / "manifest.json"
        if not manifest_path.exists():
            self.log(f"Task manifest not found: {task_id}", "ERROR")
            return

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        print("\n" + "=" * 80)
        print(f"Task Status: {task_id}")
        print("=" * 80)
        print(f"Description: {manifest['description']}")
        print(f"Created: {manifest.get('timestamp', 'unknown')}")
        print(f"Subtasks: {len(manifest['subtasks'])}")

        print("\nProgress:")
        for subtask in manifest["subtasks"]:
            subtask_id = subtask["id"]
            status = self.get_subtask_status(task_id, subtask_id)
            status_icon = {"pending": "⏳", "passed": "✅", "failed": "❌"}.get(status, "❓")
            print(f"  {status_icon} {subtask_id}: {subtask['description']}")

        print("=" * 80 + "\n")

    def get_subtask_status(self, task_id: str, subtask_id: str) -> str:
        """Get validation status of subtask."""
        validation_path = self.work_dir / task_id / subtask_id / "validation.json"
        if not validation_path.exists():
            return "pending"

        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        return "passed" if validation.get("success") else "failed"

    def find_task_for_subtask(self, subtask_id: str) -> str | None:
        """Find task ID that contains the given subtask."""
        for task_dir in self.work_dir.iterdir():
            if not task_dir.is_dir():
                continue

            manifest_path = task_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for subtask in manifest.get("subtasks", []):
                if subtask["id"] == subtask_id:
                    return task_dir.name

        return None

    def print_manifest(self, manifest: dict[str, Any]) -> None:
        """Pretty-print task manifest."""
        print("\n" + "=" * 80)
        print("Task Manifest")
        print("=" * 80)
        print(f"Description: {manifest['description']}")
        print(f"Subtasks: {len(manifest['subtasks'])}")

        for i, subtask in enumerate(manifest["subtasks"], 1):
            print(f"\n{i}. {subtask['id']}")
            print(f"   Description: {subtask['description']}")
            print(f"   Risk: {subtask['estimated_risk']}")
            print(f"   Files: {', '.join(subtask['files_affected'])}")
            print(f"   Tests required: {len(subtask['tests_required'])}")

        print("=" * 80 + "\n")

    def list_tasks(self) -> None:
        """List all tasks."""
        tasks = []
        for task_dir in self.work_dir.iterdir():
            if not task_dir.is_dir():
                continue

            manifest_path = task_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                tasks.append(
                    {
                        "id": task_dir.name,
                        "description": manifest["description"],
                        "timestamp": manifest.get("timestamp", "unknown"),
                    }
                )

        if not tasks:
            self.log("No tasks found")
            return

        print("\n" + "=" * 80)
        print("All Tasks")
        print("=" * 80)
        for task in sorted(tasks, key=lambda t: t["timestamp"], reverse=True):
            print(f"{task['id']}: {task['description']}")
        print("=" * 80 + "\n")
