"""Mermaid flowchart renderer with rich labels and subgraphs."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from codesleuth.models import CallGraph, FunctionNode
from codesleuth.renderers.base_renderer import BaseRenderer


class MermaidRenderer(BaseRenderer):
    """Renders a :class:`CallGraph` as a Mermaid flowchart inside a Markdown file."""

    def render(self, graph: CallGraph, output_path: Path, **options) -> None:
        """Write the Mermaid diagram to *output_path*.

        Options
        -------
        direction : str
            ``'TD'`` (top-down) or ``'LR'`` (left-right). Default ``'TD'``.
        max_docstring_length : int
            Truncate docstrings to this many characters. Default ``80``.
        include_orphans : bool
            If ``True``, include nodes that have no incoming or outgoing edges.
            Default ``False``.
        """
        direction: str = options.get("direction", "TD")
        max_doc: int = options.get("max_docstring_length", 80)
        include_orphans: bool = options.get("include_orphans", False)

        lines = self._build_diagram(graph, direction, max_doc, include_orphans)
        markdown = self._wrap_markdown(lines)
        output_path.write_text(markdown, encoding="utf-8")

    # ------------------------------------------------------------------
    # Node ID generation — short IDs to keep diagram text small
    # ------------------------------------------------------------------

    def _make_id_map(self, nodes: list[FunctionNode]) -> dict[str, str]:
        """Create a mapping from FunctionNode hash-key to a short id like ``n0``, ``n1``."""
        id_map: dict[str, str] = {}
        for i, fn in enumerate(nodes):
            key = self._fn_key(fn)
            if key not in id_map:
                id_map[key] = f"n{i}"
        return id_map

    @staticmethod
    def _fn_key(fn: FunctionNode) -> str:
        """Stable hash key for a FunctionNode."""
        return f"{fn.file_path}::{fn.qualified_name}::{fn.line_number}"

    # ------------------------------------------------------------------
    # Labels — compact but informative
    # ------------------------------------------------------------------

    def _node_label(self, fn: FunctionNode, max_doc: int) -> str:
        """Build a compact label: name, location, and optional short docstring."""
        parts: list[str] = []

        # Function name (bold)
        display_name = fn.name
        if fn.class_name:
            display_name = f"{fn.class_name}.{fn.name}"
        parts.append(f"<b>{self._escape(display_name)}</b>")

        # File:line (compact)
        fname = Path(fn.file_path).name
        parts.append(f"<i>{self._escape(fname)}:{fn.line_number}</i>")

        # Docstring excerpt (short)
        if fn.docstring:
            doc = fn.docstring.split("\n")[0].strip()
            if len(doc) > max_doc:
                doc = doc[: max_doc - 1] + "…"
            if doc:
                parts.append(f"<i>{self._escape(doc)}</i>")

        return "<br/>".join(parts)

    # ------------------------------------------------------------------
    # Subgraph ID
    # ------------------------------------------------------------------

    @staticmethod
    def _subgraph_id(file_path: Path) -> str:
        """Short, deterministic subgraph id from a file path."""
        h = hashlib.md5(str(file_path).encode()).hexdigest()[:6]
        name = Path(file_path).stem
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        return f"sg_{safe}_{h}"

    # ------------------------------------------------------------------
    # Diagram construction
    # ------------------------------------------------------------------

    def _build_diagram(
        self,
        graph: CallGraph,
        direction: str,
        max_doc: int,
        include_orphans: bool,
    ) -> list[str]:
        lines: list[str] = [f"flowchart {direction}"]

        # Determine which nodes to include.
        connected_keys: set[str] = set()
        for edge in graph.resolved_edges:
            connected_keys.add(self._fn_key(edge.caller))
            connected_keys.add(self._fn_key(edge.resolved_callee))  # type: ignore[arg-type]

        nodes_to_render = graph.nodes if include_orphans else [
            fn for fn in graph.nodes if self._fn_key(fn) in connected_keys
        ]

        if not nodes_to_render:
            lines.append("    NoNodes[\"No call relationships detected\"]")
            return lines

        # Build short-ID mapping.
        id_map = self._make_id_map(nodes_to_render)

        # Group nodes by file for subgraphs.
        by_file: dict[Path, list[FunctionNode]] = defaultdict(list)
        for fn in nodes_to_render:
            by_file[fn.file_path].append(fn)

        # Render subgraphs.
        for file_path in sorted(by_file.keys()):
            fns = by_file[file_path]
            sg_id = self._subgraph_id(file_path)
            sg_label = self._escape(str(file_path))
            lines.append(f"    subgraph {sg_id}[\"{sg_label}\"]")
            for fn in sorted(fns, key=lambda f: f.line_number):
                nid = id_map[self._fn_key(fn)]
                label = self._node_label(fn, max_doc)
                lines.append(f"        {nid}[\"{label}\"]")
            lines.append("    end")

        # Render edges.
        for edge in graph.resolved_edges:
            src = id_map.get(self._fn_key(edge.caller))
            dst = id_map.get(self._fn_key(edge.resolved_callee))  # type: ignore[arg-type]
            if src and dst:
                lines.append(f"    {src} -->|L{edge.line_number}| {dst}")

        return lines

    # ------------------------------------------------------------------
    # Markdown wrapper
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_markdown(diagram_lines: list[str]) -> str:
        body = "\n".join(diagram_lines)
        # Set maxTextSize high enough for large codebases.
        init_directive = (
            "%%{init: {"
            '"theme": "default", '
            '"maxTextSize": 200000, '
            '"flowchart": {"useMaxWidth": true}'
            "}}%%"
        )
        return (
            "# CodeSleuth — Call Graph\n\n"
            "_Auto-generated by [CodeSleuth](https://github.com/codesleuth)._\n\n"
            "```mermaid\n"
            f"{init_directive}\n"
            f"{body}\n"
            "```\n"
        )

    # ------------------------------------------------------------------
    # Sanitisation
    # ------------------------------------------------------------------

    @staticmethod
    def _escape(text: str) -> str:
        """Escape characters that break Mermaid syntax."""
        return (
            text.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
