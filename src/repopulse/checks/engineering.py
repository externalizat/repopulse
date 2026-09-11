"""Tests, CI, manifests and conservative version pinning checks."""

import json
import re
import tomllib
from pathlib import PurePosixPath

from packaging.requirements import InvalidRequirement, Requirement

from repopulse.models import Finding
from repopulse.scanner import SOURCE_SUFFIXES, Context

MANIFESTS = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "composer.json",
}


def tests(ctx: Context) -> list[Finding]:
    """Recognize conventional source test names and directories."""
    paths = [PurePosixPath(p) for p in ctx.files]
    found = any(
        p.suffix in SOURCE_SUFFIXES
        and (
            p.name.startswith("test_")
            or p.name.endswith(
                ("_test.go", "_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js")
            )
            or "tests" in p.parts
            or "__tests__" in p.parts
        )
        for p in paths
    )
    return (
        []
        if found
        else [
            Finding(
                message="No test source files detected",
                recommendation="Add tests under tests/ or use conventional test filenames.",
            )
        ]
    )


def ci(ctx: Context) -> list[Finding]:
    """Detect supported CI configuration locations."""
    found = any(
        (p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml")))
        or p in {".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml", "azure-pipelines.yml"}
        for p in ctx.files
    )
    return (
        []
        if found
        else [
            Finding(
                message="CI configuration missing",
                recommendation="Run tests and static checks on pull requests.",
            )
        ]
    )


def dependencies(ctx: Context) -> list[Finding]:
    """Detect common manifests, without claiming dependency resolution."""
    return (
        []
        if any(
            PurePosixPath(p).name in MANIFESTS
            or PurePosixPath(p).name.startswith("requirements")
            and p.endswith(".txt")
            for p in ctx.files
        )
        else [
            Finding(
                message="No dependency manifest detected",
                recommendation=(
                    "Document dependencies in an ecosystem manifest, "
                    "or explain that none are needed."
                ),
            )
        ]
    )


def pins(ctx: Context) -> list[Finding]:
    """Count non-exact Python and npm declarations once per manifest."""
    findings = []
    for path, text in ctx.files.items():
        name = PurePosixPath(path).name
        unpinned = 0
        try:
            requirements: list[str] = []
            if name.startswith("requirements") and name.endswith(".txt"):
                requirements = [
                    line.split(" #", 1)[0].strip()
                    for line in text.splitlines()
                    if line.strip() and not line.lstrip().startswith(("#", "-"))
                ]
            elif name == "pyproject.toml":
                project = tomllib.loads(text).get("project", {})
                requirements = project.get("dependencies", [])
                for group in project.get("optional-dependencies", {}).values():
                    requirements.extend(group)
            elif name == "package.json":
                data = json.loads(text)
                if not isinstance(data, dict):
                    raise ValueError("Manifest must be an object")
                for group in ("dependencies", "devDependencies"):
                    values = data.get(group, {})
                    if not isinstance(values, dict):
                        raise ValueError("Dependencies must be an object")
                    unpinned += sum(
                        not bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[\w.-]+)?", str(v)))
                        for v in values.values()
                    )
            for raw in requirements:
                req = Requirement(raw)
                if not any(
                    s.operator in {"==", "==="} and "*" not in s.version for s in req.specifier
                ):
                    unpinned += 1
        except (ValueError, TypeError, AttributeError, InvalidRequirement):
            findings.append(
                Finding(
                    message="Cannot parse dependency manifest",
                    recommendation="Validate the manifest and its dependency declarations.",
                    file=path,
                )
            )
            continue
        if unpinned:
            findings.append(
                Finding(
                    message=f"{unpinned} dependencies lack exact version pins",
                    recommendation=(
                        "For applications, commit a lockfile and use frozen installs. "
                        "Library version ranges may be intentional."
                    ),
                    file=path,
                )
            )
    return findings
