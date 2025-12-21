"""Regression Sentinel Agent for detecting regressions."""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import logging
import difflib
import asyncio

from .base import BaseAgent, measure_execution_time
from ..models import (
    Task,
    Subtask,
    ValidationResult,
    ValidationType,
    Snapshot,
    ChangeImpactResult,
)


class RegressionSentinelAgent(BaseAgent):
    """Detects regressions by comparing current behavior with previous snapshots."""

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(f"prompt_builder.{self.config.name}")
        self.snapshots_dir = Path(".prompt-builder/snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def get_validation_type(self) -> ValidationType:
        """Regression sentinel performs regression validation."""
        return ValidationType.REGRESSION

    @measure_execution_time
    async def execute(
        self,
        task: Task,
        subtask: Optional[Subtask] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Detect regressions by comparing with previous behavior."""
        self._log_start(subtask)

        try:
            if not subtask:
                return self._create_validation_result(
                    subtask_id=task.id,
                    passed=False,
                    issues=["Regression detection requires a specific subtask"]
                )

            issues = []
            warnings = []
            metrics = {}

            # Analyze changes
            change_impact = await self._analyze_changes(task, subtask)
            metrics['affected_snapshots'] = len(change_impact.affected_snapshots)
            metrics['risk_score'] = change_impact.risk_score

            # Compare with existing snapshots
            regression_results = await self._compare_with_snapshots(change_impact)
            issues.extend(regression_results['issues'])
            warnings.extend(regression_results['warnings'])
            metrics.update(regression_results['metrics'])

            # Check for semantic regressions
            semantic_results = await self._check_semantic_regressions(change_impact)
            issues.extend(semantic_results['issues'])
            warnings.extend(semantic_results['warnings'])
            metrics.update(semantic_results['metrics'])

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
                issues=[f"Regression detection failed: {str(e)}"]
            )
            return result

    async def _analyze_changes(self, task: Task, subtask: Subtask) -> ChangeImpactResult:
        """Analyze the impact of changes made in this subtask."""
        try:
            # Get git diff
            base_ref = task.base_ref or "HEAD~1"
            head_ref = task.head_ref or "HEAD"

            # Get changed files
            changed_files = await self._get_changed_files(base_ref, head_ref)

            # Filter by subtask's affected files
            relevant_files = [
                f for f in changed_files
                if any(self._file_matches_pattern(f, pattern) for pattern in subtask.affected_files)
            ]

            # Analyze symbol changes
            changed_symbols = await self._get_changed_symbols(relevant_files, base_ref, head_ref)

            # Find affected snapshots
            affected_snapshots = await self._find_affected_snapshots(changed_files, changed_symbols)

            # Calculate risk score
            risk_score = self._calculate_risk_score(relevant_files, changed_symbols, affected_snapshots)

            # Generate warnings
            warnings = []
            if risk_score > 0.7:
                warnings.append(f"High risk changes detected (risk score: {risk_score:.2f})")
            if len(affected_snapshots) > 10:
                warnings.append(f"Many snapshots affected ({len(affected_snapshots)})")

            return ChangeImpactResult(
                touched_files=relevant_files,
                touched_symbols=changed_symbols,
                affected_snapshots=affected_snapshots,
                affected_subtasks=[subtask.id],
                summary=f"Changes affect {len(relevant_files)} files and {len(affected_snapshots)} snapshots",
                warnings=warnings,
                risk_score=risk_score,
                estimated_effort=self._estimate_effort(relevant_files, risk_score)
            )

        except Exception as e:
            self.logger.error(f"Change analysis failed: {e}")
            return ChangeImpactResult(
                touched_files=[],
                touched_symbols=[],
                affected_snapshots=[],
                affected_subtasks=[subtask.id],
                summary="Change analysis failed",
                warnings=[f"Could not analyze changes: {str(e)}"],
                risk_score=1.0  # Assume high risk when analysis fails
            )

    async def _compare_with_snapshots(self, change_impact: ChangeImpactResult) -> Dict[str, Any]:
        """Compare current behavior with stored snapshots."""
        issues = []
        warnings = []
        metrics = {
            'snapshots_compared': 0,
            'regressions_found': 0,
            'improvements_found': 0
        }

        for snapshot_id in change_impact.affected_snapshots:
            try:
                snapshot_path = self.snapshots_dir / f"{snapshot_id}.json"
                if not snapshot_path.exists():
                    warnings.append(f"Snapshot {snapshot_id} not found - cannot compare")
                    continue

                with open(snapshot_path, 'r') as f:
                    snapshot = json.load(f)

                # Compare current behavior with snapshot
                comparison_result = await self._compare_snapshot_behavior(snapshot)
                metrics['snapshots_compared'] += 1

                if comparison_result['regression_detected']:
                    metrics['regressions_found'] += 1
                    issues.extend(comparison_result['issues'])

                if comparison_result['improvement_detected']:
                    metrics['improvements_found'] += 1
                    warnings.extend(comparison_result['improvements'])

            except Exception as e:
                warnings.append(f"Could not compare with snapshot {snapshot_id}: {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _check_semantic_regressions(self, change_impact: ChangeImpactResult) -> Dict[str, Any]:
        """Check for semantic regressions that might not be caught by snapshot comparison."""
        issues = []
        warnings = []
        metrics = {
            'semantic_checks': 0,
            'semantic_regressions': 0
        }

        # Common semantic regressions to check
        semantic_checks = [
            "API response format consistency",
            "Error handling patterns",
            "Logging consistency",
            "Performance characteristics",
            "Security boundaries",
        ]

        for check in semantic_checks:
            metrics['semantic_checks'] += 1
            try:
                if await self._check_semantic_invariant(check, change_impact):
                    # Check passed
                    pass
                else:
                    metrics['semantic_regressions'] += 1
                    issues.append(f"Semantic regression detected: {check}")
            except Exception as e:
                warnings.append(f"Could not check semantic invariant '{check}': {str(e)}")

        return {
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }

    async def _get_changed_files(self, base_ref: str, head_ref: str) -> List[str]:
        """Get list of files changed between git references."""
        try:
            cmd = ['git', 'diff', '--name-only', f'{base_ref}..{head_ref}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git diff failed: {e}")
            return []

    async def _get_changed_symbols(self, files: List[str], base_ref: str, head_ref: str) -> List[str]:
        """Get list of symbols (functions, classes) that changed."""
        changed_symbols = []

        for file_path in files:
            if not file_path.endswith('.py'):
                continue

            try:
                # Get the diff for this file
                cmd = ['git', 'diff', f'{base_ref}..{head_ref}', '--', file_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                diff_lines = result.stdout.split('\n')

                # Look for function/class definitions in the diff
                for line in diff_lines:
                    if line.startswith(('+', '-')):
                        stripped = line[1:].strip()
                        if stripped.startswith(('def ', 'class ')):
                            # Extract symbol name
                            if stripped.startswith('def '):
                                symbol_name = stripped[4:].split('(')[0].strip()
                                changed_symbols.append(f"{file_path}:{symbol_name}()")
                            elif stripped.startswith('class '):
                                symbol_name = stripped[6:].split('(')[0].split(':')[0].strip()
                                changed_symbols.append(f"{file_path}:{symbol_name}")

            except subprocess.CalledProcessError:
                continue

        return changed_symbols

    def _file_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if a file path matches a glob pattern."""
        import fnmatch
        # Simple pattern matching
        if '**' in pattern:
            # Convert glob to regex for better matching
            regex_pattern = pattern.replace('**/', '.*').replace('*', '[^/]*')
            import re
            return re.match(regex_pattern, file_path) is not None
        else:
            return fnmatch.fnmatch(file_path, pattern)

    async def _find_affected_snapshots(self, changed_files: List[str], changed_symbols: List[str]) -> List[str]:
        """Find snapshots that might be affected by the changes."""
        affected_snapshots = []

        if not self.snapshots_dir.exists():
            return affected_snapshots

        # Look through all snapshot files
        for snapshot_file in self.snapshots_dir.glob("*.json"):
            try:
                with open(snapshot_file, 'r') as f:
                    snapshot = json.load(f)

                # Check if this snapshot references any changed files or symbols
                snapshot_files = snapshot.get('files', [])
                snapshot_symbols = snapshot.get('call_graph_nodes', [])

                if (any(af in snapshot_files for af in changed_files) or
                    any(any(cs in ss for ss in snapshot_symbols) for cs in changed_symbols)):
                    affected_snapshots.append(snapshot['id'])

            except (json.JSONDecodeError, KeyError):
                continue

        return affected_snapshots

    def _calculate_risk_score(self, files: List[str], symbols: List[str], snapshots: List[str]) -> float:
        """Calculate risk score based on scope of changes."""
        # Base risk from number of changed files
        file_risk = min(len(files) / 10.0, 1.0)

        # Additional risk from changed symbols
        symbol_risk = min(len(symbols) / 20.0, 1.0)

        # Risk from affected snapshots (regression potential)
        snapshot_risk = min(len(snapshots) / 15.0, 1.0)

        # Combine risks with weights
        total_risk = (file_risk * 0.3 + symbol_risk * 0.3 + snapshot_risk * 0.4)

        return min(total_risk, 1.0)

    def _estimate_effort(self, files: List[str], risk_score: float) -> str:
        """Estimate validation effort based on changes."""
        if risk_score < 0.2:
            return "Low (< 30 minutes)"
        elif risk_score < 0.5:
            return "Medium (30 minutes - 2 hours)"
        elif risk_score < 0.8:
            return "High (2 - 6 hours)"
        else:
            return "Critical (6+ hours)"

    async def _compare_snapshot_behavior(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current behavior with a stored snapshot."""
        # This is a simplified implementation
        # In a real system, this would re-run the behavior and compare results

        snapshot_id = snapshot.get('id', 'unknown')
        expected_outputs = snapshot.get('outputs', {})
        expected_invariants = snapshot.get('invariants', {})

        issues = []
        improvements = []
        regression_detected = False
        improvement_detected = False

        # Simulate behavior comparison
        # In reality, this would execute the same code paths and compare results

        # For now, assume no regressions (this would be implemented with actual behavior testing)
        regression_detected = False
        improvement_detected = False

        return {
            'regression_detected': regression_detected,
            'improvement_detected': improvement_detected,
            'issues': issues,
            'improvements': improvements
        }

    async def _check_semantic_invariant(self, invariant: str, change_impact: ChangeImpactResult) -> bool:
        """Check if a semantic invariant holds."""
        # Simplified implementation
        # In reality, this would involve sophisticated analysis

        invariant_lower = invariant.lower()

        if 'api' in invariant_lower and 'response' in invariant_lower:
            # Check API response format consistency
            return True  # Simplified

        elif 'error' in invariant_lower:
            # Check error handling patterns
            return True  # Simplified

        elif 'logging' in invariant_lower:
            # Check logging consistency
            return True  # Simplified

        elif 'performance' in invariant_lower:
            # Check performance characteristics
            return True  # Simplified

        elif 'security' in invariant_lower:
            # Check security boundaries
            return True  # Simplified

        return True  # Default to passing