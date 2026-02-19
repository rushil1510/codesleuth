"""Tests for core data models."""

from __future__ import annotations

from pathlib import Path

from codesleuth.models import CallEdge, CallGraph, FunctionNode, ParseResult


def _fn(name: str, file: str = "a.py", class_name: str | None = None, line: int = 1) -> FunctionNode:
    qn = f"{file.replace('.py', '')}.{class_name}.{name}" if class_name else f"{file.replace('.py', '')}.{name}"
    return FunctionNode(
        name=name,
        qualified_name=qn,
        file_path=Path(file),
        line_number=line,
        class_name=class_name,
    )


class TestFunctionNode:
    """Tests for FunctionNode hash and equality."""

    def test_equal_nodes(self):
        a = _fn("foo", "x.py")
        b = _fn("foo", "x.py")
        assert a == b

    def test_different_name_not_equal(self):
        a = _fn("foo", "x.py")
        b = _fn("bar", "x.py")
        assert a != b

    def test_different_file_not_equal(self):
        a = _fn("foo", "x.py")
        b = _fn("foo", "y.py")
        assert a != b

    def test_hashable_in_set(self):
        a = _fn("foo", "x.py")
        b = _fn("foo", "x.py")
        s = {a, b}
        assert len(s) == 1

    def test_not_equal_to_non_node(self):
        a = _fn("foo")
        assert a != "not a node"


class TestCallGraph:
    """Tests for CallGraph and connected_components."""

    def test_resolved_edges(self):
        fn_a = _fn("a")
        fn_b = _fn("b")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("a.py"), line_number=1, resolved_callee=fn_b)
        e2 = CallEdge(caller=fn_a, callee_name="missing", file_path=Path("a.py"), line_number=2)

        graph = CallGraph(nodes=[fn_a, fn_b], edges=[e1, e2])
        assert len(graph.resolved_edges) == 1
        assert graph.resolved_edges[0].resolved_callee == fn_b

    def test_connected_components_single(self):
        """A fully connected graph yields a single component."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        fn_c = _fn("c", "x.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)
        e2 = CallEdge(caller=fn_b, callee_name="c", file_path=Path("x.py"), line_number=2, resolved_callee=fn_c)

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c], edges=[e1, e2])
        comps = graph.connected_components()
        assert len(comps) == 1
        assert len(comps[0].nodes) == 3

    def test_connected_components_multiple(self):
        """Disconnected nodes form separate components."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        fn_c = _fn("c", "y.py")
        fn_d = _fn("d", "y.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)
        e2 = CallEdge(caller=fn_c, callee_name="d", file_path=Path("y.py"), line_number=1, resolved_callee=fn_d)

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c, fn_d], edges=[e1, e2])
        comps = graph.connected_components()
        assert len(comps) == 2
        # Both components should have 2 nodes each.
        sizes = sorted([len(c.nodes) for c in comps])
        assert sizes == [2, 2]

    def test_connected_components_with_isolated(self):
        """Isolated nodes (no edges) each form their own component."""
        fn_a = _fn("a")
        fn_b = _fn("b")
        fn_c = _fn("c")

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c], edges=[])
        comps = graph.connected_components()
        assert len(comps) == 3

    def test_connected_components_sorted_by_size(self):
        """Components are returned largest-first."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        fn_c = _fn("c", "x.py")
        fn_d = _fn("d", "y.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)
        e2 = CallEdge(caller=fn_b, callee_name="c", file_path=Path("x.py"), line_number=2, resolved_callee=fn_c)

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c, fn_d], edges=[e1, e2])
        comps = graph.connected_components()
        assert len(comps) == 2
        assert len(comps[0].nodes) == 3  # larger first
        assert len(comps[1].nodes) == 1

    def test_empty_graph_components(self):
        graph = CallGraph()
        assert graph.connected_components() == []


class TestParseResult:
    """Tests for ParseResult."""

    def test_defaults(self):
        r = ParseResult(file_path=Path("x.py"))
        assert r.functions == []
        assert r.calls == []
