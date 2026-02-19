"""Tests for the Python AST parser."""

from __future__ import annotations

from pathlib import Path

from codesleuth.parsers.python_parser import PythonParser


class TestPythonParser:
    """Tests for :class:`PythonParser`."""

    def setup_method(self):
        self.parser = PythonParser()

    # ------------------------------------------------------------------
    # Extension support
    # ------------------------------------------------------------------

    def test_supported_extensions(self):
        assert self.parser.supported_extensions() == ["py"]

    # ------------------------------------------------------------------
    # Function extraction
    # ------------------------------------------------------------------

    def test_extracts_top_level_functions(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        names = [fn.name for fn in result.functions]
        assert "greet" in names
        assert "format_greeting" in names

    def test_extracts_class_methods(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        methods = [fn for fn in result.functions if fn.class_name == "Calculator"]
        method_names = [m.name for m in methods]
        assert "add" in method_names
        assert "add_and_greet" in method_names

    def test_extracts_docstrings(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        greet_fn = next(fn for fn in result.functions if fn.name == "greet")
        assert greet_fn.docstring == "Return a greeting string."

    def test_extracts_parameters(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        greet_fn = next(fn for fn in result.functions if fn.name == "greet")
        assert greet_fn.params == ["name"]

    # ------------------------------------------------------------------
    # Call extraction
    # ------------------------------------------------------------------

    def test_extracts_function_calls(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        # greet() calls format_greeting()
        greet_calls = [c for c in result.calls if c.caller.name == "greet"]
        callee_names = [c.callee_name for c in greet_calls]
        assert "format_greeting" in callee_names

    def test_extracts_self_method_calls(self, python_fixtures: Path):
        source = (python_fixtures / "main.py").read_text()
        result = self.parser.parse(Path("main.py"), source)

        # add_and_greet calls self.add and greet
        ag_calls = [c for c in result.calls if c.caller.name == "add_and_greet"]
        callee_names = [c.callee_name for c in ag_calls]
        assert "self.add" in callee_names
        assert "greet" in callee_names

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_handles_syntax_error_gracefully(self):
        result = self.parser.parse(Path("bad.py"), "def broken(:\n  pass")
        assert result.functions == []
        assert result.calls == []

    def test_cross_file_functions(self, python_fixtures: Path):
        source = (python_fixtures / "utils.py").read_text()
        result = self.parser.parse(Path("utils.py"), source)

        names = [fn.name for fn in result.functions]
        assert "reverse_string" in names
        assert "process" in names
