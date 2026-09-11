"""Static environment references and masked high-confidence secret patterns."""

import re
from pathlib import PurePosixPath

from repopulse.models import Finding
from repopulse.scanner import SOURCE_SUFFIXES, Context

ENV_PATTERNS = [
    r"""(?:os\.getenv|os\.environ\.get|env::var|std::env::var|System\.getenv)\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']""",
    r"""(?:os\.environ|process\.env)\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]""",
    r"process\.env\.([A-Za-z_][A-Za-z0-9_]*)",
]
BUILTINS = {"PATH", "HOME", "USER", "SHELL", "TMPDIR", "TEMP", "CI", "NODE_ENV", "PYTHONPATH"}


def env_references(ctx: Context) -> set[str]:
    """Extract static literal environment names in supported languages."""
    return {
        match
        for p, text in ctx.files.items()
        if PurePosixPath(p).suffix in SOURCE_SUFFIXES
        for pattern in ENV_PATTERNS
        for match in re.findall(pattern, text)
    } - BUILTINS


def env_example(ctx: Context) -> list[Finding]:
    """Require a template only when application environment references exist."""
    present = any(
        PurePosixPath(p).name in {".env.example", ".env.sample", ".env.template"} for p in ctx.files
    )
    if env_references(ctx) and not present:
        return [
            Finding(
                message="Environment variables used without an example file",
                recommendation="Add .env.example with placeholders and descriptions.",
            )
        ]
    return []


def env_drift(ctx: Context) -> list[Finding]:
    """Compare the repository-wide union of examples and static references."""
    examples = [
        text
        for p, text in ctx.files.items()
        if PurePosixPath(p).name in {".env.example", ".env.sample", ".env.template"}
    ]
    if not examples:
        return []  # ENV already explains the missing template.
    declared = {
        name
        for text in examples
        for name in re.findall(r"(?m)^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", text)
    } - BUILTINS
    used = env_references(ctx)
    findings = [
        Finding(
            message=f"Environment variable {name} missing from examples",
            recommendation="Document the variable with a safe placeholder.",
        )
        for name in sorted(used - declared)
    ]
    findings.extend(
        Finding(
            severity="info",
            message=f"Example variable {name} has no detected code reference",
            recommendation="Check scripts and deployment settings before removing it.",
        )
        for name in sorted(declared - used)
    )
    return findings


SECRET_PATTERNS = {
    "AWS access key ID": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b|\bgithub_pat_[A-Za-z0-9_]{40,255}\b",
    "Private key header": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "Credential assignment": (
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|password)\b"
        r"""\s*[:=]\s*["']([^"'\s]{16,})["']"""
    ),
}


def secrets(ctx: Context) -> list[Finding]:
    """Return locations and types only; redact every matched fragment entirely."""
    findings = []
    for path, text in ctx.files.items():
        for label, pattern in SECRET_PATTERNS.items():
            for match in re.finditer(pattern, text):
                value = match[1] if match.lastindex else match[0]
                if label == "Credential assignment" and (
                    any(
                        word in value.lower()
                        for word in ("example", "placeholder", "changeme", "your_", "${")
                    )
                    or len(set(value)) < 6
                    or not (re.search(r"[A-Za-z]", value) and re.search(r"\d", value))
                ):
                    continue
                findings.append(
                    Finding(
                        severity="error",
                        message=f"Potential {label}",
                        recommendation=(
                            "Verify locally; if real, revoke or rotate it "
                            "and remove it from history."
                        ),
                        file=path,
                        line=text.count("\n", 0, match.start()) + 1,
                        snippet="[REDACTED]",
                    )
                )
    return findings
