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
