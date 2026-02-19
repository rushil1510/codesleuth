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

    def test_init_directive_present(self, tmp_path: Path):
        """The maxTextSize init directive should be in the output."""
        fn_a = _fn("x", "m.py")
        fn_b = _fn("y", "m.py")
        edge = CallEdge(caller=fn_a, callee_name="y", file_path=Path("m.py"), line_number=1, resolved_callee=fn_b)
        graph = CallGraph(nodes=[fn_a, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out)
        content = out.read_text()
        assert "maxTextSize" in content
        assert "200000" in content

    def test_class_name_in_label(self, tmp_path: Path):
        """Class methods should show ClassName.method in the label."""
        fn = _fn("process", "m.py", class_name="Engine")
        fn_b = _fn("run", "m.py")
        edge = CallEdge(caller=fn, callee_name="run", file_path=Path("m.py"), line_number=1, resolved_callee=fn_b)
        graph = CallGraph(nodes=[fn, fn_b], edges=[edge])
        out = tmp_path / "output.md"

        MermaidRenderer().render(graph, out)
        content = out.read_text()
        assert "Engine.process" in content

    def test_render_components_creates_directory(self, tmp_path: Path):
        """render_components creates the output directory and writes files."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        fn_c = _fn("c", "y.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c], edges=[e1])
        out_dir = tmp_path / "components"

        written = MermaidRenderer().render_components(graph, out_dir)
        assert out_dir.exists()
        assert (out_dir / "index.md").exists()
        assert len(written) >= 2  # index + at least 1 component

    def test_render_components_index_links(self, tmp_path: Path):
        """The index.md should link to component files."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)

        graph = CallGraph(nodes=[fn_a, fn_b], edges=[e1])
        out_dir = tmp_path / "comp"

        MermaidRenderer().render_components(graph, out_dir)
        index = (out_dir / "index.md").read_text()
        assert "component_" in index
        assert "Functions" in index
        assert "Edges" in index

    def test_render_components_isolates_disconnected(self, tmp_path: Path):
        """Disconnected subgraphs become separate component files."""
        fn_a = _fn("a", "x.py")
        fn_b = _fn("b", "x.py")
        fn_c = _fn("c", "y.py")
        fn_d = _fn("d", "y.py")
        e1 = CallEdge(caller=fn_a, callee_name="b", file_path=Path("x.py"), line_number=1, resolved_callee=fn_b)
        e2 = CallEdge(caller=fn_c, callee_name="d", file_path=Path("y.py"), line_number=1, resolved_callee=fn_d)

        graph = CallGraph(nodes=[fn_a, fn_b, fn_c, fn_d], edges=[e1, e2])
        out_dir = tmp_path / "split"

        written = MermaidRenderer().render_components(graph, out_dir)
        # index + 2 components
        component_files = [f for f in written if f.name.startswith("component_")]
        assert len(component_files) == 2

