#!/usr/bin/env python3
"""
Basic usage example for Prompt Builder.

This example demonstrates how to use the Prompt Builder system programmatically
without using the CLI.
"""

import asyncio

from prompt_builder.agents import (
    BehaviorValidatorAgent,
    PlannerAgent,
    RegressionSentinelAgent,
    StaticValidatorAgent,
)
from prompt_builder.cli import run_validation_workflow
from prompt_builder.models import Task, TaskStatus


async def basic_example():
    """Demonstrate basic usage of the Prompt Builder system."""
    print("🚀 Starting Prompt Builder Basic Example\n")

    # Create a task
    task = Task(
        id="EXAMPLE-001",
        title="Add user authentication system",
        description="""
        Implement a complete user authentication system with the following features:
        1. User registration with email verification
        2. Login with JWT tokens
        3. Password reset functionality
        4. Session management
        5. Account locking after failed attempts

        The implementation should include:
        - Database models for users and sessions
        - API endpoints for authentication
        - Email service for verification
        - Security measures against common attacks
        - Comprehensive test coverage
        """,
        base_ref="HEAD~5",  # Compare with 5 commits back
        head_ref="HEAD",  # Current changes
        status=TaskStatus.PENDING,
    )

    print(f"📋 Created task: {task.title}")
    print(f"📝 Task ID: {task.id}")
    print(f"🔍 Comparing: {task.base_ref} → {task.head_ref}")
    print()

    # Run the validation workflow
    print("⚡ Running validation workflow...")
    try:
        validation_summary = await run_validation_workflow(task)

        # Display results
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)

        if validation_summary.overall_passed:
            print("✅ All validations PASSED!")
        else:
            print("❌ Some validations FAILED!")

        print("\n📈 Summary:")
        print(f"   Total Validations: {validation_summary.total_validations}")
        print(f"   Passed: {validation_summary.passed_validations}")
        print(f"   Failed: {validation_summary.failed_validations}")
        print(f"   Execution Time: {validation_summary.execution_time:.2f}s")

        # Show agent results
        print("\n🤖 Agent Results:")
        for result in validation_summary.validation_results:
            status = "✅" if result.passed else "❌"
            agent_name = result.validator_type.value.replace("_", " ").title()
            print(f"   {status} {agent_name}: {result.execution_time:.2f}s")

            if result.issues:
                for issue in result.issues:
                    print(f"      🔴 Issue: {issue}")

            if result.warnings:
                for warning in result.warnings:
                    print(f"      🟡 Warning: {warning}")

        # Show subtasks if any were created
        if task.subtasks:
            print(f"\n📋 Generated Subtasks ({len(task.subtasks)}):")
            for i, subtask in enumerate(task.subtasks, 1):
                status_emoji = {
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌",
                    TaskStatus.IN_PROGRESS: "⏳",
                    TaskStatus.PENDING: "⭕",
                }.get(subtask.status, "❓")

                print(f"   {i}. {status_emoji} {subtask.summary}")
                print(f"      Dependencies: {', '.join(subtask.dependencies) if subtask.dependencies else 'None'}")
                print(
                    f"      Files: {', '.join(subtask.affected_files[:3])}{'...' if len(subtask.affected_files) > 3 else ''}"
                )

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback

        traceback.print_exc()

    print("\n🎯 Example completed!")


