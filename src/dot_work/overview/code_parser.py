"""Code parsing utilities leveraging LibCST and radon."""

from __future__ import annotations

import json
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import libcst as cst
from radon.complexity import cc_visit  # type: ignore[import-untyped]
from radon.metrics import mi_visit  # type: ignore[import-untyped]

from .models import Argument, Feature, ModelDef, ModelField

_INTERFACE_DECORATOR_MARKERS: dict[str, list[str]] = {
    "api": ["app.get", "app.post", "router.get", "router.post", "flask.route", "bp.route"],
    "cli": ["app.command", "cli.command", "typer.command", "click.command"],
    "mcp": ["mcp", "mcp_tool"],
    "web": ["app.websocket", "socketio.on", "app.route"],
}

_INTERFACE_DOC_MARKERS: dict[str, list[str]] = {
    "api": ["api", "rest", "endpoint", "request"],
    "cli": ["cli", "command", "terminal"],
    "mcp": ["mcp", "model context"],
    "web": ["web", "http", "browser"],
}

_MODULE_TEMPLATE = cst.Module([])


def _calc_metrics(code: str) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    try:
        cc_items = cc_visit(code)
        avg_complexity = round(
            sum(item.complexity for item in cc_items) / max(1, len(cc_items)),
            2,
        )
        maintainability = round(mi_visit(code, True), 2)
        file_metrics = {"avg_complexity": avg_complexity, "maintainability_index": maintainability}

        per_item: dict[str, dict[str, float]] = {}
        lines = code.splitlines()
        for item in cc_items:
            key = f"{item.classname}.{item.name}" if item.classname else item.name
            snippet = _extract_snippet(lines, item.lineno, getattr(item, "endline", item.lineno))
            per_item[key] = {
                "avg_complexity": round(float(item.complexity), 2),
                "maintainability_index": _safe_mi(snippet, maintainability),
            }

        return file_metrics, per_item
    except Exception:
        return ({"avg_complexity": 0.0, "maintainability_index": 0.0}, {})


def _extract_snippet(lines: list[str], start: int, end: int) -> str:
    snippet = "\n".join(lines[start - 1 : end])
    return textwrap.dedent(snippet)


def _safe_mi(code: str, fallback: float) -> float:
    try:
        if not code.strip():
            return fallback
        return round(mi_visit(code, True), 2)
    except Exception:
        return fallback


def parse_python_file(path: Path, code: str, module_path: str) -> dict[str, list[Any]]:
    """Return discovered features and models for a given Python file."""

    file_metrics, item_metrics = _calc_metrics(code)

    try:
        module = cst.parse_module(code)
    except Exception:
        return {"features": [], "models": []}

    collector = _Collector(
        module_path=module_path,
        file_metrics=file_metrics,
        item_metrics=item_metrics,
    )
    module.visit(collector)
    return {"features": collector.features, "models": collector.models}


