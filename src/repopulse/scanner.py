"""Bounded text discovery. No execution, network calls, or symlink traversal."""

import os
from dataclasses import dataclass
from pathlib import Path

from repopulse.config import Config

EXCLUDED = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "virtualenv",
    "__pycache__",
    "build",
    "dist",
    "target",
    "vendor",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".next",
    ".eggs",
}
SOURCE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".cs",
    ".rb",
    ".php",
    ".sh",
    ".swift",
    ".kt",
}


@dataclass(frozen=True)
class Context:
    """Shared immutable scan inputs (paths are relative POSIX strings)."""

    root: Path
    config: Config
    files: dict[str, str]
    skipped: int = 0


def discover(root: Path, config: Config) -> Context:
    """Read UTF-8 text only; surface unreadable filesystem entries as launch errors."""
    files: dict[str, str] = {}
    skipped = 0
    excluded = EXCLUDED | set(config.exclude_dirs)

    def on_error(error: OSError) -> None:
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=on_error):
        base = Path(directory)
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in excluded
            and (base / d).relative_to(root).as_posix() not in excluded
            and not (base / d).is_symlink()
            and (base / d).resolve() == base.resolve() / d
            and not (base / d / "pyvenv.cfg").exists()
        )
        for name in sorted(names):
            path = base / name
            if name == ".git" or path.is_symlink() or not path.is_file():
                skipped += 1
                continue
            with path.open("rb") as handle:
                raw = handle.read(config.max_file_bytes + 1)
            if len(raw) > config.max_file_bytes or b"\x00" in raw:
                skipped += 1
                continue
            try:
                files[path.relative_to(root).as_posix()] = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                skipped += 1
    return Context(root, config, files, skipped)
