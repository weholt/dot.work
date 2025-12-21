"""PR Generator Agent for creating pull requests."""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import asyncio

from .base import BaseAgent, measure_execution_time
from ..models import (
    Task,
    Subtask,
    ValidationResult,
    ValidationType,
    PRInfo,
    ValidationResultSummary,
)


class PRGeneratorAgent(BaseAgent):
    """Generates pull requests when all validation passes."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")

    def get_validation_type(self) -> ValidationType:
        """PR generator performs final validation checks."""
        return ValidationType.STATIC

    @measure_execution_time
    async def execute(
        self,
        task: Task,
        subtask: Optional[Subtask] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Generate a pull request if all validations pass."""
        self._log_start(subtask)

        try:
            issues = []
            warnings = []
            metrics = {}

            # Check if we have validation results
            validation_summary = context.get('validation_summary') if context else None
            if not validation_summary:
                issues.append("No validation summary provided - cannot determine if PR should be created")
                result = self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=issues
                )
                return result

            # Verify all validations passed
            if not validation_summary.overall_passed:
                issues.append("Cannot create PR: some validations failed")
                for issue in validation_summary.critical_issues:
                    issues.append(f"Critical issue: {issue}")
                result = self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=issues
                )
                return result

            # Generate PR information
            pr_info = await self._generate_pr_info(task, validation_summary)

            # Create the pull request
            pr_result = await self._create_pull_request(pr_info)
            metrics.update(pr_result['metrics'])
            issues.extend(pr_result['issues'])
            warnings.extend(pr_result['warnings'])

            # Determine overall success
            passed = len(pr_result['issues']) == 0

            result = self._create_validation_result(
                subtask_id=task.id,
                passed=passed,
                issues=issues,
                warnings=warnings,
                metrics=metrics
            )

            self._log_success(result, subtask)
            return result

        except Exception as e:
            self._log_error(e, subtask)
            result = self._create_validation_result(
                subtask_id=task.id if subtask else task.id,
                passed=False,
                issues=[f"PR generation failed: {str(e)}"]
            )
            return result

    async def _generate_pr_info(self, task: Task, validation_summary: ValidationResultSummary) -> PRInfo:
        """Generate pull request information."""
        # Get changed files
        changed_files = await self._get_changed_files()

        # Generate PR title
        title = self._generate_pr_title(task)

        # Generate PR description
        description = self._generate_pr_description(task, validation_summary)

        # Determine base and head branches
        base_branch = task.base_ref or "main"
        head_branch = self._get_current_branch()

        # Generate labels based on task characteristics
        labels = self._generate_labels(task)

        # Suggest reviewers
        reviewers = self._suggest_reviewers(task, changed_files)

        return PRInfo(
            title=title,
            description=description,
            base_branch=base_branch,
            head_branch=head_branch,
            files_changed=changed_files,
            labels=labels,
            reviewers=reviewers,
            draft=False,  # Create as ready for review
            metadata={
                'task_id': task.id,
                'validation_summary': validation_summary.__dict__,
                'created_at': task.created_at.isoformat() if task.created_at else None
            }
        )

    async def _create_pull_request(self, pr_info: PRInfo) -> Dict[str, Any]:
        """Create the actual pull request."""
        issues = []
        warnings = []
        metrics = {
            'pr_created': False,
            'files_included': len(pr_info.files_changed),
            'labels_added': len(pr_info.labels)
        }

        try:
            # Check if we're in a git repository
            if not await self._is_git_repository():
                issues.append("Not in a git repository - cannot create PR")
                return {'issues': issues, 'warnings': warnings, 'metrics': metrics}

            # Check if there are uncommitted changes
            if await self._has_uncommitted_changes():
                warnings.append("There are uncommitted changes - consider committing them first")

            # Create PR using GitHub CLI if available
            if await self._is_gh_cli_available():
                pr_result = await self._create_pr_with_gh_cli(pr_info)
                metrics.update(pr_result['metrics'])
                issues.extend(pr_result['issues'])
                warnings.extend(pr_result['warnings'])
                if not pr_result['issues']:
                    metrics['pr_created'] = True
            else:
                # Fallback: create PR manually or provide instructions
                pr_result = await self._create_pr_manually(pr_info)
                metrics.update(pr_result['metrics'])
                warnings.extend(pr_result['warnings'])
                if 'pr_url' in pr_result:
                    metrics['pr_created'] = True

        except Exception as e:
            issues.append(f"Failed to create PR: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    def _generate_pr_title(self, task: Task) -> str:
        """Generate a PR title from the task."""
        # Clean up the task title
        title = task.title.strip()

        # Remove common prefixes
        prefixes_to_remove = ['implement ', 'add ', 'create ', 'fix ', 'update ']
        for prefix in prefixes_to_remove:
            if title.lower().startswith(prefix):
                title = title[len(prefix):]
                break

        # Capitalize first letter
        title = title[0].upper() + title[1:] if title else title

        # Add emoji based on task type
        title_lower = title.lower()
        if any(word in title_lower for word in ['fix', 'bug', 'error']):
            title = f"🐛 {title}"
        elif any(word in title_lower for word in ['feature', 'implement', 'add']):
            title = f"✨ {title}"
        elif any(word in title_lower for word in ['update', 'improve', 'enhance']):
            title = f"🔧 {title}"
        elif any(word in title_lower for word in ['test', 'testing']):
            title = f"🧪 {title}"
        elif any(word in title_lower for word in ['doc', 'documentation']):
            title = f"📚 {title}"
        else:
            title = f"🔄 {title}"

        return title

    def _generate_pr_description(self, task: Task, validation_summary: ValidationResultSummary) -> str:
        """Generate a PR description."""
        description = f"""## Summary

{task.description}

## Changes

This PR includes the following changes:

"""

        # Add subtask information
        if task.subtasks:
            for subtask in task.subtasks:
                status_emoji = "✅" if subtask.status.value == "completed" else "⏳"
                description += f"- {status_emoji} {subtask.summary}\n"

        description += f"""

## Validation

All automated checks have passed:

- **Total Validations**: {validation_summary.total_validations}
- **Passed**: {validation_summary.passed_validations}
- **Failed**: {validation_summary.failed_validations}
- **Execution Time**: {validation_summary.execution_time:.2f}s

### Validation Results

"""

        # Add validation breakdown
        validation_counts = {}
        for result in validation_summary.validation_results:
            vtype = result.validator_type.value
            validation_counts[vtype] = validation_counts.get(vtype, {'passed': 0, 'failed': 0})
            if result.passed:
                validation_counts[vtype]['passed'] += 1
            else:
                validation_counts[vtype]['failed'] += 1

        for vtype, counts in validation_counts.items():
            description += f"- **{vtype.title()}**: {counts['passed']} passed, {counts['failed']} failed\n"

        # Add warnings if any
        if validation_summary.warnings:
            description += "\n### Warnings\n\n"
            for warning in validation_summary.warnings[:5]:  # Limit to first 5 warnings
                description += f"- ⚠️ {warning}\n"
            if len(validation_summary.warnings) > 5:
                description += f"- ... and {len(validation_summary.warnings) - 5} more warnings\n"

        description += """

## Testing

- [ ] All automated tests pass
- [ ] Manual testing completed
- [ ] No regression detected

## Checklist

- [ ] Code follows project conventions
- [ ] Documentation is updated
- [ ] Tests are included/updated
- [ ] No security vulnerabilities introduced
- [ ] Performance is acceptable

---

*This PR was automatically generated by Prompt Builder multi-agent validation system.*
"""

        return description

    def _generate_labels(self, task: Task) -> List[str]:
        """Generate appropriate labels for the PR."""
        labels = []
        title_lower = task.title.lower()
        desc_lower = task.description.lower()

        # Type-based labels
        if any(word in title_lower + desc_lower for word in ['fix', 'bug', 'error']):
            labels.append('bug')
        if any(word in title_lower + desc_lower for word in ['feature', 'implement', 'add']):
            labels.append('enhancement')
        if any(word in title_lower + desc_lower for word in ['update', 'improve', 'enhance']):
            labels.append('improvement')
        if any(word in title_lower + desc_lower for word in ['test', 'testing']):
            labels.append('testing')
        if any(word in title_lower + desc_lower for word in ['doc', 'documentation']):
            labels.append('documentation')
        if any(word in title_lower + desc_lower for word in ['refactor', 'clean', 'optimize']):
            labels.append('refactoring')

        # Process labels
        if any(word in title_lower + desc_lower for word in ['ci', 'cd', 'pipeline']):
            labels.append('ci/cd')

        # Size-based label (heuristic)
        estimated_size = len(task.subtasks) if task.subtasks else 1
        if estimated_size <= 2:
            labels.append('size/S')
        elif estimated_size <= 5:
            labels.append('size/M')
        else:
            labels.append('size/L')

        return list(set(labels))  # Remove duplicates

    def _suggest_reviewers(self, task: Task, changed_files: List[str]) -> List[str]:
        """Suggest appropriate reviewers based on changed files."""
        reviewers = []

        # This is a simplified implementation
        # In a real system, this would analyze:
        # - CODEOWNERS file
        # - Recent commit history
        # - File ownership patterns
        # - Team expertise areas

        # Example heuristic suggestions
        if any('frontend' in f.lower() or 'ui' in f.lower() for f in changed_files):
            reviewers.extend(['frontend-team', 'ui-reviewers'])

        if any('backend' in f.lower() or 'api' in f.lower() for f in changed_files):
            reviewers.extend(['backend-team', 'api-reviewers'])

        if any('test' in f.lower() for f in changed_files):
            reviewers.append('qa-team')

        return list(set(reviewers))  # Remove duplicates

    async def _get_changed_files(self) -> List[str]:
        """Get list of files changed in the current branch."""
        try:
            cmd = ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode('utf-8').strip().split('\n')
            else:
                return []
        except Exception:
            return []

    def _get_current_branch(self) -> str:
        """Get the current git branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "feature-branch"

    async def _is_git_repository(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            cmd = ['git', 'rev-parse', '--git-dir']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    async def _has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            cmd = ['git', 'status', '--porcelain']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return len(stdout.decode('utf-8').strip()) > 0
        except Exception:
            return False

    async def _is_gh_cli_available(self) -> bool:
        """Check if GitHub CLI is available."""
        try:
            cmd = ['gh', '--version']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    async def _create_pr_with_gh_cli(self, pr_info: PRInfo) -> Dict[str, Any]:
        """Create PR using GitHub CLI."""
        issues = []
        warnings = []
        metrics = {}

        try:
            # Build gh CLI command
            cmd = ['gh', 'pr', 'create']
            cmd.extend(['--title', pr_info.title])
            cmd.extend(['--body', pr_info.description])
            cmd.extend(['--base', pr_info.base_branch])
            cmd.extend(['--head', pr_info.head_branch])

            if pr_info.labels:
                for label in pr_info.labels:
                    cmd.extend(['--label', label])

            if pr_info.reviewers:
                cmd.extend(['--reviewer', ','.join(pr_info.reviewers)])

            if pr_info.draft:
                cmd.append('--draft')

            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                pr_url = stdout.decode('utf-8').strip()
                metrics['pr_url'] = pr_url
                self.logger.info(f"PR created successfully: {pr_url}")
            else:
                error_msg = stderr.decode('utf-8').strip()
                issues.append(f"Failed to create PR with gh CLI: {error_msg}")

        except Exception as e:
            issues.append(f"Error running gh CLI: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _create_pr_manually(self, pr_info: PRInfo) -> Dict[str, Any]:
        """Provide instructions for manual PR creation."""
        warnings = []
        metrics = {}

        # Save PR info to a file
        pr_file = Path('.prompt-builder/pr_info.json')
        pr_file.parent.mkdir(exist_ok=True)

        try:
            with open(pr_file, 'w') as f:
                json.dump(pr_info.__dict__, f, indent=2, default=str)

            warnings.append(f"PR information saved to {pr_file}")
            warnings.append("Create PR manually using the saved information")

            metrics['pr_info_saved'] = True
        except Exception as e:
            warnings.append(f"Failed to save PR information: {str(e)}")

        return {
            'issues': [],
            'warnings': warnings,
            'metrics': metrics
        }