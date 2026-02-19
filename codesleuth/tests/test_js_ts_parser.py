"""Tests for the JavaScript / TypeScript parser."""

from __future__ import annotations

from pathlib import Path

import pytest

# tree-sitter may not be installed in CI — skip gracefully.
try:
    from tree_sitter_languages import get_language  # type: ignore[import-untyped]
    _HAS_TREE_SITTER = True
except ImportError:
    _HAS_TREE_SITTER = False

from codesleuth.parsers.js_ts_parser import JSTypeScriptParser

pytestmark = pytest.mark.skipif(not _HAS_TREE_SITTER, reason="tree-sitter-languages not installed")


class TestJSTypeScriptParser:
    """Tests for :class:`JSTypeScriptParser`."""

    def setup_method(self):
        self.parser = JSTypeScriptParser()

    def test_supported_extensions(self):
        assert set(self.parser.supported_extensions()) == {"js", "jsx", "ts", "tsx"}

    def test_extracts_functions(self, js_fixtures: Path):
        source = (js_fixtures / "index.js").read_text()
        result = self.parser.parse(Path("index.js"), source)

        names = [fn.name for fn in result.functions]
        assert "greet" in names
        assert "formatGreeting" in names

    def test_extracts_arrow_functions(self, js_fixtures: Path):
        source = (js_fixtures / "index.js").read_text()
        result = self.parser.parse(Path("index.js"), source)

        names = [fn.name for fn in result.functions]
        assert "processAndGreet" in names

    def test_extracts_class_methods(self, js_fixtures: Path):
        source = (js_fixtures / "helpers.js").read_text()
        result = self.parser.parse(Path("helpers.js"), source)

        methods = [fn for fn in result.functions if fn.class_name == "MathHelper"]
        method_names = [m.name for m in methods]
        assert "add" in method_names
        assert "addAndFormat" in method_names

    def test_extracts_jsdoc(self, js_fixtures: Path):
        source = (js_fixtures / "index.js").read_text()
        result = self.parser.parse(Path("index.js"), source)

        greet_fn = next((fn for fn in result.functions if fn.name == "greet"), None)
        assert greet_fn is not None
        assert greet_fn.docstring is not None
        assert "Greet" in greet_fn.docstring

    def test_extracts_call_edges(self, js_fixtures: Path):
        source = (js_fixtures / "index.js").read_text()
        result = self.parser.parse(Path("index.js"), source)

        greet_calls = [c for c in result.calls if c.caller.name == "greet"]
        callee_names = [c.callee_name for c in greet_calls]
        assert "formatGreeting" in callee_names

    def test_extracts_member_calls(self, js_fixtures: Path):
        source = (js_fixtures / "helpers.js").read_text()
        result = self.parser.parse(Path("helpers.js"), source)

        af_calls = [c for c in result.calls if c.caller.name == "addAndFormat"]
        callee_names = [c.callee_name for c in af_calls]
        assert any("add" in n for n in callee_names)
