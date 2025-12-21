#!/usr/bin/env python3
"""
Task Decomposer - Breaks user requests into atomic subtasks.

Uses LLM to analyze task and generate structured subtask manifest.
Each subtask is atomic, testable, and has clear success criteria.

Usage:
    python scripts/decompose_task.py <task_id> <description>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


class TaskDecomposer:
    """Decomposes tasks into atomic, testable subtasks."""

    def __init__(self, task_id: str, description: str, verbose: bool = False):
        self.task_id = task_id
        self.description = description
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.work_dir = self.project_root / ".work" / "tasks"
        self.task_dir = self.work_dir / task_id
        self.task_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        if self.verbose or level == "ERROR":
            prefix = {"INFO": "[*]", "ERROR": "[-]", "WARN": "[!]"}.get(level, "[*]")
            print(f"{prefix} {message}")

    def decompose(self) -> dict:
        """Decompose task into subtasks."""
        self.log(f"Decomposing task: {self.description}")

        # For MVP, use rule-based decomposition
        # Later: integrate with LLM for intelligent decomposition
        subtasks = self._rule_based_decompose()

        manifest = {
            "task_id": self.task_id,
            "description": self.description,
            "timestamp": datetime.now().isoformat(),
            "subtasks": subtasks,
        }

        # Save manifest
        manifest_path = self.task_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        self.log(f"Manifest saved: {manifest_path}")

        return manifest

    def _rule_based_decompose(self) -> list[dict]:
        """Rule-based task decomposition."""
        # Analyze description for keywords
        description_lower = self.description.lower()

        subtasks = []

        # Always start with planning subtask
        subtasks.append({
            "id": "subtask-0-plan",
            "description": f"Plan implementation approach for: {self.description}",
            "dependencies": [],
            "files_affected": ["(to be determined)"],
            "tests_required": [],
            "baseline_tests": ["tests/"],
            "estimated_risk": "low",
        })

        # Detect common patterns
        if any(word in description_lower for word in ["add", "create", "new"]):
            subtasks.append({
                "id": "subtask-1-create",
                "description": "Create new files/functions",
                "dependencies": ["subtask-0-plan"],
                "files_affected": ["(to be determined)"],
                "tests_required": [
                    {
                        "type": "unit",
                        "path": "(to be determined)",
                        "description": "Test new functionality",
                    }
                ],
                "baseline_tests": ["tests/unittests/"],
                "estimated_risk": "medium",
            })

        if any(word in description_lower for word in ["modify", "change", "update", "fix"]):
            subtasks.append({
                "id": "subtask-2-modify",
                "description": "Modify existing files/functions",
                "dependencies": ["subtask-0-plan"],
                "files_affected": ["(to be determined)"],
                "tests_required": [
                    {
                        "type": "unit",
                        "path": "(to be determined)",
                        "description": "Test modified functionality",
                    }
                ],
                "baseline_tests": ["tests/unittests/"],
                "estimated_risk": "high",
            })

        if any(word in description_lower for word in ["test", "coverage"]):
            subtasks.append({
                "id": "subtask-3-test",
                "description": "Add/update tests",
                "dependencies": list({s["id"] for s in subtasks if s["id"] != "subtask-0-plan"}),
                "files_affected": ["tests/"],
                "tests_required": [
                    {
                        "type": "unit",
                        "path": "(to be determined)",
                        "description": "Verify test coverage",
                    }
                ],
                "baseline_tests": ["tests/"],
                "estimated_risk": "low",
            })

        if any(word in description_lower for word in ["document", "docs"]):
            subtasks.append({
                "id": "subtask-4-docs",
                "description": "Update documentation",
                "dependencies": list({s["id"] for s in subtasks}),
                "files_affected": ["solace/docs/", "README.md"],
                "tests_required": [],
                "baseline_tests": [],
                "estimated_risk": "low",
            })

        # Always end with integration validation
        subtasks.append({
            "id": "subtask-final-integration",
            "description": "Validate system integration",
            "dependencies": [s["id"] for s in subtasks if "final" not in s["id"]],
            "files_affected": [],
            "tests_required": [
                {
                    "type": "integration",
                    "path": "tests/integration/",
                    "description": "Run full integration test suite",
                }
            ],
            "baseline_tests": ["tests/integration/", "tests/e2e/"],
            "estimated_risk": "medium",
        })

        return subtasks


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Decompose task into subtasks")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("description", help="Task description")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    decomposer = TaskDecomposer(args.task_id, args.description, args.verbose)
    manifest = decomposer.decompose()

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
