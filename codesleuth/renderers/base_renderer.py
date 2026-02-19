"""Abstract base class for graph renderers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from codesleuth.models import CallGraph


class BaseRenderer(ABC):
    """
    Abstract renderer interface.

    Concrete renderers take a :class:`CallGraph` and produce an output file
    (Mermaid markdown, SVG, JSON, etc.).
    """

    @abstractmethod
    def render(self, graph: CallGraph, output_path: Path, **options) -> None:
        """Render *graph* and write the result to *output_path*.

        Parameters
        ----------
        graph:
            The resolved call graph.
        output_path:
            Destination file path.
        **options:
            Renderer-specific options (direction, max label length, etc.).
        """
        ...
