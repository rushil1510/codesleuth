# Architecture

CodeSleuth follows a pipeline architecture: **Scan → Parse → Build → Render**.

## Pipeline

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CLI    │───▶│ FileScanner  │───▶│CallGraphBuild│───▶│MermaidRender │
│ (click)  │    │  + Registry  │    │    er        │    │    er        │
└──────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                       │                                       │
                 ┌─────┴──────┐                    ┌───────────┴──────┐
                 │            │                    │                  │
            PythonParser JSTypeScript      Single File        Split Mode
                         Parser        (1 Markdown)    (N Markdown files)
```

## Core Components

### Data Models (`models.py`)

| Class | Purpose |
|---|---|
| `FunctionNode` | A function/method found in source (name, file, line, docstring, params) |
| `CallEdge` | A call site: who calls what, and the resolved target |
| `ParseResult` | Output from parsing one file: list of functions + call edges |
| `CallGraph` | The complete graph. Key method: `connected_components()` (union-find) |

### FileScanner (`scanner.py`)

Walks the target directory tree and delegates each file to the appropriate parser.

**Exclusion layers (in priority order):**
1. **Always-skip directories** — `.git`, `node_modules`, `__pycache__`, `venv`, `.tox`, etc.
2. **CLI `--exclude` patterns** — e.g. `--exclude "*.test.*"`
3. **`.gitignore` rules** — parsed via the `pathspec` library

### Parser Registry (`parsers/registry.py`)

Maps file extensions to parser instances. When `FileScanner` encounters a `.py` file, the registry returns the `PythonParser`; for `.js`/`.ts`, the `JSTypeScriptParser`.

### PythonParser (`parsers/python_parser.py`)

Uses Python's built-in `ast` module:
- Visits `FunctionDef` / `AsyncFunctionDef` for definitions
- Visits `ClassDef` to track class scope
- Visits `Call` to extract call edges
- Extracts docstrings via `ast.get_docstring()`

### JSTypeScriptParser (`parsers/js_ts_parser.py`)

Uses `tree-sitter` with `tree-sitter-languages`:
- Queries for `function_declaration`, `method_definition`, `arrow_function`
- Extracts JSDoc comments from preceding `comment` nodes
- Tracks class scope via `class_declaration` / `class` nodes

### CallGraphBuilder (`graph_builder.py`)

Builds a symbol table and resolves raw callee names to `FunctionNode` targets using a **multi-strategy approach** (in priority order):

1. **Qualified name** — exact `module.Class.method` match
2. **`self.method`** — resolve within the caller's class
3. **Same-file** — match by simple name within the same file
4. **Cross-file** — match by simple name across all files (only if unique)

Ambiguous matches (same name in multiple files) are left unresolved.

### MermaidRenderer (`renderers/mermaid_renderer.py`)

Generates Mermaid flowchart diagrams with:
- **Subgraphs** grouped by source file
- **Rich labels** showing function name, file:line, and docstring excerpts
- **Short node IDs** (`n0`, `n1`, ...) to minimize diagram text size
- **`%%{init}%%` directive** with `maxTextSize: 200000` for large diagrams
- **Two output modes:**
  - **Single file** — one `.md` with the full diagram
  - **Split mode** — one `.md` per connected component + `index.md`

## Call Resolution Strategy

```
Raw callee: "self.add"
  │
  ├─ 1. Exact qualified name match?  ─── YES → resolved
  │     "calc.Calculator.add"
  │
  ├─ 2. self.method within class?    ─── YES → resolved
  │     caller.class_name == "Calculator",
  │     find fn named "add" in class "Calculator"
  │
  ├─ 3. Same-file match by name?     ─── YES → resolved
  │
  ├─ 4. Cross-file unique match?     ─── YES → resolved
  │
  └─ 5. Ambiguous / not found        ─── unresolved
```
