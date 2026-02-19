"""Tests for the Mermaid renderer."""

from __future__ import annotations

from pathlib import Path

from codesleuth.models import CallEdge, CallGraph, FunctionNode
from codesleuth.renderers.mermaid_renderer import MermaidRenderer


def _fn(name: str, file: str = "app.py", docstring: str | None = None, class_name: str | None = None) -> FunctionNode:
    qn = f"{file.replace('.py', '')}.{name}"
    return FunctionNode(
        name=name,
        qualified_name=qn,
        file_path=Path(file),
        line_number=1,
        class_name=class_name,
        docstring=docstring,
        params=["x"],
    )


class TestMermaidRenderer:
    """Tests for :class:`MermaidRenderer`."""

    def test_renders_basic_diagram(self, tmp_path: Path):
        fn_a = _fn("greet", "main.py", docstring="Say hello")
        fn_b = _fn("format", "main.py")
        edge = CallEdge(caller=fn_a, callee_name="format", file_path=Path("main.py"), line_number=5, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn_a, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out)
        content = out.read_text()

        assert "```mermaid" in content
        assert "flowchart TD" in content
        assert "greet" in content
        assert "format" in content

    def test_includes_docstring_in_label(self, tmp_path: Path):
        fn = _fn("greet", "main.py", docstring="Say hello to the user")
        fn_b = _fn("other", "main.py")
        edge = CallEdge(caller=fn, callee_name="other", file_path=Path("main.py"), line_number=3, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out)
        content = out.read_text()
        assert "Say hello" in content

    def test_subgraphs_per_file(self, tmp_path: Path):
        fn_a = _fn("foo", "a.py")
        fn_b = _fn("bar", "b.py")
        edge = CallEdge(caller=fn_a, callee_name="bar", file_path=Path("a.py"), line_number=2, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn_a, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out)
        content = out.read_text()
        assert "subgraph" in content
        assert "sg_a_" in content
        assert "sg_b_" in content

    def test_orphans_excluded_by_default(self, tmp_path: Path):
        fn_orphan = _fn("orphan", "main.py")
        graph = CallGraph(nodes=[fn_orphan], edges=[])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out, include_orphans=False)
        content = out.read_text()
        assert "orphan" not in content or "No call relationships" in content

    def test_orphans_included_when_requested(self, tmp_path: Path):
        fn_orphan = _fn("orphan", "main.py")
        graph = CallGraph(nodes=[fn_orphan], edges=[])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out, include_orphans=True)
        content = out.read_text()
        assert "orphan" in content

    def test_lr_direction(self, tmp_path: Path):
        fn_a = _fn("a", "m.py")
        fn_b = _fn("b", "m.py")
        edge = CallEdge(caller=fn_a, callee_name="b", file_path=Path("m.py"), line_number=1, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn_a, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out, direction="LR")
        content = out.read_text()
        assert "flowchart LR" in content
