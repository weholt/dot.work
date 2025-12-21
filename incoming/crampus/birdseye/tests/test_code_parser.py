"""Unit tests for code parser helpers."""

from __future__ import annotations

from pathlib import Path

from birdseye.code_parser import parse_python_file


def test_parse_python_file_detects_api_feature(sample_project: Path) -> None:
    api_file = sample_project / "api.py"
    result = parse_python_file(api_file, api_file.read_text(encoding="utf-8"), module_path="api.py")

    names = {feature.name for feature in result["features"]}
    assert "read_greeting" in names

    feature = next(item for item in result["features"] if item.name == "read_greeting")
    assert feature.api and feature.user_facing
    assert feature.args and feature.args[0].name == "name"
    assert feature.returns == "dict[str, str]"


def test_parse_python_file_extracts_models(sample_project: Path) -> None:
    models_file = sample_project / "models.py"
    result = parse_python_file(models_file, models_file.read_text(encoding="utf-8"), module_path="models.py")

    assert result["models"], "expected at least one model"
    profile = next(model for model in result["models"] if model.name == "Profile")
    assert len(profile.fields) == 2
    assert any(field.name == "username" for field in profile.fields)
    assert any(field.name == "bio" and (field.default in {None, "None"}) for field in profile.fields)
