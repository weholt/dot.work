"""
Rule engine for YAML-based code quality rules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_work.python.scan.models import CodeIndex


@dataclass
class Rule:
    """A code quality rule."""

    name: str
    description: str
    severity: str  # "error", "warning", "info"
    condition: dict[str, Any]


@dataclass
class RuleViolation:
    """A rule violation found during checking."""

    rule: str
    file: str
    line: int
    severity: str
    message: str


class RuleEngine:
    """Engine for evaluating YAML-based rules."""

    def __init__(self, rules_path: Path) -> None:
        """Initialize the rule engine.

        Args:
            rules_path: Path to YAML rules file.
        """
        self.rules_path = rules_path
        self.rules: list[Rule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from YAML file."""
        if not self.rules_path.exists():
            return

        try:
            data = yaml.safe_load(self.rules_path.read_text(encoding="utf-8"))
            if not data:
                return

            for rule_data in data.get("rules", []):
                rule = Rule(
                    name=rule_data.get("name", ""),
                    description=rule_data.get("description", ""),
                    severity=rule_data.get("severity", "info"),
                    condition=rule_data.get("condition", {}),
                )
                self.rules.append(rule)
        except (OSError, yaml.YAMLError, KeyError):
            pass

    def check(self, index: CodeIndex) -> list[RuleViolation]:
        """Check code index against all rules.

        Args:
            index: CodeIndex to check.

        Returns:
            List of rule violations.
        """
        violations: list[RuleViolation] = []

        for rule in self.rules:
            violations.extend(self._check_rule(rule, index))

        return violations

    def _check_rule(self, rule: Rule, index: CodeIndex) -> list[RuleViolation]:
        """Check a single rule against the index.

        Args:
            rule: Rule to check.
            index: CodeIndex to check against.

        Returns:
            List of violations for this rule.
        """
        violations: list[RuleViolation] = []
        condition = rule.condition

        # Check complexity threshold
        if "max_complexity" in condition:
            threshold = condition["max_complexity"]
            for file_entity in index.files.values():
                for func in file_entity.functions:
                    if func.complexity > threshold:
                        violations.append(
                            RuleViolation(
                                rule=rule.name,
                                file=str(func.file_path),
                                line=func.line_no,
                                severity=rule.severity,
                                message=rule.description.format(
                                    func=func.name, complexity=func.complexity
                                ),
                            )
                        )

                for cls in file_entity.classes:
                    for method in cls.methods:
                        if method.complexity > threshold:
                            violations.append(
                                RuleViolation(
                                    rule=rule.name,
                                    file=str(method.file_path),
                                    line=method.line_no,
                                    severity=rule.severity,
                                    message=rule.description.format(
                                        func=method.name,
                                        complexity=method.complexity,
                                    ),
                                )
                            )

        # Check file length
        if "max_file_length" in condition:
            max_lines = condition["max_file_length"]
            for file_entity in index.files.values():
                if file_entity.line_count > max_lines:
                    violations.append(
                        RuleViolation(
                            rule=rule.name,
                            file=str(file_entity.path),
                            line=1,
                            severity=rule.severity,
                            message=rule.description.format(
                                file=file_entity.path,
                                lines=file_entity.line_count,
                            ),
                        )
                    )

        return violations


def load_rules(rules_path: Path) -> RuleEngine:
    """Load a rule engine from a YAML rules file.

    Args:
        rules_path: Path to rules file.

    Returns:
        Configured RuleEngine instance.
    """
    return RuleEngine(rules_path)
