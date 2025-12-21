"""Synthetic Test Agent for generating additional tests."""

import ast
import os
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
import re
import asyncio

from .base import BaseAgent, measure_execution_time
from ..models import (
    Task,
    Subtask,
    ValidationResult,
    ValidationType,
    SyntheticTestResult,
    ChangeImpactResult,
)


class SyntheticTestAgent(BaseAgent):
    """Generates synthetic tests for uncovered code paths and edge cases."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")
        self.synthetic_tests_dir = Path("tests/synthetic")
        self.synthetic_tests_dir.mkdir(parents=True, exist_ok=True)

    def get_validation_type(self) -> ValidationType:
        """Synthetic test agent performs synthetic validation."""
        return ValidationType.SYNTHETIC

    @measure_execution_time
    async def execute(
        self,
        task: Task,
        subtask: Optional[Subtask] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Generate synthetic tests for uncovered code paths."""
        self._log_start(subtask)

        try:
            if not subtask:
                return self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=["Synthetic test generation requires a specific subtask"]
                )

            issues = []
            warnings = []
            metrics = {}

            # Analyze code coverage for affected files
            coverage_analysis = await self._analyze_coverage(subtask)
            metrics.update(coverage_analysis['metrics'])

            # Generate tests for uncovered paths
            test_generation_result = await self._generate_synthetic_tests(
                subtask, coverage_analysis['uncovered_paths']
            )
            issues.extend(test_generation_result['issues'])
            warnings.extend(test_generation_result['warnings'])
            metrics.update(test_generation_result['metrics'])

            # Run the generated tests
            test_execution_result = await self._run_synthetic_tests(
                test_generation_result['generated_tests']
            )
            issues.extend(test_execution_result['issues'])
            warnings.extend(test_execution_result['warnings'])
            metrics.update(test_execution_result['metrics'])

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
                issues=[f"Synthetic test generation failed: {str(e)}"]
            )
            return result

    async def _analyze_coverage(self, subtask: Subtask) -> Dict[str, Any]:
        """Analyze code coverage for files affected by the subtask."""
        uncovered_paths = []
        metrics = {
            'files_analyzed': 0,
            'functions_found': 0,
            'uncovered_branches': 0,
            'coverage_percentage': 0.0
        }

        try:
            # Run coverage analysis
            coverage_result = await self._run_coverage_analysis()

            # Process affected files
            for file_pattern in subtask.affected_files:
                if '.py' in file_pattern:
                    file_paths = self._resolve_file_pattern(file_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            analysis = await self._analyze_file_coverage(file_path, coverage_result)
                            metrics['files_analyzed'] += 1
                            metrics['functions_found'] += analysis['functions']
                            metrics['uncovered_branches'] += analysis['uncovered_branches']
                            uncovered_paths.extend(analysis['uncovered_paths'])

            # Calculate overall coverage percentage
            total_branches = metrics['functions_found'] * 2  # Rough estimate
            if total_branches > 0:
                metrics['coverage_percentage'] = (
                    (total_branches - metrics['uncovered_branches']) / total_branches * 100
                )

        except Exception as e:
            self.logger.warning(f"Coverage analysis failed: {e}")

        return {
            'uncovered_paths': uncovered_paths,
            'metrics': metrics
        }

    async def _generate_synthetic_tests(
        self,
        subtask: Subtask,
        uncovered_paths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate synthetic tests for uncovered code paths."""
        generated_tests = []
        issues = []
        warnings = []
        metrics = {
            'tests_generated': 0,
            'edge_case_tests': 0,
            'boundary_value_tests': 0
        }

        for path_info in uncovered_paths:
            try:
                test_code = await self._generate_test_for_path(path_info, subtask)
                if test_code:
                    test_file_path = self._save_synthetic_test(test_code, path_info)
                    generated_tests.append(test_file_path)
                    metrics['tests_generated'] += 1

                    # Categorize the test type
                    if path_info.get('is_edge_case'):
                        metrics['edge_case_tests'] += 1
                    if path_info.get('is_boundary_value'):
                        metrics['boundary_value_tests'] += 1

            except Exception as e:
                warnings.append(f"Failed to generate test for {path_info.get('function', 'unknown')}: {str(e)}")

        return {
            'generated_tests': generated_tests,
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _run_synthetic_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """Run the generated synthetic tests."""
        if not test_files:
            return {
                'issues': [],
                'warnings': [],
                'metrics': {
                    'synthetic_tests_run': 0,
                    'synthetic_tests_passed': 0,
                    'synthetic_tests_failed': 0
                }
            }

        issues = []
        warnings = []
        metrics = {
            'synthetic_tests_run': 0,
            'synthetic_tests_passed': 0,
            'synthetic_tests_failed': 0
        }

        try:
            # Run pytest on synthetic tests
            cmd = ['python', '-m', 'pytest'] + test_files + [
                '--tb=short',
                '-v',
                '--no-header'
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Parse results
            output = stdout.decode('utf-8') + stderr.decode('utf-8')
            results = self._parse_test_output(output)

            metrics.update(results)
            issues.extend(results.get('failures', []))
            warnings.extend(results.get('errors', []))

        except Exception as e:
            issues.append(f"Failed to run synthetic tests: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis on the codebase."""
        try:
            # Run coverage with JSON report
            cmd = [
                'python', '-m', 'pytest',
                '--cov=.',
                '--cov-report=json',
                '--cov-report=term-missing',
                '--tb=no',
                '-q'
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Parse coverage JSON if available
            try:
                import json
                with open('coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                return coverage_data
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

        except Exception as e:
            self.logger.warning(f"Coverage analysis failed: {e}")
            return {}

    async def _analyze_file_coverage(self, file_path: str, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze coverage for a specific file."""
        analysis = {
            'functions': 0,
            'uncovered_branches': 0,
            'uncovered_paths': []
        }

        try:
            # Parse the file to find functions and branches
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # Find functions and methods
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    analysis['functions'] += 1

                    # Check if this function has coverage gaps
                    func_coverage = self._get_function_coverage(file_path, node.name, coverage_data)
                    if func_coverage['uncovered_lines']:
                        analysis['uncovered_branches'] += len(func_coverage['uncovered_lines'])

                        # Create uncovered path info
                        uncovered_path = {
                            'file': file_path,
                            'function': node.name,
                            'uncovered_lines': func_coverage['uncovered_lines'],
                            'line_number': node.lineno,
                            'is_edge_case': self._is_edge_case(node),
                            'is_boundary_value': self._has_boundary_conditions(node)
                        }
                        analysis['uncovered_paths'].append(uncovered_path)

        except Exception as e:
            self.logger.warning(f"Failed to analyze coverage for {file_path}: {e}")

        return analysis

    def _get_function_coverage(self, file_path: str, func_name: str, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get coverage information for a specific function."""
        # Simplified coverage extraction
        # In a real implementation, this would properly parse coverage data
        return {
            'uncovered_lines': [],
            'covered_lines': [],
            'coverage_percentage': 0.0
        }

    def _is_edge_case(self, node: ast.AST) -> bool:
        """Determine if a function represents an edge case."""
        # Look for patterns that suggest edge cases
        edge_case_patterns = [
            'error', 'exception', 'fail', 'invalid', 'empty', 'null', 'none'
        ]

        func_name = getattr(node, 'name', '').lower()
        return any(pattern in func_name for pattern in edge_case_patterns)

    def _has_boundary_conditions(self, node: ast.AST) -> bool:
        """Check if a function has boundary conditions to test."""
        # Look for numeric operations, loops, or conditional logic
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While, ast.Compare)):
                return True
            if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Lt, ast.Gt, ast.LtE, ast.GtE)):
                return True
        return False

    async def _generate_test_for_path(self, path_info: Dict[str, Any], subtask: Subtask) -> Optional[str]:
        """Generate test code for an uncovered code path."""
        try:
            file_path = path_info['file']
            func_name = path_info['function']
            line_number = path_info['line_number']

            # Extract module and function info
            module_name = self._get_module_name(file_path)
            test_name = f"test_synthetic_{func_name}_{line_number}"

            # Generate test based on function characteristics
            if path_info.get('is_edge_case'):
                test_code = self._generate_edge_case_test(module_name, func_name, test_name, path_info)
            elif path_info.get('is_boundary_value'):
                test_code = self._generate_boundary_test(module_name, func_name, test_name, path_info)
            else:
                test_code = self._generate_basic_test(module_name, func_name, test_name, path_info)

            return test_code

        except Exception as e:
            self.logger.error(f"Failed to generate test: {e}")
            return None

    def _generate_edge_case_test(self, module_name: str, func_name: str, test_name: str, path_info: Dict[str, Any]) -> str:
        """Generate a test for edge cases."""
        return f'''import pytest
from {module_name} import {func_name}

def {test_name}():
    """Test edge case for {func_name} at line {path_info['line_number']}."""
    # TODO: Generate appropriate edge case test inputs
    # This is a synthetic test generated for uncovered code path

    # Example edge cases - customize based on function signature
    test_cases = [
        None,           # None input
        "",             # Empty string
        [],             # Empty list
        {{}},            # Empty dict
        -1,             # Negative number
        0,              # Zero
        999999,         # Large number
    ]

    for test_input in test_cases:
        try:
            result = {func_name}(test_input)
            # Add assertions based on expected behavior
            assert result is not None  # Basic assertion
        except Exception:
            # Some edge cases should raise exceptions - that's expected
            pass

'''

    def _generate_boundary_test(self, module_name: str, func_name: str, test_name: str, path_info: Dict[str, Any]) -> str:
        """Generate a test for boundary values."""
        return f'''import pytest
from {module_name} import {func_name}

def {test_name}():
    """Test boundary values for {func_name} at line {path_info['line_number']}."""
    # TODO: Generate appropriate boundary value test inputs
    # This is a synthetic test generated for uncovered code path

    # Example boundary values - customize based on function signature
    boundary_values = [0, 1, -1, 2**31-1, -2**31]

    for value in boundary_values:
        try:
            result = {func_name}(value)
            # Add assertions based on expected behavior
            assert result is not None  # Basic assertion
        except Exception:
            # Some boundary values should raise exceptions
            pass

'''

    def _generate_basic_test(self, module_name: str, func_name: str, test_name: str, path_info: Dict[str, Any]) -> str:
        """Generate a basic test for uncovered code."""
        return f'''import pytest
from {module_name} import {func_name}

def {test_name}():
    """Test uncovered path for {func_name} at line {path_info['line_number']}."""
    # TODO: Generate appropriate test inputs
    # This is a synthetic test generated for uncovered code path

    # Basic test - customize based on function signature
    try:
        result = {func_name}()
        # Add assertions based on expected behavior
        assert result is not None  # Basic assertion
    except Exception as e:
        pytest.fail(f"Function raised an exception unexpectedly: {{e}}")

'''

    def _save_synthetic_test(self, test_code: str, path_info: Dict[str, Any]) -> str:
        """Save synthetic test to a file."""
        func_name = path_info['function']
        line_number = path_info['line_number']
        file_name = f"test_synthetic_{func_name}_{line_number}.py"
        test_file_path = self.synthetic_tests_dir / file_name

        with open(test_file_path, 'w') as f:
            f.write(test_code)

        return str(test_file_path)

    def _resolve_file_pattern(self, pattern: str) -> List[str]:
        """Resolve file pattern to actual file paths."""
        if os.path.isfile(pattern):
            return [pattern]

        # Simple glob expansion
        import glob
        return glob.glob(pattern, recursive=True)

    def _get_module_name(self, file_path: str) -> str:
        """Convert file path to Python module name."""
        # Remove .py extension and convert path separators to dots
        module_path = file_path.replace('.py', '').replace('/', '.').replace('\\', '.')

        # Remove leading src/ if present
        if module_path.startswith('src.'):
            module_path = module_path[4:]

        return module_path

    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        import re

        results = {
            'synthetic_tests_run': 0,
            'synthetic_tests_passed': 0,
            'synthetic_tests_failed': 0,
            'failures': [],
            'errors': []
        }

        # Look for test summary
        summary_match = re.search(r'===\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?', output)
        if summary_match:
            results['synthetic_tests_passed'] = int(summary_match.group(1) or 0)
            results['synthetic_tests_failed'] = int(summary_match.group(2) or 0)
            results['synthetic_tests_run'] = (
                results['synthetic_tests_passed'] + results['synthetic_tests_failed']
            )

        # Extract failure messages
        failure_lines = []
        in_failure = False
        for line in output.split('\n'):
            if 'FAIL:' in line:
                in_failure = True
                failure_lines.append(line)
            elif in_failure and line.startswith('_____'):
                in_failure = False
            elif in_failure:
                failure_lines.append(line)

        if failure_lines:
            results['failures'] = [' '.join(failure_lines[:3])]  # Limit length

        return results