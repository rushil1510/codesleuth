"""Shared test fixtures for CodeSleuth tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the absolute path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def python_fixtures(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_python"


@pytest.fixture()
def js_fixtures(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_js"
