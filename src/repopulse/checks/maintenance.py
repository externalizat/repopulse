"""Source size, repository layout, and grouped debt markers."""

import re
from pathlib import PurePosixPath

from repopulse.models import Finding
from repopulse.scanner import SOURCE_SUFFIXES, Context


def todos(ctx: Context) -> list[Finding]:
    """Group literal debt markers by source file without printing source text."""
    findings = []
    for path, text in ctx.files.items():
        if PurePosixPath(path).suffix not in SOURCE_SUFFIXES:
            continue
        counts = {
            label: len(re.findall(rf"\b{label}\b", text)) for label in ("TODO", "FIXME", "HACK")
        }
        if any(counts.values()):
            summary = ", ".join(f"{label}: {n}" for label, n in counts.items() if n)
            findings.append(
                Finding(
                    message=f"Debt markers ({summary})",
                    recommendation="Link unfinished work to issues and remove obsolete markers.",
                    file=path,
                )
            )
    return findings


def large_files(ctx: Context) -> list[Finding]:
    """Flag readable source files exceeding the configured line limit."""
    return [
        Finding(
            message=f"Source file has {len(text.splitlines())} lines",
            recommendation="Split responsibilities into focused modules.",
            file=path,
        )
        for path, text in ctx.files.items()
        if PurePosixPath(path).suffix in SOURCE_SUFFIXES
        and len(text.splitlines()) > ctx.config.max_source_lines
    ]


def structure(ctx: Context) -> list[Finding]:
    """Flag coarse layout friction while allowing small flat projects."""
    root_sources = [
        p for p in ctx.files if "/" not in p and PurePosixPath(p).suffix in SOURCE_SUFFIXES
    ]
    findings = []
    if len(root_sources) > 10:
        findings.append(
            Finding(
                message=f"{len(root_sources)} source files in repository root",
                recommendation="Group related modules into a package or src/ directory.",
            )
        )
    if any(len(PurePosixPath(p).parts) > 8 for p in ctx.files):
        findings.append(
            Finding(
                message="Directory nesting exceeds eight levels",
                recommendation="Review deeply nested source layout and document its purpose.",
            )
        )
    if not ctx.files:
        findings.append(
            Finding(
                message="No readable text files discovered",
                recommendation="Check exclusions and add project files.",
            )
        )
    return findings
