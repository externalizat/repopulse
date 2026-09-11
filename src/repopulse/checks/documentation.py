"""Documentation presence, onboarding sections, and local Markdown links."""

import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from repopulse.models import Finding
from repopulse.scanner import Context


def readme_path(ctx: Context) -> str | None:
    """Locate a conventional root README without case sensitivity."""
    return next((p for p in ctx.files if p.lower() in {"readme", "readme.md", "readme.rst"}), None)


def readme(ctx: Context) -> list[Finding]:
    """Assess minimum README detail and recognizable English headings."""
    path = readme_path(ctx)
    if path is None:
        return [
            Finding(
                message="Root README missing",
                recommendation="Add a README describing purpose and usage.",
            )
        ]
    text = ctx.files[path]
    missing = []
    if len(text.split()) < 80:
        missing.append("README has fewer than 80 words")
    if not re.search(r"(?im)^#+\s+.*(feature|overview|about|purpose)", text):
        missing.append("No purpose or features heading detected")
    return [
        Finding(
            message=m,
            recommendation="Explain purpose, features, and a concrete example.",
            file=path,
        )
        for m in missing
    ]


def onboarding(ctx: Context) -> list[Finding]:
    """Look for setup and execution instructions across documentation."""
    paths = [p for p in ctx.files if p.lower().endswith((".md", ".rst")) or p == readme_path(ctx)]
    text = "\n".join(ctx.files[p] for p in paths)
    checks = {
        "installation": r"(?i)\b(install(?:ation)?|setup|getting started)\b",
        "running": r"(?i)\b(usage|quick.?start|running|how to run)\b",
    }
    return [
        Finding(
            message=f"No {label} instructions detected",
            recommendation=f"Document {label} with copyable commands.",
        )
        for label, pattern in checks.items()
        if not re.search(pattern, text)
    ]


def presence(ctx: Context, stems: tuple[str, ...], label: str) -> list[Finding]:
    """Find a community document in root, docs, or GitHub metadata."""
    if any(
        PurePosixPath(p).stem.lower() in stems or PurePosixPath(p).name.lower() in stems
        for p in ctx.files
        if "/" not in p or p.startswith((".github/", "docs/"))
    ):
        return []
    return [Finding(message=f"{label} missing", recommendation=f"Add a {label} document.")]


def links(ctx: Context) -> list[Finding]:
    """Validate simple Markdown destinations without reading linked files."""
    findings = []
    for path, text in ctx.files.items():
        if not path.lower().endswith(".md"):
            continue
        # Preserve line numbers while ignoring fenced code examples.
        text = re.sub(
            r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1[^\n]*",
            lambda m: "\n" * str(m[0]).count("\n"),
            text,
        )
        for number, line in enumerate(text.splitlines(), 1):
            line = re.sub(r"`[^`]*`", "", line)
            targets = re.findall(r"\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", line)
            targets += re.findall(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", line)
            for raw in targets:
                try:
                    url = urlsplit(raw.strip("<>"))
                except ValueError:
                    continue
                if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                    continue
                target = ctx.root / PurePosixPath(path).parent / unquote(url.path)
                resolved = target.resolve()
                outside = not resolved.is_relative_to(ctx.root)
                if outside or not target.exists():
                    findings.append(
                        Finding(
                            message="Relative Markdown link escapes repository"
                            if outside
                            else "Broken relative Markdown link",
                            recommendation="Update the link to an existing repository file.",
                            file=path,
                            line=number,
                        )
                    )
    return findings
