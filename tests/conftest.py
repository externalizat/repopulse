"""Small on-disk repository fixtures."""

import shutil
from pathlib import Path

import pytest

from repopulse.config import Config
from repopulse.scanner import Context


@pytest.fixture
def healthy(tmp_path: Path) -> Path:
    shutil.copytree(Path(__file__).parent / "fixtures" / "healthy", tmp_path, dirs_exist_ok=True)
    return tmp_path


@pytest.fixture
def context(tmp_path: Path):
    def make(files: dict[str, str], **kwargs) -> Context:
        for name, text in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return Context(tmp_path, Config(**kwargs), files)

    return make
