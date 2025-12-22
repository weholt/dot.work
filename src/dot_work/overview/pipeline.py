"""Overview orchestration pipeline."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .code_parser import export_features_to_json, parse_python_file
from .markdown_parser import extract_sections, slugify_fragment
from .models import AnalysisBundle, DocumentSection, Feature, ModelDef
from .reporter import build_markdown_report
from .scanner import iter_project_files, load_scanner_config


def analyze_project(root: Path) -> AnalysisBundle:
    """Analyze a project directory and return collected metadata."""

    root = root.resolve()
    features: list[Feature] = []
    models: list[ModelDef] = []
    documents: list[DocumentSection] = []

    scanner_config = load_scanner_config(root)

    for project_file in iter_project_files(
        root,
        include_ext=sorted(scanner_config.include_ext),
        exclude_dirs=sorted(scanner_config.exclude_dirs),
    ):
        relative = project_file.path.relative_to(root)
        text = project_file.read_text()
        if project_file.suffix == ".py":
            result = parse_python_file(project_file.path, text, module_path=str(relative))
            features.extend(result["features"])
            models.extend(result["models"])
        elif project_file.suffix == ".md":
            documents.extend(extract_sections(relative, text))

    _attach_document_references(features, documents)
    _assign_feature_ids(features)

    return AnalysisBundle(features=features, models=models, documents=documents)


def write_outputs(bundle: AnalysisBundle, output_dir: Path) -> dict[str, Path]:
    """Persist bundle to the target directory."""

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    feature_json_path = output_dir / "features.json"
    export_features_to_json(bundle.features, bundle.models, feature_json_path)

    document_json_path = output_dir / "documents.json"
    document_json_path.write_text(
        json.dumps([doc.to_dict() for doc in bundle.documents], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    overview_path = output_dir / "birdseye_overview.md"
    overview_path.write_text(build_markdown_report(bundle), encoding="utf-8")

    return {
        "features_json": feature_json_path,
        "documents_json": document_json_path,
        "overview_markdown": overview_path,
    }


def _attach_document_references(
    features: Iterable[Feature], documents: Iterable[DocumentSection]
) -> None:
    doc_lookup: dict[str, list[DocumentSection]] = {}
    for section in documents:
        leaf = section.slug.split("#")[-1]
        doc_lookup.setdefault(leaf, []).append(section)
        doc_lookup.setdefault(section.heading.lower(), []).append(section)

    for feature in features:
        candidate_slugs: set[str] = {slugify_fragment(feature.name)}
        if feature.parent:
            parent_slug = slugify_fragment(feature.parent)
            candidate_slugs.add(f"{parent_slug}-{slugify_fragment(feature.name)}")

        collected: list[DocumentSection] = []
        for candidate in candidate_slugs:
            collected.extend(doc_lookup.get(candidate, []))
        if not collected:
            continue
        anchors = [section.slug for section in collected]
        # Deduplicate while preserving order
        seen: dict[str, None] = {}
        for anchor in anchors:
            if anchor not in seen:
                seen[anchor] = None
        feature.doc_refs = list(seen.keys())


def _assign_feature_ids(features: list[Feature]) -> None:
    ordered = sorted(features, key=lambda feat: (feat.module_path, feat.kind, feat.qualified_name))
    for index, feature in enumerate(ordered, start=1):
        feature.feature_id = f"F-{index:04d}"
