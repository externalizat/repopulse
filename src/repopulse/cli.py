"""Typer commands and CI exit semantics."""

import io
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from repopulse.checks import CHECKS
from repopulse.checks.base import WARNING_PENALTIES
from repopulse.config import load_config
from repopulse.engine import scan as analyze
from repopulse.render import markdown, terminal

app = typer.Typer(no_args_is_help=True, help="Offline repository onboarding health checks.")


class Format(StrEnum):
    terminal = "terminal"
    json = "json"
    markdown = "markdown"


@app.command()
def scan(
    path: Annotated[Path, typer.Argument(help="Local repository directory")] = Path("."),
    format: Annotated[Format, typer.Option("--format")] = Format.terminal,
    output: Annotated[Path | None, typer.Option(help="Write report to this file")] = None,
    fail_under: Annotated[float | None, typer.Option(min=0, max=100)] = None,
) -> None:
    """Scan a directory. Exit 1 for secret errors or a score below the threshold."""
    try:
        import math

        if fail_under is not None and not math.isfinite(fail_under):
            raise ValueError("Threshold must be finite")
        config = load_config(path)
        report = analyze(path, config)
        if format == Format.json:
            text = report.model_dump_json(indent=2) + "\n"
        elif format == Format.markdown:
            text = markdown(report)
        else:
            buffer = io.StringIO()
            terminal(report, Console(file=buffer, width=100, force_terminal=False))
            text = buffer.getvalue()
        if output:
            output.write_text(text, encoding="utf-8")
        elif format == Format.terminal:
            terminal(report, Console())
        else:
            typer.echo(text, nl=False)
    except (OSError, ValueError) as exc:
        # Validation exceptions may contain raw TOML values; never echo those values.
        typer.echo(
            f"RepoPulse could not run ({type(exc).__name__}). "
            "Check path, permissions, configuration and output destination.",
            err=True,
        )
        raise typer.Exit(2) from None
    threshold = config.fail_under if fail_under is None else fail_under
    critical = any(f.severity == "error" for c in report.checks for f in c.findings)
    raise typer.Exit(1 if critical or report.score < threshold else 0)


@app.command()
def explain(check: str) -> None:
    """Explain a check by its ID (case insensitive)."""
    for item in CHECKS:
        if item.id == check.upper():
            typer.echo(
                f"{item.id} [{item.category}]: {item.description}\n"
                f"Starts at 100; each warning subtracts {WARNING_PENALTIES.get(item.id, 20)} "
                "and each error subtracts 40 "
                "(floor 0). Info findings do not reduce the score."
            )
            return
    typer.echo("Unknown check. Run repopulse list-checks.", err=True)
    raise typer.Exit(2)


@app.command("list-checks")
def list_checks() -> None:
    """List built-in IDs, categories and purposes."""
    for check in CHECKS:
        typer.echo(f"{check.id:14} {check.category:14} {check.description}")
