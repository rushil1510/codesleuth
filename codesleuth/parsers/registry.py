"""Registry that maps file extensions to parser instances."""

from __future__ import annotations

from codesleuth.parsers.base_parser import BaseParser


class ParserRegistry:
    """Maintains a mapping from file extension → :class:`BaseParser` instance.

    Usage::

        registry = ParserRegistry()
        registry.register(PythonParser())
        parser = registry.get_parser("py")
    """

    def __init__(self) -> None:
        self._parsers: dict[str, BaseParser] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, parser: BaseParser) -> None:
        """Register a parser for all extensions it supports."""
        for ext in parser.supported_extensions():
            ext = ext.lstrip(".")
            self._parsers[ext] = parser

    def get_parser(self, extension: str) -> BaseParser | None:
        """Return the parser for *extension*, or ``None`` if unsupported."""
        return self._parsers.get(extension.lstrip("."))

    @property
    def supported_extensions(self) -> set[str]:
        """Set of all registered extensions."""
        return set(self._parsers.keys())
