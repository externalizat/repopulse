"""Human-facing report renderers share the machine-readable model."""

import re

from rich.console import Console
from rich.table import Table

from repopulse.models import Report


def safe(value: str) -> str:
    """Strip terminal controls from untrusted repository names."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", value)


def terminal(report: Report, console: Console) -> None:
    """Render safely even when redirected to a legacy Windows code page."""

    def printable(value: str) -> str:
        return (
            safe(value).encode(console.encoding, errors="backslashreplace").decode(console.encoding)
        )

    console.print(f"RepoPulse - {report.score:.2f}/100", style="bold cyan", markup=False)
    table = Table("Category", "Score")
    for category, score in report.categories.items():
        table.add_row(category, f"{score:.2f}")
    console.print(table)
    for check in report.checks:
        for finding in check.findings:
            location = f" {finding.file}:{finding.line or '-'}" if finding.file else ""
            console.print(
                printable(f"{finding.severity.upper()} [{check.id}]{location}: {finding.message}"),
                markup=False,
            )
            console.print(printable(f"  -> {finding.recommendation}"), markup=False)
            if finding.snippet:
                console.print(f"  {finding.snippet}", markup=False)
    console.print(
        f"Passed {report.passed}/{len(report.checks)} checks | "
        f"{report.duration_seconds:.3f}s | {report.files_scanned} files | "
        f"{report.skipped_files} skipped",
        markup=False,
    )


def markdown(report: Report) -> str:
    def escape(text: str) -> str:
        import html

        return (
            html.escape(safe(text))
            .replace("|", "&#124;")
            .replace("[", "&#91;")
            .replace("`", "&#96;")
        )

    lines = [
        "# RepoPulse report",
        "",
        f"**Score: {report.score:.2f}/100**",
        "",
        "| Category | Score |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {score:.2f} |" for name, score in report.categories.items())
    lines.extend(["", "## Findings", ""])
    for check in report.checks:
        for finding in check.findings:
            location = f" ({finding.file}:{finding.line or '-'})" if finding.file else ""
            lines.append(
                f"- **{finding.severity.upper()} / {check.id}**{escape(location)}: "
                f"{escape(finding.message)}. {escape(finding.recommendation)}"
                + (f" {finding.snippet}" if finding.snippet else "")
            )
    lines.extend(
        [
            "",
            f"Passed {report.passed}/{len(report.checks)} checks. "
            f"Analyzed {report.files_scanned} files; skipped {report.skipped_files}. "
            f"Duration: {report.duration_seconds:.3f}s.",
            "",
        ]
    )
    return "\n".join(lines)
