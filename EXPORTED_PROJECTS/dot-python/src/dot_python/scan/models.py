"""
Data models for Python code scanner.

Entities representing classes, functions, imports, and the code index.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Location:
    """Source code location."""

    file_path: Path
    line_no: int
    column: int = 0


@dataclass
class FunctionEntity:
    """Represents a Python function or method."""

    name: str
    file_path: Path
    line_no: int
    end_line_no: int | None = None
    is_async: bool = False
    is_method: bool = False
    args: list[str] = field(default_factory=list)
    returns: str | None = None
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    complexity: int = 1


@dataclass
class ClassEntity:
    """Represents a Python class."""

    name: str
    file_path: Path
    line_no: int
    end_line_no: int | None = None
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionEntity] = field(default_factory=list)
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Represents an import statement."""

    module: str
    name: str | None = None  # For "from x import y"
    alias: str | None = None  # For "import x as y"
    line_no: int = 0
    is_from_import: bool = False


@dataclass
class FileEntity:
    """Represents a scanned Python source file."""

    path: Path
    functions: list[FunctionEntity] = field(default_factory=list)
    classes: list[ClassEntity] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    line_count: int = 0
    has_syntax_error: bool = False
    error_message: str | None = None


@dataclass
class Dependency:
    """Represents a dependency relationship between files."""

    from_file: Path
    to_file: Path
    import_name: str
    line_no: int


@dataclass
class CodeMetrics:
    """Complexity and quality metrics for a codebase."""

    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0
    high_complexity_functions: list[str] = field(default_factory=list)


@dataclass
class CodeIndex:
    """Main index for scanned Python codebase."""

    root_path: Path
    files: dict[str, FileEntity] = field(default_factory=dict)
    classes: dict[str, list[ClassEntity]] = field(default_factory=dict)
    functions: dict[str, list[FunctionEntity]] = field(default_factory=dict)
    imports: dict[str, list[ImportInfo]] = field(default_factory=dict)
    dependencies: list[Dependency] = field(default_factory=list)
    metrics: CodeMetrics = field(default_factory=CodeMetrics)

    def add_file(self, file_entity: FileEntity) -> None:
        """Add a file entity to the index.

        Args:
            file_entity: The file entity to add.
        """
        key = str(file_entity.path)
        self.files[key] = file_entity

        for func in file_entity.functions:
            if func.name not in self.functions:
                self.functions[func.name] = []
            self.functions[func.name].append(func)

        for cls in file_entity.classes:
            if cls.name not in self.classes:
                self.classes[cls.name] = []
            self.classes[cls.name].append(cls)

    def find_function(self, name: str) -> list[FunctionEntity] | None:
        """Find functions by name.

        Args:
            name: Function name to search for.

        Returns:
            List of matching functions or None.
        """
        return self.functions.get(name)

    def find_class(self, name: str) -> list[ClassEntity] | None:
        """Find classes by name.

        Args:
            name: Class name to search for.

        Returns:
            List of matching classes or None.
        """
        return self.classes.get(name)

    def get_complex_functions(self, threshold: int) -> list[FunctionEntity]:
        """Get functions exceeding complexity threshold.

        Args:
            threshold: Minimum complexity to include.

        Returns:
            List of complex functions.
        """
        result: list[FunctionEntity] = []
        for funcs in self.functions.values():
            for func in funcs:
                if func.complexity >= threshold:
                    result.append(func)
        return sorted(result, key=lambda f: f.complexity, reverse=True)


@dataclass
class CacheEntry:
    """Entry for incremental scan cache."""

    path: str
    mtime: float
    size: int
    hash: str | None = None
