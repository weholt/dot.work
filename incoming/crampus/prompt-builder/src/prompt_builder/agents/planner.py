"""Planner Agent for task decomposition."""

import logging
import re
from typing import Any

from ..models import (
    Subtask,
    Task,
    ValidationContract,
    ValidationResult,
    ValidationType,
)
from .base import BaseAgent, measure_execution_time


class PlannerAgent(BaseAgent):
    """Breaks down high-level tasks into atomic subtasks."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")

    def get_validation_type(self) -> ValidationType:
        """Planner performs preparatory validation."""
        return ValidationType.STATIC

    @measure_execution_time
    async def execute(
        self, task: Task, subtask: Subtask | None = None, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Decompose a task into atomic subtasks."""
        self._log_start()

        try:
            # Analyze the task description to identify subtasks
            subtasks = self._decompose_task(task)

            # Validate the decomposition
            issues, warnings = self._validate_decomposition(task, subtasks)

            # Update the task with generated subtasks
            task.subtasks = subtasks

            # Log the decomposition results
            self.logger.info(f"Decomposed task '{task.title}' into {len(subtasks)} subtasks")
            for subtask in subtasks:
                self.logger.debug(f"  - {subtask.id}: {subtask.summary}")

            result = self._create_validation_result(
                subtask_id=task.id,
                passed=len(issues) == 0,
                issues=issues,
                warnings=warnings,
                metrics={
                    "subtasks_created": len(subtasks),
                    "avg_dependencies": sum(len(s.dependencies) for s in subtasks) / len(subtasks) if subtasks else 0,
                    "max_dependencies": max(len(s.dependencies) for s in subtasks) if subtasks else 0,
                },
            )

            self._log_success(result)
            return result

        except Exception as e:
            self._log_error(e)
            result = self._create_validation_result(
                subtask_id=task.id, passed=False, issues=[f"Task decomposition failed: {str(e)}"]
            )
            return result

    def _decompose_task(self, task: Task) -> list[Subtask]:
        """Decompose a task into atomic subtasks."""
        # Use patterns and heuristics to identify subtasks
        patterns = [
            # Feature implementation patterns
            r"(?:add|implement|create|build)\s+(.+?)(?:\s+(?:function|feature|component|class|module|service|api|endpoint))?",
            r"(?:update|modify|refactor|improve|enhance)\s+(.+)",
            r"(?:fix|resolve|debug)\s+(.+?)(?:\s+(?:bug|issue|error|problem))?",
            # Testing patterns
            r"(?:test|write|create)\s+(.+?)(?:\s+(?:tests|test cases|unit tests|integration tests))?",
            r"(?:add|implement)\s+(.+?)(?:\s+(?:testing|validation|verification))?",
            # Documentation patterns
            r"(?:document|write|create|update)\s+(.+?)(?:\s+(?:docs|documentation|readme|guide))?",
            # Configuration patterns
            r"(?:configure|setup|install|deploy)\s+(.+)",
            # Performance patterns
            r"(?:optimize|improve|enhance)\s+(.+?)(?:\s+(?:performance|speed|efficiency|scalability))?",
            # Security patterns
            r"(?:secure|harden|protect)\s+(.+)",
        ]

        subtasks = []
        lines = task.description.split("\n")
        current_subtask = None
        subtask_counter = 1

        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if this line matches any of our patterns
            matched_pattern = False
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    matched_pattern = True
                    subtask_summary = match.group(1).strip()

                    # Create a new subtask
                    subtask_id = f"{task.id}-ST-{subtask_counter:03d}"

                    # Extract more details from surrounding context
                    description = self._extract_subtask_description(lines, i)

                    # Generate validation contract based on the subtask type
                    contract = self._generate_validation_contract(subtask_summary, description)

                    # Identify affected files (heuristic)
                    affected_files = self._identify_affected_files(subtask_summary, description)

                    subtask = Subtask(
                        id=subtask_id,
                        summary=subtask_summary,
                        description=description,
                        contract=contract,
                        affected_files=affected_files,
                        metadata={"original_line": line, "line_number": i + 1},
                    )

                    subtasks.append(subtask)
                    subtask_counter += 1
                    current_subtask = subtask
                    break

            # If no pattern matched, but we have a current subtask, append as details
            if not matched_pattern and current_subtask and line:
                if not current_subtask.description.endswith(line):
                    current_subtask.description += "\n" + line

        # If no subtasks were found through pattern matching, create a single subtask
        if not subtasks:
            subtask = Subtask(
                id=f"{task.id}-ST-001",
                summary=task.title,
                description=task.description,
                contract=self._generate_validation_contract(task.title, task.description),
                affected_files=self._identify_affected_files(task.title, task.description),
            )
            subtasks.append(subtask)

        # Establish dependencies between subtasks
        self._establish_dependencies(subtasks)

        return subtasks

    def _extract_subtask_description(self, lines: list[str], current_index: int) -> str:
        """Extract description for a subtask from surrounding context."""
        description_lines = [lines[current_index]]

        # Look ahead for more details
        for i in range(current_index + 1, min(current_index + 3, len(lines))):
            next_line = lines[i].strip()
            if (
                next_line
                and not next_line.startswith("#")
                and not re.match(r"^(?:add|implement|create|fix|test|document)", next_line, re.IGNORECASE)
            ):
                description_lines.append(next_line)
            else:
                break

        return "\n".join(description_lines)

    def _generate_validation_contract(self, summary: str, description: str) -> ValidationContract:
        """Generate validation contract based on subtask type."""
        contract = ValidationContract()

        summary_lower = summary.lower()
        desc_lower = description.lower()

        # Common preconditions
        contract.preconditions.append("Code compiles without errors")
        contract.preconditions.append("Dependencies are available")

        # Type-specific validation
        if any(word in summary_lower for word in ["test", "testing", "validation"]):
            contract.postconditions.append("New tests pass")
            contract.postconditions.append("Test coverage is maintained or increased")
            contract.test_cases.append("Run existing test suite")
            contract.test_cases.append("Run new test cases")

        elif any(word in summary_lower for word in ["implement", "create", "add", "build"]):
            contract.postconditions.append("New functionality works as expected")
            contract.postconditions.append("No existing functionality is broken")
            contract.test_cases.append("Run integration tests")
            contract.test_cases.append("Test new functionality")

        elif any(word in summary_lower for word in ["fix", "resolve", "debug"]):
            contract.postconditions.append("Issue is resolved")
            contract.postconditions.append("No new issues are introduced")
            contract.test_cases.append("Test the fix")
            contract.test_cases.append("Regression test for similar issues")

        elif any(word in summary_lower for word in ["update", "modify", "refactor", "improve"]):
            contract.postconditions.append("Functionality is preserved")
            contract.postconditions.append("Code quality is improved")
            contract.test_cases.append("Run all existing tests")
            contract.test_cases.append("Performance regression test")

        elif any(word in summary_lower for word in ["document", "docs", "readme"]):
            contract.postconditions.append("Documentation is accurate and complete")
            contract.test_cases.append("Review documentation for clarity")
            contract.test_cases.append("Validate documentation examples")

        elif any(word in summary_lower for word in ["configure", "setup", "install", "deploy"]):
            contract.postconditions.append("Configuration is valid")
            contract.postconditions.append("System can be deployed/started")
            contract.test_cases.append("Test configuration")
            contract.test_cases.append("Verify deployment")

        # Common invariants
        contract.invariants.append("Code follows project conventions")
        contract.invariants.append("No security vulnerabilities are introduced")
        contract.invariants.append("Performance is not significantly degraded")

        return contract

    def _identify_affected_files(self, summary: str, description: str) -> list[str]:
        """Identify files that might be affected by this subtask."""
        affected_files = []
        text = (summary + " " + description).lower()

        # Look for file patterns
        file_patterns = {
            r"\.py$": ["src/**/*.py", "tests/**/*.py"],
            r"\.js$": ["src/**/*.js", "tests/**/*.js"],
            r"\.ts$": ["src/**/*.ts", "tests/**/*.ts"],
            r"\.jsx?$": ["src/**/*.jsx", "src/**/*.js"],
            r"\.tsx?$": ["src/**/*.tsx", "src/**/*.ts"],
            r"docker": ["Dockerfile", "docker-compose*.yml"],
            r"config": ["**/config/**", "*.yaml", "*.yml", "*.toml"],
            r"documentation|docs?": ["**/*.md", "docs/**"],
            r"readme": ["README.md", "readme.md"],
        }

        for pattern, files in file_patterns.items():
            if re.search(pattern, text):
                affected_files.extend(files)

        # Look for specific file mentions
        file_mentions = re.findall(r"[/\\]([^\s/\\]+\.[a-zA-Z]+)", text)
        for mention in file_mentions:
            if mention not in affected_files:
                affected_files.append(f"**/{mention}")

        return affected_files

    def _establish_dependencies(self, subtasks: list[Subtask]):
        """Establish dependencies between subtasks based on their nature."""
        for i, subtask in enumerate(subtasks):
            summary_lower = subtask.summary.lower()

            # Test tasks generally depend on implementation tasks
            if any(word in summary_lower for word in ["test", "testing"]):
                # Look for corresponding implementation tasks
                for j, other_subtask in enumerate(subtasks[:i]):
                    other_summary = other_subtask.summary.lower()
                    if any(word in other_summary for word in ["implement", "create", "add", "fix"]):
                        if other_subtask.id not in subtask.dependencies:
                            subtask.dependencies.append(other_subtask.id)

            # Documentation tasks often depend on implementation
            elif any(word in summary_lower for word in ["document", "docs"]):
                for j, other_subtask in enumerate(subtasks[:i]):
                    other_summary = other_subtask.summary.lower()
                    if not any(word in other_summary for word in ["document", "docs"]):
                        if other_subtask.id not in subtask.dependencies:
                            subtask.dependencies.append(other_subtask.id)

    def _validate_decomposition(self, task: Task, subtasks: list[Subtask]) -> tuple[list[str], list[str]]:
        """Validate the task decomposition."""
        issues = []
        warnings = []

        if not subtasks:
            issues.append("No subtasks were generated from the task")

        # Check for circular dependencies
        self._check_circular_dependencies(subtasks, issues)

        # Check for too many subtasks (might indicate over-decomposition)
        if len(subtasks) > 20:
            warnings.append(f"Large number of subtasks ({len(subtasks)}) - consider consolidating")

        # Check for subtasks without contracts
        for subtask in subtasks:
            if not subtask.contract.postconditions:
                warnings.append(f"Subtask {subtask.id} has no postconditions")
            if not subtask.contract.test_cases:
                warnings.append(f"Subtask {subtask.id} has no test cases")

        return issues, warnings

    def _check_circular_dependencies(self, subtasks: list[Subtask], issues: list[str]):
        """Check for circular dependencies between subtasks."""
        # Build dependency graph
        dep_graph = {}
        for subtask in subtasks:
            dep_graph[subtask.id] = subtask.dependencies

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for subtask in subtasks:
            if subtask.id not in visited:
                if has_cycle(subtask.id):
                    issues.append(f"Circular dependency detected involving subtask {subtask.id}")
                    break
