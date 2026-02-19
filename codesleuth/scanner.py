"""File scanner — walks the target directory and delegates to parsers."""

from __future__ import annotations

from pathlib import Path

import pathspec  # type: ignore[import-untyped]

from codesleuth.models import ParseResult
from codesleuth.parsers.registry import ParserRegistry

# Directories that are *always* skipped regardless of .gitignore.
_ALWAYS_SKIP: set[str] = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
}


class FileScanner:
    """Recursively scans a directory tree and parses supported source files."""

    def __init__(
        self,
        root: Path,
        registry: ParserRegistry,
        extra_excludes: list[str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.registry = registry
        self._gitignore_spec = self._load_gitignore()
        self._extra_excludes = extra_excludes or []

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def scan(self) -> list[ParseResult]:
        """Walk the tree, parse each supported file, and return results."""
        results: list[ParseResult] = []

        for file_path in self._iter_files():
            ext = file_path.suffix.lstrip(".")
            parser = self.registry.get_parser(ext)
            if parser is None:
                continue

            try:
                source = file_path.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            rel_path = file_path.relative_to(self.root)
            result = parser.parse(rel_path, source)
            if result.functions or result.calls:
                results.append(result)

        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _iter_files(self):
        """Yield all files under ``self.root`` that aren't excluded."""
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if self._is_excluded(rel):
                continue
            yield path

    def _is_excluded(self, rel_path: Path) -> bool:
        """Check if a path should be skipped."""
        parts = rel_path.parts

        # Check always-skip directory names.
        for part in parts:
            if part in _ALWAYS_SKIP:
                return True

        rel_str = str(rel_path)

        # Extra CLI excludes.
        for pattern in self._extra_excludes:
            if rel_path.match(pattern):
                return True

        # .gitignore rules.
        if self._gitignore_spec and self._gitignore_spec.match_file(rel_str):
            return True

        return False

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """Load .gitignore from the project root, if present."""
        gi = self.root / ".gitignore"
        if not gi.is_file():
            return None
        try:
            lines = gi.read_text().splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", lines)
        except Exception:
            return None
