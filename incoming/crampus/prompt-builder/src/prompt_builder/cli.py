"""Command-line interface for the Prompt Builder multi-agent validation system."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
import json
from datetime import datetime

from .models import (
    Task,
    TaskStatus,
    ValidationResultSummary,
    AgentConfig,
)
from .agents import (
    PlannerAgent,
    StaticValidatorAgent,
    BehaviorValidatorAgent,
    RegressionSentinelAgent,
    SyntheticTestAgent,
    PRGeneratorAgent,
)
from .utils import setup_logging, load_config, save_config


# Create Typer app
app = typer.Typer(
    name="prompt-builder",
    help="Multi-agent validation system for preventing code regressions",
    no_args_is_help=True,
)

console = Console()


@app.command()
def start(
    task_description: str = typer.Argument(..., help="Description of the task to validate"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Task title"),
    base_ref: Optional[str] = typer.Option("HEAD~1", "--base", "-b", help="Base git reference for comparison"),
    head_ref: Optional[str] = typer.Option("HEAD", "--head", "-h", help="Head git reference for comparison"),
    config_file: Optional[str] = typer.Option("prompt-builder.toml", "--config", "-c", help="Configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    create_pr: bool = typer.Option(False, "--create-pr", help="Create pull request if all validations pass"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """Start a new validation task."""
    setup_logging(verbose)

    task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    task_title = title or task_description.split('.')[0].strip()

    console.print(f"[bold blue]Starting validation task:[/bold blue] {task_id}")
    console.print(f"[green]Title:[/green] {task_title}")
    console.print(f"[green]Base:[/green] {base_ref} → [green]Head:[/green] {head_ref}")
    console.print()

    # Create the task
    task = Task(
        id=task_id,
        title=task_title,
        description=task_description,
        base_ref=base_ref,
        head_ref=head_ref,
        status=TaskStatus.PENDING
    )

    if dry_run:
        console.print("[yellow]DRY RUN MODE[/yellow] - No actual validation will be performed")
        console.print(f"[dim]Would validate task: {task.title}[/dim]")
        return

    # Run the validation workflow
    try:
        validation_summary = asyncio.run(run_validation_workflow(task, create_pr))
        display_results(task, validation_summary)

        # Exit with appropriate code
        sys.exit(0 if validation_summary.overall_passed else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Validation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Validation failed with error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
def status(
    task_id: str = typer.Argument(..., help="Task ID to check status for"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """Check the status of a validation task."""
    setup_logging(verbose)

    # Look for task data
    task_file = Path(f".prompt-builder/tasks/{task_id}.json")
    if not task_file.exists():
        console.print(f"[red]Task {task_id} not found[/red]")
        sys.exit(1)

    try:
        with open(task_file, 'r') as f:
            task_data = json.load(f)

        task = Task(**task_data)
        display_task_status(task, verbose)

    except Exception as e:
        console.print(f"[red]Error loading task {task_id}:[/red] {e}")
        sys.exit(1)


@app.command()
def list_tasks(
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """List all validation tasks."""
    setup_logging(verbose)

    tasks_dir = Path(".prompt-builder/tasks")
    if not tasks_dir.exists():
        console.print("[yellow]No tasks found[/yellow]")
        return

    tasks = []
    for task_file in tasks_dir.glob("*.json"):
        try:
            with open(task_file, 'r') as f:
                task_data = json.load(f)
            task = Task(**task_data)

            if status_filter is None or task.status.value == status_filter:
                tasks.append(task)
        except Exception:
            continue

    if not tasks:
        console.print(f"[yellow]No tasks found"
                     f"{' with status ' + status_filter if status_filter else ''}[/yellow]")
        return

    display_task_list(tasks, verbose)


@app.command()
def validate(
    task_id: str = typer.Argument(..., help="Task ID to validate"),
    agents: Optional[List[str]] = typer.Option(None, "--agent", help="Specific agents to run"),
    create_pr: bool = typer.Option(False, "--create-pr", help="Create PR if validation passes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Run validation on an existing task."""
    setup_logging(verbose)

    # Load the task
    task_file = Path(f".prompt-builder/tasks/{task_id}.json")
    if not task_file.exists():
        console.print(f"[red]Task {task_id} not found[/red]")
        sys.exit(1)

    try:
        with open(task_file, 'r') as f:
            task_data = json.load(f)
        task = Task(**task_data)

        console.print(f"[bold blue]Validating task:[/bold blue] {task_id}")
        console.print(f"[green]Title:[/green] {task.title}")
        console.print()

        # Run validation
        validation_summary = asyncio.run(run_validation_workflow(task, create_pr, agents))
        display_results(task, validation_summary)

        sys.exit(0 if validation_summary.overall_passed else 1)

    except Exception as e:
        console.print(f"[red]Validation failed:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
def init(
    config_file: str = typer.Option("prompt-builder.toml", "--config", "-c", help="Configuration file"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration"),
):
    """Initialize a new prompt-builder project."""
    if Path(config_file).exists() and not force:
        console.print(f"[yellow]Configuration file {config_file} already exists[/yellow]")
        console.print("Use --force to overwrite")
        return

    # Create default configuration
    default_config = {
        "agents": {
            "planner": {"enabled": True, "timeout": 300},
            "static_validator": {"enabled": True, "timeout": 180},
            "behavior_validator": {"enabled": True, "timeout": 600},
            "regression_sentinel": {"enabled": True, "timeout": 240},
            "synthetic_test": {"enabled": True, "timeout": 300},
            "pr_generator": {"enabled": True, "timeout": 120}
        },
        "git": {
            "auto_push": False,
            "pr_auto_merge": False
        },
        "notifications": {
            "on_failure": True,
            "on_success": False
        }
    }

    try:
        # Create directories
        Path(".prompt-builder/tasks").mkdir(parents=True, exist_ok=True)
        Path(".prompt-builder/snapshots").mkdir(parents=True, exist_ok=True)

        # Save configuration
        import toml
        with open(config_file, 'w') as f:
            toml.dump(default_config, f)

        console.print(f"[green]✅[/green] Prompt Builder initialized successfully")
        console.print(f"[dim]Configuration saved to: {config_file}[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to initialize:[/red] {e}")
        sys.exit(1)


async def run_validation_workflow(
    task: Task,
    create_pr: bool = False,
    specific_agents: Optional[List[str]] = None
) -> ValidationResultSummary:
    """Run the complete validation workflow."""

    # Define agent execution order
    agent_configs = [
        ("planner", PlannerAgent),
        ("static_validator", StaticValidatorAgent),
        ("behavior_validator", BehaviorValidatorAgent),
        ("regression_sentinel", RegressionSentinelAgent),
        ("synthetic_test", SyntheticTestAgent),
        ("pr_generator", PRGeneratorAgent),
    ]

    # Filter agents if specified
    if specific_agents:
        agent_configs = [(name, cls) for name, cls in agent_configs if name in specific_agents]

    # Skip PR generator if not requested
    if not create_pr:
        agent_configs = [(name, cls) for name, cls in agent_configs if name != "pr_generator"]

    validation_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        # Execute agents
        for agent_name, agent_class in agent_configs:
            task_desc = f"Running {agent_name.replace('_', ' ').title()}..."
            task_progress = progress.add_task(task_desc, total=None)

            try:
                agent = agent_class()

                if agent_name == "planner":
                    # Run planner to get subtasks
                    result = await agent.execute(task)
                    if result.passed and task.subtasks:
                        # Run other agents for each subtask
                        for subtask in task.subtasks:
                            subtask.status = TaskStatus.IN_PROGRESS
                            # Other agents will be run for this subtask in the next phases

                elif agent_name == "pr_generator":
                    # PR generator needs validation summary context
                    context = {"validation_summary": ValidationResultSummary(
                        task_id=task.id,
                        total_validations=len(validation_results),
                        passed_validations=sum(1 for r in validation_results if r.passed),
                        failed_validations=sum(1 for r in validation_results if not r.passed),
                        validation_results=validation_results,
                        overall_passed=all(r.passed for r in validation_results),
                        execution_time=sum(r.execution_time for r in validation_results)
                    )}
                    result = await agent.execute(task, context=context)

                else:
                    # Other agents run on subtasks
                    if task.subtasks:
                        for subtask in task.subtasks:
                            subtask_result = await agent.execute(task, subtask)
                            validation_results.append(subtask_result)

                            # Update subtask status based on result
                            subtask.status = TaskStatus.COMPLETED if subtask_result.passed else TaskStatus.FAILED

                    result = ValidationResult(
                        validator_type=agent.get_validation_type(),
                        subtask_id=task.id,
                        passed=True,
                        issues=[],
                        warnings=[],
                        metrics={"subtasks_processed": len(task.subtasks) if task.subtasks else 0}
                    )

                validation_results.append(result)

                if result.passed:
                    progress.update(task_progress, description=f"✅ {task_desc}")
                else:
                    progress.update(task_progress, description=f"❌ {task_desc}")

            except Exception as e:
                progress.update(task_progress, description=f"💥 {task_desc}")
                validation_results.append(ValidationResult(
                    validator_type=agent.get_validation_type(),
                    subtask_id=task.id,
                    passed=False,
                    issues=[f"Agent execution failed: {str(e)}"]
                ))

        progress.stop()

    # Update task status
    task.completed_at = datetime.now()
    task.status = TaskStatus.COMPLETED if all(r.passed for r in validation_results) else TaskStatus.FAILED

    # Save task state
    save_task_state(task)

    # Create summary
    return ValidationResultSummary(
        task_id=task.id,
        total_validations=len(validation_results),
        passed_validations=sum(1 for r in validation_results if r.passed),
        failed_validations=sum(1 for r in validation_results if not r.passed),
        warnings=sum(r.warnings for r in validation_results, []),
        critical_issues=sum(r.issues for r in validation_results if not r.passed, []),
        validation_results=validation_results,
        overall_passed=all(r.passed for r in validation_results),
        execution_time=sum(r.execution_time for r in validation_results)
    )


def display_results(task: Task, summary: ValidationResultSummary):
    """Display validation results in a formatted table."""

    # Summary panel
    status_color = "green" if summary.overall_passed else "red"
    status_text = "✅ PASSED" if summary.overall_passed else "❌ FAILED"

    console.print(Panel(
        f"[{status_color} bold]{status_text}[/{status_color} bold]\n\n"
        f"Task: {task.title}\n"
        f"Total Validations: {summary.total_validations}\n"
        f"Passed: {summary.passed_validations}\n"
        f"Failed: {summary.failed_validations}\n"
        f"Execution Time: {summary.execution_time:.2f}s",
        title="Validation Summary",
        border_style=status_color
    ))

    # Detailed results table
    table = Table(title="Validation Details")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Issues", style="red")
    table.add_column("Warnings", style="yellow")
    table.add_column("Time", style="blue")

    for result in summary.validation_results:
        status = "✅" if result.passed else "❌"
        issues_text = f"{len(result.issues)}" if result.issues else "None"
        warnings_text = f"{len(result.warnings)}" if result.warnings else "None"

        table.add_row(
            result.validator_type.value,
            status,
            issues_text,
            warnings_text,
            f"{result.execution_time:.2f}s"
        )

    console.print(table)

    # Show critical issues if any
    if summary.critical_issues:
        console.print("\n[bold red]Critical Issues:[/bold red]")
        for issue in summary.critical_issues:
            console.print(f"  • {issue}")

    # Show warnings if any
    if summary.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in summary.warnings[:10]:  # Limit to first 10
            console.print(f"  • {warning}")
        if len(summary.warnings) > 10:
            console.print(f"  ... and {len(summary.warnings) - 10} more warnings")


def display_task_status(task: Task, verbose: bool = False):
    """Display status of a single task."""

    status_color = {
        TaskStatus.PENDING: "yellow",
        TaskStatus.IN_PROGRESS: "blue",
        TaskStatus.COMPLETED: "green",
        TaskStatus.FAILED: "red",
        TaskStatus.SKIPPED: "dim"
    }.get(task.status, "white")

    console.print(f"[bold]Task:[/bold] {task.id}")
    console.print(f"[bold]Title:[/bold] {task.title}")
    console.print(f"[bold]Status:[/bold] [{status_color}]{task.status.value}[/{status_color}]")
    console.print(f"[bold]Created:[/bold] {task.created_at}")

    if task.started_at:
        console.print(f"[bold]Started:[/bold] {task.started_at}")
    if task.completed_at:
        console.print(f"[bold]Completed:[/bold] {task.completed_at}")
        if task.started_at:
            duration = task.completed_at - task.started_at
            console.print(f"[bold]Duration:[/bold] {duration.total_seconds():.2f}s")

    if verbose and task.subtasks:
        console.print(f"\n[bold]Subtasks ({len(task.subtasks)}):[/bold]")
        for subtask in task.subtasks:
            subtask_color = {
                TaskStatus.PENDING: "yellow",
                TaskStatus.IN_PROGRESS: "blue",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.SKIPPED: "dim"
            }.get(subtask.status, "white")

            console.print(f"  • [{subtask_color}]{subtask.status.value}[/{subtask_color}] {subtask.summary}")


def display_task_list(tasks: List[Task], verbose: bool = False):
    """Display a list of tasks."""

    table = Table(title="Validation Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Created", style="blue")

    if verbose:
        table.add_column("Subtasks", style="green")
        table.add_column("Duration", style="yellow")

    for task in tasks:
        status_color = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.COMPLETED: "green",
            TaskStatus.FAILED: "red",
            TaskStatus.SKIPPED: "dim"
        }.get(task.status, "white")

        row = [
            task.id,
            task.title[:50] + "..." if len(task.title) > 50 else task.title,
            f"[{status_color}]{task.status.value}[/{status_color}]",
            task.created_at.strftime("%Y-%m-%d %H:%M")
        ]

        if verbose:
            row.append(str(len(task.subtasks)))
            if task.completed_at and task.started_at:
                duration = task.completed_at - task.started_at
                row.append(f"{duration.total_seconds():.1f}s")
            else:
                row.append("-")

        table.add_row(*row)

    console.print(table)


def save_task_state(task: Task):
    """Save task state to file."""
    task_dir = Path(".prompt-builder/tasks")
    task_dir.mkdir(parents=True, exist_ok=True)

    task_file = task_dir / f"{task.id}.json"

    # Convert task to JSON-serializable dict
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "base_ref": task.base_ref,
        "head_ref": task.head_ref,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "subtasks": [
            {
                "id": st.id,
                "summary": st.summary,
                "description": st.description,
                "status": st.status.value,
                "dependencies": st.dependencies,
                "affected_files": st.affected_files,
                "created_at": st.created_at.isoformat() if st.created_at else None,
                "completed_at": st.completed_at.isoformat() if st.completed_at else None,
                "metadata": st.metadata
            }
            for st in task.subtasks
        ],
        "metadata": task.metadata
    }

    with open(task_file, 'w') as f:
        json.dump(task_dict, f, indent=2)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()