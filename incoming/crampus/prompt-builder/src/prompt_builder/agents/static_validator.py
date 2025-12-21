"""Static Validator Agent for compile-level safety checks."""

import ast
import os
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from .base import BaseAgent, measure_execution_time
from ..models import (
    Task,
    Subtask,
    ValidationResult,
    ValidationType,
)


class StaticValidatorAgent(BaseAgent):
    """Performs static analysis and compile-time validation."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")

    def get_validation_type(self) -> ValidationType:
        """Static validator performs static validation."""
        return ValidationType.STATIC

    @measure_execution_time
    async def execute(
        self,
        task: Task,
        subtask: Optional[Subtask] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Perform static validation on affected files."""
        self._log_start(subtask)

        try:
            if not subtask:
                return self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=["Static validation requires a specific subtask"]
                )

            issues = []
            warnings = []
            metrics = {}

            # Get affected files for this subtask
            affected_files = subtask.affected_files

            # Perform various static checks
            syntax_results = await self._check_syntax(affected_files)
            import_results = await self._check_imports(affected_files)
            typing_results = await self._check_typing(affected_files)
            convention_results = await self._check_conventions(affected_files)

            # Aggregate results
            issues.extend(syntax_results['issues'])
            issues.extend(import_results['issues'])
            issues.extend(typing_results['issues'])
            issues.extend(convention_results['issues'])

            warnings.extend(syntax_results['warnings'])
            warnings.extend(import_results['warnings'])
            warnings.extend(typing_results['warnings'])
            warnings.extend(convention_results['warnings'])

            # Combine metrics
            metrics.update(syntax_results['metrics'])
            metrics.update(import_results['metrics'])
            metrics.update(typing_results['metrics'])
            metrics.update(convention_results['metrics'])

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
                issues=[f"Static validation failed: {str(e)}"]
            )
            return result

    async def _check_syntax(self, file_patterns: List[str]) -> Dict[str, Any]:
        """Check Python syntax in affected files."""
        issues = []
        warnings = []
        files_checked = 0
        syntax_errors = 0

        for pattern in file_patterns:
            # Expand glob patterns (basic implementation)
            if pattern.endswith('.py') or '**/*.py' in pattern:
                # Find Python files
                for file_path in self._find_files(pattern):
                    files_checked += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Parse the AST to check syntax
                        ast.parse(content, filename=file_path)

                    except SyntaxError as e:
                        syntax_errors += 1
                        issues.append(f"Syntax error in {file_path}:{e.lineno}: {e.msg}")
                    except UnicodeDecodeError:
                        warnings.append(f"Could not read {file_path} (encoding issue)")
                    except Exception as e:
                        warnings.append(f"Could not parse {file_path}: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': {
                'files_syntax_checked': files_checked,
                'syntax_errors': syntax_errors,
            }
        }

    async def _check_imports(self, file_patterns: List[str]) -> Dict[str, Any]:
        """Check for broken imports and missing dependencies."""
        issues = []
        warnings = []
        files_checked = 0
        import_errors = 0

        for pattern in file_patterns:
            if pattern.endswith('.py') or '**/*.py' in pattern:
                for file_path in self._find_files(pattern):
                    files_checked += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Parse AST to find imports
                        tree = ast.parse(content, filename=file_path)

                        # Check imports
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if not self._is_import_available(alias.name):
                                        import_errors += 1
                                        issues.append(f"Missing import '{alias.name}' in {file_path}")

                            elif isinstance(node, ast.ImportFrom):
                                if node.module and not self._is_import_available(node.module):
                                    import_errors += 1
                                    issues.append(f"Missing import '{node.module}' in {file_path}")

                    except Exception as e:
                        warnings.append(f"Could not check imports in {file_path}: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': {
                'files_import_checked': files_checked,
                'import_errors': import_errors,
            }
        }

    async def _check_typing(self, file_patterns: List[str]) -> Dict[str, Any]:
        """Check type hints and typing consistency."""
        issues = []
        warnings = []
        files_checked = 0
        functions_without_hints = 0

        for pattern in file_patterns:
            if pattern.endswith('.py') or '**/*.py' in pattern:
                for file_path in self._find_files(pattern):
                    files_checked += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        tree = ast.parse(content, filename=file_path)

                        # Check function definitions for type hints
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                # Skip dunder methods and test functions
                                if (node.name.startswith('__') and node.name.endswith('__')) or \
                                   node.name.startswith('test_'):
                                    continue

                                has_return_type = node.returns is not None
                                has_param_types = all(
                                    arg.annotation is not None
                                    for arg in node.args.args
                                    if arg.arg not in ['self', 'cls']
                                )

                                if not has_return_type or not has_param_types:
                                    functions_without_hints += 1
                                    warnings.append(
                                        f"Function '{node.name}' in {file_path} missing type hints"
                                    )

                    except Exception as e:
                        warnings.append(f"Could not check typing in {file_path}: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': {
                'files_typing_checked': files_checked,
                'functions_without_hints': functions_without_hints,
            }
        }

    async def _check_conventions(self, file_patterns: List[str]) -> Dict[str, Any]:
        """Check adherence to project conventions."""
        issues = []
        warnings = []
        files_checked = 0

        for pattern in file_patterns:
            if pattern.endswith('.py') or '**/*.py' in pattern:
                for file_path in self._find_files(pattern):
                    files_checked += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        # Check naming conventions
                        for i, line in enumerate(lines, 1):
                            line = line.strip()

                            # Check for long lines
                            if len(line) > 120:
                                warnings.append(f"Line {i} in {file_path} exceeds 120 characters")

                            # Check for TODO/FIXME comments without ticket numbers
                            if re.search(r'#\s*(TODO|FIXME|HACK)\s*$', line):
                                warnings.append(f"TODO/FIXME at line {i} in {file_path} missing ticket reference")

                            # Check for print statements (should use logging)
                            if 'print(' in line and not line.strip().startswith('#'):
                                warnings.append(f"print() statement at line {i} in {file_path} (consider using logging)")

                    except Exception as e:
                        warnings.append(f"Could not check conventions in {file_path}: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': {
                'files_conventions_checked': files_checked,
            }
        }

    def _find_files(self, pattern: str) -> List[str]:
        """Find files matching the given pattern."""
        files = []

        # Simple glob expansion - in a real implementation, use pathlib.Path.glob()
        if '**' in pattern:
            # Recursive search
            base_pattern = pattern.replace('**/', '')
            for root, dirs, filenames in os.walk('.'):
                for filename in filenames:
                    if self._matches_pattern(filename, base_pattern):
                        files.append(os.path.join(root, filename))
        else:
            # Simple file pattern
            if os.path.exists(pattern):
                files.append(pattern)
            else:
                # Try to find matching files in current directory
                for filename in os.listdir('.'):
                    if self._matches_pattern(filename, pattern):
                        files.append(filename)

        return files

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching (supports wildcards)."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)

    def _is_import_available(self, module_name: str) -> bool:
        """Check if a Python module is available for import."""
        try:
            # Handle relative imports
            if module_name.startswith('.'):
                return True  # Assume relative imports are valid

            # Try to import the module
            __import__(module_name)
            return True
        except ImportError:
            return False
        except Exception:
            # Other import errors (syntax in module, etc.)
            return False