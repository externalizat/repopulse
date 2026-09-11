"""Validated repository-local configuration."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

CATEGORIES = {"documentation", "community", "engineering", "maintenance", "security"}


class Config(BaseModel):
    """Limits use bytes and source lines, respectively."""

    model_config = ConfigDict(extra="forbid", strict=True)
    disabled_checks: list[str] = Field(default_factory=list)
    category_weights: dict[str, float] = Field(
        default_factory=lambda: dict.fromkeys(sorted(CATEGORIES), 1.0)
    )
    exclude_dirs: list[str] = Field(default_factory=list)
    max_file_bytes: int = Field(default=1_000_000, ge=1)
    max_source_lines: int = Field(default=500, ge=1)
    fail_under: float = Field(default=0, ge=0, le=100)

    @field_validator("category_weights")
    @classmethod
    def weights(cls, value: dict[str, float]) -> dict[str, float]:
        import math

        if any(k not in CATEGORIES for k in value):
            raise ValueError("Unknown category weight")
        if any(not math.isfinite(v) or v < 0 for v in value.values()):
            raise ValueError("Category weights must be finite and nonnegative")
        merged = dict.fromkeys(sorted(CATEGORIES), 1.0) | value
        if not any(merged.values()):
            raise ValueError("At least one weight must be positive")
        return merged


def load_config(root: Path) -> Config:
    """Load TOML; malformed settings fail explicitly."""
    path = root / ".repopulse.toml"
    if path.is_symlink():
        raise ValueError("Configuration must not be a symbolic link")
    return (
        Config.model_validate(tomllib.loads(path.read_text("utf-8"))) if path.exists() else Config()
    )
