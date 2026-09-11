"""Built-in check registry; append any object implementing Check to extend it."""

from repopulse.checks import documentation as docs
from repopulse.checks import engineering as eng
from repopulse.checks import maintenance as maint
from repopulse.checks import security as sec
from repopulse.checks.base import Check, Rule

CHECKS: list[Check] = [
    Rule(
        "README", "documentation", "Root README presence, length and purpose heading", docs.readme
    ),
    Rule("ONBOARDING", "documentation", "Installation and running instructions", docs.onboarding),
    Rule(
        "LICENSE",
        "community",
        "License document presence (not legal validation)",
        lambda c: docs.presence(c, ("license", "licence", "copying"), "license"),
    ),
    Rule(
        "CONTRIBUTING",
        "community",
        "Contributor guide",
        lambda c: docs.presence(c, ("contributing",), "contributing guide"),
    ),
    Rule(
        "CONDUCT",
        "community",
        "Community code of conduct",
        lambda c: docs.presence(c, ("code_of_conduct",), "code of conduct"),
    ),
    Rule("TESTS", "engineering", "Conventionally named test sources", eng.tests),
    Rule("CI", "engineering", "Continuous integration configuration", eng.ci),
    Rule("DEPENDENCIES", "engineering", "Dependency manifest presence", eng.dependencies),
    Rule("ENV", "engineering", "Environment example when variables are used", sec.env_example),
    Rule(
        "ENV_DRIFT", "engineering", "Static environment references versus examples", sec.env_drift
    ),
    Rule("LINKS", "documentation", "Local Markdown file links (not anchors)", docs.links),
    Rule("TODOS", "maintenance", "TODO, FIXME and HACK grouped by source file", maint.todos),
    Rule("LARGE_FILES", "maintenance", "Source line limit", maint.large_files),
    Rule("STRUCTURE", "maintenance", "Root clutter and deep nesting", maint.structure),
    Rule(
        "CHANGELOG",
        "documentation",
        "Change history",
        lambda c: docs.presence(c, ("changelog", "changes", "history"), "changelog"),
    ),
    Rule("PINS", "engineering", "Exact Python and npm dependency version declarations", eng.pins),
    Rule("SECRETS", "security", "Masked credential heuristics", sec.secrets),
]
