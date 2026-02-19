"""Core data models for CodeSleuth."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionNode:
    """Represents a function or method definition in the codebase."""

    name: str
    """Simple name, e.g. 'parse_file'."""

    qualified_name: str
    """Fully-qualified name, e.g. 'parsers.python_parser.PythonParser.parse_file'."""

    file_path: Path
    """Path relative to the target root."""

    line_number: int
    """1-based line number of the definition."""

    class_name: str | None = None
    """Enclosing class name, if any."""

    docstring: str | None = None
    """Extracted docstring / JSDoc comment."""

    params: list[str] = field(default_factory=list)
    """Parameter names."""

    def __hash__(self) -> int:
        return hash((self.qualified_name, self.file_path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunctionNode):
            return NotImplemented
        return (
            self.qualified_name == other.qualified_name
            and self.file_path == other.file_path
        )


@dataclass
class CallEdge:
    """Represents a function call found in the source code."""

    caller: FunctionNode
    """The function that contains the call."""

    callee_name: str
    """Raw callee name as it appears in source (e.g. 'foo', 'self.bar', 'mod.baz')."""

    file_path: Path
    """File where the call occurs."""

    line_number: int
    """1-based line number of the call site."""

    resolved_callee: FunctionNode | None = None
    """Resolved target node (filled during the resolution phase)."""


@dataclass
class ParseResult:
    """Output from parsing a single source file."""

    file_path: Path
    functions: list[FunctionNode] = field(default_factory=list)
    calls: list[CallEdge] = field(default_factory=list)


@dataclass
class CallGraph:
    """The complete cross-file call graph."""

    nodes: list[FunctionNode] = field(default_factory=list)
    edges: list[CallEdge] = field(default_factory=list)

    @property
    def resolved_edges(self) -> list[CallEdge]:
        """Return only edges whose callee was successfully resolved."""
        return [e for e in self.edges if e.resolved_callee is not None]

    def connected_components(self) -> list[CallGraph]:
        """Split graph into connected components (undirected) and return each as a CallGraph.

        Returns components sorted largest-first by node count.
        """
        # Build adjacency using node indices.
        node_to_idx: dict[int, int] = {}
        for i, fn in enumerate(self.nodes):
            node_to_idx[id(fn)] = i

        # Union-Find
        parent = list(range(len(self.nodes)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # Union nodes connected by resolved edges.
        for edge in self.resolved_edges:
            caller_idx = node_to_idx.get(id(edge.caller))
            callee_idx = node_to_idx.get(id(edge.resolved_callee))
            if caller_idx is not None and callee_idx is not None:
                union(caller_idx, callee_idx)

        # Group nodes by component root.
        from collections import defaultdict
        components: dict[int, list[int]] = defaultdict(list)
        for i in range(len(self.nodes)):
            components[find(i)].append(i)

        # Build sub-graphs.
        result: list[CallGraph] = []
        for indices in components.values():
            idx_set = set(indices)
            comp_nodes = [self.nodes[i] for i in indices]
            node_ids = {id(n) for n in comp_nodes}
            comp_edges = [
                e for e in self.edges
                if id(e.caller) in node_ids
            ]
            result.append(CallGraph(nodes=comp_nodes, edges=comp_edges))

        # Sort largest component first.
        result.sort(key=lambda g: len(g.nodes), reverse=True)
        return result

