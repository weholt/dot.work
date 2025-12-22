"""
AST entity extraction from Python source code.
"""

import ast
from pathlib import Path

from dot_work.python.scan.models import (
    ClassEntity,
    FileEntity,
    FunctionEntity,
    ImportInfo,
)


class ASTExtractor(ast.NodeVisitor):
    """Extract entities from Python AST."""

    def __init__(self, file_path: Path) -> None:
        """Initialize the extractor.

        Args:
            file_path: Path to the file being analyzed.
        """
        self.file_path = file_path
        self.functions: list[FunctionEntity] = []
        self.classes: list[ClassEntity] = []
        self.imports: list[ImportInfo] = []
        self.current_class: ClassEntity | None = None

    def extract(self, source: str) -> FileEntity:
        """Extract entities from source code.

        Args:
            source: Python source code string.

        Returns:
            FileEntity with extracted entities.
        """
        try:
            tree = ast.parse(source, filename=str(self.file_path))
            self.visit(tree)
            line_count = source.count("\n") + 1
            return FileEntity(
                path=self.file_path,
                functions=self.functions,
                classes=self.classes,
                imports=self.imports,
                line_count=line_count,
                has_syntax_error=False,
            )
        except SyntaxError as e:
            return FileEntity(
                path=self.file_path,
                functions=[],
                classes=[],
                imports=[],
                line_count=source.count("\n") + 1 if source else 0,
                has_syntax_error=True,
                error_message=str(e),
            )

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Visit function definition node.

        Args:
            node: AST function node.
        """
        is_async = isinstance(node, ast.AsyncFunctionDef)

        # Extract function info
        func = FunctionEntity(
            name=node.name,
            file_path=self.file_path,
            line_no=node.lineno,
            end_line_no=node.end_lineno,
            is_async=is_async,
            is_method=self.current_class is not None,
            args=[a.arg for a in node.args.args],
            returns=(ast.unparse(node.returns) if node.returns else None),
            docstring=ast.get_docstring(node),
            decorators=[ast.unparse(d) for d in node.decorator_list],
        )

        # Add to current class if inside class
        if self.current_class:
            self.current_class.methods.append(func)
        else:
            self.functions.append(func)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition.

        Args:
            node: AST async function node.
        """
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition node.

        Args:
            node: AST class node.
        """
        # Extract base classes
        bases = [ast.unparse(b) for b in node.bases]

        # Create class entity
        cls = ClassEntity(
            name=node.name,
            file_path=self.file_path,
            line_no=node.lineno,
            end_line_no=node.end_lineno,
            bases=bases,
            docstring=ast.get_docstring(node),
            decorators=[ast.unparse(d) for d in node.decorator_list],
        )

        # Save previous class and set current
        prev_class = self.current_class
        self.current_class = cls

        # Visit class body (will extract methods)
        self.generic_visit(node)

        # Restore previous class and add this class
        self.current_class = prev_class
        self.classes.append(cls)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement.

        Args:
            node: AST import node.
        """
        for alias in node.names:
            imp = ImportInfo(
                module=alias.name,
                alias=alias.asname,
                line_no=node.lineno,
                is_from_import=False,
            )
            self.imports.append(imp)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement.

        Args:
            node: AST import from node.
        """
        module = node.module or ""
        for alias in node.names:
            imp = ImportInfo(
                module=module,
                name=alias.name,
                alias=alias.asname,
                line_no=node.lineno,
                is_from_import=True,
            )
            self.imports.append(imp)
        self.generic_visit(node)


def extract_entities(source: str, file_path: Path) -> FileEntity:
    """Extract entities from Python source code.

    Args:
        source: Python source code string.
        file_path: Path to the source file.

    Returns:
        FileEntity with extracted entities.
    """
    extractor = ASTExtractor(file_path)
    return extractor.extract(source)
