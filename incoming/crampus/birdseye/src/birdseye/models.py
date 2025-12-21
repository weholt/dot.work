"""Domain models for feature analysis output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _str_list_factory() -> list[str]:
    return []


@dataclass(slots=True)
class Argument:
    """Represents a callable argument."""

    name: str
    annotation: str | None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "type": self.annotation}


@dataclass(slots=True)
class Feature:
    """Represents a callable surface area discovered in the project."""

    name: str
    qualified_name: str
    kind: str
    module_path: str
    parent: str | None
    docstring: str | None
    args: list[Argument]
    returns: str | None
    avg_complexity: float
    maintainability_index: float
    api: bool = False
    cli: bool = False
    mcp: bool = False
    web: bool = False
    user_facing: bool = False
    doc_refs: list[str] = field(default_factory=_str_list_factory)
    feature_id: str | None = None

    def short_doc(self) -> str:
        if not self.docstring:
            return "No description provided."
        first_sentence = self.docstring.strip().split(".\n")[0].strip()
        return first_sentence.rstrip(".") + "."

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["args"] = [arg.to_dict() for arg in self.args]
        return payload


@dataclass(slots=True)
class ModelField:
    """Represents an extracted model field."""

    name: str
    annotation: str | None
    default: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModelDef:
    """Represents a data model definition."""

    name: str
    qualified_name: str
    bases: list[str]
    docstring: str | None
    fields: list[ModelField]
    module_path: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fields"] = [field.to_dict() for field in self.fields]
        return payload


@dataclass(slots=True)
class DocumentSection:
    """Represents a markdown section for cross-reference."""

    source_path: str
    heading: str
    level: int
    content: str
    slug: str

    def summary(self) -> str:
        preview = " ".join(self.content.strip().split())
        return preview[:220] + ("…" if len(preview) > 220 else "")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisBundle:
    """Aggregate output from the analysis pipeline."""

    features: list[Feature]
    models: list[ModelDef]
    documents: list[DocumentSection]

    def to_dict(self) -> dict[str, Any]:
        return {
            "features": [feature.to_dict() for feature in self.features],
            "models": [model.to_dict() for model in self.models],
            "documents": [doc.to_dict() for doc in self.documents],
        }
