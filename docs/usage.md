# Usage Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/rushil1510/codesleuth.git
cd codesleuth

# Install in editable mode
pip3 install -e .

# Install with dev dependencies (for testing)
pip3 install -e ".[dev]"
```

## Basic Scanning

```bash
# Scan a project and generate a single diagram
codesleuth /path/to/project

# Specify output file
codesleuth /path/to/project -o my_diagram.md
```

## Split Mode (Recommended for Large Projects)

For larger codebases, the Mermaid diagram may exceed rendering limits. Use `--split` to break it into connected components:

```bash
codesleuth /path/to/project -o output_dir --split
```

This creates:
- `output_dir/index.md` — a summary table with links to each component
- `output_dir/component_00_<name>.md` — the largest connected component
- `output_dir/component_01_<name>.md` — next component
- etc.

Each component file is self-contained and renders independently. The naming is derived from the files involved in that component.

## Direction

```bash
# Top-down (default)
codesleuth /path/to/project --direction TD

# Left-to-right (better for wide codebases)
codesleuth /path/to/project --direction LR
```

## Excluding Files

```bash
# Exclude test files
codesleuth /path/to/project --exclude "test_*" --exclude "*_test.*"

# Exclude specific directories
codesleuth /path/to/project --exclude "vendor/*" --exclude "generated/*"
```

Note: `.gitignore` rules are respected automatically. Common directories like `node_modules`, `__pycache__`, `.venv` are always skipped.

## Orphan Functions

By default, functions with no call relationships are excluded from the diagram. To include them:

```bash
codesleuth /path/to/project --include-orphans
```

## Docstring Length

Control how much of each function's docstring appears in the node label:

```bash
# Show first 40 characters
codesleuth /path/to/project --max-docstring-length 40

# Show more
codesleuth /path/to/project --max-docstring-length 120
```

## Running as a Module

```bash
python3 -m codesleuth /path/to/project -o call_graph.md
```

## Full Options Reference

```
Usage: codesleuth [OPTIONS] TARGET_DIR

  Scan TARGET_DIR and generate a Mermaid call-graph diagram.

Options:
  -o, --output PATH           Output file or directory  [default: call_graph.md]
  --split / --no-split        Split into connected components  [default: no-split]
  --direction [TD|LR]         Mermaid flowchart direction  [default: TD]
  --max-docstring-length INT  Truncate docstrings  [default: 80]
  --include-orphans           Include unconnected functions  [default: False]
  --exclude TEXT              Glob patterns to exclude (repeatable)
  --help                      Show this help
```
