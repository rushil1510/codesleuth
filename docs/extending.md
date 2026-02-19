# Extending CodeSleuth

CodeSleuth is designed for easy extensibility. You can add new languages or new output formats by implementing a simple abstract interface.

## Adding a New Language Parser

### Step 1: Create the Parser

Create a new file in `codesleuth/parsers/`, e.g. `go_parser.py`:

```python
from __future__ import annotations

from pathlib import Path

from codesleuth.models import CallEdge, FunctionNode, ParseResult
from codesleuth.parsers.base_parser import BaseParser


class GoParser(BaseParser):
    """Parser for Go source files."""

    def supported_extensions(self) -> list[str]:
        return ["go"]

    def parse(self, file_path: Path, source: str) -> ParseResult:
        functions: list[FunctionNode] = []
        calls: list[CallEdge] = []

        # Your AST parsing logic here...
        # Use tree-sitter, a Go-specific library, or regex patterns.

        return ParseResult(
            file_path=file_path,
            functions=functions,
            calls=calls,
        )
```

### Step 2: Register It

In `codesleuth/cli.py`, add your parser to the registry:

```python
from codesleuth.parsers.go_parser import GoParser

def _build_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(JSTypeScriptParser())
    registry.register(GoParser())  # ← add this
    return registry
```

### Step 3: Test It

Create `codesleuth/tests/test_go_parser.py` following the same pattern as the existing parser tests.

## Adding a New Renderer

### Step 1: Create the Renderer

Create a new file in `codesleuth/renderers/`, e.g. `dot_renderer.py`:

```python
from __future__ import annotations

from pathlib import Path

from codesleuth.models import CallGraph
from codesleuth.renderers.base_renderer import BaseRenderer


class DotRenderer(BaseRenderer):
    """Renders a CallGraph as a Graphviz DOT file."""

    def render(self, graph: CallGraph, output_path: Path, **options) -> None:
        lines = ["digraph CallGraph {"]

        for edge in graph.resolved_edges:
            src = edge.caller.qualified_name
            dst = edge.resolved_callee.qualified_name
            lines.append(f'    "{src}" -> "{dst}";')

        lines.append("}")
        output_path.write_text("\n".join(lines))
```

### Step 2: Wire It Into the CLI

Add a `--format` option to `cli.py` and instantiate the appropriate renderer based on the selection.

## Key Data Structures

When implementing a parser, you'll work with these models:

| Class | What to populate |
|---|---|
| `FunctionNode` | `name`, `qualified_name`, `file_path`, `line_number`, `class_name` (optional), `docstring` (optional), `params` |
| `CallEdge` | `caller` (FunctionNode), `callee_name` (raw string as it appears in source), `file_path`, `line_number` |
| `ParseResult` | `file_path`, `functions` (list), `calls` (list) |

**Important:** The `callee_name` in `CallEdge` should be the raw name as written in source (e.g. `"foo"`, `"self.bar"`, `"module.baz"`). The `CallGraphBuilder` handles resolution.

## Tips

- Use `tree-sitter` for languages without a built-in AST module — it gives you a consistent interface across languages
- Extract the first line of docstrings/comments for the `docstring` field
- Track class scope so `class_name` is populated for methods
- For `self.method` patterns, record the callee_name as `"self.method"` — the graph builder knows how to resolve these
