"""Tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from codesleuth.cli import main


class TestCLI:
    """Tests for the click CLI."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_help_flag(self):
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "TARGET_DIR" in result.output

    def test_scan_sample_python(self, tmp_path: Path, python_fixtures: Path):
        """Smoke test: scan the sample Python fixtures and produce output."""
        out = tmp_path / "graph.md"
        result = self.runner.invoke(main, [str(python_fixtures), "-o", str(out)])

        assert result.exit_code == 0, result.output
        assert "Scanning" in result.output
        assert "Done!" in result.output
        assert out.exists()
        content = out.read_text()
        assert "```mermaid" in content

    def test_split_mode(self, tmp_path: Path, python_fixtures: Path):
        """--split produces a directory with index.md + component files."""
        out_dir = tmp_path / "output"
        result = self.runner.invoke(main, [
            str(python_fixtures), "-o", str(out_dir), "--split",
        ])

        assert result.exit_code == 0, result.output
        assert "Splitting" in result.output
        assert (out_dir / "index.md").exists()
        # Should have at least the index file.
        md_files = list(out_dir.glob("*.md"))
        assert len(md_files) >= 1

    def test_lr_direction(self, tmp_path: Path, python_fixtures: Path):
        out = tmp_path / "graph.md"
        result = self.runner.invoke(main, [
            str(python_fixtures), "-o", str(out), "--direction", "LR",
        ])
        assert result.exit_code == 0
        content = out.read_text()
        assert "flowchart LR" in content

    def test_include_orphans(self, tmp_path: Path, python_fixtures: Path):
        out = tmp_path / "graph.md"
        result = self.runner.invoke(main, [
            str(python_fixtures), "-o", str(out), "--include-orphans",
        ])
        assert result.exit_code == 0
        assert out.exists()

    def test_exclude_pattern(self, tmp_path: Path, python_fixtures: Path):
        out = tmp_path / "graph.md"
        result = self.runner.invoke(main, [
            str(python_fixtures), "-o", str(out), "--exclude", "utils*",
        ])
        assert result.exit_code == 0
        content = out.read_text()
        # utils.py functions should be excluded from the diagram.
        assert "reverse_string" not in content

    def test_nonexistent_target(self):
        result = self.runner.invoke(main, ["/nonexistent/path"])
        assert result.exit_code != 0
