"""Tests for the FileScanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from codesleuth.parsers.python_parser import PythonParser
from codesleuth.parsers.registry import ParserRegistry
from codesleuth.scanner import FileScanner


def _make_registry() -> ParserRegistry:
    reg = ParserRegistry()
    reg.register(PythonParser())
    return reg


class TestFileScanner:
    """Tests for :class:`FileScanner`."""

    def test_discovers_python_files(self, tmp_path: Path):
        """Scanner finds .py files and parses them."""
        (tmp_path / "hello.py").write_text("def greet(): pass\n")
        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].file_path == Path("hello.py")
        names = [fn.name for fn in results[0].functions]
        assert "greet" in names

    def test_ignores_unsupported_extensions(self, tmp_path: Path):
        """Non-supported files (e.g. .txt) are silently skipped."""
        (tmp_path / "notes.txt").write_text("not code")
        (tmp_path / "app.py").write_text("def run(): pass\n")
        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].file_path == Path("app.py")

    def test_skips_always_skip_dirs(self, tmp_path: Path):
        """Directories in _ALWAYS_SKIP (e.g. __pycache__) are excluded."""
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "mod.py").write_text("def cached(): pass\n")

        (tmp_path / "main.py").write_text("def main(): pass\n")
        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        file_paths = [r.file_path for r in results]
        assert Path("main.py") in file_paths

    def test_extra_excludes(self, tmp_path: Path):
        """CLI --exclude patterns filter out matching files."""
        (tmp_path / "app.py").write_text("def app(): pass\n")
        (tmp_path / "test_app.py").write_text("def test_it(): pass\n")

        scanner = FileScanner(tmp_path, _make_registry(), extra_excludes=["test_*"])
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].file_path == Path("app.py")

    def test_respects_gitignore(self, tmp_path: Path):
        """Files matching .gitignore patterns are excluded."""
        (tmp_path / ".gitignore").write_text("generated/\n")
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir()
        (gen_dir / "auto.py").write_text("def auto(): pass\n")

        (tmp_path / "src.py").write_text("def src(): pass\n")
        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].file_path == Path("src.py")

    def test_handles_nested_dirs(self, tmp_path: Path):
        """Scanner recurses into subdirectories."""
        sub = tmp_path / "pkg" / "sub"
        sub.mkdir(parents=True)
        (sub / "deep.py").write_text("def deep(): pass\n")

        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        assert "deep" in [fn.name for fn in results[0].functions]

    def test_empty_directory(self, tmp_path: Path):
        """Empty directories produce no results."""
        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()
        assert results == []

    def test_skips_node_modules(self, tmp_path: Path):
        """node_modules is always excluded."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "lib.py").write_text("def lib(): pass\n")
        (tmp_path / "app.py").write_text("def app(): pass\n")

        scanner = FileScanner(tmp_path, _make_registry())
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].file_path == Path("app.py")
