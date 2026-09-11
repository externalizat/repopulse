# RepoPulse

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Offline analysis](https://img.shields.io/badge/analysis-local_only-purple)

**Find the friction a new contributor will face before they open their first pull request.**

RepoPulse is a local Python CLI that checks repository documentation, engineering
conventions, maintenance signals, and potential credential leaks. It produces an
explainable score from 0 to 100, with file locations and practical next steps.
Repository content stays on your machine. Scans do not execute project code or
contact external services.

## Why RepoPulse?

A project can compile perfectly and still be difficult to join: its README omits
setup steps, environment variables are undocumented, links are stale, and nobody
knows how to run tests. RepoPulse makes these small obstacles visible in one report.
Use it when adopting a repository, preparing a release, or improving contributor
onboarding. A score is a starting point for discussion, not a measure of developer
performance or a guarantee of software quality.

## Features

- Seventeen independent checks with actionable info, warning, and error findings.
- Rich terminal, versioned JSON, and Markdown reports.
- Weighted categories and configurable CI thresholds.
- Static Python, JavaScript/TypeScript, Rust, and Java environment references.
- Markdown file link validation, grouped debt markers, source size and layout checks.
- Conservative credential patterns with fully redacted matched fragments.
- UTF-8 text scanning with hard exclusions, bounded reads, and no symlink traversal.

## Installation

Python 3.11 or newer is required. From a checkout of this repository:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

For development, use `python -m pip install -e ".[dev]"` instead. Installation
downloads dependencies; subsequent scans are offline. This project does not claim
to be published on PyPI. Build a distributable wheel with `python -m build` after
installing the development extras.

## Quick start

```bash
repopulse scan .
repopulse scan examples/sample-project
repopulse scan . --format json
repopulse scan . --format markdown --output report.md
repopulse scan . --fail-under 75
repopulse explain README
repopulse list-checks
```

`python -m repopulse` is equivalent to `repopulse`. Reports are written before the
exit status is set. `--output` overwrites the named file; its parent must exist.
Store reports outside the scanned tree to avoid including old reports in later scans.

Terminal excerpt from the included sample (timings depend on the machine):

```text
RepoPulse - 57.17/100
Category         Score
community         0.00
documentation    32.50
engineering      60.00
maintenance      93.33
security        100.00
WARNING [README] README.md:-: README has fewer than 80 words
  -> Explain purpose, features, and a concrete example.
...
Passed 5/17 checks | 0.004s | 4 files | 0 skipped
```

See the actual generated [sample report](examples/report.md) and
[JSON report](examples/report.json) and [full terminal report](examples/terminal.txt).

## Checks

| ID | Category | What it checks |
| --- | --- | --- |
| README | documentation | Root README, 80-word minimum, purpose/features heading |
| ONBOARDING | documentation | Installation and usage language in Markdown/RST |
| LINKS | documentation | Inline/image/reference-definition relative file links |
| CHANGELOG | documentation | Changelog, changes, or history document |
| LICENSE | community | License, licence, or copying file |
| CONTRIBUTING | community | Contributor guide |
| CONDUCT | community | Code of conduct |
| TESTS | engineering | Conventional test paths and source filenames |
| CI | engineering | GitHub, GitLab, CircleCI, Jenkins, or Azure CI config |
| DEPENDENCIES | engineering | Common ecosystem manifests |
| ENV | engineering | Example environment file when static references exist |
| ENV_DRIFT | engineering | Missing declarations and potentially unused examples |
| PINS | engineering | Exact pins in Python requirements/pyproject and npm manifests |
| TODOS | maintenance | TODO, FIXME, HACK counts grouped by source file |
| LARGE_FILES | maintenance | Source files over the configured line limit |
| STRUCTURE | maintenance | More than 10 root source files or nesting over 8 levels |
| SECRETS | security | AWS IDs, GitHub tokens, private key headers, credential assignments |

## Scoring and exit codes

Each enabled check starts at 100. README and ONBOARDING warnings subtract 50.
Missing LICENSE, CONTRIBUTING, CONDUCT, TESTS, CI, DEPENDENCIES, ENV, or CHANGELOG
subtracts 100 from that check. Other warnings subtract 20; each error subtracts
40; info findings subtract nothing. `explain` shows the penalty for each check.
A check cannot score below zero. Its category
score is the arithmetic mean of enabled checks in that category. The final score
is the weighted mean of active category scores, rounded to two decimal places.
Categories without enabled checks are removed from the denominator. Defaults give
each category equal weight. A passed check has no warning or error findings.

For example, category scores 80 and 100 with weights 3 and 1 yield 85. The threshold
compares the reported rounded score. Disabling checks changes the scope and can
raise the score, so compare repositories only with equivalent configurations.

| Exit | Meaning |
| --- | --- |
| 0 | No error findings and score meets the threshold (default 0) |
| 1 | Score below threshold **or any error finding**, including suspected secrets |
| 2 | Invalid arguments/configuration, inaccessible path, or report write failure |

Warnings alone do not fail a default scan. `--fail-under` overrides the configured
threshold. An error finding fails even at threshold 0 or security weight 0.

## Configuration

RepoPulse reads `.repopulse.toml` from the directory being scanned, not from its
parents. Unknown options and check IDs are errors. IDs are uppercase in TOML.

```toml
disabled_checks = ["PINS"]
exclude_dirs = ["generated", "examples/sample-project"]
max_file_bytes = 1000000
max_source_lines = 500
fail_under = 75

[category_weights]
documentation = 2.0
community = 1.0
engineering = 2.0
maintenance = 1.0
security = 2.0
```

Unspecified category weights stay at 1. Weights must be finite and nonnegative,
with positive total weight across enabled categories. Exclusions match directory
basenames or exact repository-relative POSIX paths; they are not globs. `.git`,
dependency directories, virtual environments and build directories remain excluded
regardless of configuration. `.gitignore` is not interpreted: this deliberately
allows accidentally present `.env` files to be checked. See
[the example configuration](examples/repopulse.example.toml).

Files over `max_file_bytes`, binary/non-UTF-8 files, and symlinked files are counted
as skipped. Excluded directories are pruned without counting their contents. A high
score does not certify skipped content. Raise the byte limit to analyze unusually
large source files; the line check only applies to files actually read.

## Use in GitHub Actions

This example installs RepoPulse from a sibling checkout of its source. Replace
`YOUR_ORG/RepoPulse` and the ref with your actual repository and reviewed commit.

```yaml
name: Repository health
on: [push, pull_request]
permissions:
  contents: read
jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          path: project
      - uses: actions/checkout@v4
        with:
          repository: YOUR_ORG/RepoPulse
          ref: YOUR_REVIEWED_COMMIT
          path: repopulse-tool
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install ./repopulse-tool
      - run: repopulse scan project --fail-under 75 --format markdown --output health.md
```

The project's own [CI workflow](.github/workflows/ci.yml) tests Python 3.11–3.13 on
Linux and Windows and runs Ruff, mypy, packaging, and a demo scan.

## Architecture

```text
src/repopulse/
  cli.py          Typer commands and exit semantics
  config.py       Strict Pydantic/TOML settings
  scanner.py      Bounded, shared text snapshot
  models.py       Finding, CheckResult, Report
  engine.py       Check execution and weighted aggregation
  render.py       Rich and Markdown presentation
  checks/
    base.py       Check protocol and Rule adapter
    __init__.py   Built-in registry
    documentation.py / engineering.py / maintenance.py / security.py
```

To add a check, implement `Check.run(Context) -> CheckResult` (or use the `Rule`
adapter), assign a stable ID and category, then register it in `CHECKS`. Add tests,
document limitations, and never include raw file contents in secret findings.
The engine is also available as `repopulse.engine.scan(Path(...))` for Python use.
JSON includes `schema_version`, scores, findings, passed count, duration, and file counts.

## Development and contributing

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Optional Make targets mirror these commands. See [CONTRIBUTING](CONTRIBUTING.md),
[community expectations](CODE_OF_CONDUCT.md), and [security reporting](SECURITY.md).

## Limitations

Checks are transparent heuristics, not semantic proofs. English README headings
are recognized; other languages may need disabled documentation checks. Test and
CI presence does not establish execution or coverage. License text is not validated.
Environment scanning detects literal names only, merges examples across a monorepo,
and ignores common operating-system variables. It can match comments and miss
dynamic access or framework-specific configuration.

Markdown scanning is intentionally lightweight: it ignores fenced/inline code,
external URLs, site-root links and anchors; it does not implement all CommonMark
syntax, nested-parenthesis destinations, or undefined reference-label validation.
Debt markers may occur in strings. Pin checks inspect declarations, including
optional/dev dependencies, but do not validate lockfiles. Ranges are often correct
for libraries; a lockfile can make an application reproducible despite a warning.
Manifest presence supports more ecosystems than version analysis.

Credential detection can produce false positives and miss secrets. Matches are
fully redacted; no source line is printed. This is not a replacement for a dedicated
secret scanner or security review. Filesystem access is local and read-only, but a
concurrently changing hostile filesystem is not a supported security boundary.

## Roadmap

- Parse Markdown with a full syntax tree and validate local heading anchors.
- Add ecosystem-specific lockfile checks and per-package monorepo scopes.
- Support translated documentation patterns and stable finding baselines.
- Add SARIF output for code-scanning integrations.

## License

[MIT](LICENSE).
