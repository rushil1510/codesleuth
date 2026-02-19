# CodeSleuth

A documentation assistant that scans codebases, builds cross-file call graphs via AST parsing, and generates **Mermaid** diagrams — perfect for onboarding new developers onto legacy projects.

## Quick Start

```bash
# Install
pip3 install -e .

# Scan a codebase (single file)
codesleuth /path/to/project -o call_graph.md

# Split into per-component files (recommended for large codebases)
codesleuth /path/to/project -o output_dir --split

# Or run as a module
python3 -m codesleuth /path/to/project -o call_graph.md
```

## Options

| Flag | Default | Description |
|---|---|---|
| `-o` / `--output` | `call_graph.md` | Output file path (single mode) or directory (split mode) |
| `--split` / `--no-split` | `False` | Split diagram by connected components into separate files |
| `--png` / `--no-png` | `False` | Export diagrams as PNG images (requires `mmdc`) |
| `--width` | `1920` | PNG image width in pixels |
| `--height` | `1080` | PNG image height in pixels |
| `--direction` | `TD` | Mermaid direction (`TD` top-down, `LR` left-right) |
| `--max-docstring-length` | `80` | Max docstring label characters |
| `--include-orphans` | `False` | Show functions with no call edges |
| `--exclude` | — | Glob patterns to skip (repeatable) |

## Output Modes

### Single File (default)
Generates one Markdown file with the full Mermaid diagram:
```bash
codesleuth ./my-project -o call_graph.md
```

### Split Mode (`--split`)
Splits the call graph into connected components, one file per component, plus an `index.md` that links them all. This is **recommended for larger codebases** where a single diagram hits Mermaid rendering limits:
```bash
codesleuth ./my-project -o graphs --split
# Output:
#   graphs/index.md                      ← summary table linking all components
#   graphs/component_00_main_utils.md    ← largest connected component
#   graphs/component_01_helpers.md       ← next component
#   ...
```

### PNG Export (`--png`)
Convert diagrams directly to PNG images at a specified resolution. Requires [`mmdc`](https://github.com/mermaid-js/mermaid-cli) (mermaid-cli):
```bash
# Install mmdc
npm install -g @mermaid-js/mermaid-cli

# Single file → PNG
codesleuth ./my-project -o diagram.md --png

# Custom resolution
codesleuth ./my-project -o diagram.md --png --width 3840 --height 2160

# Split mode + PNG (each component gets its own PNG)
codesleuth ./my-project -o graphs --split --png --width 2560 --height 1440
```

## Supported Languages


- **Python** (`.py`) — via stdlib `ast`
- **JavaScript** (`.js`, `.jsx`) — via `tree-sitter`
- **TypeScript** (`.ts`, `.tsx`) — via `tree-sitter`

## Architecture

```
codesleuth/
├── models.py          ← FunctionNode, CallEdge, CallGraph (with connected components)
├── scanner.py         ← FileScanner — walks dirs, respects .gitignore
├── graph_builder.py   ← CallGraphBuilder — symbol table + multi-strategy resolution
├── cli.py             ← Click CLI entry point
├── parsers/
│   ├── base_parser.py ← Abstract BaseParser interface
│   ├── registry.py    ← Extension → parser mapping
│   ├── python_parser.py
│   └── js_ts_parser.py
├── renderers/
│   ├── base_renderer.py ← Abstract BaseRenderer interface
│   └── mermaid_renderer.py ← Mermaid output (single + split modes)
└── tests/             ← 59 tests, 97% coverage
```

See the [docs/](docs/) directory for detailed documentation.

## Adding a New Language

1. Create a class that inherits from `BaseParser`
2. Implement `supported_extensions()` and `parse()`
3. Register it in `cli.py` → `_build_registry()`

See [docs/extending.md](docs/extending.md) for a full walkthrough.

## Development

```bash
pip3 install -e ".[dev]"
python3 -m pytest codesleuth/tests/ -v

# With coverage
python3 -m pytest codesleuth/tests/ --cov=codesleuth --cov-report=term-missing
```
