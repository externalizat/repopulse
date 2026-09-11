"""Small extension contract for independent checks."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from repopulse.models import CheckResult, Finding
from repopulse.scanner import Context

WARNING_PENALTIES = {
    "README": 50,
    "ONBOARDING": 50,
    "LICENSE": 100,
    "CONTRIBUTING": 100,
    "CONDUCT": 100,
    "TESTS": 100,
    "CI": 100,
    "DEPENDENCIES": 100,
    "ENV": 100,
    "CHANGELOG": 100,
}


class Check(Protocol):
    id: str
    category: str
    description: str

    def run(self, context: Context) -> CheckResult: ...


@dataclass
class Rule:
    """Adapt a pure finding function to the Check protocol."""

    id: str
    category: str
    description: str
    inspect: Callable[[Context], list[Finding]]

    def run(self, context: Context) -> CheckResult:
        findings = self.inspect(context)
        penalties = {"info": 0, "warning": WARNING_PENALTIES.get(self.id, 20), "error": 40}
        return CheckResult(
            id=self.id,
            category=self.category,
            score=max(0, 100 - sum(penalties[f.severity] for f in findings)),
            findings=findings,
        )
