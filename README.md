# CodeSleuth

A documentation assistant that scans codebases, builds cross-file call graphs via AST parsing, and generates **Mermaid** diagrams — perfect for onboarding new developers onto legacy projects.

## Quick Start

```bash
# Install
pip3 install -e .

# Scan a codebase
codesleuth /path/to/project -o call_graph.md

# Or run as a module
python3 -m codesleuth /path/to/project -o call_graph.md
```

## Options

| Flag | Default | Description |
|---|---|---|
| `-o` / `--output` | `call_graph.md` | Output file path |
| `--direction` | `TD` | Mermaid direction (`TD` or `LR`) |
| `--max-docstring-length` | `80` | Max docstring label characters |
| `--include-orphans` | `False` | Show functions with no call edges |
| `--exclude` | — | Glob patterns to skip (repeatable) |

## Supported Languages

- **Python** (`.py`) — via stdlib `ast`
- **JavaScript** (`.js`, `.jsx`) — via `tree-sitter`
- **TypeScript** (`.ts`, `.tsx`) — via `tree-sitter`

## Adding a New Language

1. Create a class that inherits from `BaseParser`
2. Implement `supported_extensions()` and `parse()`
3. Register it in `cli.py` → `_build_registry()`

## Development

```bash
pip3 install -e ".[dev]"
python3 -m pytest codesleuth/tests/ -v
```
