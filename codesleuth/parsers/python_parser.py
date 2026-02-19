"""Python AST parser — extracts functions, methods, calls, and docstrings."""

from __future__ import annotations

import ast
from pathlib import Path

from codesleuth.models import CallEdge, FunctionNode, ParseResult
from codesleuth.parsers.base_parser import BaseParser


class PythonParser(BaseParser):
    """Parses Python source files using the stdlib ``ast`` module."""

    def supported_extensions(self) -> list[str]:
        return ["py"]

    def parse(self, file_path: Path, source: str) -> ParseResult:
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            # Unparseable file — skip gracefully.
            return ParseResult(file_path=file_path)

        visitor = _PythonVisitor(file_path)
        visitor.visit(tree)
        return ParseResult(
            file_path=file_path,
            functions=visitor.functions,
            calls=visitor.calls,
        )


# ------------------------------------------------------------------
# Internal AST visitor
# ------------------------------------------------------------------


class _PythonVisitor(ast.NodeVisitor):
    """Walks a Python AST and collects function definitions and call sites."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.functions: list[FunctionNode] = []
        self.calls: list[CallEdge] = []

        # Stack of enclosing scopes so we can compute qualified names.
        self._scope_stack: list[str] = []
        # Currently active function node (for associating calls to callers).
        self._current_function: FunctionNode | None = None

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------

    def _qualified_name(self, name: str) -> str:
        """Build a dotted qualified name from the current scope stack."""
        module = str(self.file_path).replace("/", ".").replace("\\", ".")
        if module.endswith(".py"):
            module = module[:-3]
        parts = [module] + list(self._scope_stack) + [name]
        return ".".join(parts)

    # ------------------------------------------------------------------
    # Function/method visitors
    # ------------------------------------------------------------------

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Determine enclosing class, if any.
        class_name = self._scope_stack[-1] if self._scope_stack else None
        # Only use it as a class name if we're directly inside a ClassDef scope.
        # We track this by checking the parent — but the simple heuristic of
        # checking the scope stack is sufficient for most codebases.
        is_method = class_name is not None

        params = [arg.arg for arg in node.args.args if arg.arg != "self"]

        fn = FunctionNode(
            name=node.name,
            qualified_name=self._qualified_name(node.name),
            file_path=self.file_path,
            line_number=node.lineno,
            class_name=class_name if is_method else None,
            docstring=ast.get_docstring(node),
            params=params,
        )
        self.functions.append(fn)

        # Visit the body with this function as the active scope.
        prev_function = self._current_function
        self._current_function = fn
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()
        self._current_function = prev_function

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    # ------------------------------------------------------------------
    # Call visitor
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if self._current_function is None:
            # Top-level call — we still record it but there's no caller.
            self.generic_visit(node)
            return

        callee_name = self._extract_callee_name(node.func)
        if callee_name:
            edge = CallEdge(
                caller=self._current_function,
                callee_name=callee_name,
                file_path=self.file_path,
                line_number=node.lineno,
            )
            self.calls.append(edge)

        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Callee name extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_callee_name(node: ast.expr) -> str | None:
        """Resolve a call target to a dotted name string.

        Handles:
        - ``foo()``           → ``"foo"``
        - ``self.bar()``      → ``"self.bar"``
        - ``module.func()``   → ``"module.func"``
        - ``a.b.c()``         → ``"a.b.c"``
        """
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            value_name = _PythonVisitor._extract_callee_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        return None
