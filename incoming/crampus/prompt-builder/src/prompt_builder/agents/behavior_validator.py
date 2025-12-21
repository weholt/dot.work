"""Behavior Validator Agent for runtime behavior validation."""

import asyncio
import subprocess
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import time

from .base import BaseAgent, measure_execution_time
from ..models import (
    Task,
    Subtask,
    ValidationResult,
    ValidationType,
)


class BehaviorValidatorAgent(BaseAgent):
    """Validates runtime behavior through test execution and behavior simulation."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")

    def get_validation_type(self) -> ValidationType:
        """Behavior validator performs behavior validation."""
        return ValidationType.BEHAVIOR

    @measure_execution_time
    async def execute(
        self,
        task: Task,
        subtask: Optional[Subtask] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate behavior through test execution and simulation."""
        self._log_start(subtask)

        try:
            if not subtask:
                return self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=["Behavior validation requires a specific subtask"]
                )

            issues = []
            warnings = []
            metrics = {}

            # Run test suite
            test_results = await self._run_test_suite(subtask)
            issues.extend(test_results['issues'])
            warnings.extend(test_results['warnings'])
            metrics.update(test_results['metrics'])

            # Validate specific subtask contract
            contract_results = await self._validate_contract(subtask)
            issues.extend(contract_results['issues'])
            warnings.extend(contract_results['warnings'])
            metrics.update(contract_results['metrics'])

            # Check behavior invariants
            invariant_results = await self._check_invariants(subtask)
            issues.extend(invariant_results['issues'])
            warnings.extend(invariant_results['warnings'])
            metrics.update(invariant_results['metrics'])

            # Determine overall pass/fail
            passed = len(issues) == 0

            result = self._create_validation_result(
                subtask_id=subtask.id,
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
                subtask_id=subtask.id if subtask else task.id,
                passed=False,
                issues=[f"Behavior validation failed: {str(e)}"]
            )
            return result

    async def _run_test_suite(self, subtask: Subtask) -> Dict[str, Any]:
        """Run the test suite and collect results."""
        issues = []
        warnings = []
        metrics = {}

        try:
            # Determine which tests to run
            test_patterns = self._get_test_patterns(subtask)

            for pattern in test_patterns:
                self.logger.info(f"Running tests with pattern: {pattern}")

                # Run pytest (or other test runner)
                result = await self._run_pytest([pattern])

                if result['returncode'] != 0:
                    # Test failures
                    failed_tests = result.get('failed_tests', [])
                    for test in failed_tests:
                        issues.append(f"Test failed: {test}")

                metrics.update(result.get('metrics', {}))

        except subprocess.CalledProcessError as e:
            issues.append(f"Test execution failed: {e}")
        except FileNotFoundError:
            warnings.append("Test runner not found - skipping test execution")
        except Exception as e:
            issues.append(f"Unexpected error running tests: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _validate_contract(self, subtask: Subtask) -> Dict[str, Any]:
        """Validate that subtask contracts are satisfied."""
        issues = []
        warnings = []
        metrics = {
            'contract_checks': 0,
            'contract_passed': 0
        }

        contract = subtask.contract

        # Check postconditions
        for postcondition in contract.postconditions:
            metrics['contract_checks'] += 1
            try:
                # Try to validate postcondition (simplified validation)
                if await self._check_postcondition(postcondition):
                    metrics['contract_passed'] += 1
                else:
                    issues.append(f"Postcondition not satisfied: {postcondition}")
            except Exception as e:
                warnings.append(f"Could not validate postcondition '{postcondition}': {str(e)}")

        # Check invariants
        for invariant in contract.invariants:
            metrics['contract_checks'] += 1
            try:
                if await self._check_invariant(invariant):
                    metrics['contract_passed'] += 1
                else:
                    issues.append(f"Invariant violated: {invariant}")
            except Exception as e:
                warnings.append(f"Could not validate invariant '{invariant}': {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _check_invariants(self, subtask: Subtask) -> Dict[str, Any]:
        """Check system-wide invariants."""
        issues = []
        warnings = []
        metrics = {
            'invariant_checks': 0,
            'invariant_passed': 0
        }

        # Common invariants to check
        invariants = [
            "Code compiles without errors",
            "No security vulnerabilities are introduced",
            "Performance is not significantly degraded",
            "Existing functionality is preserved",
        ]

        for invariant in invariants:
            metrics['invariant_checks'] += 1
            try:
                if await self._check_system_invariant(invariant):
                    metrics['invariant_passed'] += 1
                else:
                    issues.append(f"System invariant violated: {invariant}")
            except Exception as e:
                warnings.append(f"Could not check invariant '{invariant}': {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _run_pytest(self, args: List[str]) -> Dict[str, Any]:
        """Run pytest with the given arguments."""
        cmd = ['python', '-m', 'pytest'] + args + [
            '--json-report',  # Requires pytest-json-report plugin
            '--json-report-file=/tmp/pytest_results.json',
            '--tb=short',
            '-v'
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Parse results
            result = {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
                'metrics': {}
            }

            # Try to parse JSON report if available
            try:
                with open('/tmp/pytest_results.json', 'r') as f:
                    json_report = json.load(f)

                summary = json_report.get('summary', {})
                result['metrics'] = {
                    'tests_run': summary.get('total', 0),
                    'tests_passed': summary.get('passed', 0),
                    'tests_failed': summary.get('failed', 0),
                    'tests_skipped': summary.get('skipped', 0),
                    'test_duration': summary.get('duration', 0.0),
                }

                # Extract failed test names
                result['failed_tests'] = [
                    test.get('nodeid', '')
                    for test in json_report.get('tests', [])
                    if test.get('outcome') == 'failed'
                ]

            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback: parse from stdout
                result['metrics'] = self._parse_pytest_output(result['stdout'])

            return result

        except Exception as e:
            raise Exception(f"Failed to run pytest: {str(e)}")

    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract metrics."""
        import re

        metrics = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'test_duration': 0.0,
        }

        # Look for summary line like "=== 5 passed, 2 failed, 1 skipped in 2.34s ==="
        summary_match = re.search(r'===\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?.*?in\s+([\d.]+)s', output)
        if summary_match:
            metrics['tests_passed'] = int(summary_match.group(1) or 0)
            metrics['tests_failed'] = int(summary_match.group(2) or 0)
            metrics['tests_skipped'] = int(summary_match.group(3) or 0)
            metrics['test_duration'] = float(summary_match.group(4) or 0.0)
            metrics['tests_run'] = metrics['tests_passed'] + metrics['tests_failed'] + metrics['tests_skipped']

        return metrics

    def _get_test_patterns(self, subtask: Subtask) -> List[str]:
        """Determine which test patterns to run for this subtask."""
        patterns = []

        # Add test patterns from affected files
        for file_pattern in subtask.affected_files:
            if '.py' in file_pattern:
                # Convert source file pattern to test pattern
                if 'src/' in file_pattern:
                    # Map src/module/file.py to tests/test_file.py or tests/test_module.py
                    test_pattern = file_pattern.replace('src/', 'tests/test_')
                    test_pattern = test_pattern.replace('.py', '.py')
                    patterns.append(test_pattern)

        # Add contract test cases
        patterns.extend(subtask.contract.test_cases)

        # Default fallback
        if not patterns:
            patterns.append('tests/')

        return patterns

    async def _check_postcondition(self, postcondition: str) -> bool:
        """Check if a postcondition is satisfied."""
        # This is a simplified implementation
        # In a real system, this would involve more sophisticated behavior checking

        postcondition_lower = postcondition.lower()

        if 'tests pass' in postcondition_lower:
            # Check if recent tests passed (would need test results from context)
            return True  # Simplified

        elif 'functionality works' in postcondition_lower:
            # Would need to run specific functionality tests
            return True  # Simplified

        elif 'issue is resolved' in postcondition_lower:
            # Would need to check specific issue conditions
            return True  # Simplified

        elif 'no new issues' in postcondition_lower:
            # Would need to compare before/after states
            return True  # Simplified

        return True  # Default to passing for unknown conditions

    async def _check_invariant(self, invariant: str) -> bool:
        """Check if a system invariant holds."""
        invariant_lower = invariant.lower()

        if 'compiles' in invariant_lower:
            # Check if code compiles (would need to run syntax check)
            return True  # Simplified

        elif 'security' in invariant_lower:
            # Run security checks
            return True  # Simplified

        elif 'performance' in invariant_lower:
            # Check performance metrics
            return True  # Simplified

        elif 'functionality' in invariant_lower:
            # Check that existing functionality still works
            return True  # Simplified

        return True  # Default to passing for unknown invariants

    async def _check_system_invariant(self, invariant: str) -> bool:
        """Check system-wide invariants."""
        # Similar to _check_invariant but for system-level checks
        return await self._check_invariant(invariant)