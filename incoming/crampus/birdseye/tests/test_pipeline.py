"""Integration tests for the analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from birdseye.pipeline import analyze_project, write_outputs


def test_analyze_project_discovers_features(sample_project: Path) -> None:
    bundle = analyze_project(sample_project)

    assert len(bundle.features) >= 4
    feature_ids = {feature.feature_id for feature in bundle.features}
    assert all(fid is not None for fid in feature_ids)

    api_feature = next(
        feature for feature in bundle.features if feature.qualified_name.endswith("api.py:read_greeting")
    )
    assert api_feature.api and api_feature.user_facing
    assert any(arg.name == "name" for arg in api_feature.args)

    cli_feature = next(feature for feature in bundle.features if feature.qualified_name.endswith("cli.py:greet"))
    assert cli_feature.cli and cli_feature.user_facing

    service_method = next(
        feature for feature in bundle.features if feature.qualified_name.endswith("services.py:GreetingService.greet")
    )
    assert service_method.doc_refs

    assert bundle.models
    profile_model = next(model for model in bundle.models if model.name == "Profile")
    field_names = {field.name for field in profile_model.fields}
    assert {"username", "bio"}.issubset(field_names)

    assert bundle.documents


def test_write_outputs_materializes_bundle(sample_project: Path, tmp_path: Path) -> None:
    bundle = analyze_project(sample_project)
    output_dir = tmp_path / "artifacts"

    artifacts = write_outputs(bundle, output_dir)

    assert artifacts["features_json"].exists()
    assert artifacts["documents_json"].exists()
    assert artifacts["overview_markdown"].exists()

    feature_payload = json.loads(artifacts["features_json"].read_text(encoding="utf-8"))
    assert "features" in feature_payload and feature_payload["features"], "features json should contain entries"

    document_payload = json.loads(artifacts["documents_json"].read_text(encoding="utf-8"))
    assert document_payload, "document json should contain sections"
