"""Serializable public report schema."""

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error"]


class Finding(BaseModel):
    """An actionable observation; never contains a raw secret."""

    severity: Severity = "warning"
    message: str
    recommendation: str
    file: str | None = None
    line: int | None = None
    snippet: str | None = None


class CheckResult(BaseModel):
    """One check's score and observations."""

    id: str
    category: str
    score: float = Field(ge=0, le=100)
    findings: list[Finding] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.severity != "info" for f in self.findings)


class Report(BaseModel):
    """Versioned machine-readable scan result."""

    schema_version: int = 1
    score: float
    categories: dict[str, float]
    checks: list[CheckResult]
    passed: int
    duration_seconds: float
    files_scanned: int
    skipped_files: int
