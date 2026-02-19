"""Tests for the call graph builder."""

from __future__ import annotations

from pathlib import Path

from codesleuth.graph_builder import CallGraphBuilder
from codesleuth.models import CallEdge, FunctionNode, ParseResult


def _fn(name: str, file: str = "a.py", class_name: str | None = None) -> FunctionNode:
    """Helper to create a FunctionNode quickly."""
    qn = f"{file.replace('.py', '')}.{class_name}.{name}" if class_name else f"{file.replace('.py', '')}.{name}"
    return FunctionNode(
        name=name,
        qualified_name=qn,
        file_path=Path(file),
        line_number=1,
        class_name=class_name,
    )


class TestCallGraphBuilder:
    """Tests for :class:`CallGraphBuilder`."""

    def test_resolves_same_file_call(self):
        fn_a = _fn("greet", "main.py")
        fn_b = _fn("format_greeting", "main.py")
        edge = CallEdge(caller=fn_a, callee_name="format_greeting", file_path=Path("main.py"), line_number=5)

        builder = CallGraphBuilder()
        builder.add_results([ParseResult(Path("main.py"), functions=[fn_a, fn_b], calls=[edge])])
        graph = builder.build()

        assert len(graph.resolved_edges) == 1
        assert graph.resolved_edges[0].resolved_callee == fn_b

    def test_resolves_self_method(self):
        fn_add = _fn("add", "calc.py", class_name="Calculator")
        fn_ag = _fn("add_and_greet", "calc.py", class_name="Calculator")
        edge = CallEdge(caller=fn_ag, callee_name="self.add", file_path=Path("calc.py"), line_number=10)

        builder = CallGraphBuilder()
        builder.add_results([ParseResult(Path("calc.py"), functions=[fn_add, fn_ag], calls=[edge])])
        graph = builder.build()

        assert len(graph.resolved_edges) == 1
        assert graph.resolved_edges[0].resolved_callee == fn_add

    def test_resolves_cross_file_call(self):
        fn_a = _fn("process", "utils.py")
        fn_b = _fn("greet", "main.py")
        edge = CallEdge(caller=fn_a, callee_name="greet", file_path=Path("utils.py"), line_number=3)

        builder = CallGraphBuilder()
        builder.add_results([
            ParseResult(Path("utils.py"), functions=[fn_a], calls=[edge]),
            ParseResult(Path("main.py"), functions=[fn_b], calls=[]),
        ])
        graph = builder.build()

        assert len(graph.resolved_edges) == 1
        assert graph.resolved_edges[0].resolved_callee == fn_b

    def test_unresolved_edge_stays_none(self):
        fn_a = _fn("caller", "a.py")
        edge = CallEdge(caller=fn_a, callee_name="nonexistent", file_path=Path("a.py"), line_number=5)

        builder = CallGraphBuilder()
        builder.add_results([ParseResult(Path("a.py"), functions=[fn_a], calls=[edge])])
        graph = builder.build()

        assert len(graph.resolved_edges) == 0
        assert len(graph.edges) == 1
        assert graph.edges[0].resolved_callee is None

    def test_ambiguous_calls_not_resolved(self):
        """When multiple functions share the same name, don't guess."""
        fn_a = _fn("helper", "a.py")
        fn_b = _fn("helper", "b.py")
        fn_caller = _fn("main", "c.py")
        edge = CallEdge(caller=fn_caller, callee_name="helper", file_path=Path("c.py"), line_number=2)

        builder = CallGraphBuilder()
        builder.add_results([
            ParseResult(Path("a.py"), functions=[fn_a], calls=[]),
            ParseResult(Path("b.py"), functions=[fn_b], calls=[]),
            ParseResult(Path("c.py"), functions=[fn_caller], calls=[edge]),
        ])
        graph = builder.build()

        assert len(graph.resolved_edges) == 0
