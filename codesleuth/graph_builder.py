"""Builds a cross-file call graph from parse results and resolves edges."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from codesleuth.models import CallEdge, CallGraph, FunctionNode, ParseResult


class CallGraphBuilder:
    """
    Aggregates :class:`ParseResult` objects, builds a symbol table, and
    resolves raw callee names to concrete :class:`FunctionNode` targets.
    """

    def __init__(self) -> None:
        self._functions: list[FunctionNode] = []
        self._edges: list[CallEdge] = []

        # Lookup indices built during the resolution phase.
        self._by_name: dict[str, list[FunctionNode]] = defaultdict(list)
        self._by_qualified: dict[str, FunctionNode] = {}
        self._by_file: dict[Path, list[FunctionNode]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_results(self, results: list[ParseResult]) -> None:
        """Ingest all parse results."""
        for r in results:
            self._functions.extend(r.functions)
            self._edges.extend(r.calls)

    def build(self) -> CallGraph:
        """Build the symbol table, resolve edges, and return the graph."""
        self._build_index()
        self._resolve_edges()
        return CallGraph(nodes=list(self._functions), edges=list(self._edges))

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        self._by_name.clear()
        self._by_qualified.clear()
        self._by_file.clear()

        for fn in self._functions:
            self._by_name[fn.name].append(fn)
            self._by_qualified[fn.qualified_name] = fn
            self._by_file[fn.file_path].append(fn)

    # ------------------------------------------------------------------
    # Edge resolution
    # ------------------------------------------------------------------

    def _resolve_edges(self) -> None:
        for edge in self._edges:
            edge.resolved_callee = self._resolve(edge)

    def _resolve(self, edge: CallEdge) -> FunctionNode | None:
        """Attempt to resolve a callee name to a FunctionNode.

        Resolution strategy (in priority order):

        1. Exact match on qualified name (e.g. ``module.ClassName.method``)
        2. ``self.method`` → match *method* in the same class context
        3. Same-file match on simple name
        4. Cross-file match on simple name (first match wins)
        """
        raw = edge.callee_name

        # 1. Exact qualified match.
        if raw in self._by_qualified:
            return self._by_qualified[raw]

        # Determine the simple name (rightmost segment).
        parts = raw.split(".")
        simple_name = parts[-1]

        # 2. self.method — resolve within the caller's class.
        if parts[0] == "self" and len(parts) == 2 and edge.caller.class_name:
            for fn in self._by_file.get(edge.file_path, []):
                if fn.name == simple_name and fn.class_name == edge.caller.class_name:
                    return fn
            # Also search cross-file for the same class name.
            for fn in self._by_name.get(simple_name, []):
                if fn.class_name == edge.caller.class_name:
                    return fn

        # 3. Same-file match.
        for fn in self._by_file.get(edge.file_path, []):
            if fn.name == simple_name:
                return fn

        # 4. Cross-file match (first hit).
        candidates = self._by_name.get(simple_name, [])
        if len(candidates) == 1:
            return candidates[0]

        # Ambiguous or unknown — leave unresolved.
        return None
