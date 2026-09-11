"""Single analysis entry point with category-normalized scoring."""

from pathlib import Path
from time import perf_counter

from repopulse.checks import CHECKS
from repopulse.config import Config, load_config
from repopulse.models import Report
from repopulse.scanner import discover


def scan(root: Path, config: Config | None = None) -> Report:
    """Analyze a local directory without executing any repository code."""
    start = perf_counter()
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Scan path must be a directory")
    config = config or load_config(root)
    unknown = set(config.disabled_checks) - {c.id for c in CHECKS}
    if unknown:
        raise ValueError(f"Unknown disabled checks: {', '.join(sorted(unknown))}")
    active = [c for c in CHECKS if c.id not in config.disabled_checks]
    if not active:
        raise ValueError("At least one check must be enabled")
    context = discover(root, config)
    results = [c.run(context) for c in active]
    categories = {
        category: sum(r.score for r in results if r.category == category)
        / sum(r.category == category for r in results)
        for category in sorted({r.category for r in results})
    }
    weights = config.category_weights
    denominator = sum(weights[c] for c in categories)
    if not denominator:
        raise ValueError("Enabled categories must have positive total weight")
    score = sum(categories[c] * weights[c] for c in categories) / denominator
    return Report(
        score=round(score, 2),
        categories={k: round(v, 2) for k, v in categories.items()},
        checks=results,
        passed=sum(r.passed for r in results),
        duration_seconds=round(perf_counter() - start, 6),
        files_scanned=len(context.files),
        skipped_files=context.skipped,
    )
