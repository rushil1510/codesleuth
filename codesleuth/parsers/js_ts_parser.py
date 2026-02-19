"""JavaScript / TypeScript parser using tree-sitter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from codesleuth.models import CallEdge, FunctionNode, ParseResult
from codesleuth.parsers.base_parser import BaseParser

# tree-sitter imports are deferred to allow graceful fallback.
_TREE_SITTER_AVAILABLE = False
try:
    from tree_sitter_languages import get_language, get_parser  # type: ignore[import-untyped]
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    pass


class JSTypeScriptParser(BaseParser):
    """Parses JavaScript and TypeScript files using ``tree-sitter``."""

    _LANG_MAP: dict[str, str] = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
    }

    def supported_extensions(self) -> list[str]:
        return ["js", "jsx", "ts", "tsx"]

    def parse(self, file_path: Path, source: str) -> ParseResult:
        if not _TREE_SITTER_AVAILABLE:
            return ParseResult(file_path=file_path)

        ext = file_path.suffix.lstrip(".")
        lang_name = self._LANG_MAP.get(ext, "javascript")

        try:
            language = get_language(lang_name)
            parser = get_parser(lang_name)
        except Exception:
            return ParseResult(file_path=file_path)

        tree = parser.parse(source.encode("utf-8"))
        root = tree.root_node

        functions: list[FunctionNode] = []
        calls: list[CallEdge] = []

        self._walk_tree(root, file_path, source, functions, calls, scope_stack=[], current_fn=None)

        return ParseResult(file_path=file_path, functions=functions, calls=calls)

    # ------------------------------------------------------------------
    # Tree walking
    # ------------------------------------------------------------------

    def _walk_tree(
        self,
        node: Any,
        file_path: Path,
        source: str,
        functions: list[FunctionNode],
        calls: list[CallEdge],
        scope_stack: list[str],
        current_fn: FunctionNode | None,
    ) -> None:
        fn_node: FunctionNode | None = None

        # ---- Function / method definitions ----
        if node.type in (
            "function_declaration",
            "method_definition",
            "generator_function_declaration",
        ):
            fn_node = self._extract_function(node, file_path, source, scope_stack)
            if fn_node:
                functions.append(fn_node)

        elif node.type == "variable_declarator":
            # Arrow functions: `const foo = () => { ... }`
            fn_child = self._find_child_type(node, ("arrow_function", "function_expression", "function"))
            if fn_child is not None:
                name_node = node.child_by_field_name("name")
                if name_node:
                    fn_node = self._make_fn_node(
                        name_node.text.decode("utf-8"),
                        node,
                        fn_child,
                        file_path,
                        source,
                        scope_stack,
                    )
                    if fn_node:
                        functions.append(fn_node)

        # ---- Call expressions ----
        elif node.type == "call_expression" and current_fn is not None:
            callee_name = self._extract_callee(node)
            if callee_name:
                calls.append(
                    CallEdge(
                        caller=current_fn,
                        callee_name=callee_name,
                        file_path=file_path,
                        line_number=node.start_point[0] + 1,
                    )
                )

        # ---- Class definitions ----
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            class_name = name_node.text.decode("utf-8") if name_node else "<anon_class>"
            new_scope = scope_stack + [class_name]
            for child in node.children:
                self._walk_tree(child, file_path, source, functions, calls, new_scope, current_fn)
            return

        # Recurse
        active_fn = fn_node or current_fn
        new_scope = scope_stack + [fn_node.name] if fn_node else scope_stack
        for child in node.children:
            self._walk_tree(child, file_path, source, functions, calls, new_scope, active_fn)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source: str,
        scope_stack: list[str],
    ) -> FunctionNode | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        name = name_node.text.decode("utf-8")
        return self._make_fn_node(name, node, node, file_path, source, scope_stack)

    def _make_fn_node(
        self,
        name: str,
        decl_node: Any,
        body_node: Any,
        file_path: Path,
        source: str,
        scope_stack: list[str],
    ) -> FunctionNode:
        module = str(file_path).replace("/", ".").replace("\\", ".")
        for ext in (".js", ".jsx", ".ts", ".tsx"):
            if module.endswith(ext):
                module = module[: -len(ext)]
                break
        parts = [module] + list(scope_stack) + [name]
        qualified = ".".join(parts)

        # Determine class context
        class_name = scope_stack[-1] if scope_stack else None

        # Extract parameters
        params = self._extract_params(body_node)

        # Extract JSDoc comment above the declaration
        docstring = self._extract_jsdoc(decl_node, source)

        return FunctionNode(
            name=name,
            qualified_name=qualified,
            file_path=file_path,
            line_number=decl_node.start_point[0] + 1,
            class_name=class_name,
            docstring=docstring,
            params=params,
        )

    @staticmethod
    def _extract_params(node: Any) -> list[str]:
        params_node = node.child_by_field_name("parameters")
        if params_node is None:
            return []
        params: list[str] = []
        for child in params_node.children:
            if child.type in ("identifier", "required_parameter", "optional_parameter"):
                # For TS typed params, grab just the name.
                name_child = child.child_by_field_name("pattern") or child.child_by_field_name("name")
                if name_child:
                    params.append(name_child.text.decode("utf-8"))
                else:
                    text = child.text.decode("utf-8")
                    if text not in ("(", ")", ","):
                        params.append(text)
        return params

    @staticmethod
    def _extract_jsdoc(node: Any, source: str) -> str | None:
        """Look for a JSDoc-style comment immediately preceding *node*."""
        prev = node.prev_sibling
        if prev is not None and prev.type == "comment":
            text = prev.text.decode("utf-8").strip()
            if text.startswith("/**"):
                # Clean up JSDoc to a plain string.
                cleaned = re.sub(r"/\*\*|\*/", "", text)
                cleaned = re.sub(r"^\s*\*\s?", "", cleaned, flags=re.MULTILINE)
                return cleaned.strip() or None
        return None

    @staticmethod
    def _extract_callee(node: Any) -> str | None:
        fn = node.child_by_field_name("function")
        if fn is None:
            return None
        if fn.type == "identifier":
            return fn.text.decode("utf-8")
        if fn.type == "member_expression":
            return fn.text.decode("utf-8")
        return None

    @staticmethod
    def _find_child_type(node: Any, types: tuple[str, ...]) -> Any | None:
        for child in node.children:
            if child.type in types:
                return child
        return None
