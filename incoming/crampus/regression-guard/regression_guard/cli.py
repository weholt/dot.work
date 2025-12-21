#!/usr/bin/env python3
"""
Main CLI entry point for Regression Guard.
"""

import argparse
import sys

from regression_guard.orchestrator import RegressionOrchestrator


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Regression Guard - Prevent regressions through iterative validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start new task
  regression-guard start "Add new feature"
  
  # Validate subtask
  regression-guard validate subtask-1-create
  
  # Finalize task
  regression-guard finalize task-20251125-120000
  
  # Show task status
  regression-guard status task-20251125-120000
  
  # List all tasks
  regression-guard list

For more information, see: https://github.com/your-username/regression-guard
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start new task")
    start_parser.add_argument("description", help="Task description")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate subtask")
    validate_parser.add_argument("subtask_id", help="Subtask ID to validate")
    validate_parser.add_argument("--task-id", help="Task ID (auto-detected if omitted)")

    # Finalize command
    finalize_parser = subparsers.add_parser("finalize", help="Finalize task")
    finalize_parser.add_argument("task_id", help="Task ID to finalize")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show task status")
    status_parser.add_argument("task_id", help="Task ID")

    # List command
    subparsers.add_parser("list", help="List all tasks")

    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--work-dir", help="Custom work directory (default: .work/tasks)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    orchestrator = RegressionOrchestrator(verbose=args.verbose, work_dir=args.work_dir)

    if args.command == "start":
        task_id = orchestrator.start_task(args.description)
        return 0 if task_id else 1

    elif args.command == "validate":
        success = orchestrator.validate_subtask(args.subtask_id, args.task_id)
        return 0 if success else 1

    elif args.command == "finalize":
        success = orchestrator.finalize_task(args.task_id)
        return 0 if success else 1

    elif args.command == "status":
        orchestrator.show_status(args.task_id)
        return 0

    elif args.command == "list":
        orchestrator.list_tasks()
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