class _Collector(cst.CSTVisitor):
    """Collects feature and model information from a module."""

    def __init__(
        self,
        module_path: str,
        file_metrics: dict[str, float],
        item_metrics: dict[str, dict[str, float]],
    ) -> None:
        self.module_path = module_path
        self.file_metrics = file_metrics
        self.item_metrics = item_metrics
        self.features: list[Feature] = []
        self.models: list[ModelDef] = []
        self._current_class: str | None = None

    # ---------------------------- class handling ---------------------------- #
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        class_name = node.name.value
        bases = [
            expr
            for expr in (
                self._render_expression(getattr(base, "value", None)) for base in node.bases
            )
            if expr
        ]
        docstring = self._extract_docstring(node)
        if self._looks_like_model(bases, node):
            fields = list(self._extract_fields(node))
            model = ModelDef(
                name=class_name,
                qualified_name=f"{self.module_path}:{class_name}",
                bases=bases,
                docstring=docstring,
                fields=fields,
                module_path=self.module_path,
            )
            self.models.append(model)
        else:
            decorators = [self._render_expression(dec.decorator) for dec in node.decorators]
            interface_flags = self._interface_flags(decorators, docstring)
            metrics = self._lookup_metrics(class_name)
            feature = Feature(
                name=class_name,
                qualified_name=f"{self.module_path}:{class_name}",
                kind="class",
                module_path=self.module_path,
                parent=None,
                docstring=docstring,
                args=[],
                returns=None,
                avg_complexity=metrics["avg_complexity"],
                maintainability_index=metrics["maintainability_index"],
                api=interface_flags["api"],
                cli=interface_flags["cli"],
                mcp=interface_flags["mcp"],
                web=interface_flags["web"],
                user_facing=False,  # Set below
            )
            feature.user_facing = self._is_user_facing(feature)
            self.features.append(feature)
        self._current_class = class_name

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self._current_class = None

    # --------------------------- function handling ------------------------- #
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        args = [
            Argument(
                name=param.name.value,
                annotation=self._render_expression(param.annotation.annotation)
                if param.annotation
                else None,
            )
            for param in node.params.params
        ]
        decorators = [self._render_expression(dec.decorator) for dec in node.decorators]
        docstring = self._extract_docstring(node)
        interface_flags = self._interface_flags(decorators, docstring)
        metrics = self._lookup_metrics(self._qualify_name(node.name.value))
        feature = Feature(
            name=node.name.value,
            qualified_name=f"{self.module_path}:{self._qualify_name(node.name.value)}",
            kind="method" if self._current_class else "function",
            module_path=self.module_path,
            parent=self._current_class,
            docstring=docstring,
            args=args,
            returns=self._render_expression(node.returns.annotation) if node.returns else None,
            avg_complexity=metrics["avg_complexity"],
            maintainability_index=metrics["maintainability_index"],
            api=interface_flags["api"],
            cli=interface_flags["cli"],
            mcp=interface_flags["mcp"],
            web=interface_flags["web"],
            user_facing=False,  # Set below
        )
        feature.user_facing = self._is_user_facing(feature)
        self.features.append(feature)

    # ---------------------------- helpers --------------------------------- #
    def _qualify_name(self, name: str) -> str:
        if self._current_class:
            return f"{self._current_class}.{name}"
        return name

    def _extract_docstring(self, node: cst.CSTNode) -> str | None:
        body = getattr(node, "body", None)
        if not body or not isinstance(body, (cst.IndentedBlock, cst.BaseSuite)):
            return None
        statements = getattr(body, "body", [])
        if not statements:
            return None
        first = statements[0]
        if isinstance(first, cst.SimpleStatementLine) and first.body:
            expr = first.body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                value = expr.value.evaluated_value
                return value.decode() if isinstance(value, bytes) else value
        return None

    def _looks_like_model(self, bases: list[str], node: cst.ClassDef) -> bool:
        base_text = " ".join(base.lower() for base in bases)
        if any(keyword in base_text for keyword in ("basemodel", "dataclass", "attrs", "model")):
            return True
        return any(isinstance(element, cst.AnnAssign) for element in node.body.body)

    def _extract_fields(self, node: cst.ClassDef) -> Iterable[ModelField]:
        for element in node.body.body:
            ann_assignments = []
            if isinstance(element, cst.AnnAssign):
                ann_assignments.append(element)
            elif isinstance(element, cst.SimpleStatementLine):
                ann_assignments.extend(
                    stmt for stmt in element.body if isinstance(stmt, cst.AnnAssign)
                )

            for ann in ann_assignments:
                name_node = ann.target
                annotation_node = ann.annotation.annotation if ann.annotation else None
                default_repr = self._render_expression(ann.value) if ann.value else None
                field_name = name_node.value if isinstance(name_node, cst.Name) else None
                if not field_name:
                    continue
                yield ModelField(
                    name=field_name,
                    annotation=self._render_expression(annotation_node)
                    if annotation_node
                    else None,
                    default=default_repr,
                )

    def _render_expression(self, node: cst.CSTNode | None) -> str | None:
        if node is None:
            return None
        try:
            result = _MODULE_TEMPLATE.code_for_node(node)
            # code_for_node returns str | bytes
            if isinstance(result, bytes):
                return result.decode()
            return result if isinstance(result, str) else str(result)
        except Exception:
            return None

    def _interface_flags(
        self, decorators: Iterable[str | None], docstring: str | None
    ) -> dict[str, bool]:
        doc = (docstring or "").lower()
        rendered = [decorator for decorator in decorators if decorator]
        flags = dict.fromkeys(_INTERFACE_DECORATOR_MARKERS, False)
        for key, markers in _INTERFACE_DECORATOR_MARKERS.items():
            if any(marker in deco for deco in rendered for marker in markers):
                flags[key] = True
                continue
            if any(hint in doc for hint in _INTERFACE_DOC_MARKERS.get(key, [])):
                flags[key] = True
        return flags

    def _lookup_metrics(self, qualified_local_name: str) -> dict[str, float]:
        metrics = self.item_metrics.get(qualified_local_name)
        if metrics:
            return metrics
        return self.file_metrics.copy()

    def _is_user_facing(self, feature: Feature) -> bool:
        doc = (feature.docstring or "").lower()
        name = feature.name.lower()
        if any(getattr(feature, key) for key in ("api", "cli", "web", "mcp")):
            return True
        if any(
            token in name
            for token in ("handle", "serve", "command", "endpoint", "route", "process_request")
        ):
            return True
        return any(
            token in doc for token in ("user", "input", "request", "api", "cli", "browser", "http")
        )

    # ---------------------------------------------------------------------- #


def export_features_to_json(
    features: Iterable[Feature], models: Iterable[ModelDef], destination: Path
) -> None:
    """Write extracted structures to JSON for subsequent LLM ingestion."""

    payload = {
        "features": [feature.to_dict() for feature in features],
        "models": [model.to_dict() for model in models],
    }
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
