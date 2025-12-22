"""
Repository for persisting and loading code indices.
"""

import json
from pathlib import Path
from typing import Any

from dot_work.python.scan.config import ScanConfig
from dot_work.python.scan.models import (
    ClassEntity,
    CodeIndex,
    FileEntity,
    FunctionEntity,
    ImportInfo,
)


class IndexRepository:
    """Repository for persisting code indices."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        """Initialize the repository.

        Args:
            config: Scan configuration. Uses default if None.
        """
        self.config = config or ScanConfig()

    def save(self, index: CodeIndex) -> None:
        """Save code index to disk.

        Args:
            index: CodeIndex to save.
        """
        self.config.ensure_directories()

        data = {
            "root_path": str(index.root_path),
            "files": {path: self._serialize_file(entity) for path, entity in index.files.items()},
            "metrics": {
                "total_files": index.metrics.total_files,
                "total_functions": index.metrics.total_functions,
                "total_classes": index.metrics.total_classes,
                "total_lines": index.metrics.total_lines,
                "avg_complexity": index.metrics.avg_complexity,
                "max_complexity": index.metrics.max_complexity,
                "high_complexity_functions": index.metrics.high_complexity_functions,
            },
        }

        self.config.index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> CodeIndex | None:
        """Load code index from disk.

        Returns:
            CodeIndex if file exists, None otherwise.
        """
        if not self.config.index_path.exists():
            return None

        try:
            data = json.loads(self.config.index_path.read_text(encoding="utf-8"))

            root_path = Path(data["root_path"])
            index = CodeIndex(root_path=root_path)

            for path_str, file_data in data.get("files", {}).items():
                file_entity = self._deserialize_file(Path(path_str), file_data)
                index.add_file(file_entity)

            metrics_data = data.get("metrics", {})
            index.metrics.total_files = metrics_data.get("total_files", 0)
            index.metrics.total_functions = metrics_data.get("total_functions", 0)
            index.metrics.total_classes = metrics_data.get("total_classes", 0)
            index.metrics.total_lines = metrics_data.get("total_lines", 0)
            index.metrics.avg_complexity = metrics_data.get("avg_complexity", 0.0)
            index.metrics.max_complexity = metrics_data.get("max_complexity", 0)
            index.metrics.high_complexity_functions = metrics_data.get(
                "high_complexity_functions", []
            )

            return index

        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def _serialize_file(self, entity: FileEntity) -> dict[str, Any]:
        """Serialize a FileEntity to dict.

        Args:
            entity: FileEntity to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "path": str(entity.path),
            "line_count": entity.line_count,
            "has_syntax_error": entity.has_syntax_error,
            "error_message": entity.error_message,
            "functions": [self._serialize_function(f) for f in entity.functions],
            "classes": [self._serialize_class(c) for c in entity.classes],
            "imports": [self._serialize_import(i) for i in entity.imports],
        }

    def _deserialize_file(self, path: Path, data: dict[str, Any]) -> FileEntity:
        """Deserialize a FileEntity from dict.

        Args:
            path: File path.
            data: Dictionary data.

        Returns:
            FileEntity instance.
        """
        return FileEntity(
            path=path,
            line_count=data.get("line_count", 0),
            has_syntax_error=data.get("has_syntax_error", False),
            error_message=data.get("error_message"),
            functions=[self._deserialize_function(f) for f in data.get("functions", [])],
            classes=[self._deserialize_class(c) for c in data.get("classes", [])],
            imports=[self._deserialize_import(i) for i in data.get("imports", [])],
        )

    def _serialize_function(self, func: FunctionEntity) -> dict[str, Any]:
        """Serialize a FunctionEntity.

        Args:
            func: FunctionEntity to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "name": func.name,
            "file_path": str(func.file_path),
            "line_no": func.line_no,
            "end_line_no": func.end_line_no,
            "is_async": func.is_async,
            "is_method": func.is_method,
            "args": func.args,
            "returns": func.returns,
            "docstring": func.docstring,
            "decorators": func.decorators,
            "complexity": func.complexity,
        }

    def _deserialize_function(self, data: dict[str, Any]) -> FunctionEntity:
        """Deserialize a FunctionEntity.

        Args:
            data: Dictionary data.

        Returns:
            FunctionEntity instance.
        """
        return FunctionEntity(
            name=data["name"],
            file_path=Path(data["file_path"]),
            line_no=data["line_no"],
            end_line_no=data.get("end_line_no"),
            is_async=data.get("is_async", False),
            is_method=data.get("is_method", False),
            args=data.get("args", []),
            returns=data.get("returns"),
            docstring=data.get("docstring"),
            decorators=data.get("decorators", []),
            complexity=data.get("complexity", 1),
        )

    def _serialize_class(self, cls: ClassEntity) -> dict[str, Any]:
        """Serialize a ClassEntity.

        Args:
            cls: ClassEntity to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "name": cls.name,
            "file_path": str(cls.file_path),
            "line_no": cls.line_no,
            "end_line_no": cls.end_line_no,
            "bases": cls.bases,
            "methods": [self._serialize_function(m) for m in cls.methods],
            "docstring": cls.docstring,
            "decorators": cls.decorators,
        }

    def _deserialize_class(self, data: dict[str, Any]) -> ClassEntity:
        """Deserialize a ClassEntity.

        Args:
            data: Dictionary data.

        Returns:
            ClassEntity instance.
        """
        return ClassEntity(
            name=data["name"],
            file_path=Path(data["file_path"]),
            line_no=data["line_no"],
            end_line_no=data.get("end_line_no"),
            bases=data.get("bases", []),
            methods=[self._deserialize_function(m) for m in data.get("methods", [])],
            docstring=data.get("docstring"),
            decorators=data.get("decorators", []),
        )

    def _serialize_import(self, imp: ImportInfo) -> dict[str, Any]:
        """Serialize an ImportInfo.

        Args:
            imp: ImportInfo to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "module": imp.module,
            "name": imp.name,
            "alias": imp.alias,
            "line_no": imp.line_no,
            "is_from_import": imp.is_from_import,
        }

    def _deserialize_import(self, data: dict[str, Any]) -> ImportInfo:
        """Deserialize an ImportInfo.

        Args:
            data: Dictionary data.

        Returns:
            ImportInfo instance.
        """
        return ImportInfo(
            module=data["module"],
            name=data.get("name"),
            alias=data.get("alias"),
            line_no=data.get("line_no", 0),
            is_from_import=data.get("is_from_import", False),
        )
