# Contributing

Install Python 3.11+ and create a virtual environment. Run
`python -m pip install -e ".[dev]"` from the repository root.

Before submitting a pull request, run:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build
repopulse scan examples/sample-project
```

Keep checks independent: use the shared Context snapshot instead of reading files
again, invoking subprocesses, or making network requests. Register a stable check
ID, explain the heuristic in README, and test both expected findings and likely
false positives. Any schema or scoring change needs a changelog entry.

Use synthetic test credentials constructed from fragments; never commit real tokens.
Secret findings must never expose the matching value or surrounding source line.
Add filesystem tests for changes to discovery and CLI tests for exit behavior.

Open a bug report with the CLI command, Python/OS version, sanitized output, and a
minimal reproduction. Feature proposals should describe the onboarding problem and
false-positive tradeoffs. Small focused pull requests are easier to review. Follow
the [code of conduct](CODE_OF_CONDUCT.md).
