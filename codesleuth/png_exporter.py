"""PNG export — converts Mermaid diagrams to PNG using mermaid-cli (mmdc)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def mmdc_available() -> bool:
    """Return True if the ``mmdc`` command is on PATH."""
    return shutil.which("mmdc") is not None


def _extract_mermaid(md_path: Path) -> str:
    """Extract the raw Mermaid code block from a Markdown file."""
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No mermaid code block found in {md_path}")
    return match.group(1)


def export_png(
    md_path: Path,
    png_path: Path | None = None,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Convert a Mermaid Markdown file to PNG.

    Parameters
    ----------
    md_path:
        Path to a ``.md`` file containing a ``mermaid`` code block.
    png_path:
        Output PNG path. Defaults to the same name with ``.png`` extension.
    width:
        Image width in pixels.
    height:
        Image height in pixels.

    Returns
    -------
    Path to the generated PNG file.

    Raises
    ------
    RuntimeError
        If ``mmdc`` is not installed or the conversion fails.
    """
    if not mmdc_available():
        raise RuntimeError(
            "mmdc (mermaid-cli) is not installed.\n"
            "Install it with: npm install -g @mermaid-js/mermaid-cli"
        )

    if png_path is None:
        png_path = md_path.with_suffix(".png")

    mermaid_code = _extract_mermaid(md_path)

    # Write mermaid code to a temp .mmd file.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mmd", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(mermaid_code)
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "mmdc",
            "-i", str(tmp_path),
            "-o", str(png_path),
            "-w", str(width),
            "-H", str(height),
            "-b", "white",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"mmdc failed (exit {result.returncode}):\n{result.stderr}"
            )
    finally:
        tmp_path.unlink(missing_ok=True)

    return png_path


def export_pngs_from_dir(
    md_dir: Path,
    width: int = 1920,
    height: int = 1080,
) -> list[Path]:
    """Convert all component Markdown files in a directory to PNG.

    Skips ``index.md``. Returns paths of generated PNGs.
    """
    pngs: list[Path] = []
    for md_file in sorted(md_dir.glob("component_*.md")):
        png = export_png(md_file, width=width, height=height)
        pngs.append(png)
    return pngs
