"""Abstract base class for language-specific parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from codesleuth.models import ParseResult


class BaseParser(ABC):
    """
    Abstract parser interface.

    Each concrete parser handles one or more file extensions and knows how to
    extract function definitions and call sites from a source file.
    """

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return file extensions this parser handles (without leading dot).

        Example: ``['py']`` or ``['js', 'jsx', 'ts', 'tsx']``.
        """
        ...

    @abstractmethod
    def parse(self, file_path: Path, source: str) -> ParseResult:
        """Parse *source* and return extracted functions and calls.

        Parameters
        ----------
        file_path:
            Path of the file relative to the target root (used for labelling).
        source:
            Raw source code content.
        """
        ...