async def individual_agents_example():
    """Demonstrate using individual agents directly."""
    print("\n" + "=" * 60)
    print("🔧 INDIVIDUAL AGENTS EXAMPLE")
    print("=" * 60)

    # Create a simple task
    task = Task(
        id="INDIVIDUAL-001",
        title="Fix login bug",
        description="Fix the authentication bug where users can't log in with special characters in passwords",
        base_ref="HEAD~1",
        head_ref="HEAD",
    )

    print(f"📋 Task: {task.title}")

    # 1. Run Planner Agent
    print("\n1️⃣ Running Planner Agent...")
    planner = PlannerAgent()
    planner_result = await planner.execute(task)
    print(f"   Status: {'✅ PASSED' if planner_result.passed else '❌ FAILED'}")
    print(f"   Subtasks created: {len(task.subtasks)}")

    if task.subtasks:
        print("   Generated subtasks:")
        for subtask in task.subtasks:
            print(f"     • {subtask.summary}")

    # 2. Run Static Validator for each subtask
    print("\n2️⃣ Running Static Validator Agent...")
    static_validator = StaticValidatorAgent()
    for subtask in task.subtasks:
        print(f"   Validating: {subtask.id}")
        result = await static_validator.execute(task, subtask)
        print(f"   Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        if result.issues:
            for issue in result.issues:
                print(f"     Issue: {issue}")

    # 3. Run Behavior Validator
    print("\n3️⃣ Running Behavior Validator Agent...")
    behavior_validator = BehaviorValidatorAgent()
    for subtask in task.subtasks:
        print(f"   Validating behavior: {subtask.id}")
        result = await behavior_validator.execute(task, subtask)
        print(f"   Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

    # 4. Run Regression Sentinel
    print("\n4️⃣ Running Regression Sentinel Agent...")
    regression_sentinel = RegressionSentinelAgent()
    for subtask in task.subtasks:
        print(f"   Checking regressions: {subtask.id}")
        result = await regression_sentinel.execute(task, subtask)
        print(f"   Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        if result.metrics.get("risk_score", 0) > 0.5:
            print(f"   ⚠️  High risk score: {result.metrics['risk_score']:.2f}")

    print("\n✅ Individual agents example completed!")


def demonstrate_task_creation():
    """Demonstrate different ways to create tasks."""
    print("\n" + "=" * 60)
    print("📝 TASK CREATION EXAMPLES")
    print("=" * 60)

    # Example 1: Feature development
    feature_task = Task(
        id="FEATURE-001",
        title="Implement real-time notifications",
        description="""
        Add real-time notification system to allow users to receive:
        - Instant message notifications
        - System alerts and updates
        - Mention notifications
        - Task assignment notifications

        Implementation should include:
        - WebSocket connections
        - Notification queuing system
        - User preferences for notification types
        - Push notifications for mobile users
        """,
        status=TaskStatus.PENDING,
    )

    print("1️⃣ Feature Development Task:")
    print(f"   Title: {feature_task.title}")
    print(f"   Status: {feature_task.status.value}")
    print(f"   Description length: {len(feature_task.description)} chars")

    # Example 2: Bug fix
    bug_task = Task(
        id="BUG-001",
        title="Fix memory leak in data processing",
        description="""
        Memory leak occurs when processing large datasets:
        - Objects not properly garbage collected
        - Memory usage increases over time
        - Application crashes after processing ~10GB of data

        Steps to reproduce:
        1. Load large dataset (>5GB)
        2. Run data transformation
        3. Monitor memory usage
        4. Observe continuous memory increase
        """,
        base_ref="origin/main",
        head_ref="fix/memory-leak",
        status=TaskStatus.PENDING,
    )

    print("\n2️⃣ Bug Fix Task:")
    print(f"   Title: {bug_task.title}")
    print(f"   Base ref: {bug_task.base_ref}")
    print(f"   Head ref: {bug_task.head_ref}")

    # Example 3: Refactoring
    refactor_task = Task(
        id="REFACTOR-001",
        title="Refactor authentication service for better testability",
        description="""
        Current authentication service is tightly coupled and hard to test.

        Refactoring goals:
        - Extract dependencies for better mocking
        - Implement dependency injection
        - Separate business logic from infrastructure
        - Add comprehensive unit tests
        - Maintain backward compatibility

        Files to modify:
        - src/services/auth_service.py
        - tests/test_auth_service.py
        """,
        status=TaskStatus.PENDING,
    )

    print("\n3️⃣ Refactoring Task:")
    print(f"   Title: {refactor_task.title}")
    print("   Focus: Testability improvement")

    print("\n✅ Task creation examples completed!")


def show_configuration_examples():
    """Show configuration examples."""
    print("\n" + "=" * 60)
    print("⚙️  CONFIGURATION EXAMPLES")
    print("=" * 60)

    # Example configuration
    config_example = """
# prompt-builder.toml

[agents.planner]
enabled = true
timeout = 300
max_retries = 3

[agents.static_validator]
enabled = true
timeout = 180
max_retries = 3

[agents.behavior_validator]
enabled = true
timeout = 600
max_retries = 3

[agents.regression_sentinel]
enabled = true
timeout = 240
max_retries = 3

[agents.synthetic_test]
enabled = true
timeout = 300
max_retries = 3

[agents.pr_generator]
enabled = true
timeout = 120
max_retries = 3

[git]
auto_push = false
pr_auto_merge = false
default_base = "main"

[notifications]
on_failure = true
on_success = false
webhook_url = "https://hooks.slack.com/..."

[paths]
tasks_dir = ".prompt-builder/tasks"
snapshots_dir = ".prompt-builder/snapshots"
synthetic_tests_dir = "tests/synthetic"
logs_dir = ".prompt-builder/logs"
"""

    print("Example configuration (prompt-builder.toml):")
    print(config_example)

    # Environment variables
    print("\nEnvironment Variables:")
    env_vars = """
PROMPT_BUILDER_LOG_LEVEL=DEBUG
PROMPT_BUILDER_GITHUB_TOKEN=ghp_...
PROMPT_BUILDER_SLACK_WEBHOOK=https://hooks.slack.com/...
PROMPT_BUILDER_TIMEOUT_MULTIPLIER=2.0
"""
    print(env_vars)

    print("\n✅ Configuration examples completed!")


async def main():
    """Run all examples."""
    print("🎯 Prompt Builder - Usage Examples")
    print("=" * 60)

    # Show task creation examples
    demonstrate_task_creation()

    # Show configuration examples
    show_configuration_examples()

    # Run basic workflow example
    await basic_example()

    # Run individual agents example
    await individual_agents_example()

    print("\n" + "=" * 60)
    print("🎉 ALL EXAMPLES COMPLETED!")
    print("=" * 60)

    print("\n💡 Next steps:")
    print("   1. Initialize your project: prompt-builder init")
    print("   2. Start your first task: prompt-builder start 'your task description'")
    print("   3. Check results: prompt-builder list-tasks")
    print("   4. Create PR if ready: prompt-builder validate TASK-ID --create-pr")


if __name__ == "__main__":
    asyncio.run(main())
