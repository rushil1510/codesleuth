"""CLI entry point for CodeSleuth."""

from __future__ import annotations

from pathlib import Path

import click

from codesleuth.graph_builder import CallGraphBuilder
from codesleuth.parsers.js_ts_parser import JSTypeScriptParser
from codesleuth.parsers.python_parser import PythonParser
from codesleuth.parsers.registry import ParserRegistry
from codesleuth.renderers.mermaid_renderer import MermaidRenderer
from codesleuth.scanner import FileScanner


def _build_registry() -> ParserRegistry:
    """Create a registry pre-loaded with all built-in parsers."""
    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(JSTypeScriptParser())
    return registry


@click.command()
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(),
    default="call_graph.md",
    show_default=True,
    help="Output file (single mode) or directory (split mode).",
)
@click.option(
    "--split/--no-split",
    default=False,
    show_default=True,
    help="Split into one file per connected component (output becomes a directory).",
)
@click.option(
    "--direction",
    type=click.Choice(["TD", "LR"], case_sensitive=False),
    default="TD",
    show_default=True,
    help="Mermaid flowchart direction.",
)
@click.option(
    "--max-docstring-length",
    type=int,
    default=80,
    show_default=True,
    help="Truncate docstrings to this many characters.",
)
@click.option(
    "--include-orphans/--no-include-orphans",
    default=False,
    show_default=True,
    help="Include functions with no call relationships.",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Glob patterns to exclude (can be specified multiple times).",
)
def main(
    target_dir: str,
    output_path: str,
    split: bool,
    direction: str,
    max_docstring_length: int,
    include_orphans: bool,
    exclude: tuple[str, ...],
) -> None:
    """Scan TARGET_DIR and generate a Mermaid call-graph diagram."""
    root = Path(target_dir)

    click.echo(f"🔍 Scanning {root} …")

    registry = _build_registry()
    scanner = FileScanner(root, registry, extra_excludes=list(exclude))
    results = scanner.scan()

    total_funcs = sum(len(r.functions) for r in results)
    total_calls = sum(len(r.calls) for r in results)
    click.echo(f"   Found {total_funcs} functions and {total_calls} call sites across {len(results)} files.")

    click.echo("🔗 Building call graph …")
    builder = CallGraphBuilder()
    builder.add_results(results)
    graph = builder.build()

    resolved = len(graph.resolved_edges)
    unresolved = len(graph.edges) - resolved
    click.echo(f"   Resolved {resolved} edges ({unresolved} unresolved).")

    renderer = MermaidRenderer()
    opts = dict(
        direction=direction.upper(),
        max_docstring_length=max_docstring_length,
        include_orphans=include_orphans,
    )

    if split:
        out_dir = Path(output_path).with_suffix("")  # strip .md if given
        click.echo(f"📂 Splitting into components → {out_dir}/")
        written = renderer.render_components(graph, out_dir, **opts)
        click.echo(f"✅ Wrote {len(written)} files (including index.md).")
    else:
        out = Path(output_path)
        click.echo(f"📄 Rendering → {out}")
        renderer.render(graph, out, **opts)
        click.echo("✅ Done!")


if __name__ == "__main__":
    main()

